/* Определение города посетителя (12.11.2026).
   1) по IP через GeoJS (только страна BY), 2) по кнопке «Точнее» — геолокация браузера.
   Выбор хранится только в браузере (localStorage "geo_v1"). */
(function(){
var C=[["Минск",53.902,27.561,"Минск"],
["Брест",52.097,23.734,"Брестская обл."],["Барановичи",53.132,26.014,"Брестская обл."],["Пинск",52.115,26.103,"Брестская обл."],["Кобрин",52.214,24.357,"Брестская обл."],["Берёза",52.538,24.98,"Брестская обл."],["Лунинец",52.247,26.804,"Брестская обл."],["Ивацевичи",52.709,25.34,"Брестская обл."],["Пружаны",52.556,24.464,"Брестская обл."],
["Витебск",55.19,30.205,"Витебская обл."],["Орша",54.509,30.425,"Витебская обл."],["Новополоцк",55.535,28.6,"Витебская обл."],["Полоцк",55.486,28.786,"Витебская обл."],["Глубокое",55.139,27.684,"Витебская обл."],["Лепель",54.881,28.694,"Витебская обл."],["Поставы",55.112,26.84,"Витебская обл."],
["Гомель",52.441,30.987,"Гомельская обл."],["Мозырь",52.049,29.245,"Гомельская обл."],["Жлобин",52.893,30.024,"Гомельская обл."],["Светлогорск",52.629,29.734,"Гомельская обл."],["Речица",52.364,30.394,"Гомельская обл."],["Калинковичи",52.129,29.329,"Гомельская обл."],["Рогачёв",53.093,30.05,"Гомельская обл."],["Добруш",52.405,31.322,"Гомельская обл."],
["Гродно",53.678,23.83,"Гродненская обл."],["Лида",53.887,25.303,"Гродненская обл."],["Слоним",53.093,25.32,"Гродненская обл."],["Волковыск",53.157,24.451,"Гродненская обл."],["Сморгонь",54.484,26.4,"Гродненская обл."],["Новогрудок",53.597,25.825,"Гродненская обл."],["Щучин",53.6,24.75,"Гродненская обл."],
["Борисов",54.228,28.505,"Минская обл."],["Солигорск",52.789,27.535,"Минская обл."],["Молодечно",54.311,26.85,"Минская обл."],["Жодино",54.098,28.333,"Минская обл."],["Слуцк",53.022,27.552,"Минская обл."],["Дзержинск",53.684,27.137,"Минская обл."],["Вилейка",54.498,26.926,"Минская обл."],["Марьина Горка",53.507,28.147,"Минская обл."],["Смолевичи",54.03,28.087,"Минская обл."],["Заславль",54.0,27.284,"Минская обл."],["Фаниполь",53.75,27.333,"Минская обл."],
["Могилёв",53.894,30.331,"Могилёвская обл."],["Бобруйск",53.145,29.225,"Могилёвская обл."],["Горки",54.286,30.986,"Могилёвская обл."],["Кричев",53.709,31.715,"Могилёвская обл."],["Осиповичи",53.307,28.637,"Могилёвская обл."],["Шклов",54.213,30.287,"Могилёвская обл."],["Быхов",53.523,30.245,"Могилёвская обл."]];
function km(a,b,c,d){var r=Math.PI/180,x=(d-b)*r*Math.cos((a+c)/2*r),y=(c-a)*r;return Math.sqrt(x*x+y*y)*6371}
function nearest(lat,lon){var best=null,bd=1e9;for(var i=0;i<C.length;i++){var d=km(lat,lon,C[i][1],C[i][2]);if(d<bd){bd=d;best=C[i]}}
  if(!best||bd>150)return null;return bd<=25?{city:best[0],region:best[3]}:{city:"",region:best[3]}}
var KEY="geo_v1";
function get(){try{return JSON.parse(localStorage.getItem(KEY)||"null")}catch(_){return null}}
function set(v){try{localStorage.setItem(KEY,JSON.stringify(v))}catch(_){}}
function css(){if(document.getElementById("geoCss"))return;var ACC=window.GEO_COLOR||"#00B4EE";var s=document.createElement("style");s.id="geoCss";s.textContent=".geob{position:fixed;top:76px;right:16px;z-index:9998;max-width:340px;background:#fff;color:#13213b;border:1px solid #dfe4ec;border-radius:14px;box-shadow:0 12px 32px rgba(15,25,45,.18);padding:14px 16px;font:15px/1.4 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}.geob b{font-weight:800}.geob .geo-acts{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}.geob button{border:0;border-radius:10px;padding:9px 14px;font:inherit;font-weight:700;cursor:pointer}.geob .y{background:"+ACC+";color:#fff}.geob .n{background:#eef1f5;color:#13213b}.geob .p{background:none;color:"+ACC+";padding:9px 4px}@media(max-width:600px){.geob{left:12px;right:12px;top:auto;bottom:90px;max-width:none}}";document.head.appendChild(s)}
function ask(g,how){css();var o=document.querySelector(".geob");if(o)o.remove();var d=document.createElement("div");d.className="geob";d.setAttribute("role","dialog");d.setAttribute("aria-label","Ваш город");
  var name=g.city||g.region;d.innerHTML='<div>📍 Ваш город — <b></b>?</div><div class="geo-acts"><button class="y" type="button">Да</button><button class="n" type="button">Выбрать другой</button>'+(how==="ip"&&navigator.geolocation?'<button class="p" type="button">Точнее</button>':'')+'</div>';
  d.querySelector("b").textContent=name;
  d.querySelector(".y").onclick=function(){set({city:g.city,region:g.region,ts:Date.now()});d.remove();if(window.GEO_APPLY)window.GEO_APPLY(g)};
  d.querySelector(".n").onclick=function(){set({skip:1,ts:Date.now()});d.remove();if(window.GEO_OTHER)window.GEO_OTHER()};
  var p=d.querySelector(".p");if(p)p.onclick=function(){p.textContent="Определяем…";navigator.geolocation.getCurrentPosition(function(pos){var r=nearest(pos.coords.latitude,pos.coords.longitude);if(r)ask(r,"gps");else{p.textContent="Не получилось"}},function(){p.textContent="Нет доступа"},{timeout:10000,maximumAge:600000})};
  document.body.appendChild(d)}
window.GEO={get:get,set:function(region,city){set({region:region||"",city:city||"",ts:Date.now()})},nearest:nearest,
  start:function(){var s=get();if(s){if(!s.skip&&window.GEO_APPLY&&window.GEO_SILENT)window.GEO_SILENT(s);return}
    fetch("https://get.geojs.io/v1/ip/geo.json").then(function(r){return r.json()}).then(function(j){if(!j||j.country_code!=="BY")return;var g=nearest(+j.latitude,+j.longitude);if(g)ask(g,"ip")}).catch(function(){})}};
})();
