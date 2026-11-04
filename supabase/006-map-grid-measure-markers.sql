-- Executar após setup.sql e 002. Pode ser repetido sem apagar dados.
begin;
create or replace function public.can_read_campaign_map(map_id uuid) returns boolean
language sql stable security definer set search_path='' as $$
 select exists(select 1 from public.campaign_items i where i.id=map_id and i.kind='map' and i.image_path is not null and (public.is_campaign_gm(i.room_id) or (i.visible and public.is_campaign_member(i.room_id))));
$$;
revoke all on function public.can_read_campaign_map(uuid) from public,anon;
grant execute on function public.can_read_campaign_map(uuid) to authenticated;
create table if not exists public.campaign_map_settings (
 item_id uuid primary key,
 room_id uuid not null references public.campaign_rooms(id) on delete cascade,
 grid_enabled boolean not null default false,
 grid_columns integer not null default 20 check(grid_columns between 2 and 200),
 units_per_cell numeric not null default 1.5 check(units_per_cell between 0.1 and 100000),
 unit text not null default 'm' check(unit in ('m','km')),
 grid_color text not null default '#e0c49a' check(grid_color ~ '^#[0-9a-fA-F]{6}$'),
 revision bigint not null default 1,
 foreign key(room_id,item_id) references public.campaign_items(room_id,id) on delete cascade
);
create table if not exists public.campaign_map_markers (
 id uuid primary key,
 item_id uuid not null,
 room_id uuid not null references public.campaign_rooms(id) on delete cascade,
 created_by uuid not null references auth.users(id),
 creator_name text not null,
 kind text not null check(kind in ('pin','ruler')),
 label text not null check(char_length(label) between 1 and 80),
 color text not null check(color ~ '^#[0-9a-fA-F]{6}$'),
 x double precision not null check(x between 0 and 100),
 y double precision not null check(y between 0 and 100),
 end_x double precision check(end_x between 0 and 100),
 end_y double precision check(end_y between 0 and 100),
 created_at timestamptz not null default now(),
 check((kind='pin' and end_x is null and end_y is null) or (kind='ruler' and end_x is not null and end_y is not null)),
 foreign key(room_id,item_id) references public.campaign_items(room_id,id) on delete cascade
);
create index if not exists campaign_map_markers_item on public.campaign_map_markers(item_id);
alter table public.campaign_map_settings enable row level security;
alter table public.campaign_map_markers enable row level security;
revoke all on public.campaign_map_settings,public.campaign_map_markers from public,anon,authenticated;
grant select on public.campaign_map_settings,public.campaign_map_markers to authenticated;
drop policy if exists map_settings_read on public.campaign_map_settings;
create policy map_settings_read on public.campaign_map_settings for select to authenticated using(public.can_read_campaign_map(item_id));
drop policy if exists map_markers_read on public.campaign_map_markers;
create policy map_markers_read on public.campaign_map_markers for select to authenticated using(public.can_read_campaign_map(item_id));
create or replace function public.save_campaign_map_settings(map_id uuid,expected_revision bigint,payload jsonb) returns jsonb
language plpgsql security definer set search_path='' as $$
declare target_room uuid; current_row public.campaign_map_settings;
begin
 select room_id into target_room from public.campaign_items where id=map_id and kind='map' and image_path is not null;
 if target_room is null or not public.is_campaign_gm(target_room) then raise exception 'Somente o mestre pode configurar a escala do mapa.'; end if;
 if expected_revision is null or expected_revision<0 or jsonb_typeof(payload->'grid_enabled') is distinct from 'boolean' or jsonb_typeof(payload->'grid_columns') is distinct from 'number' or jsonb_typeof(payload->'units_per_cell') is distinct from 'number' or coalesce(payload->>'unit','') not in ('m','km') or coalesce(payload->>'grid_color','') !~ '^#[0-9a-fA-F]{6}$' then raise exception 'Configuração de mapa inválida.'; end if;
 if (payload->>'grid_columns')::numeric not between 2 and 200 or (payload->>'grid_columns')::numeric<>trunc((payload->>'grid_columns')::numeric) or (payload->>'units_per_cell')::numeric not between 0.1 and 100000 then raise exception 'Escala fora dos limites.'; end if;
 perform id from public.campaign_items where id=map_id for update;
 select * into current_row from public.campaign_map_settings where item_id=map_id for update;
 if coalesce(current_row.revision,0)<>expected_revision then raise exception using errcode='40001',message='A escala mudou em outra sessão. Recarregue a configuração antes de salvar.'; end if;
 insert into public.campaign_map_settings(item_id,room_id,grid_enabled,grid_columns,units_per_cell,unit,grid_color)
 values(map_id,target_room,(payload->>'grid_enabled')::boolean,(payload->>'grid_columns')::integer,(payload->>'units_per_cell')::numeric,payload->>'unit',payload->>'grid_color')
 on conflict(item_id) do update set grid_enabled=excluded.grid_enabled,grid_columns=excluded.grid_columns,units_per_cell=excluded.units_per_cell,unit=excluded.unit,grid_color=excluded.grid_color,revision=campaign_map_settings.revision+1 returning * into current_row;
 return to_jsonb(current_row);
end; $$;
create or replace function public.create_campaign_map_marker(map_id uuid,marker_id uuid,payload jsonb) returns jsonb
language plpgsql security definer set search_path='' as $$
declare target_room uuid; nickname text; current_row public.campaign_map_markers; field text;
begin
 if marker_id is null or not public.can_read_campaign_map(map_id) then raise exception 'Abra um mapa revelado desta campanha para marcar.'; end if;
 select room_id into target_room from public.campaign_items where id=map_id for update;
 select display_name into nickname from public.campaign_members where room_id=target_room and user_id=auth.uid();
 if nickname is null then raise exception 'Entre na campanha.'; end if;
 select * into current_row from public.campaign_map_markers where id=marker_id;
 if found then
  if current_row.item_id<>map_id or current_row.created_by<>auth.uid() then raise exception 'Identificador de marcador já utilizado.'; end if;
  return to_jsonb(current_row);
 end if;
 if (select count(*) from public.campaign_map_markers where item_id=map_id)>=200 then raise exception 'Limite de 200 marcadores por mapa. Remova um antes de adicionar outro.'; end if;
 if coalesce(payload->>'kind','') not in ('pin','ruler') or jsonb_typeof(payload->'label') is distinct from 'string' or char_length(trim(payload->>'label')) not between 1 and 80 or coalesce(payload->>'color','') !~ '^#[0-9a-fA-F]{6}$' then raise exception 'Marcador inválido.'; end if;
 foreach field in array array['x','y'] loop
  if jsonb_typeof(payload->field) is distinct from 'number' or (payload->>field)::numeric not between 0 and 100 then raise exception 'Coordenada inválida.'; end if;
 end loop;
 if payload->>'kind'='ruler' then
  if not exists(select 1 from public.campaign_map_settings where item_id=map_id) then raise exception 'O mestre precisa configurar a escala antes de compartilhar uma medida.'; end if;
  foreach field in array array['end_x','end_y'] loop
   if jsonb_typeof(payload->field) is distinct from 'number' or (payload->>field)::numeric not between 0 and 100 then raise exception 'Destino inválido.'; end if;
  end loop;
 elsif payload->>'end_x' is not null or payload->>'end_y' is not null then raise exception 'Um marcador simples não tem destino.';
 end if;
 insert into public.campaign_map_markers(id,item_id,room_id,created_by,creator_name,kind,label,color,x,y,end_x,end_y)
 values(marker_id,map_id,target_room,auth.uid(),nickname,payload->>'kind',trim(payload->>'label'),payload->>'color',(payload->>'x')::double precision,(payload->>'y')::double precision,(payload->>'end_x')::double precision,(payload->>'end_y')::double precision) returning * into current_row;
 return to_jsonb(current_row);
end; $$;
create or replace function public.delete_campaign_map_marker(marker_id uuid) returns void
language plpgsql security definer set search_path='' as $$
declare marker public.campaign_map_markers;
begin
 select * into marker from public.campaign_map_markers where id=marker_id;
 if marker.id is null then return; end if;
 if not public.can_read_campaign_map(marker.item_id) or (marker.created_by<>auth.uid() and not public.is_campaign_gm(marker.room_id)) then raise exception 'Somente o autor ou o mestre pode remover este marcador.'; end if;
 delete from public.campaign_map_markers where id=marker_id;
end; $$;
revoke all on function public.save_campaign_map_settings(uuid,bigint,jsonb),public.create_campaign_map_marker(uuid,uuid,jsonb),public.delete_campaign_map_marker(uuid) from public,anon;
grant execute on function public.save_campaign_map_settings(uuid,bigint,jsonb),public.create_campaign_map_marker(uuid,uuid,jsonb),public.delete_campaign_map_marker(uuid) to authenticated;
commit;
