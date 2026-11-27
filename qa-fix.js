/* qa-fix (27.11.2026): гость тоже видит «Пожаловаться» — ведёт на вход */
(function(){
  var root=document.getElementById("view"); if(!root) return;
  function add(){
    var side=root.querySelector(".adpage .adside");
    if(!side||typeof user==="undefined"||user||document.getElementById("qaReport")) return;
    side.insertAdjacentHTML("beforeend",'<a class="link danger-link" id="qaReport" href="#login">Пожаловаться на объявление (нужно войти)</a>');
  }
  new MutationObserver(add).observe(root,{childList:true,subtree:true});
  add();
})();

/* qa-fix: латиница → кириллица («stiralnaya»), только если по запросу ничего не найдено */
(function(){
  var PAIRS={shch:"щ",sch:"щ",zh:"ж",kh:"х",ts:"ц",ch:"ч",sh:"ш",yo:"ё",yu:"ю",ya:"я",ju:"ю",ja:"я",ye:"е",
    a:"а",b:"б",c:"к",d:"д",e:"е",f:"ф",g:"г",h:"х",i:"и",j:"й",k:"к",l:"л",m:"м",n:"н",o:"о",p:"п",q:"к",r:"р",s:"с",t:"т",u:"у",v:"в",w:"в",x:"кс",y:"ы",z:"з"};
  function translit(q){
    if(!/^[a-z0-9\s'-]+$/i.test(q)||!/[a-z]{3}/i.test(q)) return "";
    return q.toLowerCase().replace(/'/g,"ь").replace(/([aeiou])y(?![aeou])/g,"$1й")
      .replace(/shch|sch|zh|kh|ts|ch|sh|yo|yu|ya|ju|ja|ye|[a-z]/g,function(m){return PAIRS[m]});
  }
  var n=0;
  (function wait(){
    /* ждём, пока подключится search-fix: наша проверка идёт после его исправлений */
    if(typeof search!=="function"||String(search).indexOf("fixWords")<0){if(++n<400)setTimeout(wait,25);return}
    var inner=search, from="";
    search=function(s,offset){
      var self=this;
      return inner.apply(self,arguments).then(function(r){
        if(offset>0||s!==S||!r||r.total||!S.q) return r;
        var was=S.q, ru=translit(was); if(!ru) return r;
        S.q=ru;
        return inner.call(self,S,0).then(function(r2){
          if(r2&&r2.total){from=was;var i=document.getElementById("q");if(i)i.value=S.q;return r2}
          S.q=was;return r},function(){S.q=was;return r});
      });
    };
    var render=renderHome;
    renderHome=async function(){
      from="";
      var res=await render.apply(this,arguments);
      var box=document.getElementById("results");
      if(from&&currentView()==="home"&&box){
        var text="Показаны результаты по запросу «"+S.q+"» (вы искали «"+from+"»).";
        var note=document.getElementById("fixNote");
        if(note) note.textContent=text;
        else box.insertAdjacentHTML("beforebegin",'<p class="note" id="fixNote">'+esc(text)+'</p>');
        var h=document.querySelector(".toolbar h1");if(h)h.textContent="Поиск: «"+S.q+"»";
      }
      return res;
    };
    if(currentView()==="home"&&S.q&&translit(S.q)) renderHome();
  })();
})();
