const CACHE_NAME = 'dash-transparencia-v3';
const ASSETS = [
  '/',
  'https://cdn.jsdelivr.net/npm/chart.js' // Caso você decida voltar com os gráficos
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    })
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((response) => {
      return response || fetch(e.request);
    })
  );
});
