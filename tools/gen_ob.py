#!/usr/bin/env python3
"""Генератор статических страниц объявлений Абисто с ЧПУ: /ob/<id>-<slug>.

Запускается GitHub Actions (см. .github/workflows/ob.yml) раз в час.
Берёт активные объявления из Supabase (публичный ключ из config.js),
пишет ob/*.html и sitemap-ob.xml, удаляет страницы снятых объявлений.
Только стандартная библиотека Python.
"""
import json, os, re, html, urllib.request, datetime, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://abisto.by"
OUT = os.path.join(ROOT, "ob")

TR = {"а":"a","б":"b","в":"v","г":"g","д":"d","е":"e","ё":"e","ж":"zh","з":"z","и":"i","й":"y","к":"k","л":"l","м":"m",
      "н":"n","о":"o","п":"p","р":"r","с":"s","т":"t","у":"u","ф":"f","х":"h","ц":"c","ч":"ch","ш":"sh","щ":"sch","ъ":"",
      "ы":"y","ь":"","э":"e","ю":"yu","я":"ya","і":"i","ў":"u"}

def slug(t, n=60):
    s = "".join(TR.get(c, c) for c in str(t).lower())
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if len(s) > n:
        s = s[:n].rsplit("-", 1)[0] if "-" in s[:n] else s[:n]
    return s or "obyavlenie"

def ad_path(a):
    return "/ob/%d-%s" % (a["id"], slug(a.get("title") or ""))

def cfg():
    s = open(os.path.join(ROOT, "config.js"), encoding="utf-8").read()
    url = re.search(r'url:\s*"([^"]+)"', s).group(1)
    key = re.search(r'anonKey:\s*"([^"]+)"', s).group(1)
    return url, key

def fetch_ads(url, key):
    cols = "id,cat,sub,title,descr,price,price_type,haggle,cond,region,city,photos,created_at,bumped_at,currency,price_usd,is_demo"
    out, off = [], 0
    while True:
        q = "%s/rest/v1/ads?select=%s&status=eq.active&order=id.asc&limit=1000&offset=%d" % (url, cols, off)
        req = urllib.request.Request(q, headers={"apikey": key, "Authorization": "Bearer " + key})
        with urllib.request.urlopen(req, timeout=60) as r:
            part = json.loads(r.read().decode("utf-8"))
        out += part
        if len(part) < 1000:
            return out
        off += 1000

E = lambda s: html.escape(str(s if s is not None else ""), quote=True)

def price_text(a):
    if a.get("price_type") == "free":
        return "Даром"
    if a.get("price") is not None and a.get("price_type") != "deal":
        p = a["price"]
        p = int(p) if float(p).is_integer() else p
        return "{:,}".format(p).replace(",", "\u00a0") + "\u00a0ƃ"
    return "Договорная"

NO_COND = {"services", "jobs", "realty", "free"}

def page(a, cmap, siblings, photo_base):
    cat, sub = a.get("cat") or "", a.get("sub") or ""
    cname = cmap["cats"].get(cat, "")
    sslug = cmap["subs"].get(cat + "|" + sub)
    path = ad_path(a)
    url = SITE + path
    city = a.get("city") or a.get("region") or "Беларусь"
    pr = price_text(a)
    pr_seo = (" — %s руб." % ("{:g}".format(float(a["price"])))) if (a.get("price") is not None and a.get("price_type") == "fixed") else ""
    has_city = city.lower()[:max(4, len(city) - 1)] in a["title"].lower()
    title = "%s%s%s | Абисто" % (a["title"], pr_seo, "" if has_city else ", " + city)
    descr_raw = re.sub(r"\s+", " ", a.get("descr") or "").strip()
    meta_d = ("%s%s. %s%s. %s" % (a["title"], pr_seo, (sub + ", ") if sub else "", city, descr_raw))[:158]
    photos = [p for p in (a.get("photos") or []) if isinstance(p, str)][:10]
    img = lambda b, t=False: "%s/%s%s.jpg" % (photo_base, b, "_t" if t else "")
    og = img(photos[0]) if photos else SITE + "/og.png"
    bc = [("Абисто", SITE + "/")]
    if cname: bc.append((cname, SITE + "/kategorii/" + cat))
    if sslug: bc.append((sub, SITE + "/kategorii/" + sslug))
    bc.append((a["title"], url))
    ld_bc = {"@context": "https://schema.org", "@type": "BreadcrumbList",
             "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(bc)]}
    prod = {"@context": "https://schema.org", "@type": "Product", "name": a["title"], "url": url,
            "description": (descr_raw or a["title"])[:500]}
    if photos: prod["image"] = [img(p) for p in photos[:5]]
    if cname: prod["category"] = cname + (" / " + sub if sub else "")
    if a.get("price") is not None and a.get("price_type") == "fixed":
        prod["offers"] = {"@type": "Offer", "price": "{:g}".format(float(a["price"])), "priceCurrency": "BYN",
                          "availability": "https://schema.org/InStock", "url": url,
                          "itemCondition": "https://schema.org/NewCondition" if a.get("cond") == "new" else "https://schema.org/UsedCondition",
                          "areaServed": city}
    date = (a.get("bumped_at") or a.get("created_at") or "")[:10]
    try:
        d = datetime.date.fromisoformat(date); date_h = d.strftime("%d.%m.%Y")
    except Exception:
        date_h = ""
    facts = []
    if cat not in NO_COND and a.get("cond") in ("new", "used"):
        facts.append(("Состояние", "Новое" if a["cond"] == "new" else "Б/у"))
    if a.get("haggle"): facts.append(("Торг", "уместен"))
    facts.append(("Город", ", ".join(x for x in [a.get("city"), a.get("region")] if x) or "Беларусь"))
    if date_h: facts.append(("Опубликовано", date_h))
    gal = "".join('<a href="%s" target="_blank" rel="noopener"><img src="%s" alt="%s — фото %d" loading="%s" width="320" height="240"></a>'
                  % (E(img(p)), E(img(p, True)), E(a["title"]), i + 1, "eager" if i == 0 else "lazy") for i, p in enumerate(photos))
    sib = "".join('<a class="ad" href="%s"><b>%s</b>%s<div class="muted">%s</div></a>'
                  % (ad_path(s), E(price_text(s)), E(s["title"]), E(s.get("city") or "")) for s in siblings)
    descr_html = "<br>".join(E(l) for l in (a.get("descr") or "").splitlines()) or "Описание не указано."
    return f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(meta_d)}">
<link rel="canonical" href="{url}"><meta name="robots" content="index,follow">
<meta property="og:type" content="product"><meta property="og:site_name" content="Абисто"><meta property="og:locale" content="ru_BY">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(meta_d)}"><meta property="og:url" content="{url}"><meta property="og:image" content="{E(og)}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/kategorii/k.css">
<style>.ob{{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:20px;align-items:start}}.gal{{display:flex;gap:8px;overflow-x:auto;scroll-snap-type:x mandatory}}.gal img{{height:240px;width:auto;max-width:90vw;object-fit:cover;border-radius:12px;scroll-snap-align:start;background:#e8ecf2}}.box{{background:#fff;border:1px solid #dfe4ec;border-radius:12px;padding:16px}}.pr{{font-size:28px;font-weight:800;margin:0 0 10px}}.facts{{margin:0;display:grid;grid-template-columns:auto 1fr;gap:4px 12px;font-size:15px}}.facts dt{{color:#5b6880}}.facts dd{{margin:0}}.ds{{white-space:normal;max-width:780px}}@media(max-width:820px){{.ob{{grid-template-columns:1fr}}}}</style>
<script type="application/ld+json">{json.dumps(ld_bc, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(prod, ensure_ascii=False)}</script>
</head><body>
<header class="h"><div class="w"><a class="logo" href="/"><img src="/logo.svg" alt="" width="34" height="34">Abisto</a><a class="post" href="/#post">+ Подать объявление</a></div></header>
<main class="w">
<nav class="bc" aria-label="Навигация">{" › ".join('<a href="%s">%s</a>' % (u.replace(SITE, "") or "/", E(n)) for n, u in bc[:-1])} › <span>{E(a["title"])}</span></nav>
<h1>{E(a["title"])}</h1>
<div class="ob"><div>
{('<div class="gal">' + gal + '</div>') if gal else ''}
<h2>Описание</h2><p class="ds">{descr_html}</p>
</div><aside class="box"><p class="pr">{E(pr)}</p><dl class="facts">{"".join("<dt>%s</dt><dd>%s</dd>" % (E(k), E(v)) for k, v in facts)}</dl>
<p><a class="btn" href="/#ad/{a["id"]}">Написать продавцу</a><a class="btn sec" href="/#ad/{a["id"]}">Показать телефон</a></p></aside></div>
{('<h2>Похожие объявления' + (' — ' + E(sub) if sub else '') + '</h2><div class="ads">' + sib + '</div>') if sib else ''}
<p style="margin-top:24px">{('<a class="btn sec" href="/kategorii/%s">Все объявления «%s»</a>' % (sslug, E(sub))) if sslug else ''}<a class="btn sec" href="/#post">Подать объявление бесплатно</a></p>
</main>
<footer class="f"><div class="w"><a href="/kategorii/">Все категории</a> · <a href="/#rules">Правила</a> · <a href="/#privacy">Конфиденциальность</a> · © Абисто</div></footer>
<script src="/config.js"></script><script src="/kategorii/k.js"></script>
</body></html>
"""

def catmap():
    """Названия рубрик и ЧПУ подрубрик берём из хлебных крошек страниц kategorii/*.html."""
    m = {"cats": {}, "subs": {}}
    d = os.path.join(ROOT, "kategorii")
    for f in sorted(os.listdir(d)):
        if not f.endswith(".html"):
            continue
        s = open(os.path.join(d, f), encoding="utf-8").read()
        j = re.search(r'"BreadcrumbList","itemListElement":(\[.*?\])\}</script>', s)
        if not j:
            continue
        it = json.loads(j.group(1))
        if len(it) >= 3:
            m["cats"][it[2]["item"].rsplit("/", 1)[1]] = it[2]["name"]
        if len(it) == 4:
            m["subs"][it[2]["item"].rsplit("/", 1)[1] + "|" + it[3]["name"]] = it[3]["item"].rsplit("/", 1)[1]
    return m

def main():
    url, key = cfg()
    ads = json.load(open(sys.argv[1], encoding="utf-8")) if len(sys.argv) > 1 else fetch_ads(url, key)
    ads = [a for a in ads if not a.get("is_demo") and a.get("title")]
    cmap = catmap()
    photo_base = url + "/storage/v1/object/public/photos"
    os.makedirs(OUT, exist_ok=True)
    keep = set()
    by_sub = {}
    for a in sorted(ads, key=lambda x: x.get("bumped_at") or x.get("created_at") or "", reverse=True):
        by_sub.setdefault((a.get("cat"), a.get("sub")), []).append(a)
    for a in ads:
        sib = [s for s in by_sub.get((a.get("cat"), a.get("sub")), []) if s["id"] != a["id"]][:8]
        name = ad_path(a)[4:] + ".html"
        keep.add(name)
        p = os.path.join(OUT, name)
        new = page(a, cmap, sib, photo_base)
        if not os.path.exists(p) or open(p, encoding="utf-8").read() != new:
            open(p, "w", encoding="utf-8").write(new)
    for f in os.listdir(OUT):
        if f.endswith(".html") and f not in keep:
            os.remove(os.path.join(OUT, f))
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for a in sorted(ads, key=lambda x: x["id"]):
        lm = (a.get("bumped_at") or a.get("created_at") or "")[:10]
        sm.append("  <url><loc>%s%s</loc>%s<changefreq>weekly</changefreq><priority>0.6</priority></url>"
                  % (SITE, ad_path(a), ("<lastmod>%s</lastmod>" % lm) if lm else ""))
    sm.append("</urlset>")
    smt = "\n".join(sm) + "\n"
    sp = os.path.join(ROOT, "sitemap-ob.xml")
    if not os.path.exists(sp) or open(sp, encoding="utf-8").read() != smt:
        open(sp, "w", encoding="utf-8").write(smt)
    print("ads:", len(ads))

if __name__ == "__main__":
    main()
