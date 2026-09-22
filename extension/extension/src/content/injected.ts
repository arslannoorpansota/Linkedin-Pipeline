import { CHANNEL } from '../lib/channel';

const MAX_SEEN = 400;

// Narrow on purpose. Matching all of /sales-api/ swamps the store with
// presence pings and widget lookups that carry no lead data.
const PATTERNS = [
  /\/sales-api\/salesApiLeadSearch/i,
  /\/sales-api\/salesApiPeopleSearch/i,
  /\/sales-api\/salesApiAccountSearch/i,
];

interface Capture { url: string; body: unknown; error?: string; at: number }
interface Diag { loaded: boolean; all: string[]; matched: string[]; buffer: Capture[] }

const MAX_BUFFER = 30;

const diag: Diag = { loaded: true, all: [], matched: [], buffer: [] };
(window as unknown as { __LLE: Diag }).__LLE = diag;

function record(url: string, matched: boolean): void {
  if (diag.all.length < MAX_SEEN) diag.all.push(url);
  if (matched && diag.matched.length < MAX_SEEN) diag.matched.push(url);
}

function matches(url: string): boolean {
  return PATTERNS.some(p => p.test(url));
}

function post(url: string, body: unknown, error?: string): void {
  // Buffer as well as broadcast: the search fires on page load, which is often
  // before the dashboard exists to hear it.
  diag.buffer.push({ url, body, error, at: Date.now() });
  if (diag.buffer.length > MAX_BUFFER) diag.buffer.shift();
  window.postMessage({ channel: CHANNEL, url, body, error }, window.location.origin);
}

function emit(url: string, body: unknown): void {
  if (typeof body !== 'string') return post(url, body);
  try {
    post(url, JSON.parse(body));
  } catch (e) {
    post(url, null, `response was not JSON (${String(e).slice(0, 80)})`);
  }
}

// Only surface API traffic. Announcing every image and tracker floods the
// message channel and errors once for each one when no dashboard is open.
const INTERESTING = /\/sales-api\/|\/voyager\/api\//i;

function handle(url: string, read: () => Promise<unknown> | unknown): void {
  const hit = matches(url);
  record(url, hit);
  if (hit || INTERESTING.test(url)) {
    window.postMessage({ channel: CHANNEL, seen: url, hit }, window.location.origin);
  }
  if (!hit) return;
  try {
    const body = read();
    if (body instanceof Promise) {
      body.then(b => emit(url, b)).catch(e => post(url, null, `read failed: ${String(e).slice(0, 80)}`));
    } else {
      emit(url, body);
    }
  } catch (e) {
    post(url, null, `read threw: ${String(e).slice(0, 80)}`);
  }
}

const origFetch = window.fetch;
window.fetch = async function (...args: Parameters<typeof fetch>) {
  const res = await origFetch.apply(this, args);
  try {
    const first = args[0];
    const url = typeof first === 'string' ? first
      : first instanceof URL ? first.href
      : (first as Request).url;
    const clone = res.clone();
    handle(url, () => clone.text());
  } catch { /* ignore */ }
  return res;
};

const origOpen = XMLHttpRequest.prototype.open;
const origSend = XMLHttpRequest.prototype.send;

XMLHttpRequest.prototype.open = function (this: XMLHttpRequest, method: string, url: string | URL, ...rest: unknown[]) {
  // LinkedIn opens these with relative paths; absolutise so downstream URL
  // parsing (logging, dedupe) works.
  let absolute: string;
  try { absolute = new URL(String(url), window.location.href).href; }
  catch { absolute = String(url); }
  (this as XMLHttpRequest & { __lleUrl?: string }).__lleUrl = absolute;
  return origOpen.apply(this, [method, url, ...rest] as never);
};

XMLHttpRequest.prototype.send = function (this: XMLHttpRequest, ...args: unknown[]) {
  const url = (this as XMLHttpRequest & { __lleUrl?: string }).__lleUrl;
  if (url) {
    this.addEventListener('load', () => handle(url, () => {
      // Reading responseText throws unless responseType is '' or 'text'.
      // Sales Navigator serves its search results as a blob.
      const type = this.responseType;
      if (type === '' || type === 'text') return this.responseText;
      if (type === 'json') return this.response;
      if (type === 'blob') return (this.response as Blob).text();
      if (type === 'arraybuffer') {
        return new TextDecoder().decode(this.response as ArrayBuffer);
      }
      throw new Error(`unsupported responseType '${type}'`);
    }));
  }
  return origSend.apply(this, args as never);
};

window.addEventListener('message', event => {
  if (event.source !== window) return;
  const data = event.data as { channel?: string; cmd?: string };
  if (data?.channel !== CHANNEL) return;

  if (data.cmd === 'replay') {
    window.postMessage({ channel: CHANNEL, replay: diag.buffer }, window.location.origin);
    return;
  }

  if (data.cmd !== 'diag') return;
  // Keep both ends: the interesting calls fire on page load, and a tail-only
  // slice pushes them out behind high-frequency polling.
  const ends = <T>(xs: T[], n: number): T[] =>
    xs.length <= n * 2 ? xs : [...xs.slice(0, n), ...xs.slice(-n)];
  window.postMessage({ channel: CHANNEL, diag: {
    loaded: true,
    total: diag.all.length,
    totalMatched: diag.matched.length,
    all: ends(diag.all, 60),
    matched: ends(diag.matched, 30),
    buffered: diag.buffer.length,
  } }, window.location.origin);
});

console.info('[LLE] interceptor active on', window.location.href);
