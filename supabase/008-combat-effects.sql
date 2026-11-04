-- Após 003 e 004. Preserva fichas, condições escritas, Visões, artefatos e mapas.
begin;
create or replace function public.campaign_effects_ready() returns boolean language sql stable as $$ select true $$;
revoke all on function public.campaign_effects_ready() from public,anon;
grant execute on function public.campaign_effects_ready() to authenticated;

-- O relógio é aplicado no servidor apenas quando muda a rodada ou o combate.
create or replace function public.advance_character_effects(data jsonb,combat_id uuid,round_number integer,is_running boolean,is_ending boolean) returns jsonb
language plpgsql set search_path='' as $$
declare effect jsonb; result jsonb:='[]'; remaining integer; old_clock jsonb:=data->'effectClock';
begin
 for effect in select value from jsonb_array_elements(coalesce(data->'effects','[]')) loop
  if effect->'rounds'='null'::jsonb then result:=result||jsonb_build_array(effect);continue;end if;
  if is_ending or (is_running and effect->>'combatId' is not null and effect->>'combatId'<>combat_id::text) then continue;end if;
  if not is_running then result:=result||jsonb_build_array(effect);continue;end if;
  remaining:=(effect->>'remaining')::integer;
  if effect->>'combatId'=combat_id::text and old_clock->>'id'=combat_id::text then remaining:=remaining-greatest(0,round_number-(old_clock->>'round')::integer);end if;
  if remaining>0 then result:=result||jsonb_build_array(effect||jsonb_build_object('remaining',remaining,'combatId',combat_id));end if;
 end loop;
 data:=jsonb_set(data,'{effects}',result);
 if jsonb_array_length(result)=0 then return data-'effectClock';end if;
 return jsonb_set(data,'{effectClock}',jsonb_build_object('id',combat_id,'round',round_number,'running',is_running));
end;$$;
revoke all on function public.advance_character_effects(jsonb,uuid,integer,boolean,boolean) from public,anon,authenticated;

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
   else remaining:=duration;scope:=case when duration is not null and active then battle else null end;end if;
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
revoke all on function public.validate_campaign_character_effects() from public,anon,authenticated;
drop trigger if exists campaign_character_effects_validation on public.campaign_characters;
create trigger campaign_character_effects_validation before insert or update of data on public.campaign_characters for each row execute function public.validate_campaign_character_effects();

create or replace function public.tick_campaign_effects() returns trigger
language plpgsql security definer set search_path='' as $$
declare ending boolean:=false;
begin
 if tg_op='INSERT' then if not new.running then return new;end if;
 else
  ending:=old.running and not new.running;
  if not ending and (not new.running or (old.running and old.combat_id=new.combat_id and old.round=new.round)) then return new;end if;
 end if;
 update public.campaign_characters set data=public.advance_character_effects(data,new.combat_id,new.round,new.running,ending),revision=revision+1,updated_at=now()
 where room_id=new.room_id and not deleted and jsonb_array_length(coalesce(data->'effects','[]'))>0;
 return new;
end;$$;
revoke all on function public.tick_campaign_effects() from public,anon,authenticated;
drop trigger if exists campaign_effects_clock on public.campaign_combats;
create trigger campaign_effects_clock after insert or update on public.campaign_combats for each row execute function public.tick_campaign_effects();

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
  if entry->>'character_id' is not null and not exists(select 1 from public.campaign_characters where room_id=target_room and id=(entry->>'character_id')::uuid and not deleted) then raise exception 'Escolha uma ficha ativa desta campanha.';end if;
  entries:=entries||jsonb_build_array(jsonb_build_object('id',entry->>'id','name',trim(entry->>'name'),'initiative',(entry->>'initiative')::integer,'bonus',(entry->>'bonus')::integer,'enabled',(entry->>'enabled')::boolean,'character_id',nullif(entry->>'character_id','')::uuid));
 end loop;
 selected_id:=nullif(payload->>'active_id','')::uuid;
 if (payload->>'running')::boolean then
  if selected_id is null or not exists(select 1 from jsonb_array_elements(entries) c where c->>'id'=selected_id::text and (c->>'enabled')::boolean) then raise exception 'Selecione um participante ativo.'; end if;
 elsif selected_id is not null then raise exception 'Combate encerrado não pode ter turno ativo.';
 end if;
 perform id from public.campaign_rooms where id=target_room for update;
 insert into public.campaign_combats(room_id) values(target_room) on conflict(room_id) do nothing;
 select * into current_row from public.campaign_combats where room_id=target_room for update;
 if current_row.revision<>expected_revision then raise exception 'O combate foi alterado em outra aba. Atualize e tente novamente.'; end if;
 if current_row.running and (payload->>'running')::boolean and current_row.combat_id=(payload->>'combat_id')::uuid and (payload->>'round')::integer<current_row.round then raise exception 'As rodadas deste combate não podem retroceder.';end if;
 update public.campaign_combats set combat_id=(payload->>'combat_id')::uuid,combatants=entries,active_id=selected_id,round=(payload->>'round')::integer,running=(payload->>'running')::boolean,revision=revision+1,updated_at=now() where room_id=target_room returning * into current_row;
 return to_jsonb(current_row);
end; $$;
revoke all on function public.save_campaign_combat(uuid,bigint,jsonb) from public,anon;
grant execute on function public.save_campaign_combat(uuid,bigint,jsonb) to authenticated;
commit;
