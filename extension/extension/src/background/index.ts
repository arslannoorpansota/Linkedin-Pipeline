import { getState, setState, reset, jitter, type QueueItem } from './queue';

const DASHBOARD = 'dashboard.html';

async function openDashboard(): Promise<void> {
  const url = chrome.runtime.getURL(DASHBOARD);
  const existing = await chrome.tabs.query({ url });
  const tab = existing[0];
  if (tab?.id !== undefined) {
    await chrome.tabs.update(tab.id, { active: true });
    if (tab.windowId !== undefined) await chrome.windows.update(tab.windowId, { focused: true });
    return;
  }
  await chrome.tabs.create({ url });
}

chrome.action.onClicked.addListener(() => { void openDashboard(); });

/* ---- the visit queue ------------------------------------------------- */

/** The tab the queue drives. Kept in session storage so a suspended worker
 *  can pick the run back up instead of opening a second tab. */
async function workTabId(): Promise<number | null> {
  const got = await chrome.storage.local.get('workTabId');
  const id = got['workTabId'] as number | undefined;
  if (id === undefined) return null;
  try { await chrome.tabs.get(id); return id; } catch { return null; }
}

async function setWorkTab(id: number | null): Promise<void> {
  if (id === null) await chrome.storage.local.remove('workTabId');
  else await chrome.storage.local.set({ workTabId: id });
}

function notify(payload: unknown): void {
  // The dashboard may be closed; a dropped message is not an error.
  chrome.runtime.sendMessage({ type: 'queue', ...(payload as object) }).catch(() => {});
}

/** Wait for a tab to finish loading, or give up. */
function waitForLoad(tabId: number, timeoutMs = 45000): Promise<boolean> {
  return new Promise(resolve => {
    let done = false;
    const finish = (ok: boolean) => {
      if (done) return;
      done = true;
      chrome.tabs.onUpdated.removeListener(onUpdated);
      clearTimeout(timer);
      resolve(ok);
    };
    const onUpdated = (id: number, info: { status?: string }) => {
      if (id === tabId && info.status === 'complete') finish(true);
    };
    const timer = setTimeout(() => finish(false), timeoutMs);
    chrome.tabs.onUpdated.addListener(onUpdated);
  });
}

/** Ask the content script to read the page it is sitting on. */
async function scrape(tabId: number, kind: 'company' | 'profile'): Promise<unknown> {
  try {
    return await chrome.tabs.sendMessage(tabId, { type: 'scrape', kind });
  } catch {
    return { ok: false, error: 'content script did not answer' };
  }
}

async function step(): Promise<void> {
  const state = await getState();
  if (!state.running) return;

  if (state.index >= state.items.length) {
    await setState({ running: false, stoppedReason: 'finished the list' });
    notify({ event: 'done', visited: state.visited.length, failed: state.failed.length });
    return;
  }

  const item = state.items[state.index] as QueueItem;
  let tabId = await workTabId();
  if (tabId === null) {
    const tab = await chrome.tabs.create({ url: item.companyUrl, active: false });
    tabId = tab.id ?? null;
    await setWorkTab(tabId);
  } else {
    await chrome.tabs.update(tabId, { url: item.companyUrl });
  }
  if (tabId === null) {
    await setState({ running: false, stoppedReason: 'could not open a tab' });
    return;
  }

  const loaded = await waitForLoad(tabId);
  await new Promise(r => setTimeout(r, 1500));

  const result = loaded
    ? await scrape(tabId, 'company')
    : { ok: false, error: 'page did not finish loading' };

  const res = result as { ok?: boolean; blocked?: boolean; error?: string };

  // Then the person. The company page cannot tell us whether the founder is
  // technical; their own profile can, and it renders in a background tab.
  if (!res?.blocked && item.profileUrl) {
    await new Promise(r => setTimeout(r, jitter(2000, 4000)));
    await chrome.tabs.update(tabId, { url: item.profileUrl });
    const pLoaded = await waitForLoad(tabId);
    await new Promise(r => setTimeout(r, 1500));
    if (pLoaded) await scrape(tabId, 'profile');
  }

  if (res?.blocked) {
    await setState({ running: false, stoppedReason: 'LinkedIn showed a limit or verification notice' });
    notify({ event: 'blocked', item });
    return;
  }

  const next = await getState();
  const visited = res?.ok ? [...next.visited, item.companyUrl] : next.visited;
  const failed = res?.ok ? next.failed
    : [...next.failed, { url: item.companyUrl, reason: res?.error ?? 'unknown' }];

  await setState({ index: next.index + 1, visited, failed });
  notify({
    event: 'progress', index: next.index + 1, total: next.items.length,
    company: item.company, ok: Boolean(res?.ok),
  });

  if (!(await getState()).running) return;
  setTimeout(() => { void step(); }, jitter(next.minDelay, next.maxDelay));
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.type === 'queue:start') {
    void (async () => {
      await setState({
        running: true, items: msg.items as QueueItem[], index: 0,
        minDelay: msg.minDelay ?? 6000, maxDelay: msg.maxDelay ?? 12000,
        startedAt: new Date().toISOString(), stoppedReason: null,
        visited: [], failed: [],
      });
      sendResponse({ ok: true, queued: (msg.items as QueueItem[]).length });
      void step();
    })();
    return true;
  }

  if (msg?.type === 'queue:stop') {
    void (async () => {
      await setState({ running: false, stoppedReason: 'stopped by you' });
      sendResponse({ ok: true });
    })();
    return true;
  }

  if (msg?.type === 'queue:state') {
    void (async () => sendResponse(await getState()))();
    return true;
  }

  if (msg?.type === 'queue:reset') {
    void (async () => { await reset(); await setWorkTab(null); sendResponse({ ok: true }); })();
    return true;
  }

  return false;
});
