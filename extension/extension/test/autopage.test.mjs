import * as esbuild from 'esbuild';

const r = await esbuild.build({
  entryPoints: [new URL('../src/content/autopage.ts', import.meta.url).pathname],
  bundle: true, format: 'esm', write: false, target: 'node20',
});

// minimal DOM + controllable clock
let now = 0, queue = [];
const clock = {
  setTimeout: (fn, ms) => { const id = queue.length; queue.push({ id, at: now + ms, fn }); return id; },
  clearTimeout: id => { queue = queue.filter(t => t.id !== id); },
};
function tick() {
  const due = queue.sort((a, b) => a.at - b.at).shift();
  if (!due) return false;
  now = due.at; due.fn(); return true;
}
function runAll(max = 200) { let n = 0; while (tick() && n++ < max); }

const dom = { next: null, bodyText: '' };
globalThis.window = { setTimeout: clock.setTimeout };
globalThis.clearTimeout = clock.clearTimeout;
globalThis.document = {
  querySelector: sel => (sel.includes('Next') || sel.includes('next')) ? dom.next : null,
  get body() { return { innerText: dom.bodyText }; },
};

const { AutoPager } = await import('data:text/javascript;base64,' +
  Buffer.from(r.outputFiles[0].text).toString('base64'));

const a = (c, m) => { if (!c) { console.error('FAIL: ' + m); process.exit(1); } };
const cfg = { maxPages: 5, minDelay: 1000, maxDelay: 2000 };
const mkBtn = () => ({ clicks: 0, disabled: false, attrs: {},
  click() { this.clicks++; }, getAttribute(k) { return this.attrs[k] ?? null; } });

// 1. stops at the page limit
dom.next = mkBtn(); dom.bodyText = '';
let events = [];
new AutoPager(cfg, e => events.push(e)).start();
runAll();
a(dom.next.clicks === 5, `expected 5 clicks, got ${dom.next.clicks}`);
let stop = events.find(e => e.kind === 'stopped');
a(stop && stop.reason.includes('5-page limit'), JSON.stringify(stop));
a(events.filter(e => e.kind === 'progress').length === 5, 'progress per page');
console.log('page limit           OK  (5 clicks then stop, never overruns)');

// 2. randomised interval inside the configured window
queue = []; now = 0; dom.next = mkBtn(); events = [];
const gaps = [];
let last = 0;
new AutoPager(cfg, () => { gaps.push(now - last); last = now; }).start();
runAll();
const real = gaps.slice(0, 5);
a(real.every(g => g >= 1000 && g <= 2000), `gaps out of range: ${real}`);
a(new Set(real).size > 1, 'delays must be jittered, not fixed');
console.log('jitter               OK  (all gaps within 1-2s, not constant)');

// 3. halts on LinkedIn's commercial-use notice
queue = []; now = 0; dom.next = mkBtn(); events = [];
dom.bodyText = "You've reached the commercial use limit for this month.";
new AutoPager(cfg, e => events.push(e)).start();
runAll();
a(dom.next.clicks === 0, 'must not click after a limit notice');
stop = events.find(e => e.kind === 'stopped');
a(stop && stop.reason.includes('limit or verification'), JSON.stringify(stop));
console.log('block notice         OK  (0 clicks, halts immediately)');

// 4. stops on the last page
queue = []; now = 0; dom.bodyText = ''; events = [];
dom.next = mkBtn(); dom.next.disabled = true;
new AutoPager(cfg, e => events.push(e)).start();
runAll();
a(dom.next.clicks === 0, 'disabled Next must not be clicked');
a(events.find(e => e.kind === 'stopped').reason.includes('last page'), 'last page');
console.log('last page            OK  (disabled Next respected)');

// 4b. aria-disabled
queue = []; now = 0; events = [];
dom.next = mkBtn(); dom.next.attrs['aria-disabled'] = 'true';
new AutoPager(cfg, e => events.push(e)).start();
runAll();
a(dom.next.clicks === 0, 'aria-disabled Next must not be clicked');
console.log('aria-disabled        OK');

// 5. missing Next button
queue = []; now = 0; dom.next = null; events = [];
new AutoPager(cfg, e => events.push(e)).start();
runAll();
a(events.find(e => e.kind === 'stopped').reason.includes('no Next button'), 'no next');
console.log('no Next button       OK  (stops rather than spinning)');

// 6. stop() is immediate and idempotent
queue = []; now = 0; dom.next = mkBtn(); events = [];
const p = new AutoPager(cfg, e => events.push(e));
p.start(); tick(); tick();
const before = dom.next.clicks;
p.stop(); p.stop();
runAll();
a(dom.next.clicks === before, 'no clicks after stop');
a(events.filter(e => e.kind === 'stopped').length === 1, 'one stop event only');
a(p.active === false, 'inactive after stop');
console.log('manual stop          OK  (immediate, idempotent)');

console.log('\nAUTOPAGE TESTS PASSED');
