/* abisto cats-fix (27.11.2026): плитки категорий на главной — ровная сетка в 2 ряда.
   Раньше ряды были разной длины, и последние плитки верхнего ряда висели без пары.
   Теперь плитки стоят столбиками по две (верх/низ), широкие — в паре с широкими, последние две — друг над другом.
   Разметку плиток делает штатная renderCats(); здесь только порядок. Подключается из config.js; чтобы отключить — удалить блок cats-fix. */
(function(){
  if(window.__abCatsFix) return; window.__abCatsFix=1;
  /* столбики: [верх, низ]; "*" — плитка «Все» */
  var COLS=[["*","electronics"],["realty","auto"],["jobs","services"],["clothes","phones"],["kids","computers"],["appliances","repair"],
    ["furniture","menswear"],["home","hobby"],["garden","animals"],["beauty","business"],["wedding","other"]];
  function css(){if(document.getElementById("catsFixCss"))return;var st=document.createElement("style");st.id="catsFixCss";
    st.textContent=".cat-row .cgrid{display:grid;grid-auto-flow:column;grid-template-rows:auto auto;gap:10px;width:max-content;padding-right:16px}";
    document.head.appendChild(st)}
  function arrange(){var row=document.getElementById("catRow");if(!row)return;
    var tiles=[].slice.call(row.querySelectorAll(".cat"));if(!tiles.length||row.querySelector(".cgrid"))return;
    var by={},used={},order=[];
    tiles.forEach(function(t){by[t.classList.contains("allcats")?"*":t.getAttribute("data-cat")]=t});
    COLS.forEach(function(c){c.forEach(function(k){if(by[k]&&!used[k]){order.push(by[k]);used[k]=1}})});
    tiles.forEach(function(t){var k=t.classList.contains("allcats")?"*":t.getAttribute("data-cat");if(!used[k]){order.push(t);used[k]=1}}); /* новые разделы — в конец */
    var g=document.createElement("div");g.className="cgrid";order.forEach(function(t){g.appendChild(t)});
    row.innerHTML="";row.appendChild(g)}
  var n=0;
  (function wait(){
    if(typeof renderCats==="function"){
      try{css();var _rc=renderCats;renderCats=function(){var r=_rc.apply(this,arguments);try{arrange()}catch(_){}return r};arrange()}
      catch(e){if(window.console)console.warn("cats-fix",e)} return}
    if(++n<400) setTimeout(wait,25);
  })();
})();
