# -*- coding: utf-8 -*-
"""Мобильная шапка как в приложениях Куфара и Авито: одна строка «поиск + фильтры», город в подсказке."""
import os
p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'index.html')
s = open(p, encoding='utf-8').read()

def rep(o, n):
    global s
    assert o in s, o[:70]
    s = s.replace(o, n, 1)

SLIDERS = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 7h9M17 7h3M4 17h3M11 17h9"/><circle cx="15" cy="7" r="2.3"/><circle cx="9" cy="17" r="2.3"/></svg>'

# кнопка фильтров рядом с поиском (видна только на телефоне)
rep('<label class="loc" title="Регион">',
    '<button class="m-filt" id="mFilt" type="button" aria-label="Фильтры и регион">' + SLIDERS + '<span class="fbadge" id="mFiltN" hidden></span></button>\n    <label class="loc" title="Регион">')

# стили
rep('@media (max-width:860px){\n  .topbar{display:none}',
    '''.m-filt{display:none}
@media (max-width:860px){
  header .hrow{flex-wrap:nowrap;gap:10px;padding-block:10px}
  header .logo,header .catalog-btn,header .loc,header .geo-btn,header .hnav{display:none!important}
  header .hrow .search{order:0;flex:1 1 auto;height:48px;border-radius:14px;min-width:0}
  header .search button{order:-1;padding:0 2px 0 14px;height:48px}
  header .search input{height:48px;padding:0 14px 0 10px;font-size:17px}
  header .search input::-webkit-search-cancel-button{display:none}
  .m-filt{display:grid;place-items:center;flex:none;width:48px;height:48px;border:0;border-radius:14px;background:#eef1f5;color:#1d2633;position:relative;cursor:pointer}
  .m-filt svg{width:24px;height:24px}
  .m-filt .fbadge{position:absolute;top:4px;right:4px;min-width:18px;height:18px;line-height:18px;border-radius:9px;background:var(--accent);color:#fff;font-size:11px;font-weight:700;padding:0 5px}
  :root[data-theme="dark"] .m-filt{background:#222;color:#eee}
}
@media (max-width:860px) and (prefers-color-scheme:dark){:root:not([data-theme="light"]) .m-filt{background:#222;color:#eee}}
@media (max-width:860px){
  .topbar{display:none}''')

# город в подсказке поиска («Поиск в Гомеле»), счётчик фильтров на кнопке
rep('function resolveAlias(){',
    '''function inCity(n){
  const ex={"Гродно":"Гродно","Молодечно":"Молодечно","Жодино":"Жодино","Иваново":"Иваново","Глубокое":"Глубоком","Минск":"Минске"};
  if(ex[n])return ex[n];
  if(/ская обл\\.$/.test(n))return n.replace(/ская обл\\.$/,"ской обл.");
  if(/ичи$/.test(n))return n.replace(/и$/,"ах");
  if(/[ьй]$/.test(n))return n.slice(0,-1)+"е";
  if(/[ая]$/.test(n))return n.slice(0,-1)+"е";
  if(/[оеиуы]$/.test(n))return n;
  return n+"е";
}
function updMobileSearch(){
  const q=$("#q"),b=$("#mFiltN");if(!q)return;
  const mob=matchMedia("(max-width:860px)").matches,place=S.city||S.region;
  q.placeholder=mob?(place?"Поиск в "+inCity(place):"Поиск по всей Беларуси"):"Поиск объявлений";
  if(b){const n=afCount()-(S.q?1:0);b.hidden=!(n>0);b.textContent=n>0?n:""}
}
function resolveAlias(){''')
rep('async function renderHome(){\n  resolveAlias();\n', 'async function renderHome(){\n  resolveAlias();updMobileSearch();\n')

# нажатие на кнопку фильтров: открыть панель (с выбором области и города)
rep('$("#regionTop").addEventListener("change",',
    '''$("#mFilt").addEventListener("click",()=>{filtersOpen=true;if(currentView()==="home"){const pn=document.querySelector("aside.panel");if(pn)pn.classList.add("open")}else goHome()});
  matchMedia("(max-width:860px)").addEventListener("change",updMobileSearch);updMobileSearch();
  $("#regionTop").addEventListener("change",''')
open(p, 'w', encoding='utf-8').write(s)
rep('  header .hrow{flex-wrap:wrap;gap:10px}\n  header .search{order:5;flex-basis:100%}\n','')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
