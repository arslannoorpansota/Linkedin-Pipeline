import { CHANNEL } from '../lib/channel';
import { AutoPager, type AutoPageConfig, type AutoPageEvent } from './autopage';
import { parseCompanyPage, founderGate, pageIsReady } from '../lib/company';
import { parseProfilePage, rateProfile, profileIsReady } from '../lib/profile';
import { BLOCK_MARKERS } from '../background/queue';

console.info('[LLE] content script running on', window.location.href);

let pager: AutoPager | null = null;
let invalidated = false;

/** True once the extension has been reloaded out from under this page.
 *  sendMessage then throws synchronously, so a promise catch never sees it. */
function send(message: unknown): void {
  if (invalidated) return;
  try {
    const result = chrome.runtime.sendMessage(message);
    if (result && typeof result.catch === 'function') result.catch(() => {});
  } catch {
    invalidated = true;
    pager?.stop('extension was reloaded — reload this tab');
  }
}

function report(event: AutoPageEvent): void {
  send({ type: 'autopage', event });
}

window.addEventListener('message', event => {
  if (event.source !== window || invalidated) return;
  const data = event.data as { channel?: string; url?: string; body?: unknown;
    error?: string; diag?: unknown; seen?: string; hit?: boolean };
  if (data?.channel !== CHANNEL) return;

  if (data.seen) {
    send({ type: 'seen', url: data.seen, hit: data.hit });
    return;
  }
  if (!data.url || data.diag) return;

  send({
    type: 'capture',
    url: data.url,
    body: data.body,
    error: data.error,
    pageUrl: window.location.href,
  });
});

window.addEventListener('beforeunload', () => pager?.stop('left the page'));

function alive(): boolean {
  try { return Boolean(chrome.runtime?.id); } catch { return false; }
}

if (!alive()) {
  console.info('[LLE] runtime id unavailable at inject time');
}

try {
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.type === 'ping') {
    sendResponse({
      ok: true,
      url: window.location.href,
      isSalesNav: window.location.pathname.startsWith('/sales/'),
      paging: pager?.active ?? false,
    });
    return true;
  }

  if (msg?.type === 'autopage:start') {
    pager?.stop('restarted');
    pager = new AutoPager(msg.config as AutoPageConfig, report);
    pager.start();
    sendResponse({ ok: true });
    return true;
  }

  if (msg?.type === 'scrape') {
    const text = document.body?.innerText?.slice(0, 4000).toLowerCase() ?? '';
    if (BLOCK_MARKERS.some(m => text.includes(m))) {
      sendResponse({ ok: false, blocked: true, url: window.location.href });
      return true;
    }
    // Pages paint well after `load`; poll rather than guess a delay, or we
    // read an empty shell and call it "no engineers".
    const wantProfile = msg.kind === 'profile';
    void (async () => {
      const ready = wantProfile ? profileIsReady : pageIsReady;
      const deadline = Date.now() + 15000;
      while (!ready(document) && Date.now() < deadline) {
        await new Promise(r => setTimeout(r, 500));
      }
      if (wantProfile) {
        try {
          const facts = parseProfilePage(document, window.location.href);
          const verdict = rateProfile(facts);
          send({ type: 'profile', facts, verdict, pageUrl: window.location.href });
          sendResponse({ ok: true, ready: profileIsReady(document), facts, verdict });
        } catch (err) {
          sendResponse({ ok: false, error: String(err) });
        }
        return;
      }
      try {
        const facts = parseCompanyPage(document, window.location.href);
        const gate = founderGate(facts);
        send({ type: 'company', facts, gate, pageUrl: window.location.href });
        sendResponse({ ok: true, ready: pageIsReady(document), facts, gate });
      } catch (err) {
        sendResponse({ ok: false, error: String(err) });
      }
    })();
    return true;
  }

  if (msg?.type === 'autopage:stop') {
    pager?.stop();
    sendResponse({ ok: true });
    return true;
  }

  if (msg?.type === 'replay') {
    let settled = false;
    const onReply = (event: MessageEvent) => {
      if (event.source !== window) return;
      const data = event.data as { channel?: string; replay?: unknown };
      if (data?.channel !== CHANNEL || !data.replay) return;
      window.removeEventListener('message', onReply);
      settled = true;
      sendResponse({ ok: true, pageUrl: window.location.href, captures: data.replay });
    };
    window.addEventListener('message', onReply);
    window.postMessage({ channel: CHANNEL, cmd: 'replay' }, window.location.origin);
    setTimeout(() => {
      if (settled) return;
      window.removeEventListener('message', onReply);
      sendResponse({ ok: false, captures: [] });
    }, 1500);
    return true;
  }

  if (msg?.type === 'diag') {
    let settled = false;
    const onReply = (event: MessageEvent) => {
      if (event.source !== window) return;
      const data = event.data as { channel?: string; diag?: unknown };
      if (data?.channel !== CHANNEL || !data.diag) return;
      window.removeEventListener('message', onReply);
      settled = true;
      sendResponse({ ok: true, url: window.location.href, ...(data.diag as object) });
    };
    window.addEventListener('message', onReply);
    window.postMessage({ channel: CHANNEL, cmd: 'diag' }, window.location.origin);
    setTimeout(() => {
      if (settled) return;
      window.removeEventListener('message', onReply);
      sendResponse({ ok: false, url: window.location.href,
                     error: 'MAIN-world interceptor did not respond' });
    }, 1500);
    return true;
  }

  return false;
});
} catch {
  invalidated = true;
}
