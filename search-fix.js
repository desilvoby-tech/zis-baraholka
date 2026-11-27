/* abisto search-fix (аудит, модуль 2, 27.11.2026): поиск и фильтры. Свой код.
   - фильтры в адресе страницы (?q=&cat=&sub=&region=&city=&min=&max=&sort=&e.поле=&f.поле=&t.поле=), восстановление по ссылке и после F5;
   - числа в фильтрах: «1,5» → 1.5, «1.2.3» больше не даёт ошибку базы; «от» > «до» — меняются местами;
   - ответ на устаревший запрос не перезаписывает выдачу (быстрая смена фильтров, «Показать ещё»);
   - пустая выдача по запросу латиницей → поиск в русской раскладке (ghjlfv → продам);
   - символы % _ \ в запросе не работают как шаблон;
   - (v2) пустая выдача → поиск по словам в любом порядке и форме («угловой диван», «ремонт ноутбука», «елку»),
     пока в базе не подключён tools/migration-2026-11-23-search.sql (до 100 объявлений);
   - (v2) «Сбросить фильтры» оставляет подкатегорию, как «Сбросить всё»;
   - (v3) бытовые слова («стиралка», «холодос», «телик», «велик») и опечатки («холодильнек») —
     по словарю из названий разделов, подкатегорий и видов; если объявлений нет — ссылка на подходящий раздел.
   Подключается из config.js. Чтобы отключить — удалить блок search-fix в config.js. */
(function(){
  if(window.__abSearchFix) return; window.__abSearchFix=1;
  /* #c/раздел из ссылки важнее фильтров в адресе (адрес берём из записи навигации: роутер мог уже заменить хэш) */
  var initHash=location.hash;try{var ne=performance.getEntriesByType("navigation")[0];if(ne&&ne.name)initHash=new URL(ne.name).hash}catch(_){}

  function numIn(v){v=String(v==null?"":v).replace(/,/g,".").replace(/[^\d.]/g,"");var i=v.indexOf(".");
    if(i>=0)v=v.slice(0,i+1)+v.slice(i+1).replace(/\./g,"");v=v.replace(/\.$/,"");return v.charAt(0)==="."?"0"+v:v}
  function fixRange(a,b){a=a||"";b=b||"";if(a!==""&&b!==""&&+a>+b)return [b,a];return [a,b]}
  var SORTS=["new","cheap","dear","popular"];
  var SKEYS=["q","cat","sub","region","city","cond","min","max","user","photo","sort"];
  function isSKey(k){return SKEYS.indexOf(k)>=0||/^[eft]\./.test(k)}
  function hasSKeys(str){var u=new URLSearchParams(str),r=false;u.forEach(function(v,k){if(isSKey(k))r=true});return r}
  var EN_RU={q:"й",w:"ц",e:"у",r:"к",t:"е",y:"н",u:"г",i:"ш",o:"щ",p:"з","[":"х","]":"ъ",a:"ф",s:"ы",d:"в",f:"а",g:"п",h:"р",j:"о",k:"л",l:"д",";":"ж","'":"э",z:"я",x:"ч",c:"с",v:"м",b:"и",n:"т",m:"ь",",":"б",".":"ю","`":"ё"};
  function fixLayout(q){if(!/^[a-z\[\];',.`\s]+$/i.test(q)||!/[a-z]/i.test(q))return "";
    var r=q.toLowerCase().split("").map(function(c){return EN_RU[c]!=null?EN_RU[c]:c}).join("");
    return /[а-яё]/.test(r)&&r!==q.toLowerCase()?r:""}
  /* грубое русское окончание: «стиральную» → «стиральн», «ноутбука» → «ноутбук» */
  var END=/^(.{4,}?)(иями|ями|ами|ого|его|ому|ему|ыми|ими|ий|ый|ой|ая|яя|ое|ее|ые|ие|ую|юю|ах|ях|ам|ям|ом|ем|ов|ев|ей|ия|ье|а|я|у|ю|ы|и|е|о|ь|й)$/;
  function stem(w){if(w.length<5)return w;var m=END.exec(w);return m?m[1]:w}
  function yo(t){return String(t||"").toLowerCase().replace(/ё/g,"е")}
  /* бытовые слова → как пишут в объявлениях */
  var SYN={"стиралка":"стиральная машина","стиралку":"стиральная машина","стиралки":"стиральная машина","стиралок":"стиральная машина",
    "посудомойка":"посудомоечная машина","посудомойку":"посудомоечная машина","посудомойки":"посудомоечная машина",
    "холодос":"холодильник","холодосы":"холодильник","холодоса":"холодильник","микроволновая":"микроволновка","свч":"микроволновка",
    "телик":"телевизор","телики":"телевизор","телек":"телевизор","телека":"телевизор",
    "велик":"велосипед","велики":"велосипед","велика":"велосипед","самокатик":"самокат",
    "ноуты":"ноутбук","ноута":"ноутбук","комп":"компьютер","компы":"компьютер","компа":"компьютер","пк":"компьютер",
    "мобила":"телефон","мобилу":"телефон","мобильник":"телефон","мобильники":"телефон","смарт":"смартфон","айфон":"iphone","айфоны":"iphone",
    "пылик":"пылесос","кофемашинка":"кофемашина","тачка":"автомобиль","тачку":"автомобиль","машинка":"машина",
    "кроссы":"кроссовки","кросы":"кроссовки","джинсики":"джинсы","колонка":"колонки","наушы":"наушники",
    "диванчик":"диван","столик":"стол","шкафчик":"шкаф","кроватка":"кровать"};
  function lev(a,b,max){if(Math.abs(a.length-b.length)>max)return max+1;var prev=[],cur,i,j;for(j=0;j<=b.length;j++)prev[j]=j;
    for(i=1;i<=a.length;i++){cur=[i];var lo=i;for(j=1;j<=b.length;j++){cur[j]=Math.min(prev[j]+1,cur[j-1]+1,prev[j-1]+(a[i-1]===b[j-1]?0:1));if(cur[j]<lo)lo=cur[j]}
      if(lo>max)return max+1;prev=cur}return prev[b.length]}

  function install(){
    function sToQS(s,base){var u=new URLSearchParams(base||"");
      Array.from(u.keys()).filter(isSKey).forEach(function(k){u.delete(k)});
      ["q","cat","sub","region","city","cond","min","max","user"].forEach(function(k){if(s[k])u.set(k,String(s[k]))});
      if(s.photo)u.set("photo","1"); if(s.sort&&s.sort!=="new")u.set("sort",s.sort);
      [["eq","e."],["nmin","f."],["nmax","t."]].forEach(function(p){var o=s[p[0]]||{};Object.keys(o).forEach(function(k){if(o[k])u.set(p[1]+k,o[k])})});
      return u.toString()}
    function qsToS(str){var u=new URLSearchParams(str),s=freshFilters(),g=function(k){return (u.get(k)||"").slice(0,100)};
      s.q=g("q").trim();
      var c=CAT[g("cat")];if(c){s.cat=g("cat");var sb_=g("sub");if(c.subs.indexOf(sb_)>=0||(c.alias&&c.alias[sb_]))s.sub=sb_}
      if(REGIONS[g("region")]){s.region=g("region");if(REGIONS[s.region].indexOf(g("city"))>=0)s.city=g("city")}
      if(g("cond")==="new"||g("cond")==="used")s.cond=g("cond");
      var mm=fixRange(numIn(g("min")),numIn(g("max")));s.min=mm[0];s.max=mm[1];
      s.photo=u.get("photo")==="1"; if(SORTS.indexOf(g("sort"))>=0)s.sort=g("sort");
      if(/^[0-9a-f-]{36}$/i.test(g("user")))s.user=g("user");
      u.forEach(function(v,k){var m=/^([eft])\.([\w-]{1,40})$/.exec(k);if(!m||!v)return;
        if(m[1]==="e")s.eq[m[2]]=v.slice(0,100);else{var n=numIn(v);if(n)(m[1]==="f"?s.nmin:s.nmax)[m[2]]=n}});
      if(!s.cat){Object.keys(s.eq).forEach(function(k){if(k!=="delivery"&&k!=="exchange")delete s.eq[k]});s.nmin={};s.nmax={}}
      return s}
    function syncUrl(){if(currentView()!=="home")return;var cur=location.search.replace(/^\?/,""),qs=sToQS(S,cur);
      if(qs!==cur)history.replaceState(history.state,"",location.pathname+(qs?"?"+qs:"")+location.hash)}
    function restore(){S=qsToS(location.search);var q=document.getElementById("q"),r=document.getElementById("regionTop");
      if(q)q.value=S.q;if(r)r.value=S.region}
    function normRanges(){var mm=fixRange(S.min,S.max);S.min=mm[0];S.max=mm[1];
      var ks={};Object.keys(S.nmin||{}).concat(Object.keys(S.nmax||{})).forEach(function(k){ks[k]=1});
      Object.keys(ks).forEach(function(k){var r=fixRange(S.nmin[k],S.nmax[k]);if(r[0])S.nmin[k]=r[0];else delete S.nmin[k];if(r[1])S.nmax[k]=r[1];else delete S.nmax[k]})}

    /* словарь из дерева разделов: основа слова → {слово, раздел, подкатегория} */
    var VOC=null;
    function vocab(){if(VOC)return VOC;VOC={};
      function add(t,cat,sub){yo(t).split(/[^a-zа-я0-9]+/).forEach(function(w){if(w.length>=4){var st=stem(w);if(!VOC[st])VOC[st]={w:w,cat:cat,sub:sub,label:t}}})}
      try{CATS.forEach(function(c){add(c.name,c.id,"");(c.subs||[]).forEach(function(x){add(x,c.id,x)})});
        Object.keys(SUB3||{}).forEach(function(k){var cs=k.split("|");(SUB3[k]||[]).forEach(function(x){add(x,cs[0],cs[1])})});
        CATS.forEach(function(c){(c.fields||[]).forEach(function(f){(f.o||[]).forEach(function(o){add(o,"","")})})})}catch(_){}
      return VOC}
    function fixWords(q){var ws=yo(q).split(/[^a-zа-я0-9]+/).filter(function(w){return w.length>=2}),out=[],hit=null,changed=false,V=vocab();
      ws.forEach(function(w){
        if(SYN[w]&&SYN[w]!==w){out.push(SYN[w]);changed=true;var h=V[stem(yo(SYN[w]).split(" ")[0])];if(h&&h.sub&&!hit)hit=h;return}
        var st=stem(w);
        if(V[st]){if(V[st].sub&&!hit)hit=V[st];out.push(w);return}
        if(w.length>=5){var max=st.length>=8?2:1,best=null,bd=max+1;
          Object.keys(V).forEach(function(k){if(k.charAt(0)!==st.charAt(0))return;var d=lev(st,k,max);if(d<bd){bd=d;best=k}});
          if(best){out.push(V[best].w);changed=true;if(V[best].sub&&!hit)hit=V[best];return}}
        out.push(w)});
      return {q:changed?out.join(" "):"",hit:hit}}

    /* запрос: без шаблонов LIKE */
    var _sp=searchParams;
    searchParams=function(){var p=_sp.apply(this,arguments);
      if(p&&p.q!=null){p.q=String(p.q).replace(/[%_\\]/g," ").replace(/\s+/g," ").trim();if(!p.q)delete p.q}
      return p};

    /* устаревшие ответы и раскладка */
    var tok=0, layoutFrom="", wordsMode=false, pendingSub=null, fixedFrom="", suggest=null;
    var _search=search;
    function hang(){return new Promise(function(){})} /* ответ устарел — выдачу не трогаем */
    /* поиск по словам: сервер ищет фразу целиком, поэтому берём самое длинное слово (основу),
       а остальные слова проверяем здесь — в любом порядке, ё = е */
    function byWords(q,force){
      var ws=yo(q).split(/[^a-zа-я0-9]+/).filter(function(w){return w.length>=2}).map(stem);
      if(!ws.length) return Promise.resolve(null);
      var probe=ws.slice().sort(function(a,b){return b.length-a.length})[0],tries=[];
      if(force||probe!==yo(q).trim())tries.push(probe);
      for(var i=probe.indexOf("е"),k=0;i>=0&&k<3;i=probe.indexOf("е",i+1),k++)tries.push(probe.slice(0,i)+"ё"+probe.slice(i+1));
      var seen={},items=[];
      return tries.reduce(function(pr,t){return pr.then(function(){
        return _search(Object.assign({},S,{q:t}),0,100).then(function(r){(r&&r.items||[]).forEach(function(a){if(!seen[a.id]){seen[a.id]=1;items.push(a)}})})})},Promise.resolve())
      .then(function(){
        var ok=items.filter(function(a){var tx=yo(a.title)+" "+yo(a.descr);return ws.every(function(w){return tx.indexOf(w)>=0})});
        return ok.length?{total:ok.length,items:ok}:null})}
    search=function(s,offset){var my=tok,args=arguments;
      return _search.apply(this,args).then(function(r){
        if(my!==tok) return hang();
        if(offset>0||s!==S||!r||r.total||!S.q) return r;
        var alt=fixLayout(S.q);
        var p=alt?_search(Object.assign({},S,{q:alt}),0).then(function(r2){
            if(my!==tok) return hang();
            if(r2&&r2.total){layoutFrom=S.q;S.q=alt;var q=document.getElementById("q");if(q)q.value=alt;return r2}
            return null}):Promise.resolve(null);
        return p.then(function(rr){if(rr)return rr;
          return byWords(S.q).then(function(rw){if(my!==tok)return hang();if(rw){wordsMode=true;return rw}
            /* бытовые слова и опечатки */
            var fx=fixWords(S.q);suggest=fx.hit;
            if(!fx.q) return r;
            return byWords(fx.q,true).then(function(rf){if(my!==tok)return hang();
              if(rf){fixedFrom=S.q;S.q=fx.q;var qi=document.getElementById("q");if(qi)qi.value=fx.q;return rf}
              return r})},function(){return r})})})};

    var restored=false;
    var _rh=renderHome;
    renderHome=async function(){
      if(!restored){restored=true;if(hasSKeys(location.search)&&initHash.indexOf("#c/")!==0)restore()}
      if(pendingSub!==null){if(S.cat)S.sub=pendingSub;pendingSub=null}
      normRanges(); tok++; layoutFrom=""; wordsMode=false; fixedFrom=""; suggest=null; syncUrl();
      var res=await _rh.apply(this,arguments);
      if(layoutFrom&&currentView()==="home"){
        var h=document.querySelector(".toolbar h1");if(h)h.textContent="Поиск: «"+S.q+"»";
        var box=document.getElementById("results");
        if(box&&!document.getElementById("layoutNote"))box.insertAdjacentHTML("beforebegin",'<p class="note" id="layoutNote">Показаны результаты по запросу «'+esc(S.q)+'» — исправлена раскладка клавиатуры («'+esc(layoutFrom)+'»).</p>');
        try{seoHome()}catch(_){}
      }
      if(fixedFrom&&currentView()==="home"){
        var h2=document.querySelector(".toolbar h1");if(h2)h2.textContent="Поиск: «"+S.q+"»";
        var bf=document.getElementById("results");
        if(bf&&!document.getElementById("fixNote"))bf.insertAdjacentHTML("beforebegin",'<p class="note" id="fixNote">Показаны результаты по запросу «'+esc(S.q)+'» (вы искали «'+esc(fixedFrom)+'»).</p>');
        try{seoHome()}catch(_){}
      }
      else if(suggest&&suggest.cat&&CAT[suggest.cat]&&currentView()==="home"&&typeof homeTotal!=="undefined"&&!homeTotal){
        var bs=document.getElementById("results"),href="#c/"+encodeURIComponent(suggest.cat)+(suggest.sub?"/"+encodeURIComponent(suggest.sub):"");
        if(bs&&!document.getElementById("sugNote"))bs.insertAdjacentHTML("beforebegin",'<p class="note" id="sugNote">Возможно, вам подойдёт раздел <a href="'+esc(href)+'">'+esc(suggest.sub||CAT[suggest.cat].name)+'</a> ('+esc(CAT[suggest.cat].name)+').</p>');
      }
      if(wordsMode&&currentView()==="home"){var bx=document.getElementById("results");
        if(bx&&!document.getElementById("wordsNote"))bx.insertAdjacentHTML("beforebegin",'<p class="note" id="wordsNote">Точного совпадения нет — показаны объявления, где есть все слова запроса.</p>')}
      syncUrl();
      return res};

    /* «Сбросить фильтры» — подкатегория остаётся (до штатного обработчика) */
    document.addEventListener("click",function(e){var t=e.target;if(t&&t.id==="fReset"&&S.cat&&S.sub)pendingSub=S.sub},true);

    /* числа в полях фильтров — до штатного обработчика */
    document.addEventListener("change",function(e){var t=e.target;if(!t||!t.dataset)return;
      if(t.id==="fMin"||t.id==="fMax"||t.dataset.nmin||t.dataset.nmax)t.value=numIn(t.value)},true);

    /* если главная уже показана до подключения — восстановить фильтры из адреса */
    if(currentView()==="home"&&document.getElementById("results")&&hasSKeys(location.search)&&initHash.indexOf("#c/")!==0){restored=true;restore();renderHome()}
    else if(currentView()==="home"&&document.getElementById("results")){restored=true;var qi=document.getElementById("q");if(qi)qi.value=S.q;syncUrl()}
  }

  var n=0;
  (function wait(){
    if(typeof renderHome==="function"&&typeof search==="function"&&typeof searchParams==="function"&&typeof freshFilters==="function"){
      try{install()}catch(e){if(window.console)console.warn("search-fix",e)} return}
    if(++n<400) setTimeout(wait,25);
  })();
})();
