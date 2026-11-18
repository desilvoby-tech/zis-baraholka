# -*- coding: utf-8 -*-
"""Генерирует статические SEO-страницы /kategorii/ и sitemap.xml по дереву kufar_tree.TREE.
Страницы старых подкатегорий превращаются в переадресацию на новые."""
import json, os, re, sys, html, datetime, urllib.parse
sys.path.insert(0, os.path.dirname(__file__))
from kufar_tree import TREE, MAP, subs_of, kinds_of, alias_of

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = os.path.join(ROOT, "kategorii")
SITE = "https://abisto.by"
TODAY = datetime.date.today().isoformat()
TRM = {"а":"a","б":"b","в":"v","г":"g","д":"d","е":"e","ё":"e","ж":"zh","з":"z","и":"i","й":"y","к":"k","л":"l","м":"m","н":"n","о":"o","п":"p","р":"r","с":"s","т":"t","у":"u","ф":"f","х":"h","ц":"c","ч":"ch","ш":"sh","щ":"sch","ъ":"","ы":"y","ь":"","э":"e","ю":"yu","я":"ya","і":"i","ў":"u"}
E = lambda s: html.escape(str(s), quote=True)
CITIES = "Минск, Гомель, Брест, Гродно, Витебск, Могилёв"

def slug(t):
    s = "".join(TRM.get(c, c) for c in t.lower())
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def page_slug(cid, sub=None):
    return cid if not sub else cid + "-" + slug(sub)

def hash_link(cid, sub=None, kind=None):
    p = ["c", cid] + ([sub] if sub else []) + ([kind] if kind else [])
    return "/#" + "/".join(urllib.parse.quote(x, safe="") for x in p)

def lower_list(xs):
    return ", ".join(x[0].lower() + x[1:] if not x[:2].isupper() else x for x in xs)

def page(title, desc, canon, crumbs, h1, intro, sections, dataq, robots="index,follow", extra_head=""):
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u} for i, (n, u) in enumerate(crumbs)]}
    bc = " › ".join(f'<a href="{E(u)}">{E(n)}</a>' for n, u in crumbs[:-1]) + f" › <span>{E(crumbs[-1][0])}</span>"
    sec = ""
    for h, items in sections:
        if items:
            sec += f"<h2>{E(h)}</h2><ul class=\"grid\">" + "".join(f'<li><a href="{E(u)}">{E(n)}</a></li>' for n, u in items) + "</ul>"
    ads = f'<h2>Свежие объявления</h2><div id="ads" class="ads" data-q="{E(dataq)}"><p class="muted">Загрузка…</p></div>' if dataq is not None else ""
    return f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}">
<link rel="canonical" href="{E(canon)}"><meta name="robots" content="{robots}">
<meta property="og:type" content="website"><meta property="og:site_name" content="Абисто"><meta property="og:locale" content="ru_BY">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{E(canon)}"><meta property="og:image" content="{SITE}/og.png">
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/kategorii/k.css">{extra_head}
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script></head>
<body><header class="h"><div class="w"><a class="logo" href="/"><img src="/logo.svg" alt="" width="34" height="34">Abisto</a><a class="post" href="/#post">+ Подать объявление</a></div></header>
<main class="w"><nav class="bc" aria-label="Навигация">{bc}</nav>
<h1>{E(h1)}</h1><p class="intro">{E(intro)}</p>
<p><a class="btn" href=""></a></p>
{sec}{ads}
<section class="faq"><h2>Как продать или купить на Абисто</h2><p>Абисто — бесплатная доска объявлений по всей Беларуси: {CITIES} и другие города. Разместить объявление можно за минуту: добавьте фото, цену и описание. Покупатели пишут в чат или звонят напрямую, без комиссии сайта.</p></section>
</main><footer class="f"><div class="w"><a href="/kategorii/">Все категории</a> · <a href="/#rules">Правила</a> · <a href="/#privacy">Конфиденциальность</a> · © Абисто</div></footer>
<script src="/config.js"></script><script src="/kategorii/k.js"></script></body></html>
'''

def with_buttons(doc, look):
    return doc.replace('<p><a class="btn" href=""></a></p>', f'<p><a class="btn" href="{E(look)}">Смотреть объявления</a> <a class="btn sec" href="/#post">Подать объявление бесплатно</a></p>')

def main():
    written, urls = set(), []
    cat_name = {cid: name for cid, name, _ in TREE}
    real = {}
    # главная каталога
    look = "/"
    doc = page("Каталог объявлений Беларуси — все категории | Абисто",
               "Все категории бесплатных объявлений в Беларуси: " + lower_list([n for _, n, _ in TREE[:8]]) + "…",
               SITE + "/kategorii/", [("Абисто", "/"), ("Каталог", "/kategorii/")], "Каталог объявлений",
               f"На Абисто {len(TREE)} разделов и сотни подкатегорий объявлений по всей Беларуси — как на Куфаре. Выберите раздел, чтобы посмотреть свежие предложения от частных лиц и магазинов.",
               [("Категории", [(n, "/kategorii/" + cid) for cid, n, _ in TREE])], None)
    open(os.path.join(K, "index.html"), "w", encoding="utf-8").write(with_buttons(doc, look)); written.add("index.html")
    urls.append((SITE + "/kategorii/", "0.8"))
    for cid, name, subs in TREE:
        items = []
        for x in subs:
            s = subs_of(x); al = alias_of(x)
            items.append((s, "/kategorii/" + page_slug(*(al if al else (cid, s)))))
            if not al:
                real[(cid, s)] = kinds_of(x)
        names = [subs_of(x) for x in subs]
        doc = page(f"{name} — купить и продать в Беларуси | Абисто",
                   f"{name} в Беларуси: свежие объявления — {lower_list(names[:3])}. {CITIES}. Цены и фото, без комиссии на Абисто.",
                   f"{SITE}/kategorii/{cid}", [("Абисто", "/"), ("Каталог", "/kategorii/"), (name, "/kategorii/" + cid)],
                   f"{name} в Беларуси", f"Объявления в категории «{name}» по всей Беларуси: {lower_list(names)}.",
                   [("Подкатегории", items)], cid)
        open(os.path.join(K, cid + ".html"), "w", encoding="utf-8").write(with_buttons(doc, hash_link(cid))); written.add(cid + ".html")
        urls.append((f"{SITE}/kategorii/{cid}", "0.8"))
    for (cid, s), kinds in real.items():
        name = cat_name[cid]
        sib = [(subs_of(x), "/kategorii/" + page_slug(*(alias_of(x) or (cid, subs_of(x))))) for c2, _, ss in TREE if c2 == cid for x in ss if subs_of(x) != s]
        kk = kinds or []
        desc_tail = (" — " + lower_list(kk[:3])) if kk else ""
        doc = page(f"{s} — купить и продать в Беларуси | Абисто",
                   f"{s} в Беларуси: свежие объявления{desc_tail}. {CITIES}. Цены и фото, без комиссии на Абисто.",
                   f"{SITE}/kategorii/{page_slug(cid, s)}",
                   [("Абисто", "/"), ("Каталог", "/kategorii/"), (name, "/kategorii/" + cid), (s, "/kategorii/" + page_slug(cid, s))],
                   f"{s} в Беларуси",
                   f"Объявления «{s}» в разделе «{name}» по всей Беларуси" + (f": {lower_list(kk)}." if kk else "."),
                   [("Похожие подкатегории", sib), ("Виды", [(k, hash_link(cid, s, k)) for k in kk])], f"{cid}|{s}")
        fn = page_slug(cid, s) + ".html"
        assert fn not in written, fn
        open(os.path.join(K, fn), "w", encoding="utf-8").write(with_buttons(doc, hash_link(cid, s))); written.add(fn)
        urls.append((f"{SITE}/kategorii/{page_slug(cid, s)}", "0.6"))
    # старые страницы -> переадресация
    redirected = 0
    for fn in sorted(os.listdir(K)):
        if not fn.endswith(".html") or fn in written:
            continue
        old_slug = fn[:-5]
        target = None
        cid = old_slug.split("-", 1)[0]
        for (oc, os_), (nc, ns, _, _) in MAP.items():
            if os_ and page_slug(oc, os_) == old_slug and ns != "@GENDER":
                target = page_slug(nc, ns)
        if old_slug == "kids-detskaya-odezhda":
            target = page_slug("kids", "Одежда для девочек")
        if old_slug.startswith("free"):
            target = None
        if target is None:
            target = cid if cid in cat_name else ""
        url = "/kategorii/" + target
        open(os.path.join(K, fn), "w", encoding="utf-8").write(
            f'<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>Раздел переехал | Абисто</title>'
            f'<link rel="canonical" href="{SITE}{url}"><meta name="robots" content="noindex,follow">'
            f'<meta http-equiv="refresh" content="0;url={url}"></head><body><p>Раздел переехал: <a href="{url}">{SITE}{url}</a></p></body></html>\n')
        redirected += 1
    # sitemap: заменяем блок каталога
    sm = open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()
    keep = [l for l in sm.splitlines() if "<url>" in l and "/kategorii/" not in l]
    head = [l for l in keep if "<loc>https://abisto.by/</loc>" in l]
    rest = [l for l in keep if l not in head]
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'] + head
    lines += [f"  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod><changefreq>daily</changefreq><priority>{p}</priority></url>" for u, p in urls]
    lines += rest + ["</urlset>"]
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(len(written), "pages,", redirected, "redirects,", len(urls), "catalog urls in sitemap")

if __name__ == "__main__":
    main()
