-- Executar após 002 e 004. Pode ser repetido; preserva os dados existentes.
begin;
create table if not exists public.campaign_rolls (
 seq bigint generated always as identity primary key,
 id uuid not null,
 room_id uuid not null references public.campaign_rooms(id) on delete cascade,
 actor_id uuid not null references auth.users(id),
 actor_name text not null,
 character_id uuid,
 character_name text,
 kind text not null check(kind in ('dice','skill','resistance','damage','vision')),
 detail text not null check(char_length(detail) between 1 and 2500),
 total integer not null check(total between -999999 and 999999),
 created_at timestamptz not null default now(),
 unique(room_id,id)
);
create index if not exists campaign_rolls_room_sequence on public.campaign_rolls(room_id,seq desc);
alter table public.campaign_rolls enable row level security;
revoke all on public.campaign_rolls from public,anon,authenticated;
grant select on public.campaign_rolls to authenticated;
drop policy if exists rolls_read on public.campaign_rolls;
create policy rolls_read on public.campaign_rolls for select to authenticated using(public.is_campaign_member(room_id));
create or replace function public.record_campaign_roll(target_room uuid,roll_id uuid,payload jsonb) returns jsonb
language plpgsql security definer set search_path='' as $$
declare nickname text; sheet public.campaign_characters; saved public.campaign_rolls; linked_id uuid;
begin
 select display_name into nickname from public.campaign_members where room_id=target_room and user_id=auth.uid();
 if nickname is null or roll_id is null then raise exception 'Entre na sala para compartilhar rolagens.'; end if;
 -- Serializa por sala: a sequência acompanha a ordem de confirmação e repetições não duplicam resultados.
 perform id from public.campaign_rooms where id=target_room for update;
 select * into saved from public.campaign_rolls where room_id=target_room and id=roll_id;
 if found then
  if saved.actor_id<>auth.uid() then raise exception 'Identificador de rolagem já utilizado.'; end if;
  return to_jsonb(saved);
 end if;
 if jsonb_typeof(payload) is distinct from 'object' or coalesce(payload->>'kind','') not in ('dice','skill','resistance','damage','vision') or jsonb_typeof(payload->'detail') is distinct from 'string' or char_length(payload->>'detail') not between 1 and 2500 or jsonb_typeof(payload->'total') is distinct from 'number' then raise exception 'Rolagem inválida.'; end if;
 if (payload->>'total')::numeric not between -999999 and 999999 or (payload->>'total')::numeric<>trunc((payload->>'total')::numeric) then raise exception 'Resultado inválido.'; end if;
 linked_id:=nullif(payload->>'character_id','')::uuid;
 if linked_id is not null then
  select * into sheet from public.campaign_characters where room_id=target_room and id=linked_id and not deleted;
  if sheet.id is null or (sheet.owner_id<>auth.uid() and not public.is_campaign_gm(target_room)) then raise exception 'Somente o dono ou o mestre pode rolar por esta ficha.'; end if;
 end if;
 insert into public.campaign_rolls(id,room_id,actor_id,actor_name,character_id,character_name,kind,detail,total)
 values(roll_id,target_room,auth.uid(),nickname,linked_id,sheet.data->>'name',payload->>'kind',payload->>'detail',(payload->>'total')::integer) returning * into saved;
 return to_jsonb(saved);
end; $$;
revoke all on function public.record_campaign_roll(uuid,uuid,jsonb) from public,anon;
grant execute on function public.record_campaign_roll(uuid,uuid,jsonb) to authenticated;

do $$begin
 if not exists(select 1 from pg_constraint where conname='campaign_character_conditions_valid' and conrelid='public.campaign_characters'::regclass) then
  alter table public.campaign_characters add constraint campaign_character_conditions_valid check(not(data ? 'conditions') or (jsonb_typeof(data->'conditions')='string' and char_length(data->>'conditions')<=300));
 end if;
end;$$;
alter table public.campaign_tokens add column if not exists character_id uuid;
do $$begin
 if not exists(select 1 from pg_constraint where conname='campaign_tokens_character_room_fk' and conrelid='public.campaign_tokens'::regclass) then
  alter table public.campaign_tokens add constraint campaign_tokens_character_room_fk foreign key(room_id,character_id) references public.campaign_characters(room_id,id);
 end if;
end;$$;
create or replace function public.check_campaign_token_sheet() returns trigger
language plpgsql security definer set search_path='' as $$
declare sheet public.campaign_characters;
begin
 if new.character_id is not null then
  select * into sheet from public.campaign_characters where room_id=new.room_id and id=new.character_id and not deleted;
  if sheet.id is null then raise exception 'Escolha uma ficha ativa desta campanha.'; end if;
  new.name:=sheet.data->>'name';
  new.owner_id:=case when new.kind='character' then sheet.owner_id else null end;
 end if;
 return new;
end; $$;
revoke all on function public.check_campaign_token_sheet() from public,anon,authenticated;
drop trigger if exists campaign_token_sheet_check on public.campaign_tokens;
create trigger campaign_token_sheet_check before insert or update of character_id,kind,owner_id on public.campaign_tokens for each row execute function public.check_campaign_token_sheet();
create or replace function public.link_campaign_token(token_id uuid,sheet_id uuid) returns jsonb
language plpgsql security definer set search_path='' as $$
declare token public.campaign_tokens;
begin
 select * into token from public.campaign_tokens where id=token_id for update;
 if token.id is null or not public.is_campaign_gm(token.room_id) then raise exception 'Somente o mestre pode vincular tokens.'; end if;
 update public.campaign_tokens set character_id=sheet_id,owner_id=null,name=coalesce((select data->>'name' from public.campaign_characters where room_id=token.room_id and id=token.character_id),token.name) where id=token_id returning * into token;
 return to_jsonb(token);
end; $$;
revoke all on function public.link_campaign_token(uuid,uuid) from public,anon;
grant execute on function public.link_campaign_token(uuid,uuid) to authenticated;
commit;
