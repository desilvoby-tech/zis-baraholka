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
