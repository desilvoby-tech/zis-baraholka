#!/usr/bin/env python3
"""SEO-тексты для страниц каталога /kategorii/ (abisto.by).

Отдельный шаг после tools/gen_ob.py в .github/workflows/ob.yml. Код генераторов не меняет:
- вставляет блок текста между метками <!--seo-text-->…<!--/seo-text--> перед секцией «Как продать или купить»;
- подкатегориям без активных объявлений ставит noindex,follow, с первым объявлением — снова index,follow;
  основные разделы и корень каталога всегда index;
- noindex-подкатегории убирает из sitemap.xml, с первым объявлением возвращает адрес обратно.
Смысловые тексты — в tools/seo_texts.json (раздел без текста получает только абзац с данными).
Данные — активные объявления из Supabase по публичному ключу из config.js. Нулевые значения не выводятся.
Только стандартная библиотека Python.
"""
import hashlib, html, json, os, re, sys, urllib.request, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KDIR = os.path.join(ROOT, "kategorii")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kufar_tree import TREE  # noqa: E402

E = lambda s: html.escape(str(s), quote=True)
MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
CITY_IN = {"Минск": "Минске", "Гомель": "Гомеле", "Брест": "Бресте", "Гродно": "Гродно", "Витебск": "Витебске",
           "Могилёв": "Могилёве", "Могилев": "Могилёве", "Бобруйск": "Бобруйске", "Барановичи": "Барановичах",
           "Борисов": "Борисове", "Пинск": "Пинске", "Орша": "Орше", "Мозырь": "Мозыре", "Солигорск": "Солигорске",
           "Новополоцк": "Новополоцке", "Лида": "Лиде", "Молодечно": "Молодечно", "Полоцк": "Полоцке",
           "Жлобин": "Жлобине", "Светлогорск": "Светлогорске", "Речица": "Речице", "Слуцк": "Слуцке",
           "Жодино": "Жодино", "Кобрин": "Кобрине", "Слоним": "Слониме", "Волковыск": "Волковыске"}
ROBOTS_RE = re.compile(r'<meta name="robots" content="[^"]*"\s*/?>')
DATAQ_RE = re.compile(r'data-q="([^"]*)"')
BLOCK_RE = re.compile(r"<!--seo-text-->.*?<!--/seo-text--> ?", re.S)
ANCHOR = '<section class="faq">'


def city_in(c):
    if c in CITY_IN:
        return "в " + CITY_IN[c]
    if c.endswith(("ь", "й")):
        return "в " + c[:-1] + "е"
    if c.endswith(("а", "я")):
        return "в " + c[:-1] + "е"
    if c.endswith(("о", "е", "и", "ы", "у")):
        return "в г. " + c
    return "в " + c + "е"


def plural(n, one, few, many):
    n = abs(n) % 100
    if 11 <= n <= 19:
        return many
    n %= 10
    return one if n == 1 else few if 2 <= n <= 4 else many


def pick(key, variants):
    h = int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16)
    return variants[h % len(variants)]


def fmt_price(p):
    p = int(p) if float(p).is_integer() else round(float(p), 2)
    return "{:,}".format(p).replace(",", " ")


def fmt_date(iso):
    d = datetime.date.fromisoformat(iso[:10])
    return f"{d.day} {MONTHS[d.month - 1]} {d.year} года"


def cfg():
    s = open(os.path.join(ROOT, "config.js"), encoding="utf-8").read()
    url = re.search(r'url\s*:\s*["\']([^"\']+)', s).group(1)
    key = re.search(r'anonKey\s*:\s*["\']([^"\']+)', s).group(1)
    return url, key


def fetch_ads():
    url, key = cfg()
    out, off = [], 0
    cols = "id,cat,sub,price,price_type,city,created_at,bumped_at,is_demo"
    while True:
        q = "%s/rest/v1/ads?select=%s&status=eq.active&order=id.asc&limit=1000&offset=%d" % (url, cols, off)
        req = urllib.request.Request(q, headers={"apikey": key, "Authorization": "Bearer " + key})
        with urllib.request.urlopen(req, timeout=60) as r:
            b = json.loads(r.read().decode("utf-8"))
        out += b
        off += 1000
        if len(b) < 1000:
            return [a for a in out if not a.get("is_demo")]


def tree_index():
    """cid -> (name, {sub: [kinds]})"""
    idx = {}
    for cid, name, subs in TREE:
        d = {}
        for s in subs:
            if isinstance(s, (list, tuple)):
                d[s[0]] = list(s[1])
            else:
                d[s] = []
        idx[cid] = (name, d)
    return idx


def lower_first(s):
    """«Ноутбуки» -> «ноутбуки», но «MacBook», «SSD», «PlayStation», «0+» не трогаем."""
    if len(s) > 1 and "А" <= s[0] <= "Я" and s[1].islower():
        return s[0].lower() + s[1:]
    return s


def join_ru(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " и " + xs[-1]


def kinds_text(kinds):
    return join_ru([lower_first(k) for k in kinds])


def cities_text(cs):
    """['Гомель','Гродно','Минск'] -> 'в Гомеле, Гродно и Минске'"""
    parts = [city_in(c) for c in cs]
    parts = [parts[0]] + [p[2:] if p.startswith("в ") and not p.startswith("в г. ") else p for p in parts[1:]]
    return join_ru(parts)


def data_paragraph(key, ads, where):
    """where: 'в этой подкатегории' / 'в разделе'. Возвращает HTML-абзац или ''."""
    n = len(ads)
    if not n:
        return ""
    noun = plural(n, "объявление", "объявления", "объявлений")
    s1 = pick(key + "|n", [f"Сейчас {where} {n} {plural(n, 'активное', 'активных', 'активных')} {noun}",
                           f"На Абисто {where} сейчас {n} {noun}",
                           f"{where[0].upper() + where[1:]} сейчас {n} {noun}"])
    cities = {}
    for a in ads:
        c = (a.get("city") or "").strip()
        if c:
            cities[c] = cities.get(c, 0) + 1
    top = sorted(cities, key=lambda c: (-cities[c], c))
    if len(top) == 1:
        s1 += (", все — " if n > 1 else " — ") + city_in(top[0]) + "."
    elif top:
        if len(top) <= 3:
            s1 += ": " + cities_text(top) + "."
        else:
            s1 += ": " + cities_text(top[:3] + ["__"]).rsplit(" и ", 1)[0] + " и других городах."
    else:
        s1 += "."
    parts = [s1]
    priced = sorted(float(a["price"]) for a in ads if a.get("price") is not None and a.get("price_type") not in ("free", "deal"))
    deal = sum(1 for a in ads if a.get("price_type") == "deal")
    free = sum(1 for a in ads if a.get("price_type") == "free")
    if len(priced) >= 3:
        parts.append(pick(key + "|p", [f"Цены — от {fmt_price(priced[0])} до {fmt_price(priced[-1])} ƃ.",
                                        f"Цены в объявлениях — от {fmt_price(priced[0])} до {fmt_price(priced[-1])} ƃ."]))
    elif deal == n:
        parts.append(pick(key + "|d", ["Цены в них договорные: точную сумму обсуждают с продавцом или исполнителем.",
                                        "Цена во всех объявлениях договорная — её уточняют в переписке или по телефону."]))
    if free:
        parts.append(f"{free} {plural(free, 'объявление', 'объявления', 'объявлений')} — «даром».")
    newest = max((a.get("bumped_at") or a.get("created_at") or "") for a in ads)
    if newest:
        parts.append(pick(key + "|t", [f"Последнее объявление добавлено или обновлено {fmt_date(newest)}.",
                                        f"Самое свежее объявление — от {fmt_date(newest)}."]))
    return "<p>" + E(" ".join(parts)) + "</p>"


def section_block(texts, cid, sub, name, kinds, ads, key):
    sec = texts.get("sections", {}).get(cid) or {}
    subt = texts.get("subs", {}).get(f"{cid}|{sub}") if sub else None
    out = []
    title = (subt or {}).get("h2") or (f"{sub}: {sec['h2_sub']}" if sub and sec.get("h2_sub") else sec.get("h2") if not sub else None)
    if not title:
        title = f"{sub or name} на Абисто"
    out.append(f"<h2>{E(title)}</h2>")
    if subt and subt.get("about"):
        out.append(f"<p>{E(subt['about'])}</p>")
    elif sub and kinds:
        out.append("<p>" + E(pick(key + "|k", [f"В подкатегории «{sub}» — объявления о том, что ищут чаще всего: {kinds_text(kinds)}.",
                                              f"Здесь собраны объявления «{sub}»: {kinds_text(kinds)}."])) + "</p>")
    elif not sub and sec.get("about"):
        out.append(f"<p>{E(sec['about'])}</p>")
    if sub and not ads:
        # пустая подкатегория (noindex): коротко, без общих советов раздела — их нет смысла дублировать
        out.append("<p>" + E(pick(key + "|e", [f"Объявлений в подкатегории «{sub}» пока нет. Разместите первое — это бесплатно.",
                                              "Здесь пока нет объявлений. Подайте своё бесплатно — его увидят посетители Абисто."])) + "</p>")
        return '<section class="seo-text">' + "".join(out) + "</section>"
    dp = data_paragraph(key, ads, "в этой подкатегории" if sub else "в разделе")
    if dp:
        out.append(dp)
    for k in ("tips", "safety"):
        src = subt if (subt and subt.get(k)) else sec   # подкатегория может переопределить советы раздела
        if src.get(k):
            ttl = src.get(k + "_title") or sec.get(k + "_title")
            out.append(f"<p><b>{E(ttl)}</b> {E(src[k])}</p>" if ttl else f"<p>{E(src[k])}</p>")
    if sec.get("cta"):
        out.append(f"<p>{E(sec['cta'])}</p>")
    return '<section class="seo-text">' + "".join(out) + "</section>"


def shingles(block_html):
    w = html.unescape(re.sub(r"<[^>]+>", " ", block_html)).lower().split()
    return {tuple(w[i:i + 5]) for i in range(len(w) - 4)}


def similarity_warnings(blocks):
    """blocks: [(file, html)] индексируемых страниц по порядку. Предупреждение, если у соседей > 60% общих шинглов."""
    sh = [(f, shingles(b)) for f, b in blocks]
    for (fa, a), (fb, b) in zip(sh, sh[1:]):
        j = len(a & b) / max(1, len(a | b))
        if j > 0.6:
            print(f"::warning::seo_text: похожие тексты {fa} и {fb}: {j:.0%}")


SITE = "https://abisto.by/kategorii/"


def sync_sitemap(sub_state):
    """sub_state: {slug: (indexed, newest_iso)} для подкатегорий. noindex-адреса убираем из sitemap.xml,
    а когда в подкатегории появляется объявление — возвращаем (в формате gen_kategorii.py, priority 0.6).
    Основные разделы и прочие адреса не трогаем. Возвращает (убрано, добавлено)."""
    p = os.path.join(ROOT, "sitemap.xml")
    if not os.path.exists(p):
        return 0, 0
    src = open(p, encoding="utf-8").read()
    lines = src.split("\n")
    present = {}
    for i, ln in enumerate(lines):
        m = re.search(r"<loc>" + re.escape(SITE) + r"([^<]+)</loc>", ln)
        if m:
            present[m.group(1)] = i
    drop = {present[s] for s, (ix, _) in sub_state.items() if not ix and s in present}
    add = [s for s, (ix, _) in sorted(sub_state.items()) if ix and s not in present]
    if not drop and not add:
        return 0, 0
    out = [ln for i, ln in enumerate(lines) if i not in drop]
    last = max((i for i, ln in enumerate(out) if "<loc>" + SITE in ln), default=None)
    if last is None:
        last = next(i for i, ln in enumerate(out) if "</urlset>" in ln) - 1
    new = [f"  <url><loc>{SITE}{s}</loc><lastmod>{(sub_state[s][1] or datetime.date.today().isoformat())[:10]}</lastmod>"
           f"<changefreq>daily</changefreq><priority>0.6</priority></url>" for s in add]
    out[last + 1:last + 1] = new
    open(p, "w", encoding="utf-8").write("\n".join(out))
    return len(drop), len(add)


def main():
    texts = json.load(open(os.path.join(ROOT, "tools", "seo_texts.json"), encoding="utf-8"))
    enabled = set(texts.get("enabled", []))
    ads = fetch_ads()
    idx = tree_index()
    stats = {"pages": 0, "text": 0, "noindex": 0, "index": 0, "changed": 0}
    indexed_blocks = []
    sub_state = {}
    for f in sorted(os.listdir(KDIR)):
        if not f.endswith(".html") or f == "index.html":
            continue
        p = os.path.join(KDIR, f)
        t = open(p, encoding="utf-8").read()
        if 'http-equiv="refresh"' in t:
            continue
        m = DATAQ_RE.search(t)
        if not m:
            continue
        stats["pages"] += 1
        cid, _, sub = html.unescape(m.group(1)).partition("|")
        mine = [a for a in ads if a.get("cat") == cid and (not sub or a.get("sub") == sub)]
        t2 = BLOCK_RE.sub("", t)
        if cid in enabled and cid in idx and ANCHOR in t2:
            name, subs = idx[cid]
            blk = section_block(texts, cid, sub, name, subs.get(sub, []), mine, f)
            t2 = t2.replace(ANCHOR, "<!--seo-text-->" + blk + "<!--/seo-text--> " + ANCHOR, 1)
            stats["text"] += 1
            if not sub or mine:
                indexed_blocks.append((f, blk))
        if sub:
            robots = "index,follow" if mine else "noindex,follow"
            t2 = ROBOTS_RE.sub(f'<meta name="robots" content="{robots}">', t2, count=1)
            stats["index" if mine else "noindex"] += 1
            sub_state[f[:-5]] = (bool(mine), max(((a.get("bumped_at") or a.get("created_at") or "") for a in mine), default=""))
        if t2 != t:
            open(p, "w", encoding="utf-8").write(t2)
            stats["changed"] += 1
    stats["sitemap_removed"], stats["sitemap_added"] = sync_sitemap(sub_state)
    similarity_warnings(indexed_blocks)
    print("seo_text:", stats, "ads:", len(ads))


if __name__ == "__main__":
    main()
