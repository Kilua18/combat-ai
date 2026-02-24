// Combat.AI — Service Worker v1.0
// Cache l'app HTML pour un accès offline rapide.
// Les ressources CDN (MediaPipe) restent chargées depuis le réseau.

const CACHE_NAME = 'combat-ai-v1';
const APP_SHELL = [
    'combat-ai-v2.html',
    'manifest.json',
    'icon.svg'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(APP_SHELL))
    );
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
        )
    );
    self.clients.claim();
});

self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // Ressources CDN → réseau uniquement (pas de cache local)
    if (url.hostname.includes('jsdelivr.net') || url.hostname.includes('googleapis.com')) {
        event.respondWith(fetch(event.request));
        return;
    }

    // App shell → cache d'abord, réseau en fallback
    event.respondWith(
        caches.match(event.request).then(cached => {
            if (cached) return cached;
            return fetch(event.request).then(response => {
                if (!response || response.status !== 200) return response;
                const clone = response.clone();
                caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                return response;
            });
        })
    );
});
