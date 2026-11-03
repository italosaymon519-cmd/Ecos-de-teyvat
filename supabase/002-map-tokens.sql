-- Executar DEPOIS de setup.sql. Não executar setup.sql novamente.
begin;
create unique index if not exists campaign_items_room_identity on public.campaign_items(room_id,id);
create table if not exists public.campaign_tokens (
 id uuid primary key default gen_random_uuid(),
 room_id uuid not null,
 item_id uuid not null,
 name text not null check(char_length(name) between 1 and 80),
 kind text not null check(kind in ('character','enemy','ally')),
 color text not null default '#d9ba7e' check(color ~ '^#[0-9a-fA-F]{6}$'),
 owner_id uuid,
 x double precision not null default 50 check(x>=0 and x<=100),
 y double precision not null default 50 check(y>=0 and y<=100),
 size double precision not null default 4 check(size>=2 and size<=10),
 check(kind='character' or owner_id is null),
 foreign key(room_id,item_id) references public.campaign_items(room_id,id) on delete cascade,
 foreign key(room_id,owner_id) references public.campaign_members(room_id,user_id)
);
create index if not exists campaign_tokens_map on public.campaign_tokens(item_id);
alter table public.campaign_tokens enable row level security;
revoke all on public.campaign_tokens from public,anon,authenticated;
grant select,insert,delete on public.campaign_tokens to authenticated;
grant update(x,y) on public.campaign_tokens to authenticated;
drop policy if exists tokens_read on public.campaign_tokens;
create policy tokens_read on public.campaign_tokens for select to authenticated using (
 public.is_campaign_gm(room_id) or (public.is_campaign_member(room_id) and exists(select 1 from public.campaign_items i where i.id=item_id and i.room_id=campaign_tokens.room_id and i.visible))
);
drop policy if exists tokens_insert on public.campaign_tokens;
create policy tokens_insert on public.campaign_tokens for insert to authenticated with check (
 public.is_campaign_gm(room_id) and exists(select 1 from public.campaign_items i where i.id=item_id and i.room_id=campaign_tokens.room_id and i.kind='map')
);
drop policy if exists tokens_move on public.campaign_tokens;
create policy tokens_move on public.campaign_tokens for update to authenticated using (
 public.is_campaign_gm(room_id) or (owner_id=auth.uid() and public.is_campaign_member(room_id) and exists(select 1 from public.campaign_items i where i.id=item_id and i.room_id=campaign_tokens.room_id and i.visible))
) with check (
 public.is_campaign_gm(room_id) or (owner_id=auth.uid() and public.is_campaign_member(room_id) and exists(select 1 from public.campaign_items i where i.id=item_id and i.room_id=campaign_tokens.room_id and i.visible))
);
drop policy if exists tokens_delete on public.campaign_tokens;
create policy tokens_delete on public.campaign_tokens for delete to authenticated using (public.is_campaign_gm(room_id));
commit;
