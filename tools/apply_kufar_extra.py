# -*- coding: utf-8 -*-
"""Ручные правки к категориям как на Куфаре: подсказки поиска, верхнее меню, «Даром»."""
import os
p=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'index.html');s=open(p,encoding='utf-8').read()
def rep(o,n):
    global s
    assert o in s,o[:60]; s=s.replace(o,n,1)
rep('for(const k of SUB3[x]||[])if(','for(const k of (c.alias&&c.alias[x]?[]:SUB3[c.id+"|"+x])||[])if(')
import re
m=re.search(r'<a href="#" data-topcat="realty">Недвижимость</a>.*?data-topcat="free">Отдам даром</a>',s)
assert m; s=s[:m.start()]+'<a href="#" data-topcat="realty">Недвижимость</a><a href="#" data-topcat="auto">Авто</a><a href="#" data-topcat="services">Услуги</a><a href="#" data-topcat="jobs">Работа</a><a href="#" data-topcat="business">Для бизнеса</a><a href="#" data-topcat="free">Даром</a>'+s[m.end():]
rep('S={...freshFilters(),cat:a.dataset.topcat};goHome()','S={...freshFilters(),cat:a.dataset.topcat==="free"?"":a.dataset.topcat};if(a.dataset.topcat==="free")S.max="0";goHome()')
rep('if(S.min||S.max)L.push(["price",(S.min?"от "+S.min:"")+(S.max?" до "+S.max:"")+"\\u00a0ƃ"]);','if(S.min||S.max)L.push(["price",S.max==="0"&&!S.min?"Даром":(S.min?"от "+S.min:"")+(S.max?" до "+S.max:"")+"\\u00a0ƃ"]);')
rep('if(s.min||s.max)parts.push((s.min?"от "+s.min:"")+(s.max?" до "+s.max:"")+"\\u00a0ƃ");','if(s.min||s.max)parts.push(s.max==="0"&&!s.min?"даром":(s.min?"от "+s.min:"")+(s.max?" до "+s.max:"")+"\\u00a0ƃ");')
s=s.replace('Каталог Абисто: 22 категории и сотни подкатегорий','Каталог Абисто: 21 раздел и сотни подкатегорий, как на Куфаре')
open(p,'w',encoding='utf-8').write(s)
