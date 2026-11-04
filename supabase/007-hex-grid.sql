-- Executar após 006. Preserva escalas, marcadores e mapas existentes.
begin;
alter table public.campaign_map_settings add column if not exists grid_type text not null default 'square';
do $$begin
 if not exists(select 1 from pg_constraint where conname='campaign_map_grid_type_valid' and conrelid='public.campaign_map_settings'::regclass) then
  alter table public.campaign_map_settings add constraint campaign_map_grid_type_valid check(grid_type in ('square','hex'));
 end if;
end;$$;
create or replace function public.save_campaign_map_grid_settings(map_id uuid,expected_revision bigint,payload jsonb) returns jsonb
language plpgsql security definer set search_path='' as $$
declare target_room uuid; current_row public.campaign_map_settings;
begin
 select room_id into target_room from public.campaign_items where id=map_id and kind='map' and image_path is not null;
 if target_room is null or not public.is_campaign_gm(target_room) then raise exception 'Somente o mestre pode configurar a escala do mapa.'; end if;
 if coalesce(payload->>'grid_type','') not in ('square','hex') then raise exception 'Tipo de grade inválido.'; end if;
 if expected_revision is null or expected_revision<0 or jsonb_typeof(payload->'grid_enabled') is distinct from 'boolean' or jsonb_typeof(payload->'grid_columns') is distinct from 'number' or jsonb_typeof(payload->'units_per_cell') is distinct from 'number' or coalesce(payload->>'unit','') not in ('m','km') or coalesce(payload->>'grid_color','') !~ '^#[0-9a-fA-F]{6}$' then raise exception 'Configuração de mapa inválida.'; end if;
 if (payload->>'grid_columns')::numeric not between 2 and 200 or (payload->>'grid_columns')::numeric<>trunc((payload->>'grid_columns')::numeric) or (payload->>'units_per_cell')::numeric not between 0.1 and 100000 then raise exception 'Escala fora dos limites.'; end if;
 perform id from public.campaign_items where id=map_id for update;
 select * into current_row from public.campaign_map_settings where item_id=map_id for update;
 if coalesce(current_row.revision,0)<>expected_revision then raise exception using errcode='40001',message='A escala mudou em outra sessão. Recarregue a configuração antes de salvar.'; end if;
 insert into public.campaign_map_settings(item_id,room_id,grid_enabled,grid_columns,units_per_cell,unit,grid_color,grid_type)
 values(map_id,target_room,(payload->>'grid_enabled')::boolean,(payload->>'grid_columns')::integer,(payload->>'units_per_cell')::numeric,payload->>'unit',payload->>'grid_color',payload->>'grid_type')
 on conflict(item_id) do update set grid_enabled=excluded.grid_enabled,grid_columns=excluded.grid_columns,units_per_cell=excluded.units_per_cell,unit=excluded.unit,grid_color=excluded.grid_color,grid_type=excluded.grid_type,revision=campaign_map_settings.revision+1 returning * into current_row;
 return to_jsonb(current_row);
end; $$;
revoke all on function public.save_campaign_map_grid_settings(uuid,bigint,jsonb) from public,anon;
grant execute on function public.save_campaign_map_grid_settings(uuid,bigint,jsonb) to authenticated;
commit;
