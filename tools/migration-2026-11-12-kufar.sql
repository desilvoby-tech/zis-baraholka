-- Абисто: функции как на kufar.by (12.11.2026)
-- Снижение цены, «был в сети», блокировка собеседника, подписки на продавцов,
-- стоп-слова (автомодерация), журнал модерации.

-- 1. Снижение цены
alter table public.ads add column if not exists old_price numeric;
alter table public.ads add column if not exists price_drop_at timestamptz;

create or replace function public.ads_price_track() returns trigger language plpgsql as $$
begin
  if new.price_type = 'fixed' and old.price_type = 'fixed' and new.price is not null and old.price is not null
     and new.price < old.price then
    new.old_price := greatest(old.price, coalesce(case when old.price_drop_at > now() - interval '30 days' then old.old_price end, 0));
    new.price_drop_at := now();
  elsif new.price is distinct from old.price or new.price_type is distinct from old.price_type then
    new.old_price := null; new.price_drop_at := null;
  elsif current_user in ('authenticated','anon') then
    new.old_price := old.old_price; new.price_drop_at := old.price_drop_at;
  end if;
  return new;
end $$;
drop trigger if exists ads_price_track on public.ads;
create trigger ads_price_track before update on public.ads for each row execute function public.ads_price_track();

create or replace function public.ads_price_clear() returns trigger language plpgsql as $$
begin
  if current_user in ('authenticated','anon') then new.old_price := null; new.price_drop_at := null; end if;
  return new;
end $$;
drop trigger if exists ads_price_clear on public.ads;
create trigger ads_price_clear before insert on public.ads for each row execute function public.ads_price_clear();

-- 2. «Был в сети»
alter table public.profiles add column if not exists last_seen timestamptz;
create or replace function public.touch_seen() returns void language sql security definer set search_path = public as $$
  update public.profiles set last_seen = now() where id = auth.uid() and (last_seen is null or last_seen < now() - interval '2 minutes');
$$;
revoke all on function public.touch_seen() from public, anon;
grant execute on function public.touch_seen() to authenticated;

-- 3. Блокировка собеседника
create table if not exists public.user_blocks(
  user_id uuid not null references auth.users(id) on delete cascade,
  blocked_id uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key(user_id, blocked_id), check (user_id <> blocked_id));
alter table public.user_blocks enable row level security;
drop policy if exists "blocks own" on public.user_blocks;
create policy "blocks own" on public.user_blocks for all to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());

create or replace function public.chat_block_state(other uuid) returns jsonb language sql stable security definer set search_path = public as $$
  select jsonb_build_object(
    'i_blocked', exists(select 1 from public.user_blocks where user_id = auth.uid() and blocked_id = other),
    'blocked_me', exists(select 1 from public.user_blocks where user_id = other and blocked_id = auth.uid()));
$$;
grant execute on function public.chat_block_state(uuid) to authenticated;

drop policy if exists "msg not blocked" on public.messages;
create policy "msg not blocked" on public.messages as restrictive for insert to authenticated
  with check (not exists (select 1 from public.conversations c join public.user_blocks b
    on b.blocked_id = auth.uid() and b.user_id = case when c.buyer_id = auth.uid() then c.seller_id else c.buyer_id end
    where c.id = messages.conversation_id));
drop policy if exists "conv not blocked" on public.conversations;
create policy "conv not blocked" on public.conversations as restrictive for insert to authenticated
  with check (not exists (select 1 from public.user_blocks b where b.user_id = conversations.seller_id and b.blocked_id = auth.uid()));

-- 4. Подписки на продавцов
create table if not exists public.follows(
  follower uuid not null references auth.users(id) on delete cascade,
  seller uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key(follower, seller), check (follower <> seller));
alter table public.follows enable row level security;
drop policy if exists "follows own" on public.follows;
create policy "follows own" on public.follows for all to authenticated
  using (follower = auth.uid()) with check (follower = auth.uid());
create or replace function public.follower_count(s uuid) returns int language sql stable security definer set search_path = public as $$
  select count(*)::int from public.follows where seller = s;
$$;
grant execute on function public.follower_count(uuid) to anon, authenticated;

-- 5. Стоп-слова (автомодерация)
create table if not exists public.stop_words(word text primary key check (length(trim(word)) >= 2), created_at timestamptz not null default now());
alter table public.stop_words enable row level security;
drop policy if exists "stop words admin" on public.stop_words;
create policy "stop words admin" on public.stop_words for all to authenticated using (public.is_admin()) with check (public.is_admin());

create or replace function public.ads_stopwords() returns trigger language plpgsql security definer set search_path = public as $$
declare w text;
begin
  if auth.uid() is not null and not public.is_admin() then
    if new.status = 'active' and (tg_op = 'INSERT' or new.title is distinct from old.title or new.descr is distinct from old.descr or old.status <> 'active') then
      select s.word into w from public.stop_words s
        where lower(coalesce(new.title,'') || ' ' || coalesce(new.descr,'')) like '%' || lower(trim(s.word)) || '%' limit 1;
      if w is not null then
        new.status := 'blocked';
        new.mod_note := 'Автопроверка: «' || w || '». Модератор проверит объявление.';
      end if;
    end if;
  end if;
  return new;
end $$;
drop trigger if exists ads_stopwords on public.ads;
create trigger ads_stopwords before insert or update on public.ads for each row execute function public.ads_stopwords();

-- 6. Журнал модерации
create table if not exists public.mod_log(
  id bigint generated always as identity primary key,
  admin_id uuid, action text not null, target text, note text,
  created_at timestamptz not null default now());
alter table public.mod_log enable row level security;
drop policy if exists "mod log read" on public.mod_log;
create policy "mod log read" on public.mod_log for select to authenticated using (public.is_admin());

create or replace function public.log_ads_mod() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if tg_op = 'DELETE' then
    if public.is_admin() and old.user_id is distinct from auth.uid() then
      insert into public.mod_log(admin_id, action, target, note) values (auth.uid(), 'Удалено объявление', '#' || old.id || ' ' || left(old.title, 80), null);
    end if;
    return old;
  end if;
  if new.status is distinct from old.status then
    if public.is_admin() and old.user_id is distinct from auth.uid() and coalesce(new.mod_note,'') <> 'ban' and coalesce(old.mod_note,'') <> 'ban' then
      insert into public.mod_log(admin_id, action, target, note)
      values (auth.uid(), case when new.status = 'blocked' then 'Скрыто объявление' when old.status = 'blocked' then 'Возвращено объявление' else 'Статус: ' || new.status end,
              '#' || new.id || ' ' || left(new.title, 80), new.mod_note);
    elsif new.status = 'blocked' and new.mod_note like 'Автопроверка%' then
      insert into public.mod_log(admin_id, action, target, note) values (null, 'Автоскрытие', '#' || new.id || ' ' || left(new.title, 80), new.mod_note);
    end if;
  end if;
  return new;
end $$;
drop trigger if exists log_ads_mod on public.ads;
create trigger log_ads_mod after update or delete on public.ads for each row execute function public.log_ads_mod();

create or replace function public.log_ads_auto() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if new.status = 'blocked' and new.mod_note like 'Автопроверка%' then
    insert into public.mod_log(admin_id, action, target, note) values (null, 'Автоскрытие', '#' || new.id || ' ' || left(new.title, 80), new.mod_note);
  end if;
  return new;
end $$;
drop trigger if exists log_ads_auto on public.ads;
create trigger log_ads_auto after insert on public.ads for each row execute function public.log_ads_auto();

create or replace function public.log_ban() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if new.banned is distinct from old.banned then
    insert into public.mod_log(admin_id, action, target) values (auth.uid(), case when new.banned then 'Заблокирован пользователь' else 'Разблокирован пользователь' end, coalesce(new.name, '') || ' (' || new.id || ')');
  end if;
  return new;
end $$;
drop trigger if exists log_ban on public.profiles;
create trigger log_ban after update of banned on public.profiles for each row execute function public.log_ban();

-- 7. search_ads: фильтры «Частное лицо / Компания» и «Цена снижена»
-- В текущее определение search_ads перед условием по тексту (p->>'q') добавлены строки:
--   and (p->>'seller' is null or exists(select 1 from public.profiles pr where pr.id = a.user_id and coalesce(pr.is_business,false) = (p->>'seller' = 'company')))
--   and (coalesce((p->>'drop')::boolean,false) = false or a.price_drop_at > now() - interval '30 days')
