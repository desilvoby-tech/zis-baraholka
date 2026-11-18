-- Abisto: рейтинг, сделки и отзывы продавца с другого сайта (Kufar) переносятся в профиль при вводе кода.
alter table public.profiles add column if not exists ext jsonb;

-- Пользователь не может сам подделать ext: менять его может только админ или функция claim_ads.
create or replace function public.profiles_protect_ext() returns trigger
language plpgsql as $$
begin
  if coalesce(current_setting('abisto.allow_ext', true), '') = '1'
     or exists (select 1 from public.admins where user_id = auth.uid()) then
    return new;
  end if;
  if tg_op = 'INSERT' then new.ext := null;
  elsif new.ext is distinct from old.ext then new.ext := old.ext; end if;
  return new;
end $$;
drop trigger if exists profiles_protect_ext on public.profiles;
create trigger profiles_protect_ext before insert or update on public.profiles
  for each row execute function public.profiles_protect_ext();

create or replace function public.claim_ads(p_code text, p_phone text default null)
returns int language plpgsql security definer set search_path = public as $$
declare c public.ad_claims; n int; ph text := nullif(trim(coalesce(p_phone,'')), ''); x jsonb;
begin
  if auth.uid() is null then raise exception 'Войдите на сайт, чтобы получить объявление'; end if;
  select * into c from public.ad_claims
   where code = upper(trim(p_code)) and claimed_by is null for update;
  if not found then raise exception 'Код не найден или уже использован'; end if;
  if c.created_by = auth.uid() then raise exception 'Этот код нужно передать продавцу'; end if;

  select a.attrs->'ext_seller' into x from public.ads a
   where a.id = any(c.ad_ids) and a.user_id = c.created_by and a.attrs ? 'ext_seller' limit 1;

  update public.ads
     set user_id = auth.uid(),
         phone = coalesce(ph, phone),
         show_phone = coalesce(ph, phone) is not null,
         attrs = attrs - 'ext_seller'
   where id = any(c.ad_ids) and user_id = c.created_by;
  get diagnostics n = row_count;

  update public.conversations set seller_id = auth.uid()
   where ad_id = any(c.ad_ids) and seller_id = c.created_by;

  perform set_config('abisto.allow_ext', '1', true);
  update public.profiles
     set phone = coalesce(phone, ph),
         ext = case when x is null then ext else x end
   where id = auth.uid();

  update public.ad_claims set claimed_by = auth.uid(), claimed_at = now() where code = c.code;
  return n;
end $$;
revoke all on function public.claim_ads(text, text) from public, anon;
grant execute on function public.claim_ads(text, text) to authenticated;

notify pgrst, 'reload schema';
