// Voxera Service Worker — Offline-First
// Version bump here to force sw update
const SW_VERSION = "voxera-sw-v1";

// App-shell assets to precache (Next.js static chunks are hashed; we cache the shell routes instead)
const PRECACHE_URLS = ["/", "/_next/static/css/", "/manifest.json"];

// Routes that use Stale-While-Revalidate
const SWR_PATTERNS = [
  /\/api\/domains(\/[^/]+)?$/,
  /\/api\/ledger\//,
  /\/api\/guardrail\/active-holds/,
];

// Routes that are NEVER cached
const NEVER_CACHE_PATTERNS = [
  /\/api\/convai\/signed-url/,
  /^ws:/,
  /^wss:/,
];

// Routes that are write operations — never cache
const NEVER_CACHE_METHODS = ["POST", "PUT", "PATCH", "DELETE"];

const CACHE_NAME = SW_VERSION;
const RUNTIME_CACHE = `${SW_VERSION}-runtime`;

// ── Install: precache shell ────────────────────────────────────────────────
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(["/"]))
      .then(() => self.skipWaiting())
  );
});

// ── Activate: clear old caches ────────────────────────────────────────────
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((k) => k !== CACHE_NAME && k !== RUNTIME_CACHE)
            .map((k) => caches.delete(k))
        )
      )
      .then(() => self.clients.claim())
  );
});

// ── Fetch: routing logic ───────────────────────────────────────────────────
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // 1. Never cache WebSocket upgrade requests
  if (request.headers.get("upgrade") === "websocket") return;

  // 2. Never cache write methods
  if (NEVER_CACHE_METHODS.includes(request.method)) return;

  // 3. Never cache specific patterns
  if (NEVER_CACHE_PATTERNS.some((p) => p.test(url.pathname + url.search))) return;

  // 4. Stale-While-Revalidate for GET /api/domains/*, /api/ledger/*, /api/guardrail/active-holds
  if (SWR_PATTERNS.some((p) => p.test(url.pathname))) {
    event.respondWith(swrStrategy(request));
    return;
  }

  // 5. Network-first with cache fallback for pages & other GET requests
  if (request.mode === "navigate" || request.destination === "document") {
    event.respondWith(networkFirstStrategy(request));
    return;
  }

  // 6. Cache-first for static assets (_next/static/*)
  if (url.pathname.startsWith("/_next/static/")) {
    event.respondWith(cacheFirstStrategy(request));
    return;
  }
});

// ── Strategies ─────────────────────────────────────────────────────────────

async function swrStrategy(request) {
  const cache = await caches.open(RUNTIME_CACHE);
  const cached = await cache.match(request);

  // Kick off network fetch regardless
  const fetchPromise = fetch(request.clone())
    .then((networkResponse) => {
      if (networkResponse && networkResponse.ok) {
        cache.put(request, networkResponse.clone());
      }
      return networkResponse;
    })
    .catch(() => null);

  // Return cached immediately if available, else wait for network
  return cached || fetchPromise;
}

async function networkFirstStrategy(request) {
  const cache = await caches.open(RUNTIME_CACHE);
  try {
    const networkResponse = await fetch(request.clone());
    if (networkResponse && networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch {
    const cached = await cache.match(request);
    if (cached) return cached;
    // Offline fallback: return the root shell
    const shell = await caches.match("/");
    return shell || new Response("Offline", { status: 503 });
  }
}

async function cacheFirstStrategy(request) {
  const cache = await caches.open(RUNTIME_CACHE);
  const cached = await cache.match(request);
  if (cached) return cached;
  try {
    const networkResponse = await fetch(request.clone());
    if (networkResponse && networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch {
    return new Response("Offline", { status: 503 });
  }
}

