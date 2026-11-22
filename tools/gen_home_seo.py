# -*- coding: utf-8 -*-
"""Пересобирает статический блок «Категории объявлений» (<div class="seo-cats">) в index.html
по дереву tools/kufar_tree.TREE — те же разделы, названия, порядок и адреса, что в /kategorii/.
Запускать после tools/gen_kategorii.py:  python3 tools/gen_home_seo.py"""
import os, re, sys, html
sys.path.insert(0, os.path.dirname(__file__))
from kufar_tree import TREE, subs_of, alias_of

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = lambda s: html.escape(str(s), quote=True)
TRM = {"а":"a","б":"b","в":"v","г":"g","д":"d","е":"e","ё":"e","ж":"zh","з":"z","и":"i","й":"y","к":"k","л":"l","м":"m","н":"n","о":"o","п":"p","р":"r","с":"s","т":"t","у":"u","ф":"f","х":"h","ц":"c","ч":"ch","ш":"sh","щ":"sch","ъ":"","ы":"y","ь":"","э":"e","ю":"yu","я":"ya","і":"i","ў":"u"}

def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", "".join(TRM.get(c, c) for c in t.lower())).strip("-")

def page_slug(cid, sub=None):  # как в gen_kategorii.py
    return cid if not sub else cid + "-" + slug(sub)

def block():
    out = []
    for cid, name, subs in TREE:
        li = []
        for x in subs:
            s = subs_of(x); al = alias_of(x)
            li.append(f'<li><a href="/kategorii/{page_slug(*(al if al else (cid, s)))}">{E(s)}</a></li>')
        out.append(f'<section><h3><a href="/kategorii/{cid}">{E(name)}</a></h3><ul>{"".join(li)}</ul></section>')
    return '<div class="seo-cats">' + "".join(out) + "</div>"

def main():
    p = os.path.join(ROOT, "index.html")
    s = open(p, encoding="utf-8").read()
    a = s.index('<div class="seo-cats">')
    b = s.index("</div>", a) + len("</div>")
    assert "<div" not in s[a + 5:b - 6], "внутри seo-cats неожиданно есть <div>"
    s = s[:a] + block() + s[b:]
    # проверка: все ссылки блока ведут на существующие «живые» страницы /kategorii/ (не на переадресации)
    kd = os.path.join(ROOT, "kategorii")
    if os.path.isdir(kd):
        bad = []
        for u in re.findall(r'href="/kategorii/([a-z0-9-]+)"', block()):
            f = os.path.join(kd, u + ".html")
            if not os.path.exists(f) or "Раздел переехал" in open(f, encoding="utf-8").read():
                bad.append(u)
        if bad:
            print("ВНИМАНИЕ, ссылки на отсутствующие/переадресующие страницы:", bad)
    open(p, "w", encoding="utf-8").write(s)
    print("seo-cats:", len(TREE), "разделов,", sum(len(x[2]) for x in TREE), "подкатегорий")

if __name__ == "__main__":
    main()
