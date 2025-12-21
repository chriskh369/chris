// Firebase Cloud Messaging Service Worker
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js');

// Firebase configuration - StudyHub-Push
const firebaseConfig = {
  apiKey: "AIzaSyDmf_rSXQqEOdwd1ByauoNn6XZohWi0TnU",
  authDomain: "studyhub-push.firebaseapp.com",
  projectId: "studyhub-push",
  storageBucket: "studyhub-push.firebasestorage.app",
  messagingSenderId: "843406915404",
  appId: "1:843406915404:web:198625675fc8ede1b3c1e9"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage((payload) => {
  console.log('[Firebase SW] Background message:', payload);

  const notificationTitle = payload.notification?.title || 'StudyHub';
  const notificationOptions = {
    body: payload.notification?.body || 'יש לך התראה חדשה',
    icon: '/chris/icons/icon-192.png',
    badge: '/chris/icons/icon-192.png',
    tag: payload.data?.tag || 'studyhub-firebase',
    vibrate: [200, 100, 200],
    data: { url: '/chris/' }
  };

  return self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url.includes('/chris/') && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow('/chris/');
      }
    })
  );
});
