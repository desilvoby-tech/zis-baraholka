-- Abisto: передача перенесённых объявлений настоящим продавцам по коду
-- + переименование аккаунта администратора «Ремонт техники» → «Абисто».
-- Выполнить один раз в базе abisto-db (Supabase Studio → SQL Editor).

update public.profiles set name = 'Абисто'
 where name = 'Ремонт техники' and id in (select user_id from public.admins);

create table if not exists public.ad_claims (
  code        text primary key,
  ad_ids      bigint[] not null,
  seller_name text,
  created_by  uuid not null default auth.uid(),
  created_at  timestamptz not null default now(),
  claimed_by  uuid,
  claimed_at  timestamptz
);
alter table public.ad_claims enable row level security;
drop policy if exists ad_claims_admin on public.ad_claims;
create policy ad_claims_admin on public.ad_claims for all
  using (exists (select 1 from public.admins where user_id = auth.uid()))
  with check (exists (select 1 from public.admins where user_id = auth.uid()));

create or replace function public.claim_ads(p_code text, p_phone text default null)
returns int language plpgsql security definer set search_path = public as $$
declare c public.ad_claims; n int; ph text := nullif(trim(coalesce(p_phone,'')), '');
begin
  if auth.uid() is null then raise exception 'Войдите на сайт, чтобы получить объявление'; end if;
  select * into c from public.ad_claims
   where code = upper(trim(p_code)) and claimed_by is null for update;
  if not found then raise exception 'Код не найден или уже использован'; end if;
  if c.created_by = auth.uid() then raise exception 'Этот код нужно передать продавцу'; end if;

  update public.ads
     set user_id = auth.uid(),
         phone = coalesce(ph, phone),
         show_phone = coalesce(ph, phone) is not null
   where id = any(c.ad_ids) and user_id = c.created_by;
  get diagnostics n = row_count;

  update public.conversations set seller_id = auth.uid()
   where ad_id = any(c.ad_ids) and seller_id = c.created_by;

  if ph is not null then
    update public.profiles set phone = ph where id = auth.uid() and phone is null;
  end if;

  update public.ad_claims set claimed_by = auth.uid(), claimed_at = now() where code = c.code;
  return n;
end $$;
revoke all on function public.claim_ads(text, text) from public, anon;
grant execute on function public.claim_ads(text, text) to authenticated;

notify pgrst, 'reload schema';
