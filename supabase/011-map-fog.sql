-- Após 010. Preserva mapas existentes: a névoa começa desativada.
begin;
create table if not exists public.campaign_map_fog (
 item_id uuid primary key, room_id uuid not null references public.campaign_rooms(id) on delete cascade,
 enabled boolean not null default false, regions jsonb not null default '[]', revision bigint not null default 1,
 foreign key(room_id,item_id) references public.campaign_items(room_id,id) on delete cascade
);
alter table public.campaign_map_fog enable row level security;
revoke all on public.campaign_map_fog from public,anon,authenticated;
grant select on public.campaign_map_fog to authenticated;
drop policy if exists fog_read on public.campaign_map_fog;
create policy fog_read on public.campaign_map_fog for select to authenticated using(public.can_read_campaign_map(item_id));
create or replace function public.campaign_fog_point_visible(map_id uuid,px double precision,py double precision) returns boolean
language sql stable security definer set search_path='' as $$
 select public.can_read_campaign_map(map_id) and coalesce((select not f.enabled or coalesce((select (r.value->>'reveal')::boolean from jsonb_array_elements(f.regions) with ordinality r where px>=(r.value->>'x')::double precision and px<=(r.value->>'x')::double precision+(r.value->>'width')::double precision and py>=(r.value->>'y')::double precision and py<=(r.value->>'y')::double precision+(r.value->>'height')::double precision order by r.ordinality desc limit 1),false) from public.campaign_map_fog f where f.item_id=map_id),true);
$$;
create or replace function public.save_campaign_map_fog(map_id uuid,expected_revision bigint,payload jsonb) returns jsonb
language plpgsql security definer set search_path='' as $$
declare target uuid; current_row public.campaign_map_fog; r jsonb; k text; n numeric;
begin
 select room_id into target from public.campaign_items where id=map_id and kind='map' and image_path is not null for update;
 if target is null or not public.is_campaign_gm(target) then raise exception 'Somente o mestre pode alterar a névoa.'; end if;
 if octet_length(payload::text)>65536 or expected_revision is null or expected_revision<0 or jsonb_typeof(payload->'enabled') is distinct from 'boolean' or jsonb_typeof(payload->'regions') is distinct from 'array' then raise exception 'Névoa inválida.'; end if;
 if jsonb_array_length(payload->'regions')>200 then raise exception 'Limite de 200 áreas. Use Cobrir tudo ou Revelar tudo para reiniciar.'; end if;
 for r in select value from jsonb_array_elements(payload->'regions') loop
  if jsonb_typeof(r->'reveal') is distinct from 'boolean' then raise exception 'Área inválida.'; end if;
  foreach k in array array['x','y','width','height'] loop
   if jsonb_typeof(r->k) is distinct from 'number' then raise exception 'Coordenada inválida.'; end if;
   n:=(r->>k)::numeric;if n<0 or n>100 or (k in ('width','height') and n=0) then raise exception 'Área fora do mapa.'; end if;
  end loop;
  if (r->>'x')::numeric+(r->>'width')::numeric>100 or (r->>'y')::numeric+(r->>'height')::numeric>100 then raise exception 'Área fora do mapa.'; end if;
 end loop;
 select * into current_row from public.campaign_map_fog where item_id=map_id for update;
 if coalesce(current_row.revision,0)<>expected_revision then raise exception 'A névoa mudou em outra sessão. Atualize e tente novamente.' using errcode='40001'; end if;
 insert into public.campaign_map_fog(item_id,room_id,enabled,regions) values(map_id,target,(payload->>'enabled')::boolean,payload->'regions')
 on conflict(item_id) do update set enabled=excluded.enabled,regions=excluded.regions,revision=campaign_map_fog.revision+1 returning * into current_row;
 return to_jsonb(current_row);
end; $$;
revoke all on function public.campaign_fog_point_visible(uuid,double precision,double precision),public.save_campaign_map_fog(uuid,bigint,jsonb) from public,anon;
grant execute on function public.campaign_fog_point_visible(uuid,double precision,double precision),public.save_campaign_map_fog(uuid,bigint,jsonb) to authenticated;
drop policy if exists tokens_read on public.campaign_tokens;
create policy tokens_read on public.campaign_tokens for select to authenticated using(public.is_campaign_gm(room_id) or (public.is_campaign_member(room_id) and public.campaign_fog_point_visible(item_id,x,y)));
drop policy if exists tokens_move on public.campaign_tokens;
create policy tokens_move on public.campaign_tokens for update to authenticated using(public.is_campaign_gm(room_id) or (owner_id=auth.uid() and public.is_campaign_member(room_id) and public.campaign_fog_point_visible(item_id,x,y))) with check(public.is_campaign_gm(room_id) or (owner_id=auth.uid() and public.is_campaign_member(room_id) and public.campaign_fog_point_visible(item_id,x,y)));
drop policy if exists map_markers_read on public.campaign_map_markers;
create policy map_markers_read on public.campaign_map_markers for select to authenticated using(public.can_read_campaign_map(item_id) and (public.is_campaign_gm(room_id) or (public.campaign_fog_point_visible(item_id,x,y) and (kind='pin' or public.campaign_fog_point_visible(item_id,end_x,end_y)))));
create or replace function public.create_campaign_map_marker(map_id uuid,marker_id uuid,payload jsonb) returns jsonb
language plpgsql security definer set search_path='' as $$
declare target_room uuid; nickname text; current_row public.campaign_map_markers; field text;
begin
 if marker_id is null or not public.can_read_campaign_map(map_id) then raise exception 'Abra um mapa revelado desta campanha para marcar.'; end if;
 select room_id into target_room from public.campaign_items where id=map_id for update;
 if not public.is_campaign_gm(target_room) and (not public.campaign_fog_point_visible(map_id,(payload->>'x')::double precision,(payload->>'y')::double precision) or (payload->>'kind'='ruler' and not public.campaign_fog_point_visible(map_id,(payload->>'end_x')::double precision,(payload->>'end_y')::double precision))) then raise exception 'Escolha uma área revelada do mapa.'; end if;
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
 'fog',coalesce((select jsonb_agg(to_jsonb(t) order by t.item_id) from public.campaign_map_fog t where room_id=target_room),'[]'),
 'combat',(select to_jsonb(t) from public.campaign_combats t where room_id=target_room),
 'rolls',coalesce((select jsonb_agg(to_jsonb(t) order by t.seq) from public.campaign_rolls t where room_id=target_room),'[]'));
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
 if jsonb_typeof(coalesce(payload->'fog','[]'::jsonb)) is distinct from 'array' or jsonb_array_length(coalesce(payload->'fog','[]'::jsonb))>500 then raise exception 'Névoa de backup inválida.'; end if;
 for entry in select value from jsonb_array_elements(coalesce(payload->'fog','[]'::jsonb)) loop
  if not exists(select 1 from public.campaign_items where room_id=job.room_id and id=(entry->>'item_id')::uuid) then raise exception 'Névoa fora da sala restaurada.'; end if;
  perform public.save_campaign_map_fog((entry->>'item_id')::uuid,0,entry);
 end loop;
 update public.campaign_restore_jobs set completed=true where id=job.id;
 return job.room_id;
end; $$;
commit;
