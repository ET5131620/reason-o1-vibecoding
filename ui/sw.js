// REASON O1 · service worker
// Não guarda a página nem a API em cache: a página leva um token novo a cada arranque.
// Só serve uma página de ajuda quando o servidor local não está a correr.
const CACHE = "o1-offline-v1";
const OFFLINE = "/ui/offline.html";
self.addEventListener("install", e => e.waitUntil(caches.open(CACHE).then(c => c.addAll([OFFLINE, "/ui/icons/icon-192.png"])).then(() => self.skipWaiting())));
self.addEventListener("activate", e => e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener("fetch", e => {
  if (e.request.mode !== "navigate") return;           // tudo o resto vai direto à rede
  e.respondWith(fetch(e.request).catch(() => caches.match(OFFLINE)));
});
