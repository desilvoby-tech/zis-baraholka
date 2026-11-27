/* Service worker abisto (12.11.2026): сеть в приоритете, кэш — для офлайна */
const C="abisto-v1";const SHELL=["/","/logo.svg","/favicon.svg","/icon-192.png","/manifest.webmanifest"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting()))});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==C).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener("fetch",e=>{const r=e.request;if(r.method!=="GET")return;const u=new URL(r.url);if(u.origin!==location.origin)return;
/* настройки всегда сверяются с сервером, иначе правки доходят до посетителей до 4 часов */
const q=/^\/(config|geo)\.js$/.test(u.pathname)?new Request(r.url,{cache:"no-cache"}):r;
e.respondWith(fetch(q).then(res=>{if(res.ok&&res.type==="basic"){const cp=res.clone();caches.open(C).then(c=>c.put(r,cp))}return res}).catch(()=>caches.match(r).then(m=>m||(r.mode==="navigate"?caches.match("/"):Response.error()))))});
