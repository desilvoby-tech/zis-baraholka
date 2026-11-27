// Настройки подключения к базе ЗИС Барахолки.
// Замените ВСТАВЬТЕ_СЮДА на Publishable key (sb_publishable_...) из Supabase → Settings → API Keys.
window.ZIS_CONFIG = {
  url: "https://api.abisto.by",
  anonKey: "sb_publishable_Uykq4JYZ01U3ghb_O2sLXW_TqXK-tmT",
  google: true,
  yandex: true,   // включить после настройки функции oauth
  mailru: true
};

/* addons (27.11.2026): крупные карточки + галерея. Чтобы отключить — удалить этот блок. */
(function(){try{var l=document.createElement("link");l.rel="stylesheet";l.href="/addons.css?v=4";document.head.appendChild(l);var s=document.createElement("script");s.src="/addons.js?v=4";s.defer=true;document.head.appendChild(s)}catch(e){}})();

/* search-fix (27.11.2026): поиск и фильтры — адрес с фильтрами, числа, раскладка. Чтобы отключить — удалить этот блок. */
(function(){try{var s=document.createElement("script");s.src="/search-fix.js?v=3";document.head.appendChild(s)}catch(e){}})();

/* cats-fix (27.11.2026): плитки категорий на главной — ровная сетка в 2 ряда. Чтобы отключить — удалить этот блок. */
(function(){try{var s=document.createElement("script");s.src="/cats-fix.js?v=1";document.head.appendChild(s)}catch(e){}})();

/* mobile-search (28.11.2026): поиск на всю ширину на телефоне + закрытие фильтров + «Сбросить всё». Чтобы отключить — удалить этот блок. */
(function(){try{var l=document.createElement("link");l.rel="stylesheet";l.href="/mobile-search.css?v=2";document.head.appendChild(l);var s=document.createElement("script");s.src="/mobile-search.js?v=2";s.defer=true;document.head.appendChild(s)}catch(e){}})();

/* kufar-gallery (28.11.2026): фото в объявлении как на Куфаре. Чтобы отключить — удалить этот блок. */
(function(){try{var l=document.createElement("link");l.rel="stylesheet";l.href="/kufar-gallery.css?v=1";document.head.appendChild(l)}catch(e){}})();

/* qa-fix (27.11.2026): замечания проверки. Чтобы отключить — удалить этот блок. */
(function(){try{var l=document.createElement("link");l.rel="stylesheet";l.href="/qa-fix.css?v=1";document.head.appendChild(l);var s=document.createElement("script");s.src="/qa-fix.js?v=1";s.defer=true;document.head.appendChild(s)}catch(e){}})();
