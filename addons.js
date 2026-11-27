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
    if(!main||ths.length<2) return; gal.dataset.enh="1";
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
    function close(){document.removeEventListener("keydown",key,true);box.remove();document.body.style.overflow=prevOv}
    function key(e){if(e.key==="Escape"){close();e.stopPropagation()}else if(e.key==="ArrowLeft"){show(i-1);e.stopPropagation();e.preventDefault()}else if(e.key==="ArrowRight"){show(i+1);e.stopPropagation();e.preventDefault()}}
    var prevOv=document.body.style.overflow;document.body.style.overflow="hidden";
    x.onclick=close;p.onclick=function(e){e.stopPropagation();show(i-1)};q.onclick=function(e){e.stopPropagation();show(i+1)};
    box.onclick=function(e){if(e.target===box)close()};
    swipe(box,function(){show(i+1)},function(){show(i-1)});
    box.appendChild(img);box.appendChild(x);if(n>1){box.appendChild(p);box.appendChild(q);box.appendChild(num)}
    document.body.appendChild(box);document.addEventListener("keydown",key,true);show(i);
  }
  var pend=false;
  function scan(){pend=false;[].forEach.call(document.querySelectorAll(".gal:not([data-enh])"),enhance)}
  new MutationObserver(function(){if(!pend){pend=true;requestAnimationFrame(scan)}}).observe(document.documentElement,{childList:true,subtree:true});
  scan();
})();
