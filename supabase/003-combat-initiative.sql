-- Executar após setup.sql. Preserva salas, imagens e tokens.
begin;
create table if not exists public.campaign_combats (
 room_id uuid primary key references public.campaign_rooms(id) on delete cascade,
 combat_id uuid not null default gen_random_uuid(),
 combatants jsonb not null default '[]'::jsonb,
 active_id uuid,
 round integer not null default 1 check(round>=1),
 running boolean not null default false,
 revision bigint not null default 0,
 updated_at timestamptz not null default now()
);
alter table public.campaign_combats enable row level security;
revoke all on public.campaign_combats from public,anon,authenticated;
grant select on public.campaign_combats to authenticated;
drop policy if exists combat_read on public.campaign_combats;
create policy combat_read on public.campaign_combats for select to authenticated using(public.is_campaign_member(room_id));
create or replace function public.save_campaign_combat(target_room uuid, expected_revision bigint, payload jsonb) returns jsonb
language plpgsql security definer set search_path='' as $$
declare entry jsonb; entries jsonb; current_row public.campaign_combats; seen text[]:=array[]::text[]; selected_id uuid;
begin
 if not public.is_campaign_gm(target_room) then raise exception 'Somente o mestre pode controlar o combate.'; end if;
 if jsonb_typeof(payload->'combatants') is distinct from 'array' or jsonb_typeof(payload->'running') is distinct from 'boolean' or jsonb_typeof(payload->'round') is distinct from 'number' then raise exception 'Dados de combate inválidos.'; end if;
 if jsonb_array_length(payload->'combatants')>200 or (payload->>'round')::numeric not between 1 and 1000000 or (payload->>'round')::numeric<>trunc((payload->>'round')::numeric) then raise exception 'Limite do combate excedido.'; end if;
 perform (payload->>'combat_id')::uuid;
 if payload->>'combat_id' is null then raise exception 'Identificação de combate ausente.'; end if;
 entries:='[]'::jsonb;
 for entry in select value from jsonb_array_elements(payload->'combatants') loop
  if jsonb_typeof(entry->'id') is distinct from 'string' or jsonb_typeof(entry->'name') is distinct from 'string' or char_length(trim(entry->>'name')) not between 1 and 80 or jsonb_typeof(entry->'initiative') is distinct from 'number' or jsonb_typeof(entry->'bonus') is distinct from 'number' or jsonb_typeof(entry->'enabled') is distinct from 'boolean' then raise exception 'Participante inválido.'; end if;
  perform (entry->>'id')::uuid;
  if (entry->>'id')=any(seen) then raise exception 'Participantes duplicados.'; end if;
  seen:=array_append(seen,entry->>'id');
  if (entry->>'initiative')::numeric not between -100 and 100 or (entry->>'initiative')::numeric<>trunc((entry->>'initiative')::numeric) or (entry->>'bonus')::numeric not between -30 and 30 or (entry->>'bonus')::numeric<>trunc((entry->>'bonus')::numeric) then raise exception 'Iniciativa ou bônus inválido.'; end if;
  entries:=entries||jsonb_build_array(jsonb_build_object('id',entry->>'id','name',trim(entry->>'name'),'initiative',(entry->>'initiative')::integer,'bonus',(entry->>'bonus')::integer,'enabled',(entry->>'enabled')::boolean));
 end loop;
 selected_id:=nullif(payload->>'active_id','')::uuid;
 if (payload->>'running')::boolean then
  if selected_id is null or not exists(select 1 from jsonb_array_elements(entries) c where c->>'id'=selected_id::text and (c->>'enabled')::boolean) then raise exception 'Selecione um participante ativo.'; end if;
 elsif selected_id is not null then raise exception 'Combate encerrado não pode ter turno ativo.';
 end if;
 insert into public.campaign_combats(room_id) values(target_room) on conflict(room_id) do nothing;
 select * into current_row from public.campaign_combats where room_id=target_room for update;
 if current_row.revision<>expected_revision then raise exception 'O combate foi alterado em outra aba. Atualize e tente novamente.'; end if;
 update public.campaign_combats set combat_id=(payload->>'combat_id')::uuid,combatants=entries,active_id=selected_id,round=(payload->>'round')::integer,running=(payload->>'running')::boolean,revision=revision+1,updated_at=now() where room_id=target_room returning * into current_row;
 return to_jsonb(current_row);
end; $$;
revoke all on function public.save_campaign_combat(uuid,bigint,jsonb) from public,anon;
grant execute on function public.save_campaign_combat(uuid,bigint,jsonb) to authenticated;
commit;
