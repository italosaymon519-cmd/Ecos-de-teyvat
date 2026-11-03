-- Executar uma vez no SQL Editor de um projeto Supabase.
-- A chave pública é segura SOMENTE com estas políticas habilitadas.
begin;
create table public.campaign_rooms (
  id uuid primary key default gen_random_uuid(),
  name text not null check (char_length(name) between 1 and 100),
  gm_id uuid not null references auth.users(id),
  invite_code text not null unique default upper(replace(gen_random_uuid()::text, '-', '')),
  created_at timestamptz not null default now()
);
create table public.campaign_members (
  room_id uuid not null references public.campaign_rooms(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  display_name text not null check (char_length(display_name) between 1 and 60),
  joined_at timestamptz not null default now(),
  primary key (room_id, user_id)
);
create table public.campaign_items (
  id uuid primary key default gen_random_uuid(),
  room_id uuid not null references public.campaign_rooms(id) on delete cascade,
  kind text not null check (kind in ('map','scene','npc')),
  title text not null check (char_length(title) between 1 and 120),
  public_text text not null default '' check (char_length(public_text) <= 20000),
  image_path text,
  visible boolean not null default false,
  is_current boolean not null default false,
  updated_at timestamptz not null default now(),
  check (not is_current or visible),
  check (image_path is null or (image_path like room_id::text || '/%' and image_path !~ '\.\.' and char_length(image_path) < 256))
);
create index campaign_items_room on public.campaign_items(room_id);
create index campaign_members_user on public.campaign_members(user_id);

create function public.is_campaign_member(target uuid) returns boolean
language sql stable security definer set search_path = '' as $$
 select exists(select 1 from public.campaign_members where room_id=target and user_id=(select auth.uid()));
$$;
create function public.is_campaign_gm(target uuid) returns boolean
language sql stable security definer set search_path = '' as $$
 select exists(select 1 from public.campaign_rooms where id=target and gm_id=(select auth.uid()));
$$;
revoke all on function public.is_campaign_member(uuid), public.is_campaign_gm(uuid) from public, anon;
grant execute on function public.is_campaign_member(uuid), public.is_campaign_gm(uuid) to authenticated;

alter table public.campaign_rooms enable row level security;
alter table public.campaign_members enable row level security;
alter table public.campaign_items enable row level security;
revoke all on public.campaign_rooms, public.campaign_members, public.campaign_items from anon, authenticated;
grant select(id,name,gm_id,created_at) on public.campaign_rooms to authenticated;
grant select on public.campaign_members to authenticated;
grant select,insert,update,delete on public.campaign_items to authenticated;
create policy rooms_read on public.campaign_rooms for select to authenticated using (public.is_campaign_member(id));
create policy members_read on public.campaign_members for select to authenticated using (public.is_campaign_member(room_id));
create policy items_read on public.campaign_items for select to authenticated using (public.is_campaign_gm(room_id) or (visible and public.is_campaign_member(room_id)));
create policy items_insert on public.campaign_items for insert to authenticated with check (public.is_campaign_gm(room_id));
create policy items_update on public.campaign_items for update to authenticated using (public.is_campaign_gm(room_id)) with check (public.is_campaign_gm(room_id));
create policy items_delete on public.campaign_items for delete to authenticated using (public.is_campaign_gm(room_id));

create function public.create_campaign_room(room_name text, member_name text) returns uuid
language plpgsql security definer set search_path = '' as $$
declare new_id uuid;
begin
 if auth.uid() is null then raise exception 'Entre na sua conta.'; end if;
 if char_length(trim(room_name)) not between 1 and 100 or char_length(trim(member_name)) not between 1 and 60 then raise exception 'Nome inválido.'; end if;
 if (select count(*) from public.campaign_rooms where gm_id=auth.uid()) >= 20 then raise exception 'Limite de 20 salas por mestre.'; end if;
 insert into public.campaign_rooms(name,gm_id) values(trim(room_name),auth.uid()) returning id into new_id;
 insert into public.campaign_members(room_id,user_id,display_name) values(new_id,auth.uid(),trim(member_name));
 return new_id;
end; $$;
create function public.join_campaign_room(code text, member_name text) returns uuid
language plpgsql security definer set search_path = '' as $$
declare target uuid;
begin
 if auth.uid() is null then raise exception 'Entre na sua conta.'; end if;
 if char_length(trim(member_name)) not between 1 and 60 then raise exception 'Nome inválido.'; end if;
 select id into target from public.campaign_rooms where invite_code=upper(trim(code));
 if target is null then raise exception 'Convite inválido.'; end if;
 insert into public.campaign_members(room_id,user_id,display_name) values(target,auth.uid(),trim(member_name)) on conflict(room_id,user_id) do update set display_name=excluded.display_name;
 return target;
end; $$;
create function public.campaign_invite(target uuid) returns text
language plpgsql security definer set search_path = '' as $$
declare code text;
begin
 if not public.is_campaign_gm(target) then raise exception 'Somente o mestre pode consultar o convite.'; end if;
 select invite_code into code from public.campaign_rooms where id=target;
 return code;
end; $$;
create function public.present_campaign_item(item_id uuid) returns void
language plpgsql security definer set search_path = '' as $$
declare target uuid;
begin
 select room_id into target from public.campaign_items where id=item_id;
 if target is null or not public.is_campaign_gm(target) then raise exception 'Somente o mestre pode apresentar conteúdo.'; end if;
 perform id from public.campaign_rooms where id=target for update;
 update public.campaign_items set is_current=false,updated_at=now() where room_id=target and is_current;
 update public.campaign_items set is_current=true,visible=true,updated_at=now() where id=item_id;
end; $$;
revoke all on function public.create_campaign_room(text,text), public.join_campaign_room(text,text), public.present_campaign_item(uuid), public.campaign_invite(uuid) from public, anon;
grant execute on function public.create_campaign_room(text,text), public.join_campaign_room(text,text), public.present_campaign_item(uuid), public.campaign_invite(uuid) to authenticated;

-- Imagens privadas: somente membros podem ler imagens reveladas; somente o mestre escreve.
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values('campaign-images','campaign-images',false,15728640,array['image/png','image/jpeg','image/webp'])
on conflict(id) do update set public=false,file_size_limit=excluded.file_size_limit,allowed_mime_types=excluded.allowed_mime_types;
create policy campaign_images_read on storage.objects for select to authenticated using (
 bucket_id='campaign-images' and (
  exists(select 1 from public.campaign_rooms r where r.id::text=split_part(storage.objects.name,'/',1) and public.is_campaign_gm(r.id))
  or exists(select 1 from public.campaign_items i where i.image_path=storage.objects.name and i.visible and public.is_campaign_member(i.room_id))
 ));
create policy campaign_images_insert on storage.objects for insert to authenticated with check (
 bucket_id='campaign-images' and exists(select 1 from public.campaign_rooms r where r.id::text=split_part(storage.objects.name,'/',1) and public.is_campaign_gm(r.id))
);
create policy campaign_images_delete on storage.objects for delete to authenticated using (
 bucket_id='campaign-images' and exists(select 1 from public.campaign_rooms r where r.id::text=split_part(storage.objects.name,'/',1) and public.is_campaign_gm(r.id))
);
commit;
