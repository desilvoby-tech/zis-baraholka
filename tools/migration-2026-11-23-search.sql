-- Абисто · поиск по словам (аудит, модуль 2, 2026-11-23)
-- ЗАГОТОВКА. НЕ ПРИМЕНЕНА. Применять только после подтверждения владельца (Supabase → SQL Editor).
--
-- Что даёт:
--   * слова запроса ищутся в любом порядке и в любой форме: «угловой диван» → «Диван угловой»,
--     «ремонт ноутбука» → «Ремонт ноутбуков…», «стиральную машину» → «Стиральная машина…»;
--   * ё = е: «елку» находит «ёлку»;
--   * символы % и _ больше не работают как «любой текст» (сейчас «р%т» — шаблон LIKE);
--     запрос только из знаков препинания считается пустым (как сейчас пустая строка);
--   * по-прежнему работает поиск подстроки; слова можно писать раздельно («eco 235» → «Eco-235»);
--
-- Как подключить (после проверки):
--   в определении public.search_ads условие по тексту (p->>'q') заменить на
--     and public.ad_text_match(a.title, a.descr, p->>'q')
--   (если в функции объявление называется не «a» — подставить своё имя).
--   Там же рекомендуется:
--     limit  least(greatest(coalesce((p->>'limit')::int, 40), 1), 100)
--     offset greatest(coalesce((p->>'offset')::int, 0), 0)
--     цена:  public.ad_num(p->>'min') / public.ad_num(p->>'max') вместо ::numeric
--            (сейчас «1.2.3» в поле цены даёт ошибку базы на экране).
--
-- Откат: drop function public.ad_text_match(text,text,text); drop function public.ad_norm(text); drop function public.ad_num(text);
--        и вернуть прежнее условие в search_ads.

create or replace function public.ad_norm(t text) returns text
language sql immutable parallel safe as
$$ select translate(lower(coalesce(t, '')), 'ё', 'е') $$;

create or replace function public.ad_num(t text) returns numeric
language sql immutable parallel safe as
$$ select case when btrim(coalesce(t, '')) ~ '^\d+(\.\d+)?$' then btrim(t)::numeric end $$;

create or replace function public.ad_text_match(title text, descr text, q text) returns boolean
language plpgsql immutable parallel safe as $$
declare
  nq  text := btrim(regexp_replace(public.ad_norm(q), '\s+', ' ', 'g'));
  doc text := public.ad_norm(title) || ' ' || public.ad_norm(descr);
  tq  tsquery;
begin
  if nq = '' or nq !~ '[[:alnum:]]' then return true; end if;
  -- 1) подстрока целиком (без спецсимволов LIKE)
  if strpos(doc, nq) > 0 then return true; end if;
  -- 2) каждое слово запроса встречается как подстрока (любой порядок; «eco 235», «ноут»)
  if not exists (
       select 1 from regexp_split_to_table(nq, '[^[:alnum:]]+') w
       where w <> '' and strpos(doc, w) = 0) then
    return true;
  end if;
  -- 3) все слова запроса в любом порядке, с русской морфологией (формы слов)
  tq := plainto_tsquery('russian', nq);
  if tq is null or numnode(tq) = 0 then return false; end if;
  return to_tsvector('russian', doc) @@ tq;
end $$;
