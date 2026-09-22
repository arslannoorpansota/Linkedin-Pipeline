import type { Lead, Settings } from './types';

const DB_NAME = 'lle';
const DB_VERSION = 2;

const STORE_LEADS = 'leads';
const STORE_RAW = 'raw';
const STORE_META = 'meta';
const STORE_COMPANIES = 'companies';

let dbPromise: Promise<IDBDatabase> | null = null;

function open(): Promise<IDBDatabase> {
  if (dbPromise) return dbPromise;
  dbPromise = new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE_LEADS)) {
        const s = db.createObjectStore(STORE_LEADS, { keyPath: 'key' });
        s.createIndex('stage', 'lead.stage');
      }
      if (!db.objectStoreNames.contains(STORE_RAW)) {
        db.createObjectStore(STORE_RAW, { autoIncrement: true });
      }
      if (!db.objectStoreNames.contains(STORE_META)) {
        db.createObjectStore(STORE_META);
      }
      if (!db.objectStoreNames.contains(STORE_COMPANIES)) {
        db.createObjectStore(STORE_COMPANIES, { keyPath: 'companyId' });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
  return dbPromise;
}

function tx<T>(store: string, mode: IDBTransactionMode, fn: (s: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  return open().then(db => new Promise<T>((resolve, reject) => {
    const t = db.transaction(store, mode);
    const req = fn(t.objectStore(store));
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  }));
}

export function leadKey(lead: Lead): string | null {
  return lead.profileId || lead.salesUrn || null;
}

export async function putLeads(leads: Lead[]): Promise<number> {
  const db = await open();
  return new Promise((resolve, reject) => {
    const t = db.transaction(STORE_LEADS, 'readwrite');
    const store = t.objectStore(STORE_LEADS);
    let written = 0;
    for (const lead of leads) {
      const key = leadKey(lead);
      if (!key) continue;
      store.put({ key, lead });
      written++;
    }
    t.oncomplete = () => resolve(written);
    t.onerror = () => reject(t.error);
  });
}

export async function allLeads(): Promise<Lead[]> {
  const rows = await tx<Array<{ key: string; lead: Lead }>>(STORE_LEADS, 'readonly', s => s.getAll());
  return rows.map(r => r.lead);
}

export async function countLeads(): Promise<number> {
  return tx<number>(STORE_LEADS, 'readonly', s => s.count());
}

export async function clearLeads(): Promise<void> {
  await tx(STORE_LEADS, 'readwrite', s => s.clear());
  await tx(STORE_RAW, 'readwrite', s => s.clear());
}

export async function putRaw(url: string, body: unknown): Promise<void> {
  await tx(STORE_RAW, 'readwrite', s => s.add({ url, body, at: new Date().toISOString() }));
}

export async function allRaw(): Promise<unknown[]> {
  return tx<unknown[]>(STORE_RAW, 'readonly', s => s.getAll());
}

export async function getSettings(): Promise<Settings> {
  const v = await tx<Settings | undefined>(STORE_META, 'readonly', s => s.get('settings'));
  return { captureRaw: true, autoRun: false, ...(v ?? {}) };
}

export async function setSettings(settings: Settings): Promise<void> {
  await tx(STORE_META, 'readwrite', s => s.put(settings, 'settings'));
}


/* ---- company facts from the account pages ---------------------------- */

export function putCompany(record: unknown): Promise<IDBValidKey> {
  return tx(STORE_COMPANIES, 'readwrite', s => s.put(record as never));
}

export function allCompanies<T = unknown>(): Promise<T[]> {
  return tx<T[]>(STORE_COMPANIES, 'readonly', s => s.getAll() as IDBRequest<T[]>);
}

export function clearCompanies(): Promise<void> {
  return tx(STORE_COMPANIES, 'readwrite', s => s.clear()).then(() => undefined);
}
