# Абисто (abisto.by) — передача дел

Доска объявлений по Беларуси в духе Kufar/Avito. Статичный сайт на GitHub Pages + Supabase (Free). Обновлено 10.11.2026.

## Что сделано
- Объявления: подача с фото (Supabase Storage `photos`), 22 категории с подкатегориями и полями, ~190 городов (все 115 городов РБ + посёлки), поиск/фильтры (в т.ч. по подкатегориям: авто — марка, год, пробег, коробка; квартиры — комнаты, площадь, этаж; телефоны — бренд, память), сортировка, избранное, сохранённые поиски, похожие/недавние.
- Цена в BYN (свой знак рубля) + «≈ $» по курсу НБРБ; можно вводить в USD.
- Кабинет продавца: статистика 7/30 дней (просмотры, показы телефона, избранное, чаты) + график; вкладки Активные/Черновики/Проданные/Архив; массовые действия; черновики; профиль магазина.
- Сообщения (realtime), отзывы и рейтинг (после переписки), жалобы и модерация (#admin).
- Вход: почта+пароль, ссылка на почту, Telegram (@abisto_bot).
- Уведомления о новых объявлениях по сохранённым поискам в Telegram.
- Быстрая карточка (кэш + параллельные запросы), заглушки без фото, мобильная панель «Позвонить/Написать», выпадающее меню «Все категории», страница #cats.
- Бренд: логотип-сфера из точек #00B4EE (logo.svg), favicon, og.png; акцент #00B4EE; свои цветные SVG-значки категорий.
- Страницы #rules и #privacy (Закон РБ № 99-З), согласие при регистрации.
- Карта объявлений (кнопка 🗺 в выдаче): Leaflet + OpenStreetMap, города геокодируются через Nominatim с кэшем в localStorage.
- Демо-наполнение: 23 объявления от аккаунта demo@abisto.by «Пример продавца», флаг `ads.is_demo`, бейдж «Пример объявления». Удалить: `delete from public.ads where is_demo; delete from auth.users where email='demo@abisto.by';` (SQL — demo.sql). Без фото (заглушки).
- Наполнение: 14 объявлений об услугах мастерских владельца (Гомель), владелец-модератор desilvo.by@gmail.com.

## Структура кода
- `index.html` — весь сайт одним файлом: CSS (база + светлая тема + блоки по этапам), разметка шапки/подвала, JS (hash-роутер `route()`, рендеры `renderHome/renderAd/renderPost/renderMy/renderProfile/renderFavs/renderMsgs/renderChat/renderUser/renderLogin/renderAdmin/renderAllCats/renderLegal`). Ключевые константы: `REGIONS`, `CATS` (поля `fields`, привязка к подкатегориям `s`), `ART`/`ART_DEFS` (значки), `NOCOND` (категории без «Состояния»).
- `config.js` — `window.ZIS_CONFIG={url, anonKey}` (publishable key, вставлял владелец).
- `logo.svg`, `favicon.svg`, `favicon-32.png`, `apple-touch-icon.png`, `og.png`, `CNAME` (abisto.by).
- Edge Function `tg` (Supabase) — вход через Telegram, привязка Telegram, уведомления (`event: ad_new`), команды бота /start, /stop. Копия кода — в проекте Claude «АБИСТО» (`claude/abisto-tg-function.ts`).

## База (Supabase, проект «Abisto», ref gmksjjksvlkmhicbnbtj)
- Таблицы: profiles, ads, favorites, saved_searches (notify), conversations, messages, reviews, reports, admins, ad_stats, login_codes, notify_log. RLS на всех.
- RPC: search_ads, cat_counts, sub_counts, increment_views, track_phone, my_fav_counts, is_admin.
- Триггеры: ads_insert_guard/ads_guard (поднятие раз в сутки, черновики), fav_stat/chat_stat, ad_notify (pg_net → функция tg), profiles_tg_guard (tg_chat_id/notify_chat_id меняет только функция).
- Полная схема — в проекте Claude (`claude/zis-baraholka-schema.sql`).
- Секреты функции: TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_NAME (задаёт владелец). Verify JWT у функции выключен.

## Как выкладывать
- Сайт: правка `index.html` в репозитории → GitHub Pages пересобирает за ~1–3 мин. Из Cowork: на странице github.com/…/edit/main/index.html скачать raw, применить замены в JS, сверить SHA-256 с локальной сборкой, вставить paste-событием в редактор, Commit.
- Бинарные файлы: github.com/…/upload/main (File через DataTransfer в input).
- SQL: Supabase → SQL Editor. Функция: Edge Functions → tg → Code → Deploy updates.

## Ключевые решения
- Без своего сервера и платных сервисов: GitHub Pages + Supabase Free.
- Один файл `index.html` без сборки — проще выкладывать из браузера.
- Telegram вместо Яндекс/VK/Google: не нужны регистрации приложений.
- Telegram-вход создаёт аккаунт tg<chat_id>@telegram.abisto.by.

## Что осталось
- Реквизиты оператора в Политике (ФИО/ИП, УНП, e-mail).
- Проверить живое уведомление по сохранённому поиску.
- Фото к объявлениям об услугах и «Магазин» в профиле desilvo.
- Свой SMTP (Brevo) — встроенная почта Supabase ~2 письма/час.
- SEO (hash-адреса плохо индексируются), www.abisto.by (CNAME не резолвился).
- По желанию: входы Яндекс/Mail.ru/VK/Google; контраст белого текста на #00B4EE (можно кнопки #0098cc).
