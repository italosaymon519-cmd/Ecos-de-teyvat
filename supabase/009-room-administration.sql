-- Administração da campanha. Execute depois das atualizações 002–008.
-- Não apaga fichas, mapas, rolagens ou marcadores.
begin;
create or replace function public.rotate_campaign_invite(target_room uuid) returns text
language plpgsql security definer set search_path='' as $$
declare code text;
begin
 perform 1 from public.campaign_rooms where id=target_room for update;
 if not public.is_campaign_gm(target_room) then raise exception 'Somente o mestre pode renovar convites.'; end if;
 update public.campaign_rooms set invite_code=upper(replace(gen_random_uuid()::text,'-','')) where id=target_room returning invite_code into code;
 return code;
end; $$;

create or replace function public.transfer_campaign_character(target_room uuid,character_id uuid,new_owner uuid,expected_revision bigint) returns jsonb
language plpgsql security definer set search_path='' as $$
declare sheet public.campaign_characters;
begin
 perform 1 from public.campaign_rooms where id=target_room for update;
 if not public.is_campaign_gm(target_room) then raise exception 'Somente o mestre pode transferir fichas.'; end if;
 if not exists(select 1 from public.campaign_members where room_id=target_room and user_id=new_owner) then raise exception 'Escolha um participante desta sala.'; end if;
 select * into sheet from public.campaign_characters where room_id=target_room and id=character_id and not deleted for update;
 if sheet.id is null then raise exception 'Ficha não encontrada nesta sala.'; end if;
 if sheet.revision<>expected_revision then raise exception 'A ficha mudou. Atualize antes de transferir.' using errcode='40001'; end if;
 if sheet.owner_id=new_owner then return to_jsonb(sheet); end if;
 update public.campaign_characters set owner_id=new_owner,revision=revision+1,updated_at=now() where room_id=target_room and id=character_id returning * into sheet;
 update public.campaign_tokens set owner_id=case when kind='character' then new_owner else null end where room_id=target_room and campaign_tokens.character_id=sheet.id;
 return to_jsonb(sheet);
end; $$;

create or replace function public.remove_campaign_member(target_room uuid,member_id uuid) returns text
language plpgsql security definer set search_path='' as $$
declare master_id uuid; code text;
begin
 select gm_id into master_id from public.campaign_rooms where id=target_room for update;
 if master_id is distinct from auth.uid() then raise exception 'Somente o mestre pode remover participantes.'; end if;
 if member_id=master_id then raise exception 'O mestre não pode ser removido.'; end if;
 if not exists(select 1 from public.campaign_members where room_id=target_room and user_id=member_id) then raise exception 'Participante não encontrado nesta sala.'; end if;
 -- Preserva as fichas, inclusive arquivadas. Tokens ativos passam ao mestre.
 update public.campaign_characters set owner_id=master_id,revision=revision+1,updated_at=now() where room_id=target_room and owner_id=member_id;
 update public.campaign_tokens t set character_id=null,owner_id=null where t.room_id=target_room and exists(select 1 from public.campaign_characters c where c.room_id=t.room_id and c.id=t.character_id and c.deleted);
 update public.campaign_tokens t set owner_id=case when t.kind='character' then c.owner_id else null end from public.campaign_characters c where t.room_id=target_room and c.room_id=t.room_id and c.id=t.character_id and not c.deleted and t.owner_id is distinct from (case when t.kind='character' then c.owner_id else null end);
 update public.campaign_tokens set owner_id=null where room_id=target_room and owner_id=member_id;
 delete from public.campaign_presence where room_id=target_room and user_id=member_id;
 delete from public.campaign_members where room_id=target_room and user_id=member_id;
 -- O convite antigo não permite que o participante removido volte sozinho.
 code:=public.rotate_campaign_invite(target_room);
 return code;
end; $$;
-- Serializa entrada/presença com remoção e renovação para evitar corridas.
create or replace function public.join_campaign_room(code text, member_name text) returns uuid
language plpgsql security definer set search_path='' as $$
declare target uuid;
begin
 if auth.uid() is null then raise exception 'Entre na sua conta.'; end if;
 if char_length(trim(member_name)) not between 1 and 60 then raise exception 'Nome inválido.'; end if;
 select id into target from public.campaign_rooms where invite_code=upper(trim(code)) for update;
 if target is null then raise exception 'Convite inválido.'; end if;
 insert into public.campaign_members(room_id,user_id,display_name) values(target,auth.uid(),trim(member_name)) on conflict(room_id,user_id) do update set display_name=excluded.display_name;
 return target;
end; $$;
create or replace function public.campaign_heartbeat(target_room uuid,session_id uuid) returns void
language plpgsql security definer set search_path='' as $$
begin
 perform 1 from public.campaign_rooms where id=target_room for update;
 if not public.is_campaign_member(target_room) then raise exception 'Entre na sala.'; end if;
 delete from public.campaign_presence p where p.room_id=target_room and p.last_seen<now()-interval '1 day';
 insert into public.campaign_presence(room_id,user_id,session_id) values(target_room,auth.uid(),campaign_heartbeat.session_id) on conflict on constraint campaign_presence_pkey do update set last_seen=now();
end; $$;
revoke all on function public.join_campaign_room(text,text),public.campaign_heartbeat(uuid,uuid) from public,anon;
grant execute on function public.join_campaign_room(text,text),public.campaign_heartbeat(uuid,uuid) to authenticated;
revoke all on function public.rotate_campaign_invite(uuid),public.transfer_campaign_character(uuid,uuid,uuid,bigint),public.remove_campaign_member(uuid,uuid) from public,anon;
grant execute on function public.rotate_campaign_invite(uuid),public.transfer_campaign_character(uuid,uuid,uuid,bigint),public.remove_campaign_member(uuid,uuid) to authenticated;
commit;
