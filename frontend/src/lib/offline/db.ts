/**
 * Voxera IndexedDB wrapper — native API, zero heavy dependencies.
 *
 * Object stores:
 *   domains   — DomainProfile[]    keyed by id
 *   ledger    — LedgerEntryItem[]  keyed by sessionId
 *   holds     — InterceptHoldItem[] keyed by id
 *   outbox    — OutboxItem[]        keyed by id (used by outbox.ts)
 *   meta      — arbitrary key/value pairs
 */

const DB_NAME = "voxera-offline";
const DB_VERSION = 1;

export type StoreNames = "domains" | "ledger" | "holds" | "outbox" | "meta";

let _db: IDBDatabase | null = null;

function openDB(): Promise<IDBDatabase> {
  if (_db) return Promise.resolve(_db);

  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;

      if (!db.objectStoreNames.contains("domains")) {
        db.createObjectStore("domains", { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains("ledger")) {
        db.createObjectStore("ledger", { keyPath: "sessionId" });
      }
      if (!db.objectStoreNames.contains("holds")) {
        db.createObjectStore("holds", { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains("outbox")) {
        db.createObjectStore("outbox", { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains("meta")) {
        db.createObjectStore("meta");
      }
    };

    request.onsuccess = (event) => {
      _db = (event.target as IDBOpenDBRequest).result;
      resolve(_db);
    };

    request.onerror = (event) => {
      reject((event.target as IDBOpenDBRequest).error);
    };
  });
}

// ── Generic helpers ──────────────────────────────────────────────────────────

export async function dbGet<T>(store: StoreNames, key: IDBValidKey): Promise<T | undefined> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(store, "readonly");
    const req = tx.objectStore(store).get(key);
    req.onsuccess = () => resolve(req.result as T | undefined);
    req.onerror = () => reject(req.error);
  });
}

export async function dbGetAll<T>(store: StoreNames): Promise<T[]> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(store, "readonly");
    const req = tx.objectStore(store).getAll();
    req.onsuccess = () => resolve(req.result as T[]);
    req.onerror = () => reject(req.error);
  });
}

export async function dbPut<T>(store: StoreNames, value: T, key?: IDBValidKey): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(store, "readwrite");
    const req = key !== undefined
      ? tx.objectStore(store).put(value, key)
      : tx.objectStore(store).put(value);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}

export async function dbPutAll<T>(store: StoreNames, items: T[]): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(store, "readwrite");
    const os = tx.objectStore(store);
    items.forEach((item) => os.put(item));
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function dbDelete(store: StoreNames, key: IDBValidKey): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(store, "readwrite");
    const req = tx.objectStore(store).delete(key);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}

export async function dbClear(store: StoreNames): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(store, "readwrite");
    const req = tx.objectStore(store).clear();
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}

// ── Meta helpers ─────────────────────────────────────────────────────────────

export async function metaGet<T>(key: string): Promise<T | undefined> {
  return dbGet<T>("meta", key);
}

export async function metaSet<T>(key: string, value: T): Promise<void> {
  return dbPut<T>("meta", value, key);
}

