/* abisto addons (27.11.2026): стрелки, счётчик, свайп и полноэкранный просмотр в галерее объявления. Свой код. */
(function(){
  if(window.__abAddons) return; window.__abAddons=1;
  var L='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"/></svg>';
  var R='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7"/></svg>';
  function mk(tag,cls,html){var e=document.createElement(tag);if(cls)e.className=cls;if(html)e.innerHTML=html;return e}
  function full(src){return src.replace(/_t\.jpg(\?.*)?$/,".jpg$1")}
  function swipe(el,onL,onR){
    var x0=null,y0=0,t0=0;
    el.addEventListener("touchstart",function(e){var t=e.touches[0];x0=t.clientX;y0=t.clientY;t0=Date.now()},{passive:true});
    el.addEventListener("touchend",function(e){if(x0===null)return;var t=e.changedTouches[0],dx=t.clientX-x0,dy=t.clientY-y0;x0=null;
      if(Math.abs(dx)>40&&Math.abs(dx)>Math.abs(dy)*1.4&&Date.now()-t0<800){el.__swiped=Date.now();(dx<0?onL:onR)()}},{passive:true});
  }
  function enhance(gal){
    if(gal.dataset.enh) return;
    var main=gal.querySelector(".main"); var ths=[].slice.call(gal.querySelectorAll(".thumbs [data-th]"));
    if(!main) return;
    if(ths.length<2){ /* одно фото (например, перенесённые объявления): тоже открывается на весь экран */
      var one=main.querySelector("img"); if(!one) return; gal.dataset.enh="1";
      gal.appendChild(mk("span","g-zoom","Нажмите, чтобы увеличить"));
      main.style.cursor="zoom-in";
      main.addEventListener("click",function(){lightbox([full(one.getAttribute("src")||one.src)],0)});
      return;
    }
    gal.dataset.enh="1";
    var n=ths.length;
    function cur(){for(var i=0;i<n;i++)if(ths[i].getAttribute("aria-current")==="true")return i;return 0}
    var count=mk("span","g-count"); var zoom=mk("span","g-zoom","Нажмите, чтобы увеличить");
    function upd(){var i=cur();count.textContent=(i+1)+" / "+n;var b=ths[i];if(b&&b.parentNode&&b.scrollIntoView){var p=b.parentNode;p.scrollLeft=b.offsetLeft-(p.clientWidth-b.offsetWidth)/2}}
    function go(i){i=(i+n)%n;ths[i].click();upd()}
    var prev=mk("button","g-nav g-prev",L),next=mk("button","g-nav g-next",R);
    prev.type=next.type="button";prev.setAttribute("aria-label","Предыдущее фото");next.setAttribute("aria-label","Следующее фото");
    prev.onclick=function(e){e.stopPropagation();go(cur()-1)};next.onclick=function(e){e.stopPropagation();go(cur()+1)};
    gal.appendChild(prev);gal.appendChild(next);gal.appendChild(count);gal.appendChild(zoom);
    ths.forEach(function(b){b.addEventListener("click",function(){setTimeout(upd,0)})});
    swipe(main,function(){go(cur()+1)},function(){go(cur()-1)});
    main.addEventListener("click",function(e){if(main.__swiped&&Date.now()-main.__swiped<400)return;lightbox(ths.map(function(b){return full(b.querySelector("img").getAttribute("src")||b.querySelector("img").src)}),cur(),function(i){go(i)})});
    gal.tabIndex=0;
    gal.addEventListener("keydown",function(e){if(e.key==="ArrowLeft"){go(cur()-1);e.preventDefault()}else if(e.key==="ArrowRight"){go(cur()+1);e.preventDefault()}});
    upd();
  }
  function lightbox(urls,i,onChange){
    var n=urls.length,box=mk("div","lb"),img=mk("img"),x=mk("button","lb-x","×"),num=mk("div","lb-n");
    var p=mk("button","g-nav g-prev",L),q=mk("button","g-nav g-next",R);
    x.type=p.type=q.type="button";x.setAttribute("aria-label","Закрыть");p.setAttribute("aria-label","Предыдущее фото");q.setAttribute("aria-label","Следующее фото");
    img.alt="";
    function show(k){i=(k+n)%n;img.src=urls[i];num.textContent=(i+1)+" / "+n;onChange&&onChange(i);
      [urls[(i+1)%n],urls[(i-1+n)%n]].forEach(function(u){var im=new Image();im.src=u})}
    function close(){document.removeEventListener("keydown",key,true);removeEventListener("hashchange",close);box.remove();document.body.style.overflow=prevOv}
    function key(e){if(e.key==="Escape"){close();e.stopPropagation()}else if(e.key==="ArrowLeft"){show(i-1);e.stopPropagation();e.preventDefault()}else if(e.key==="ArrowRight"){show(i+1);e.stopPropagation();e.preventDefault()}}
    var prevOv=document.body.style.overflow;document.body.style.overflow="hidden";
    x.onclick=close;p.onclick=function(e){e.stopPropagation();show(i-1)};q.onclick=function(e){e.stopPropagation();show(i+1)};
    box.onclick=function(e){if(e.target===box)close()};
    swipe(box,function(){show(i+1)},function(){show(i-1)});
    box.appendChild(img);box.appendChild(x);if(n>1){box.appendChild(p);box.appendChild(q);box.appendChild(num)}
    document.body.appendChild(box);document.addEventListener("keydown",key,true);addEventListener("hashchange",close);show(i);
  }
  /* ---- Карточки в стиле «Авито»: название, под ним цена; сердечко справа от названия, «три точки» справа от цены ---- */
  var DOTS='<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/></svg>';
  var menu=null;
  function closeMenu(){if(menu){menu.remove();menu=null}}
  function openMenu(btn,card){
    closeMenu();var fav=card.querySelector("[data-fav]"),on=fav&&fav.getAttribute("aria-pressed")==="true";
    menu=mk("div","av-menu");
    var a=mk("button","",on?"Убрать из избранного":"В избранное"),b=mk("button","","Скопировать ссылку");
    a.type=b.type="button";
    a.onclick=function(e){e.preventDefault();e.stopPropagation();if(fav)fav.click();closeMenu()};
    b.onclick=function(e){e.preventDefault();e.stopPropagation();var u=new URL(card.getAttribute("href"),location.href).href;
      try{navigator.clipboard.writeText(u)}catch(x){var t=mk("textarea");t.value=u;document.body.appendChild(t);t.select();try{document.execCommand("copy")}catch(y){}t.remove()}
      b.textContent="Ссылка скопирована";setTimeout(closeMenu,900)};
    menu.appendChild(a);menu.appendChild(b);document.body.appendChild(menu);
    var r=btn.getBoundingClientRect(),w=menu.offsetWidth;
    menu.style.top=(window.scrollY+r.bottom+4)+"px";menu.style.left=Math.max(8,Math.min(window.scrollX+r.right-w,document.documentElement.clientWidth-w-8))+"px";
  }
  document.addEventListener("click",function(e){if(menu&&!menu.contains(e.target)&&!(e.target.closest&&e.target.closest(".av-dots")))closeMenu()},true);
  window.addEventListener("scroll",closeMenu,{passive:true});
  function card(c){
    if(c.dataset.av) return;
    var body=c.querySelector(".cbody"),t=body&&body.querySelector(".ctitle"),p=body&&body.querySelector(".price"),fav=c.querySelector(".ph .fav");
    if(!body||!t||!p) return; c.dataset.av="1";
    var row1=mk("div","av-t"),row2=mk("div","av-p"),dots=mk("button","av-dots",DOTS);
    dots.type="button";dots.setAttribute("aria-label","Ещё");
    dots.onclick=function(e){e.preventDefault();e.stopPropagation();if(menu){closeMenu();return}openMenu(dots,c)};
    row1.appendChild(t);if(fav)row1.appendChild(fav);
    row2.appendChild(p);row2.appendChild(dots);
    body.insertBefore(row2,body.firstChild);body.insertBefore(row1,body.firstChild);
  }
  /* ---- Переписка на телефоне: при открытой клавиатуре видны шапка диалога, сообщения и поле ввода ---- */
  var chatOn=false;
  function fitChat(){
    var c=document.querySelector(".chat"),ta=document.getElementById("chatText");
    if(!c||!ta||document.activeElement!==ta||innerWidth>860){if(c&&c.style.height){c.style.height="";c.style.minHeight=""}return}
    var vv=window.visualViewport,vh=vv?vv.height:innerHeight,hb=0,hd=document.querySelector("header");
    if(hd){var ps=getComputedStyle(hd).position;if(ps==="sticky"||ps==="fixed")hb=hd.offsetHeight}
    c.style.minHeight="0";c.style.height=Math.max(200,vh-hb-8)+"px";
    var top=c.getBoundingClientRect().top-(vv?vv.offsetTop:0);
    if(Math.abs(top-hb-4)>2)window.scrollBy(0,top-hb-4);
    var m=document.getElementById("msgs");if(m)m.scrollTop=m.scrollHeight;
  }
  function chatSoon(){setTimeout(fitChat,60);setTimeout(fitChat,350)}
  document.addEventListener("focusin",function(e){if(e.target&&e.target.id==="chatText"){chatOn=true;document.body.classList.add("chat-typing");chatSoon()}});
  document.addEventListener("focusout",function(e){if(e.target&&e.target.id==="chatText"){chatOn=false;document.body.classList.remove("chat-typing");setTimeout(fitChat,120)}});
  if(window.visualViewport)visualViewport.addEventListener("resize",function(){if(chatOn)fitChat()});
  addEventListener("resize",function(){if(chatOn)chatSoon()});

  var pend=false;
  function scan(){pend=false;[].forEach.call(document.querySelectorAll(".gal:not([data-enh])"),enhance);[].forEach.call(document.querySelectorAll(".card:not([data-av])"),card)}
  new MutationObserver(function(){if(!pend){pend=true;requestAnimationFrame(scan)}}).observe(document.documentElement,{childList:true,subtree:true});
  scan();
})();
