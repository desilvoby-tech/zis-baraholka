/* mobile-search.js (28.11.2026): на телефоне панель фильтров можно закрыть крестиком, тапом по затемнённому фону или Esc. Чтобы отключить — удалить блок mobile-search в config.js */
(function(){
  var mq=window.matchMedia?window.matchMedia("(max-width:900px)"):null;
  function done(){var d=document.getElementById("fDone");if(d)d.click()}
  function sync(){
    var p=document.querySelector("aside.panel");
    var back=document.getElementById("fBack");
    var open=!!(p&&p.classList.contains("open")&&mq&&mq.matches);
    if(p&&!p.querySelector(".f-x")){
      var x=document.createElement("button");
      x.type="button";x.className="f-x";x.setAttribute("aria-label","Закрыть фильтры");x.textContent="×";
      x.addEventListener("click",done);
      p.insertBefore(x,p.firstChild);
    }
    if(open&&!back){
      back=document.createElement("div");back.id="fBack";
      back.addEventListener("click",done);
      document.body.appendChild(back);
    }else if(!open&&back){back.remove()}
  }
  var t=0;
  function later(){if(t)return;t=setTimeout(function(){t=0;sync()},30)}
  new MutationObserver(later).observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:["class"]});
  document.addEventListener("keydown",function(e){if(e.key==="Escape"&&document.getElementById("fBack"))done()});
  sync();
})();
