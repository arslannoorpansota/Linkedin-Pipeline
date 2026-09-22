import { allCompanies, allLeads, allProfiles, allRaw, clearCompanies, clearLeads, clearProfiles, countLeads, getSettings, putCompany, putLeads, putProfile, putRaw, setSettings } from '../db';
import { parseLeads } from '../lib/salesnav';
import { download, rowsToCsv, toCsv, toJson } from '../lib/csv';
import type { CaptureStats, Lead } from '../types';

const el = <T extends HTMLElement>(id: string): T => {
  const node = document.getElementById(id);
  if (!node) throw new Error(`missing #${id}`);
  return node as T;
};

const SALESNAV = 'https://www.linkedin.com/sales/*';
const LINKEDIN = 'https://www.linkedin.com/*';
const TRACE_SLOTS = 56;
const MAX_LOG = 120;
const CAPTURE_TIMEOUT_MS = 45_000;

const stats: CaptureStats = { pages: 0, leads: 0, lastCapturedAt: null, unparsed: 0 };
const seenPages = new Set<string>();
const seenPaths = new Map<string, number>();

let paging = false;
let watchdog: number | null = null;
let logCount = 0;

/* ---- connection state ---------------------------------------------- */

function setConn(state: 'idle' | 'live' | 'alert', label: string): void {
  const node = el('conn');
  node.dataset['state'] = state;
  node.textContent = label;
}

function setStatus(text: string, alert = false): void {
  const node = el('status');
  node.textContent = text;
  node.dataset['tone'] = alert ? 'alert' : 'info';
}

/* ---- capture trace -------------------------------------------------- */

const trace = el('trace');
for (let i = 0; i < TRACE_SLOTS; i++) trace.appendChild(document.createElement('i'));

function pushTrace(kind: 'tick' | 'hit'): void {
  const first = trace.firstElementChild;
  if (first) trace.removeChild(first);
  const bar = document.createElement('i');
  if (kind === 'hit') bar.className = 'hit';
  else bar.className = 'fresh';
  trace.appendChild(bar);
  if (kind === 'tick') {
    setTimeout(() => bar.classList.remove('fresh'), 900);
  }
}

/* ---- activity log --------------------------------------------------- */

const logBox = el('log');

function log(kind: 'ok' | 'hit' | 'bad' | 'dim', what: string, note = ''): void {
  if (logCount === 0) logBox.innerHTML = '';
  const glyph = kind === 'hit' ? '◆' : kind === 'bad' ? '✕' : kind === 'ok' ? '✓' : '·';
  const line = document.createElement('p');
  line.className = kind;
  line.innerHTML =
    `<span class="t">${new Date().toLocaleTimeString([], { hour12: false })}</span>`
    + `<span class="g">${glyph}</span><span class="what"></span><span class="n"></span>`;
  (line.querySelector('.what') as HTMLElement).textContent = what;
  (line.querySelector('.n') as HTMLElement).textContent = note;
  logBox.prepend(line);
  if (++logCount > MAX_LOG) logBox.lastElementChild?.remove();
}

/* ---- rendering ------------------------------------------------------ */

function renderStats(): void {
  el('s-leads').textContent = stats.leads.toLocaleString();
  el('s-pages').textContent = String(stats.pages);
  el('s-unparsed').textContent = String(stats.unparsed);
  el('s-last').textContent = stats.lastCapturedAt
    ? new Date(stats.lastCapturedAt).toLocaleTimeString([], { hour12: false })
    : '—';
  el('tblCount').textContent = stats.leads ? `${stats.leads.toLocaleString()} captured` : '';
}

function cell(text: string | null, cls = ''): string {
  const safe = (text ?? '—').replace(/[<>&]/g, m =>
    ({ '<': '&lt;', '>': '&gt;', '&': '&amp;' }[m] ?? m));
  return `<td${cls ? ` class="${cls}"` : ''}>${safe}</td>`;
}

function renderTable(leads: Lead[]): void {
  if (leads.length === 0) {
    el('tbody').innerHTML =
      '<tr><td colspan="7" class="tbl-empty">Nothing captured yet.</td></tr>';
    return;
  }
  const recent = leads.slice(-60).reverse();
  el('tbody').innerHTML = recent.map((lead, i) =>
    '<tr>'
    + cell(String(leads.length - i), 'idx')
    + cell(lead.fullName, 'name')
    + cell(lead.currentTitle, 'dim')
    + cell(lead.companyName)
    + cell(lead.industry, 'dim')
    + cell(lead.location, 'dim')
    + cell(lead.yearsInRole === null ? '—' : `${lead.yearsInRole}`, 'num')
    + '</tr>').join('');
}

async function refresh(): Promise<void> {
  const leads = await allLeads();
  stats.leads = leads.length;
  renderStats();
  renderTable(leads);
}

/* ---- capture handling ----------------------------------------------- */

function pathOf(url: string): string {
  try { return new URL(url, 'https://www.linkedin.com').pathname; }
  catch { return url.split('?')[0] ?? url; }
}

function endpointName(url: string): string {
  return pathOf(url).replace(/^\/sales-api\//, '').replace(/^\/voyager\/api\//, '') || url;
}

function pageLabel(): string {
  return stats.pages > 0 ? `page ${stats.pages}` : 'this page';
}

async function handleCapture(url: string, body: unknown, pageUrl: string,
                             error?: string): Promise<void> {
  const name = endpointName(url);

  if (error) {
    log('bad', 'Could not read a page of results', '');
    setStatus('LinkedIn sent something we could not read. '
      + 'If this keeps happening, use "Something looks wrong" below.', true);
    return;
  }

  const settings = await getSettings();
  if (settings.captureRaw) await putRaw(url, body);

  const page = /(?:page|start)=(\d+)/i.exec(url)?.[1];
  const { leads, unparsed } = parseLeads(body, {
    kind: 'salesnav',
    searchUrl: pageUrl,
    page: page ? Number(page) : 0,
    capturedAt: new Date().toISOString(),
  });

  if (!seenPages.has(url)) { seenPages.add(url); stats.pages++; }
  stats.unparsed += unparsed;
  stats.lastCapturedAt = new Date().toISOString();

  if (leads.length === 0) {
    const shape = body && typeof body === 'object'
      ? `keys: ${Object.keys(body as object).slice(0, 6).join(', ') || 'none'}`
      : `body was ${typeof body}`;
    log('bad', 'Found a results page but no leads on it', '');
    setStatus('LinkedIn changed how results are sent, so nothing could be read. '
      + 'Open "Something looks wrong" and download the technical log.', true);
    console.info('[LLE] unparsed payload —', shape);
    renderStats();
    return;
  }

  await putLeads(leads);
  const total = await countLeads();
  log('hit', `Collected from ${pageLabel()}`, `+${leads.length}`);
  setConn('live', 'Collecting');
  setStatus(`${total.toLocaleString()} leads collected so far`
    + (paging ? ' — still going.' : '. Press Download leads when you are ready.'));
  await refresh();
}

/* ---- messaging ------------------------------------------------------ */

chrome.runtime.onMessage.addListener(msg => {
  if (msg?.type === 'seen') {
    const path = pathOf(msg.url as string);
    const n = (seenPaths.get(path) ?? 0) + 1;
    seenPaths.set(path, n);
    pushTrace(msg.hit ? 'hit' : 'tick');
    setConn('live', paging ? 'Collecting' : 'Connected');
    return;
  }

  if (msg?.type === 'company') {
    void (async () => {
      await putCompany({ ...(msg.facts as object), gate: msg.gate });
      const n = (await allCompanies()).length;
      el('visitStat').textContent = `${n} companies read`;
    })();
    return;
  }

  if (msg?.type === 'profile') {
    void (async () => {
      await putProfile({ ...(msg.facts as object), verdict: msg.verdict });
      const n = (await allProfiles()).length;
      el('visitStat').textContent += ` / ${n} profiles`;
    })();
    return;
  }

  if (msg?.type === 'queue') {
    const m = msg as { event: string; index?: number; total?: number;
                       company?: string; ok?: boolean; visited?: number; failed?: number };
    if (m.event === 'progress') {
      setStatus(`Reading ${m.index} of ${m.total}: ${m.company}`);
      el('visitProgress').textContent = `${m.index} / ${m.total}`;
    } else if (m.event === 'done') {
      setConn('idle', 'Finished');
      setStatus(`Done. Read ${m.visited} companies, ${m.failed} could not be read. `
        + `Press Download company data.`, false);
      visitBtn.textContent = 'Start visiting';
    } else if (m.event === 'blocked') {
      setConn('alert', 'Stopped');
      setStatus('LinkedIn showed a limit or verification notice. Stop for today; '
        + 'progress is saved and you can resume later.', true);
      visitBtn.textContent = 'Start visiting';
    }
    return;
  }

  if (msg?.type === 'capture') {
    void handleCapture(msg.url as string, msg.body, msg.pageUrl as string,
                       msg.error as string | undefined);
    return;
  }

  if (msg?.type === 'autopage') {
    const e = msg.event as { kind: string; page?: number; maxPages?: number;
                             reason?: string; pages?: number };
    if (e.kind === 'progress') {
      el('pageStat').textContent = `page ${e.page} of ${e.maxPages}`;
      armWatchdog(true);
    } else if (e.kind === 'stopped') {
      setPagingUi(false);
      el('pageStat').textContent = `finished · ${e.pages} pages`;
      const done = /last page|page limit/.test(e.reason ?? '');
      setStatus(done
        ? `Finished — read ${e.pages} pages. Press Download leads.`
        : `Stopped early — ${e.reason}. Your leads so far are saved.`, !done);
      setConn('idle', done ? 'Finished' : 'Stopped');
      log(done ? 'ok' : 'bad', done ? 'Finished collecting' : 'Stopped early',
          `${e.pages} pages`);
      if (autoRunBox.checked) void exportAll();
    }
  }
});

/* ---- run control ---------------------------------------------------- */

const pageBtn = el<HTMLButtonElement>('page');
const maxPages = el<HTMLInputElement>('maxPages');
const minDelay = el<HTMLInputElement>('minDelay');
const maxDelay = el<HTMLInputElement>('maxDelay');
const autoRunBox = el<HTMLInputElement>('autoRun');
const captureRaw = el<HTMLInputElement>('captureRaw');

async function salesNavTab(): Promise<chrome.tabs.Tab | null> {
  const tabs = await chrome.tabs.query({ url: SALESNAV });
  return tabs[0] ?? null;
}

function setPagingUi(on: boolean): void {
  paging = on;
  pageBtn.textContent = on ? 'Stop collecting' : 'Start collecting';
  pageBtn.dataset['running'] = String(on);
  for (const input of [maxPages, minDelay, maxDelay]) input.disabled = on;
  if (!on) armWatchdog(false);
}

function armWatchdog(on: boolean): void {
  if (watchdog !== null) { clearTimeout(watchdog); watchdog = null; }
  if (!on) return;
  watchdog = window.setTimeout(() => {
    if (paging) void stopRun('nothing arrived for 45 seconds');
  }, CAPTURE_TIMEOUT_MS);
}

async function stopRun(reason: string): Promise<void> {
  const tab = await salesNavTab();
  if (tab?.id !== undefined) {
    await chrome.tabs.sendMessage(tab.id, { type: 'autopage:stop' }).catch(() => {});
  }
  setPagingUi(false);
  el('pageStat').textContent = 'stopped';
  setStatus(`Stopped — ${reason}. Everything collected so far is saved.`, true);
  setConn('idle', 'Stopped');
}

pageBtn.addEventListener('click', async () => {
  if (paging) return void stopRun('you stopped it');

  const tab = await salesNavTab();
  if (tab?.id === undefined) {
    setConn('alert', 'No search open');
    return setStatus('Open a Sales Navigator search in another tab first.', true);
  }

  const lo = Math.max(2, Number(minDelay.value) || 4);
  const hi = Math.max(lo, Number(maxDelay.value) || 9);
  const config = { maxPages: Math.max(1, Number(maxPages.value) || 30),
                   minDelay: lo * 1000, maxDelay: hi * 1000 };

  const ok = await chrome.tabs.sendMessage(tab.id, { type: 'autopage:start', config })
    .then(() => true).catch(() => false);
  if (!ok) {
    setConn('alert', 'Cannot reach tab');
    return setStatus('Could not reach your Sales Navigator tab. Reload it and try again.', true);
  }

  setPagingUi(true);
  armWatchdog(true);
  setConn('live', 'Collecting');
  el('pageStat').textContent = `up to ${config.maxPages} pages`;
  setStatus(`Collecting — reading up to ${config.maxPages} pages, `
    + `pausing ${lo}–${hi} seconds between each. You can leave this running.`);
  log('ok', 'Started collecting', `${config.maxPages} pages max`);
});

/* ---- exports -------------------------------------------------------- */

async function exportAll(): Promise<void> {
  const leads = await allLeads();
  if (leads.length === 0) return;
  const stamp = Date.now();
  download(`leads-${stamp}.csv`, toCsv(leads), 'text/csv');
  setTimeout(() => download(`leads-${stamp}.json`, toJson(leads), 'application/json'), 400);
  log('ok', 'Saved to Downloads', `${leads.length} leads`);
}

el('csv').addEventListener('click', async () => {
  const leads = await allLeads();
  if (leads.length === 0) return setStatus('No leads collected yet.', true);
  download(`leads-${Date.now()}.csv`, toCsv(leads), 'text/csv');
  setStatus(`Saved ${leads.length.toLocaleString()} leads to your Downloads folder. `
    + `Now run ./run.sh in your terminal.`);
});

el('json').addEventListener('click', async () => {
  const leads = await allLeads();
  if (leads.length === 0) return setStatus('No leads collected yet.', true);
  download(`leads-${Date.now()}.json`, toJson(leads), 'application/json');
  setStatus(`Saved full details for ${leads.length.toLocaleString()} leads to Downloads.`);
});

el('raw').addEventListener('click', async () => {
  const raw = await allRaw();
  if (raw.length === 0) return setStatus('No technical log stored. '
    + 'Tick "Keep technical log", then collect again.', true);
  download(`raw-${Date.now()}.json`, JSON.stringify(raw, null, 2), 'application/json');
  setStatus(`Saved the technical log (${raw.length} item(s)) to Downloads.`);
});

el('clear').addEventListener('click', async () => {
  const total = await countLeads();
  if (!confirm(`Delete all ${total} captured leads and stored payloads?`)) return;
  await clearLeads();
  stats.pages = 0; stats.unparsed = 0; stats.lastCapturedAt = null;
  seenPages.clear();
  setStatus('All leads deleted.');
  log('ok', 'Deleted all leads', `${total} removed`);
  await refresh();
});

captureRaw.addEventListener('change', async () => {
  const settings = await getSettings();
  await setSettings({ ...settings, captureRaw: captureRaw.checked });
});

autoRunBox.addEventListener('change', async () => {
  const settings = await getSettings();
  await setSettings({ ...settings, autoRun: autoRunBox.checked });
  if (autoRunBox.checked && !paging) void beginAutoRun();
});

/* ---- diagnostics ---------------------------------------------------- */

el('diag').addEventListener('click', async () => {
  const tabs = await chrome.tabs.query({ url: LINKEDIN });
  if (tabs.length === 0) {
    return setStatus('No LinkedIn tab is open.', true);
  }

  const report: string[] = [];
  for (const tab of tabs) {
    if (tab.id === undefined) continue;
    const res = await chrome.tabs.sendMessage(tab.id, { type: 'diag' })
      .catch((e: Error) => ({ ok: false, url: tab.url, error: `no content script (${e.message})` }));
    report.push(JSON.stringify(res, null, 2));
  }

  const first = report[0] ?? '';
  if (first.includes('no content script')) {
    setStatus('Not connected to that tab. Reload your Sales Navigator tab and try again.', true);
  } else if (first.includes('did not respond')) {
    setStatus('Connected, but not reading the page yet. Reload your Sales Navigator tab.', true);
  } else {
    const p = JSON.parse(first) as { total?: number; totalMatched?: number };
    setStatus((p.totalMatched ?? 0) > 0
      ? `Working — found ${p.totalMatched} page(s) of results. Technical log saved to Downloads.`
      : `Connected, but no search results have come through yet. `
        + `Try moving to the next page of your search. Log saved to Downloads.`,
      (p.totalMatched ?? 0) === 0);
  }
  download(`diagnostic-${Date.now()}.json`, `[${report.join(',')}]`, 'application/json');
});

/* ---- replay + boot -------------------------------------------------- */

async function replayBuffered(): Promise<number> {
  const tabs = await chrome.tabs.query({ url: LINKEDIN });
  let replayed = 0;
  for (const tab of tabs) {
    if (tab.id === undefined) continue;
    const res = await chrome.tabs.sendMessage(tab.id, { type: 'replay' })
      .catch(() => null) as { pageUrl?: string; captures?: unknown[] } | null;
    for (const capture of res?.captures ?? []) {
      const c = capture as { url: string; body: unknown; error?: string };
      await handleCapture(c.url, c.body, res?.pageUrl ?? tab.url ?? '', c.error);
      replayed++;
    }
  }
  return replayed;
}

async function beginAutoRun(): Promise<void> {
  if (!(await salesNavTab())) {
    setConn('alert', 'No search open');
    return setStatus('Set to start automatically, but no Sales Navigator search is open.', true);
  }
  log('ok', 'Starting automatically', '');
  pageBtn.click();
}

void (async () => {
  const settings = await getSettings();
  captureRaw.checked = settings.captureRaw;
  autoRunBox.checked = settings.autoRun;
  await refresh();

  const tab = await salesNavTab();
  setConn(tab ? 'live' : 'idle', tab ? 'Connected' : 'No search open');
  if (!tab) setStatus('Open a Sales Navigator search in another tab, then come back here.', true);
  else setStatus('Ready. Press Start collecting, and leave this page open.');

  const replayed = await replayBuffered();
  if (replayed > 0) log('ok', 'Picked up leads collected before this page opened', '');

  if (settings.autoRun) setTimeout(() => { if (!paging) void beginAutoRun(); }, 1200);
})();


/* ---- visit queue: walk every company page ---------------------------- */

const visitBtn = el<HTMLButtonElement>('visit');
let queueItems: { row: string; company: string; companyUrl: string; profileUrl: string }[] = [];

el('loadList').addEventListener('click', () => el<HTMLInputElement>('visitFile').click());

el<HTMLInputElement>('visitFile').addEventListener('change', async event => {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;
  const text = await file.text();
  const lines = text.split(/\r?\n/).filter(Boolean);
  const head = (lines.shift() ?? '').split(',').map(h => h.replace(/^"|"$/g, '').trim());
  const iRow = head.indexOf('row');
  const iCo = head.indexOf('company');
  const iUrl = head.indexOf('companyUrl');
  const iProf = head.indexOf('profileUrl');
  if (iUrl < 0) return setStatus('That CSV has no companyUrl column.', true);

  queueItems = lines.map(line => {
    const cells = line.match(/("([^"]|"")*"|[^,]*)/g)?.filter((_, i) => i % 2 === 0) ?? [];
    const cell = (i: number) => (cells[i] ?? '').replace(/^"|"$/g, '').replace(/""/g, '"').trim();
    return { row: cell(iRow), company: cell(iCo), companyUrl: cell(iUrl), profileUrl: cell(iProf) };
  }).filter(x => x.companyUrl.startsWith('http'));

  el('visitStat').textContent = `${queueItems.length} companies loaded`;
  setStatus(`Loaded ${queueItems.length} companies. Press Start visiting.`);
});

visitBtn.addEventListener('click', async () => {
  try {
  const state = await chrome.runtime.sendMessage({ type: 'queue:state' });
  if (state?.running) {
    await chrome.runtime.sendMessage({ type: 'queue:stop' });
    visitBtn.textContent = 'Start visiting';
    return setStatus('Stopped. Progress is saved.', true);
  }
  if (queueItems.length === 0) return setStatus('Load a CSV with company URLs first.', true);

  const lo = Math.max(4, Number(el<HTMLInputElement>('visitMin').value) || 6) * 1000;
  const hi = Math.max(lo, Number(el<HTMLInputElement>('visitMax').value) * 1000 || lo + 6000);
  const res = await chrome.runtime.sendMessage({
    type: 'queue:start', items: queueItems, minDelay: lo, maxDelay: hi,
  });
  if (res?.ok) {
    visitBtn.textContent = 'Stop visiting';
    setConn('live', 'Visiting');
    setStatus(`Visiting ${res.queued} company pages. Leave this window open.`);
  } else {
    setStatus('The background worker did not start the run. '
      + 'Reload the extension at chrome://extensions, then try again.', true);
  }
  } catch (err) {
    setConn('alert', 'Error');
    setStatus(`Could not start: ${String(err)}. Reload the extension and this page.`, true);
    console.error('[LLE] visit start failed', err);
  }
});

el('companyCsv').addEventListener('click', async () => {
  const rows = await allCompanies<Record<string, unknown>>();
  if (rows.length === 0) return setStatus('No company data yet.', true);
  const flat = rows.map(r => {
    const g = (r['gate'] ?? {}) as Record<string, unknown>;
    return {
      companyId: r['companyId'], name: r['name'], headcount: r['headcount'],
      revenue: r['revenue'], industry: r['industry'], location: r['location'],
      website: r['website'], employeesListed: r['employeesListed'],
      decisionMakers: r['decisionMakers'], cxoCount: r['cxoCount'],
      keep: g['keep'], gateReason: g['reason'], hasCto: g['hasCto'],
      engineerTitles: (g['engineerTitles'] as string[] ?? []).join(' | '),
      confident: g['confident'],
      titles: (r['titles'] as string[] ?? []).join(' | '),
      capturedAt: r['capturedAt'],
      domSample: r['domSample'],
    };
  });
  download(`companies-${Date.now()}.csv`, rowsToCsv(flat as never), 'text/csv');
  setStatus(`Saved ${flat.length} companies to Downloads.`);
});

el('companyCsv').addEventListener('dblclick', () => {/* noop */});

async function exportProfiles(): Promise<void> {
  const rows = await allProfiles<Record<string, unknown>>();
  if (rows.length === 0) return setStatus('No profile data yet.', true);
  const flat = rows.map(r => {
    const v = (r['verdict'] ?? {}) as Record<string, unknown>;
    return {
      profileId: r['profileId'], name: r['name'], headline: r['headline'],
      currentTitle: r['currentTitle'], about: r['about'],
      experience: (r['experience'] as string[] ?? []).join(' | '),
      education: (r['education'] as string[] ?? []).join(' | '),
      profileRating: v['rating'], profileReason: v['reason'],
      technical: v['technical'],
      evidence: (v['evidence'] as string[] ?? []).join(' | '),
      capturedAt: r['capturedAt'], domSample: r['domSample'],
    };
  });
  download(`profiles-${Date.now()}.csv`, rowsToCsv(flat as never), 'text/csv');
  setStatus(`Saved ${flat.length} profiles to Downloads.`);
}
el('profileCsv').addEventListener('click', () => { void exportProfiles(); });

el('clearCompanies').addEventListener('click', async () => {
  await clearProfiles();
  await clearCompanies();
  el('visitStat').textContent = '0 companies read';
  setStatus('Cleared stored company data.');
});
