/**
 * Voxera Connectivity Monitor
 *
 * Does NOT trust navigator.onLine alone.
 * Pings GET /api/health every 5 s with a 2 s timeout to determine true
 * online status. Runs flush() automatically on every offline→online
 * transition. Provides exponential backoff for flush retries (1s→2s→4s…→30s).
 */

import { getApiBase } from "../api";
import { flush } from "./outbox";

// ── State ─────────────────────────────────────────────────────────────────

let _isOnline = true; // optimistic default
let _pollIntervalId: ReturnType<typeof setInterval> | null = null;
let _backoffTimeoutId: ReturnType<typeof setTimeout> | null = null;
let _backoffDelay = 1000; // ms, doubles each failed flush attempt, cap 30s
const MAX_BACKOFF_MS = 30_000;

// ── Subscribers ───────────────────────────────────────────────────────────

type ConnListener = (online: boolean) => void;
const listeners = new Set<ConnListener>();

/** Subscribe to online/offline state changes. Returns unsubscribe fn. */
export function subscribe(fn: ConnListener): () => void {
  listeners.add(fn);
  fn(_isOnline); // emit current state immediately
  return () => listeners.delete(fn);
}

export function isOnline(): boolean {
  return _isOnline;
}

// ── Core ping ─────────────────────────────────────────────────────────────

async function pingHealth(): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 2000);
    const res = await fetch(`${getApiBase()}/api/health`, {
      method: "GET",
      cache: "no-store",
      signal: controller.signal,
    });
    clearTimeout(timer);
    return res.ok;
  } catch {
    return false;
  }
}

async function checkConnectivity() {
  const nowOnline = await pingHealth();

  if (nowOnline !== _isOnline) {
    _isOnline = nowOnline;
    listeners.forEach((fn) => fn(_isOnline));

    if (_isOnline) {
      // Transitioned online → flush outbox with backoff retry
      _backoffDelay = 1000;
      scheduleFlush(0);
    }
  }
}

// ── Flush with exponential backoff ────────────────────────────────────────

async function scheduleFlush(delay: number) {
  if (_backoffTimeoutId) clearTimeout(_backoffTimeoutId);
  _backoffTimeoutId = setTimeout(async () => {
    try {
      const synced = await flush();
      if (synced > 0) {
        // Reset backoff after successful sync
        _backoffDelay = 1000;
      }
    } catch {
      // Still failing — back off
      _backoffDelay = Math.min(_backoffDelay * 2, MAX_BACKOFF_MS);
      if (_isOnline) scheduleFlush(_backoffDelay);
    }
  }, delay);
}

// ── Public init / stop ────────────────────────────────────────────────────

/**
 * Start the connectivity monitor (call once on app mount).
 * Polls every 5 s. Also listens to browser online/offline events as a fast
 * path (still verifies with a real ping before acting).
 */
export function startConnectivityMonitor() {
  if (typeof window === "undefined") return;
  if (_pollIntervalId !== null) return; // already started

  // Immediate first check
  checkConnectivity();

  // Poll every 5 s
  _pollIntervalId = setInterval(checkConnectivity, 5000);

  // Browser events as fast-path triggers (we still verify with ping)
  window.addEventListener("online", checkConnectivity);
  window.addEventListener("offline", checkConnectivity);
}

export function stopConnectivityMonitor() {
  if (_pollIntervalId !== null) {
    clearInterval(_pollIntervalId);
    _pollIntervalId = null;
  }
  if (_backoffTimeoutId !== null) {
    clearTimeout(_backoffTimeoutId);
    _backoffTimeoutId = null;
  }
  if (typeof window !== "undefined") {
    window.removeEventListener("online", checkConnectivity);
    window.removeEventListener("offline", checkConnectivity);
  }
}

