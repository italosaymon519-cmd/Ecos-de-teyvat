-- Depois de 002–009. Backup consistente e restauração isolada, repetível.
begin;
create table if not exists public.campaign_restore_jobs (
 id uuid primary key, source_room uuid not null references public.campaign_rooms(id),
 room_id uuid not null unique references public.campaign_rooms(id) on delete cascade,
 owner_id uuid not null references auth.users(id), completed boolean not null default false
);
alter table public.campaign_restore_jobs enable row level security;
revoke all on public.campaign_restore_jobs from public,anon,authenticated;
create or replace function public.export_campaign_backup(target_room uuid) returns jsonb
language plpgsql security definer set search_path='' as $$
begin
 if not public.is_campaign_gm(target_room) then raise exception 'Somente o mestre pode exportar a campanha.'; end if;
 return jsonb_build_object(
 'name',(select name from public.campaign_rooms where id=target_room),
 'items',coalesce((select jsonb_agg(to_jsonb(t) order by t.id) from public.campaign_items t where room_id=target_room),'[]'),
 'characters',coalesce((select jsonb_agg(to_jsonb(t) order by t.id) from public.campaign_characters t where room_id=target_room),'[]'),
 'tokens',coalesce((select jsonb_agg(to_jsonb(t) order by t.id) from public.campaign_tokens t where room_id=target_room),'[]'),
 'settings',coalesce((select jsonb_agg(to_jsonb(t) order by t.item_id) from public.campaign_map_settings t where room_id=target_room),'[]'),
 'markers',coalesce((select jsonb_agg(to_jsonb(t) order by t.id) from public.campaign_map_markers t where room_id=target_room),'[]'),
 'combat',(select to_jsonb(t) from public.campaign_combats t where room_id=target_room),
 'rolls',coalesce((select jsonb_agg(to_jsonb(t) order by t.seq) from public.campaign_rolls t where room_id=target_room),'[]'));
end; $$;
create or replace function public.prepare_campaign_restore(source_room uuid,job_id uuid,room_name text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare job public.campaign_restore_jobs; target uuid;
begin
 if not public.is_campaign_gm(source_room) or job_id is null then raise exception 'Somente o mestre pode restaurar uma campanha.'; end if;
 -- A mesma tentativa nunca cria duas salas, mesmo se a resposta se perder.
 perform 1 from public.campaign_rooms where id=prepare_campaign_restore.source_room for update;
 select * into job from public.campaign_restore_jobs where id=job_id;
 if found then
  if job.owner_id<>auth.uid() or job.source_room<>prepare_campaign_restore.source_room then raise exception 'Restauração pertence a outra sessão.'; end if;
  return jsonb_build_object('room_id',job.room_id,'completed',job.completed);
 end if;
 target:=public.create_campaign_room(room_name,'Mestre');
 insert into public.campaign_restore_jobs(id,source_room,room_id,owner_id) values(job_id,source_room,target,auth.uid());
 return jsonb_build_object('room_id',target,'completed',false);
end; $$;
create or replace function public.finish_campaign_restore(job_id uuid,payload jsonb) returns uuid
language plpgsql security definer set search_path='' as $$
declare job public.campaign_restore_jobs; entry jsonb; sheet jsonb; current_sheet jsonb; battle jsonb; path text; saved jsonb;
begin
 select * into job from public.campaign_restore_jobs where id=job_id for update;
 if job.id is null or job.owner_id<>auth.uid() or not public.is_campaign_gm(job.room_id) then raise exception 'Somente o mestre desta restauração pode concluir.'; end if;
 if job.completed then return job.room_id; end if;
 perform 1 from public.campaign_rooms where id=job.room_id for update;
 if exists(select 1 from public.campaign_items where room_id=job.room_id) or exists(select 1 from public.campaign_characters where room_id=job.room_id) or exists(select 1 from public.campaign_members where room_id=job.room_id and user_id<>auth.uid()) then raise exception 'A sala de destino foi alterada. Inicie uma nova restauração.'; end if;
 if jsonb_typeof(payload) is distinct from 'object' or octet_length(payload::text)>16777216 then raise exception 'Backup inválido ou muito grande.'; end if;
 foreach path in array array['items','characters','tokens','settings','markers','rolls'] loop
  if jsonb_typeof(payload->path) is distinct from 'array' then raise exception 'Coleção inválida: %',path; end if;
 end loop;
 if jsonb_array_length(payload->'items')>500 or jsonb_array_length(payload->'characters')>500 or jsonb_array_length(payload->'tokens')>2000 or jsonb_array_length(payload->'markers')>5000 or jsonb_array_length(payload->'settings')>500 or jsonb_array_length(payload->'rolls')>10000 then raise exception 'Backup excede os limites de restauração.'; end if;
 for entry in select value from jsonb_array_elements(payload->'items') loop
  path:=entry->>'image_path';
  if path is not null and (split_part(path,'/',1)<>job.room_id::text or not exists(select 1 from storage.objects where bucket_id='campaign-images' and name=path)) then raise exception 'Imagem do backup ainda não foi enviada.'; end if;
  insert into public.campaign_items(id,room_id,kind,title,public_text,image_path,visible,is_current)
  values((entry->>'id')::uuid,job.room_id,entry->>'kind',entry->>'title',entry->>'public_text',path,(entry->>'visible')::boolean,(entry->>'is_current')::boolean);
 end loop;
 -- Instala o relógio antes das fichas; a validação preserva o restante dos efeitos.
 battle:=payload->'combat';
 if battle is not null and battle<>'null'::jsonb then
  saved:=public.save_campaign_combat(job.room_id,0,battle||jsonb_build_object('combatants',coalesce((select jsonb_agg(value-'character_id') from jsonb_array_elements(battle->'combatants')),'[]'::jsonb)));
 end if;
 -- Arquivadas primeiro: não contam contra o limite de 50 fichas ativas.
 for entry in select value from jsonb_array_elements(payload->'characters') order by (value->>'deleted')::boolean desc loop
  sheet:=entry->'data';
  current_sheet:=public.save_campaign_character(job.room_id,(entry->>'id')::uuid,0,sheet);
  if (entry->>'deleted')::boolean then perform public.save_campaign_character(job.room_id,(entry->>'id')::uuid,(current_sheet->>'revision')::bigint,null); end if;
 end loop;
 for entry in select value from jsonb_array_elements(payload->'tokens') loop
  if not exists(select 1 from public.campaign_items where room_id=job.room_id and id=(entry->>'item_id')::uuid and kind='map') then raise exception 'Token sem mapa válido.'; end if;
  insert into public.campaign_tokens(id,room_id,item_id,name,kind,color,owner_id,x,y,size,character_id)
  values((entry->>'id')::uuid,job.room_id,(entry->>'item_id')::uuid,entry->>'name',entry->>'kind',entry->>'color',case when entry->>'kind'='character' then auth.uid() else null end,(entry->>'x')::double precision,(entry->>'y')::double precision,(entry->>'size')::double precision,(entry->>'character_id')::uuid);
 end loop;
 for entry in select value from jsonb_array_elements(payload->'settings') loop
  if not exists(select 1 from public.campaign_items where room_id=job.room_id and id=(entry->>'item_id')::uuid) then raise exception 'Escala fora da sala restaurada.'; end if;
  perform public.save_campaign_map_grid_settings((entry->>'item_id')::uuid,0,entry);
 end loop;
 for entry in select value from jsonb_array_elements(payload->'markers') loop
  if not exists(select 1 from public.campaign_items where room_id=job.room_id and id=(entry->>'item_id')::uuid) then raise exception 'Marcador fora da sala restaurada.'; end if;
  perform public.create_campaign_map_marker((entry->>'item_id')::uuid,(entry->>'id')::uuid,entry);
  update public.campaign_map_markers set creator_name=left(coalesce(entry->>'creator_name','Mestre'),60) where id=(entry->>'id')::uuid and room_id=job.room_id;
 end loop;
 for entry in select value from jsonb_array_elements(payload->'rolls') loop
  insert into public.campaign_rolls(id,room_id,actor_id,actor_name,character_id,character_name,kind,detail,total,created_at)
  values((entry->>'id')::uuid,job.room_id,auth.uid(),left(coalesce(entry->>'actor_name','Mestre'),60),(entry->>'character_id')::uuid,entry->>'character_name',entry->>'kind',entry->>'detail',(entry->>'total')::integer,(entry->>'created_at')::timestamptz);
 end loop;
 if battle is not null and battle<>'null'::jsonb then perform public.save_campaign_combat(job.room_id,(saved->>'revision')::bigint,battle); end if;
 update public.campaign_restore_jobs set completed=true where id=job.id;
 return job.room_id;
end; $$;
revoke all on function public.export_campaign_backup(uuid),public.prepare_campaign_restore(uuid,uuid,text),public.finish_campaign_restore(uuid,jsonb) from public,anon;
grant execute on function public.export_campaign_backup(uuid),public.prepare_campaign_restore(uuid,uuid,text),public.finish_campaign_restore(uuid,jsonb) to authenticated;
create or replace function public.validate_campaign_character_effects() returns trigger
language plpgsql security definer set search_path='' as $$
declare effect jsonb; previous jsonb; normalized jsonb:='[]'; seen text[]:=array[]::text[]; duration integer; remaining integer; battle uuid; round_number integer; active boolean; scope uuid; amount numeric;
begin
 if not(new.data ? 'effects') then return new;end if;
 if jsonb_typeof(new.data->'effects') is distinct from 'array' then raise exception 'Lista de efeitos inválida.';end if;
 if jsonb_array_length(new.data->'effects')>30 then raise exception 'Limite de 30 efeitos por ficha.';end if;
 select combat_id,round,running into battle,round_number,active from public.campaign_combats where room_id=new.room_id;
 active:=coalesce(active,false);round_number:=coalesce(round_number,1);
 for effect in select value from jsonb_array_elements(new.data->'effects') loop
  if jsonb_typeof(effect->'id') is distinct from 'string' or effect->>'id'=any(seen) or jsonb_typeof(effect->'name') is distinct from 'string' or char_length(trim(effect->>'name')) not between 1 and 80 or coalesce(effect->>'kind','') not in ('condition','shield','defense','check','damage') or jsonb_typeof(effect->'amount') is distinct from 'number' then raise exception 'Efeito inválido.';end if;
  perform (effect->>'id')::uuid;seen:=array_append(seen,effect->>'id');amount:=(effect->>'amount')::numeric;
  if amount<>trunc(amount) or (effect->>'kind'='condition' and amount<>0) or (effect->>'kind'='shield' and amount not between 1 and 9999) or (effect->>'kind' in ('defense','check','damage') and (amount=0 or amount not between -30 and 30)) then raise exception 'Valor do efeito inválido.';end if;
  if not(effect ? 'rounds') or (effect->'rounds'<>'null'::jsonb and (jsonb_typeof(effect->'rounds') is distinct from 'number' or (effect->>'rounds')::numeric not between 1 and 100 or (effect->>'rounds')::numeric<>trunc((effect->>'rounds')::numeric))) then raise exception 'Duração inválida.';end if;
  duration:=(effect->>'rounds')::integer;
  -- Atualizações feitas pelo gatilho do relógio já trazem a duração calculada.
  if pg_trigger_depth()>1 then
   remaining:=(effect->>'remaining')::integer;scope:=(effect->>'combatId')::uuid;
  else
   previous:=null;
   if tg_op='UPDATE' then select value into previous from jsonb_array_elements(coalesce(old.data->'effects','[]')) where value->>'id'=effect->>'id';end if;
   if previous is not null then duration:=(previous->>'rounds')::integer;remaining:=(previous->>'remaining')::integer;scope:=(previous->>'combatId')::uuid;
   else remaining:=case when tg_op='INSERT' then coalesce((effect->>'remaining')::integer,duration) else duration end;scope:=case when duration is not null and active then battle else null end;end if;
  end if;
  if duration is null then remaining:=null;scope:=null;
  elsif remaining is null or remaining not between 1 and duration then raise exception 'Duração restante inválida.';end if;
  normalized:=normalized||jsonb_build_array(jsonb_build_object('id',effect->>'id','name',trim(effect->>'name'),'kind',effect->>'kind','amount',amount,'rounds',duration,'remaining',remaining,'combatId',scope));
 end loop;
 new.data:=jsonb_set(new.data,'{effects}',normalized);
 if jsonb_array_length(normalized)=0 then new.data:=new.data-'effectClock';
 elsif pg_trigger_depth()=1 then new.data:=jsonb_set(new.data,'{effectClock}',jsonb_build_object('id',case when active then battle else null end,'round',round_number,'running',active));end if;
 return new;
end;$$;
commit;
