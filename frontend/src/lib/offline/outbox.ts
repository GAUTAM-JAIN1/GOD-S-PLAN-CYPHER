/**
 * Voxera Outbox — queues write operations while offline and flushes them when
 * the network returns.
 *
 * Each item: { id, idempotency_key, endpoint, method, payload,
 *              status: pending|syncing|failed, retries, created_at }
 */

import { dbGetAll, dbPut, dbDelete, dbPutAll } from "./db";
import { getApiBase } from "../api";

// ── Types ─────────────────────────────────────────────────────────────────

export type OutboxStatus = "pending" | "syncing" | "failed";

export interface OutboxItem {
  id: string;
  idempotency_key: string;
  endpoint: string;
  method: string;
  payload: Record<string, unknown>;
  status: OutboxStatus;
  retries: number;
  created_at: string;
}

// ── Subscribers ───────────────────────────────────────────────────────────

type Listener = (items: OutboxItem[]) => void;
const listeners = new Set<Listener>();

async function notify() {
  const items = await dbGetAll<OutboxItem>("outbox");
  listeners.forEach((fn) => fn(items));
}

/** Subscribe to outbox changes. Returns an unsubscribe function. */
export function subscribe(fn: Listener): () => void {
  listeners.add(fn);
  // emit current state immediately
  dbGetAll<OutboxItem>("outbox").then((items) => fn(items));
  return () => listeners.delete(fn);
}

// ── Core API ──────────────────────────────────────────────────────────────

/** Add a write operation to the outbox. */
export async function enqueue(
  endpoint: string,
  method: string,
  payload: Record<string, unknown>,
  idempotency_key?: string
): Promise<OutboxItem> {
  const item: OutboxItem = {
    id: crypto.randomUUID(),
    idempotency_key: idempotency_key ?? crypto.randomUUID(),
    endpoint,
    method,
    payload,
    status: "pending",
    retries: 0,
    created_at: new Date().toISOString(),
  };
  await dbPut<OutboxItem>("outbox", item);
  await notify();
  return item;
}

/** How many items are pending or failed (not yet synced). */
export async function getPendingCount(): Promise<number> {
  const items = await dbGetAll<OutboxItem>("outbox");
  return items.filter((i) => i.status !== "syncing").length;
}

/**
 * Flush all pending outbox items to the server.
 * Items are sent in creation order, one at a time (serial — so server sees
 * idempotency keys in the same logical order they were created).
 * Returns the number of successfully synced items.
 */
export async function flush(): Promise<number> {
  const all = await dbGetAll<OutboxItem>("outbox");
  const pending = all
    .filter((i) => i.status !== "syncing")
    .sort((a, b) => a.created_at.localeCompare(b.created_at));

  let synced = 0;

  for (const item of pending) {
    // Mark as syncing
    await dbPut<OutboxItem>("outbox", { ...item, status: "syncing" });
    await notify();

    try {
      const url = `${getApiBase()}${item.endpoint}`;
      const res = await fetch(url, {
        method: item.method,
        headers: {
          "Content-Type": "application/json",
          "X-Idempotency-Key": item.idempotency_key,
        },
        body: JSON.stringify({
          ...item.payload,
          idempotency_key: item.idempotency_key,
        }),
      });

      if (res.ok || res.status === 409) {
        // 409 Conflict means "already processed" — treat as success
        await dbDelete("outbox", item.id);
        synced++;
      } else {
        // Server error — mark failed, keep for retry
        const updated: OutboxItem = {
          ...item,
          status: "failed",
          retries: item.retries + 1,
        };
        await dbPut<OutboxItem>("outbox", updated);
      }
    } catch {
      // Network still unavailable
      const updated: OutboxItem = {
        ...item,
        status: "failed",
        retries: item.retries + 1,
      };
      await dbPut<OutboxItem>("outbox", updated);
    }

    await notify();
  }

  return synced;
}

