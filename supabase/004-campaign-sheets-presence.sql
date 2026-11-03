-- Execute depois de setup.sql. Pode ser executado novamente; preserva os dados.
begin;
create table if not exists public.campaign_characters (
 room_id uuid not null references public.campaign_rooms(id) on delete cascade,
 id uuid not null,
 owner_id uuid not null references auth.users(id),
 data jsonb not null,
 deleted boolean not null default false,
 revision bigint not null default 1,
 updated_at timestamptz not null default now(),
 primary key(room_id,id)
);
create table if not exists public.campaign_presence (
 room_id uuid not null references public.campaign_rooms(id) on delete cascade,
 user_id uuid not null references auth.users(id) on delete cascade,
 session_id uuid not null,
 last_seen timestamptz not null default now(),
 primary key(room_id,user_id,session_id)
);
alter table public.campaign_characters enable row level security;
alter table public.campaign_presence enable row level security;
revoke all on public.campaign_characters,public.campaign_presence from public,anon,authenticated;
grant select on public.campaign_characters,public.campaign_presence to authenticated;
drop policy if exists characters_read on public.campaign_characters;
create policy characters_read on public.campaign_characters for select to authenticated using(public.is_campaign_member(room_id));
drop policy if exists presence_read on public.campaign_presence;
create policy presence_read on public.campaign_presence for select to authenticated using(public.is_campaign_member(room_id) and last_seen>now()-interval '90 seconds');
create or replace function public.save_campaign_character(target_room uuid,character_id uuid,expected_revision bigint,payload jsonb) returns jsonb
language plpgsql security definer set search_path='' as $$
declare current_row public.campaign_characters; field text; v numeric;
begin
 if expected_revision is null or expected_revision<0 or character_id is null or not public.is_campaign_member(target_room) then raise exception 'Entre na sala para salvar fichas com uma versão válida.'; end if;
 -- Serializa criação, limite e edição na mesma sala.
 perform id from public.campaign_rooms where id=target_room for update;
 select * into current_row from public.campaign_characters where room_id=target_room and id=character_id for update;
 if found then
  if current_row.owner_id<>auth.uid() and not public.is_campaign_gm(target_room) then raise exception 'Somente o dono ou o mestre pode editar esta ficha.'; end if;
  if current_row.revision<>expected_revision then raise exception using errcode='40001',message='A ficha foi alterada em outra sessão. Escolha qual versão manter.'; end if;
 else
  if expected_revision<>0 or payload is null then raise exception using errcode='40001',message='A ficha mudou. Atualize a mesa.'; end if;
  if (select count(*) from public.campaign_characters where room_id=target_room and not deleted)>=50 then raise exception 'Limite de 50 fichas por campanha.'; end if;
 end if;
 if payload is not null then
  if current_row.deleted and (select count(*) from public.campaign_characters where room_id=target_room and not deleted)>=50 then raise exception 'Limite de 50 fichas por campanha.'; end if;
  if jsonb_typeof(payload) is distinct from 'object' or octet_length(payload::text)>65536 or payload->>'id' is distinct from character_id::text or jsonb_typeof(payload->'name') is distinct from 'string' or char_length(trim(payload->>'name')) not between 1 and 80 or coalesce(payload->>'element','') not in ('Pyro','Hydro','Anemo','Electro','Cryo','Geo','Dendro') then raise exception 'Ficha inválida.'; end if;
  if jsonb_typeof(payload->'attrs') is distinct from 'array' then raise exception 'Atributos inválidos.'; end if;
  if jsonb_array_length(payload->'attrs')<>5 then raise exception 'Informe cinco atributos.'; end if;
  for field in select value::text from jsonb_array_elements(payload->'attrs') loop
   v:=field::numeric; if v not between 0 and 30 or v<>trunc(v) then raise exception 'Atributo inválido.'; end if;
  end loop;
  foreach field in array array['hp','maxHp','ee','eReady','qLong'] loop
   if jsonb_typeof(payload->field) is distinct from 'number' then raise exception 'Recurso inválido: %',field; end if;
   v:=(payload->>field)::numeric; if v<0 or v<>trunc(v) or v>1000000 then raise exception 'Recurso inválido: %',field; end if;
  end loop;
  if (payload->>'maxHp')::numeric not between 1 and 9999 or (payload->>'hp')::numeric>(payload->>'maxHp')::numeric or (payload->>'ee')::numeric>3 or (payload->>'qLong')::numeric>3 or jsonb_typeof(payload->'qShort') is distinct from 'boolean' then raise exception 'PV, EE ou Supremo inválido.'; end if;
  if payload ? 'level' and (jsonb_typeof(payload->'level') is distinct from 'number' or (payload->>'level')::numeric not between 1 and 20 or (payload->>'level')::numeric<>trunc((payload->>'level')::numeric)) then raise exception 'Nível inválido.'; end if;
  if not(payload ? 'mark') or (payload->'mark'<>'null'::jsonb and payload->>'mark' is distinct from payload->>'element') then raise exception 'Marca incompatível com a Visão.'; end if;
  foreach field in array array['skills','talents'] loop
   if jsonb_typeof(payload->field) is distinct from 'string' or (select count(*) from regexp_split_to_table(payload->>field,',') x where trim(x)<>'')>2 then raise exception 'Escolha até duas perícias e dois talentos.'; end if;
  end loop;
 end if;
 if current_row.id is null then
  insert into public.campaign_characters(room_id,id,owner_id,data) values(target_room,character_id,auth.uid(),payload) returning * into current_row;
 else
  update public.campaign_characters set data=coalesce(payload,data),deleted=payload is null,revision=revision+1,updated_at=now() where room_id=target_room and id=character_id returning * into current_row;
 end if;
 return to_jsonb(current_row);
end; $$;
-- Reação é atômica: o jogador controla o segundo participante, a marca do primeiro é consumida.
create or replace function public.react_campaign_characters(target_room uuid,source_id uuid,trigger_id uuid,source_revision bigint,trigger_revision bigint) returns jsonb
language plpgsql security definer set search_path='' as $$
declare a public.campaign_characters; b public.campaign_characters; first_element text; second_element text; compatible boolean;
begin
 if source_revision is null or trigger_revision is null or not public.is_campaign_member(target_room) or source_id=trigger_id then raise exception 'Participantes inválidos.'; end if;
 perform id from public.campaign_rooms where id=target_room for update;
 select * into a from public.campaign_characters where room_id=target_room and id=source_id and not deleted for update;
 select * into b from public.campaign_characters where room_id=target_room and id=trigger_id and not deleted for update;
 if a.id is null or b.id is null or (b.owner_id<>auth.uid() and not public.is_campaign_gm(target_room)) then raise exception 'Escolha seu personagem para realizar a reação.'; end if;
 if a.revision<>source_revision or b.revision<>trigger_revision then raise exception using errcode='40001',message='Uma ficha mudou. Atualize e tente reagir novamente.'; end if;
 first_element:=a.data->>'element'; second_element:=b.data->>'element';
 if a.data->>'mark' is distinct from first_element then raise exception 'O primeiro personagem precisa preparar sua marca.'; end if;
 compatible:=first_element<>second_element and (
 (first_element in ('Anemo','Geo') and second_element in ('Pyro','Hydro','Electro','Cryo')) or
 (second_element in ('Anemo','Geo') and first_element in ('Pyro','Hydro','Electro','Cryo')) or
 (first_element='Pyro' and second_element in ('Hydro','Cryo','Electro','Dendro')) or
 (second_element='Pyro' and first_element in ('Hydro','Cryo','Electro','Dendro')) or
 (first_element='Hydro' and second_element in ('Cryo','Dendro')) or
 (second_element='Hydro' and first_element in ('Cryo','Dendro')) or
 (first_element='Electro' and second_element in ('Cryo','Dendro')) or
 (second_element='Electro' and first_element in ('Cryo','Dendro')));
 if not coalesce(compatible,false) then raise exception 'Combinação elemental inválida.'; end if;
 update public.campaign_characters set data=jsonb_set(jsonb_set(data,'{ee}',to_jsonb(least(3,(data->>'ee')::int+1))),'{mark}','null'::jsonb),revision=revision+1,updated_at=now() where room_id=target_room and id=source_id returning * into a;
 update public.campaign_characters set data=jsonb_set(data,'{ee}',to_jsonb(least(3,(data->>'ee')::int+1))),revision=revision+1,updated_at=now() where room_id=target_room and id=trigger_id returning * into b;
 return jsonb_build_array(to_jsonb(a),to_jsonb(b));
end; $$;
create or replace function public.campaign_heartbeat(target_room uuid,session_id uuid) returns void
language plpgsql security definer set search_path='' as $$
begin
 if not public.is_campaign_member(target_room) then raise exception 'Entre na sala.'; end if;
 delete from public.campaign_presence p where p.room_id=target_room and p.last_seen<now()-interval '1 day';
 insert into public.campaign_presence(room_id,user_id,session_id) values(target_room,auth.uid(),campaign_heartbeat.session_id) on conflict on constraint campaign_presence_pkey do update set last_seen=now();
end; $$;
create or replace function public.leave_campaign_session(target_room uuid,session_id uuid) returns void
language plpgsql security definer set search_path='' as $$
begin
 delete from public.campaign_presence p where p.room_id=target_room and p.user_id=auth.uid() and p.session_id=leave_campaign_session.session_id;
end; $$;
revoke all on function public.save_campaign_character(uuid,uuid,bigint,jsonb),public.react_campaign_characters(uuid,uuid,uuid,bigint,bigint),public.campaign_heartbeat(uuid,uuid),public.leave_campaign_session(uuid,uuid) from public,anon;
grant execute on function public.save_campaign_character(uuid,uuid,bigint,jsonb),public.react_campaign_characters(uuid,uuid,uuid,bigint,bigint),public.campaign_heartbeat(uuid,uuid),public.leave_campaign_session(uuid,uuid) to authenticated;
commit;
