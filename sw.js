// StudyHub Service Worker v4.0
const CACHE_NAME = 'studyhub-v4';
const OFFLINE_URL = '/chris/';

// Files to cache for offline use
const CACHE_FILES = [
  '/chris/',
  '/chris/index.html',
  '/chris/manifest.json',
  '/chris/icons/icon-192.png',
  '/chris/icons/icon-512.png',
  '/chris/icons/icon-192-maskable.png',
  '/chris/icons/icon-512-maskable.png',
  'https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700;800&display=swap',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
];

// Install event - cache essential files
self.addEventListener('install', (event) => {
  console.log('[SW] Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Caching files');
        return cache.addAll(CACHE_FILES);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') return;

  // Skip API requests (GitHub, Cloudinary) - always go to network
  const url = new URL(event.request.url);
  if (url.hostname.includes('github') ||
      url.hostname.includes('cloudinary') ||
      url.hostname.includes('api.')) {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then((cachedResponse) => {
        // Return cached response if found
        if (cachedResponse) {
          // Fetch fresh version in background
          fetch(event.request).then((response) => {
            if (response && response.status === 200) {
              caches.open(CACHE_NAME).then((cache) => {
                cache.put(event.request, response.clone());
              });
            }
          }).catch(() => {});
          return cachedResponse;
        }

        // Not in cache - fetch from network
        return fetch(event.request)
          .then((response) => {
            // Cache successful responses
            if (response && response.status === 200) {
              const responseClone = response.clone();
              caches.open(CACHE_NAME).then((cache) => {
                cache.put(event.request, responseClone);
              });
            }
            return response;
          })
          .catch(() => {
            // Offline fallback for HTML pages
            if (event.request.headers.get('accept').includes('text/html')) {
              return caches.match(OFFLINE_URL);
            }
          });
      })
  );
});

// Handle messages from the app
self.addEventListener('message', (event) => {
  if (event.data === 'skipWaiting') {
    self.skipWaiting();
  }

  // Handle notification request from app
  if (event.data && event.data.type === 'SHOW_NOTIFICATION') {
    self.registration.showNotification(event.data.title, {
      body: event.data.body,
      icon: '/chris/icons/icon-192.png',
      badge: '/chris/icons/icon-192.png',
      tag: event.data.tag || 'studyhub',
      requireInteraction: true,
      vibrate: [200, 100, 200],
      data: { url: '/chris/' }
    });
  }
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      // If app is already open, focus it
      for (const client of clientList) {
        if (client.url.includes('/chris/') && 'focus' in client) {
          return client.focus();
        }
      }
      // Otherwise open new window
      if (clients.openWindow) {
        return clients.openWindow('/chris/');
      }
    })
  );
});

// Push notification event (for future push server support)
self.addEventListener('push', (event) => {
  if (!event.data) return;

  const data = event.data.json();
  event.waitUntil(
    self.registration.showNotification(data.title || 'StudyHub', {
      body: data.body || 'יש לך התראה חדשה',
      icon: '/chris/icons/icon-192.png',
      badge: '/chris/icons/icon-192.png',
      tag: data.tag || 'studyhub-push',
      requireInteraction: true,
      vibrate: [200, 100, 200],
      data: { url: '/chris/' }
    })
  );
});
