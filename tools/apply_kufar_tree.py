# -*- coding: utf-8 -*-
"""Переводит index.html на дерево категорий kufar_tree.TREE и пишет SQL-миграцию объявлений."""
import json, re, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from kufar_tree import TREE, MAP, subs_of, kinds_of, alias_of

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = lambda x: json.dumps(x, ensure_ascii=False)

def build_index():
    p = os.path.join(ROOT, "index.html")
    s = open(p, encoding="utf-8").read()

    # 1) константы-списки подкатегорий для полей
    s = re.sub(r'const AUTO_VEH=\[[^\]]*\];', 'const AUTO_VEH=' + J(["Легковые авто", "Грузовики и автобусы", "Мототехника", "Спецтехника", "Сельхозтехника"]) + ';', s, 1)
    s = re.sub(r'const ROOMS_SUBS=\[[^\]]*\];', 'const ROOMS_SUBS=' + J(["Квартиры", "Комнаты", "Дома, коттеджи", "Новостройки"]) + ';', s, 1)
    s = re.sub(r'const PHONE_SUBS=\[[^\]]*\];', 'const PHONE_SUBS=' + J(["Мобильные телефоны", "Планшеты", "Умные часы и фитнес-браслеты"]) + ';', s, 1)

    # 2) CATS: имена, подкатегории, порядок; «Отдам даром» убирается (на Куфаре это цена «Бесплатно»)
    a = s.index("const CATS = [\n") + len("const CATS = [\n")
    b = s.index("\n];", a)
    body = s[a:b]
    parts = re.split(r'(?m)^(?=  \{id:")', body)
    entries = {}
    for part in parts:
        if not part.strip():
            continue
        cid = re.match(r'  \{id:"([a-z]+)"', part).group(1)
        entries[cid] = part.rstrip().rstrip(",")
    out = []
    for cid, name, subs in TREE:
        e = entries[cid]
        e = re.sub(r'name:"[^"]*"', 'name:' + J(name), e, 1)
        e, n = re.subn(r'subs:\[[^\]]*\]', 'subs:' + J([subs_of(x) for x in subs]), e, 1)
        assert n == 1, cid
        out.append(e)
    s = s[:a] + ",\n".join(out) + s[b:]

    # 3) SUB3 (третий уровень «Вид») — ключ «раздел|подкатегория»
    sub3 = {}
    alias = {}
    for cid, name, subs in TREE:
        for x in subs:
            if kinds_of(x):
                sub3[cid + "|" + subs_of(x)] = kinds_of(x)
            if alias_of(x):
                alias[cid + "|" + subs_of(x)] = list(alias_of(x))
    a = s.index("const SUB3={")
    b = s.index("\n};", a) + 3
    s = s[:a] + "const SUB3={\n" + ",\n".join(J(k) + ":" + J(v) for k, v in sub3.items()) + "\n};\n/* Пункты, которые Куфар показывает в двух разделах: объявления живут в целевом разделе */\nconst SUB_ALIAS=" + J(alias) + ";" + s[b:]

    s = re.sub(r'const EXTRA_SUBS=\{[^\n]*\};', 'const EXTRA_SUBS={};', s, 1)
    old = '    for(const s of c.subs)if(SUB3[s])c.fields.unshift({k:"kind",l:"Вид",t:"sel",o:SUB3[s],s:[s],sub3:true});'
    new = ('    c.alias={};for(const s of c.subs){const al=SUB_ALIAS[c.id+"|"+s];if(al)c.alias[s]=al}\n'
           '    c.postSubs=c.subs.filter(s=>!c.alias[s]);\n'
           '    for(const s of c.postSubs){const k=SUB3[c.id+"|"+s];if(k)c.fields.unshift({k:"kind",l:"Вид",t:"sel",o:k,s:[s],sub3:true})}')
    assert old in s; s = s.replace(old, new, 1)

    # 4) в форме подачи — только «настоящие» подкатегории
    old = '<select class="inp" id="pSub"><option value="">Выберите</option>${c.subs.map('
    assert old in s; s = s.replace(old, '<select class="inp" id="pSub"><option value="">Выберите</option>${c.postSubs.map(', 1)
    old = '(c.subs.length&&!d.sub)?"Выберите подкатегорию."'
    assert old in s; s = s.replace(old, '(c.postSubs.length&&!d.sub)?"Выберите подкатегорию."', 1)

    # 5) переход по псевдониму (как на Куфаре: «Наушники» в «Телефонах» ведут в «Электронику»)
    old = 'async function renderHome(){\n'
    new = ('function resolveAlias(){const c=CAT[S.cat],al=c&&S.sub&&c.alias&&c.alias[S.sub];if(al){S.cat=al[0];S.sub=al[1];S.eq={};S.nmin={};S.nmax={};return true}return false}\n'
           'async function renderHome(){\n  resolveAlias();\n')
    assert old in s; s = s.replace(old, new, 1)

    # 6) третий уровень: ключ по разделу
    s = s.replace('S.sub&&SUB3[S.sub]?', 'S.sub&&SUB3[S.cat+"|"+S.sub]?')
    s = s.replace('${SUB3[S.sub].map(', '${SUB3[S.cat+"|"+S.sub].map(')
    assert 'SUB3[S.sub]' not in s, [m.start() for m in re.finditer(r'SUB3\[S\.sub\]', s)]
    rest = [m.start() for m in re.finditer(r'SUB3\[(?!c\.id|S\.cat|k\b)', s)]
    open(p, "w", encoding="utf-8").write(s)
    return rest

def build_sql():
    rows = []
    def add(oc, os_, ok, nc, ns, mode, nk):
        rows.append("(%s)" % ",".join("null" if v is None else "'" + v.replace("'", "''") + "'" for v in (oc, os_, ok, nc, ns, mode, nk)))
    for (oc, os_), (nc, ns, kd, km) in MAP.items():
        if ns == "@GENDER":
            continue
        add(oc, os_, None, nc, ns, "set" if kd else "keep", kd)
        for ok, v in km.items():
            if isinstance(v, str):
                add(oc, os_, ok, nc, ns, "set", v)
            else:
                cc, ss, kk = (nc,) + tuple(v) if len(v) == 2 else v
                add(oc, os_, ok, cc, ss, "set" if kk else "drop", kk)
    valid = []
    for cid, name, subs in TREE:
        for x in subs:
            for k in (kinds_of(x) or []):
                valid.append("('%s','%s','%s')" % (cid, subs_of(x).replace("'", "''"), k.replace("'", "''")))
    k = MAP[("kids", "Детская одежда")][3]
    sql = f"""-- Абисто: дерево категорий как на kufar.by (13.11.2026). Выполнить один раз в Supabase → SQL Editor.
begin;
create table if not exists public.ads_cat_backup_20261113 as select id, cat, sub, attrs from public.ads;

-- Детская одежда делится на «для девочек» / «для мальчиков» / «до 1 года»
update public.ads set
  sub = case when attrs->>'kind' = 'Для новорождённых' then 'Одежда до 1 года'
             when attrs->>'gender' = 'Мальчик' then 'Одежда для мальчиков' else 'Одежда для девочек' end,
  attrs = case when attrs->>'kind' in ('Верхняя одежда','Школьная форма') then attrs
               when attrs->>'kind' = 'Спортивная' then attrs || '{{"kind":"Спортивная одежда"}}'::jsonb
               else coalesce(attrs,'{{}}'::jsonb) - 'kind' end
where cat = 'kids' and sub = 'Детская одежда';

create temp table catmap(oc text, os text, ok text, nc text, ns text, mode text, nk text) on commit drop;
insert into catmap values
{",\n".join(rows)};

update public.ads a set cat = x.nc, sub = x.ns,
  attrs = case x.mode when 'set' then coalesce(a.attrs,'{{}}'::jsonb) || jsonb_build_object('kind', x.nk)
                      when 'drop' then coalesce(a.attrs,'{{}}'::jsonb) - 'kind' else a.attrs end
from (select a2.id, m.* from public.ads a2 cross join lateral (
        select * from catmap m where m.oc = a2.cat and m.os = coalesce(a2.sub,'') and (m.ok is null or m.ok = a2.attrs->>'kind')
        order by m.ok is null limit 1) m) x
where a.id = x.id;

-- «Отдам даром» больше не раздел: такие объявления — с ценой «Бесплатно»
update public.ads set price_type = 'free', price = null where id in (select id from public.ads_cat_backup_20261113 where cat = 'free');

-- вид, которого нет в новой подкатегории, убираем
create temp table kinds_ok(cat text, sub text, kind text) on commit drop;
insert into kinds_ok values
{",\n".join(valid)};
update public.ads a set attrs = a.attrs - 'kind'
where a.attrs ? 'kind' and not exists (select 1 from kinds_ok k where k.cat = a.cat and k.sub = a.sub and k.kind = a.attrs->>'kind');

-- сохранённые поиски
update public.saved_searches s set params = jsonb_set(jsonb_set(s.params, '{{cat}}', to_jsonb(m.nc)), '{{sub}}', to_jsonb(m.ns))
from catmap m where m.ok is null and m.oc = s.params->>'cat' and m.os = coalesce(s.params->>'sub','') and coalesce(s.params->>'sub','') <> '';
update public.saved_searches set params = (params - 'sub') || '{{"cat":"","max":"0"}}'::jsonb where params->>'cat' = 'free';
commit;

-- проверка: какие разделы/подкатегории теперь у объявлений
select cat, sub, count(*) from public.ads group by 1, 2 order by 1, 2;
"""
    path = os.path.join(ROOT, "tools", "migration-2026-11-13-categories.sql")
    open(path, "w", encoding="utf-8").write(sql)
    return path

if __name__ == "__main__":
    print("SUB3 refs left:", build_index())
    print(build_sql())
