import { CHANNEL } from '../lib/channel';
import { AutoPager, type AutoPageConfig, type AutoPageEvent } from './autopage';

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
