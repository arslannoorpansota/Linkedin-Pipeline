import * as esbuild from 'esbuild';
import { readFileSync } from 'node:fs';

const r = await esbuild.build({
  entryPoints: [new URL('../src/lib/salesnav.ts', import.meta.url).pathname],
  bundle: true, format: 'esm', write: false, target: 'node20',
});
const mod = await import('data:text/javascript;base64,' +
  Buffer.from(r.outputFiles[0].text).toString('base64'));

const fixture = JSON.parse(readFileSync(
  new URL('./fixtures/leadsearch.json', import.meta.url), 'utf8'));
const src = { kind: 'salesnav', searchUrl: 'x', page: 1, capturedAt: new Date().toISOString() };
const a = (c, m) => { if (!c) { console.error('FAIL: ' + m); process.exit(1); } };

const { leads, unparsed } = mod.parseLeads(fixture, src);
a(leads.length === 6, `expected 6 leads, got ${leads.length}`);
a(unparsed === 0, `expected 0 unparsed, got ${unparsed}`);
console.log(`real payload         OK  -> ${leads.length} leads, ${unparsed} unparsed`);

const required = ['profileId', 'fullName', 'currentTitle', 'companyName', 'location'];
for (const f of required) {
  const n = leads.filter(l => l[f] !== null && l[f] !== '').length;
  a(n === leads.length, `${f} only filled ${n}/${leads.length}`);
}
console.log('core fields          OK  -> profileId, name, title, company, location all 100%');

const signals = ['industry', 'yearsInRole', 'yearsAtCompany', 'startedOn', 'companyUrn'];
for (const f of signals) {
  const n = leads.filter(l => l[f] !== null).length;
  a(n >= leads.length - 1, `${f} only filled ${n}/${leads.length}`);
  console.log(`  ${f.padEnd(16)} ${n}/${leads.length}`);
}
console.log('qualifying signals   OK  -> recovered from currentPositions');

const u = mod.parseSalesUrn('urn:li:fs_salesProfile:(ACwAAAU0K_ABe1k,NAME_SEARCH,TNTB)');
a(u.profileId === 'ACwAAAU0K_ABe1k' && u.authType === 'NAME_SEARCH' && u.authToken === 'TNTB',
  JSON.stringify(u));
console.log('salesUrn parse       OK  ->', u.profileId, u.authType, u.authToken);

const withUrl = leads.filter(l => l.salesUrl?.startsWith('https://www.linkedin.com/sales/lead/'));
a(withUrl.length === leads.length, `salesUrl missing on ${leads.length - withUrl.length}`);
console.log('sales profile links  OK  -> all', leads.length, 'resolvable');

a(leads.every(l => l.memberId && /^\d+$/.test(l.memberId)), 'numeric memberId');
console.log('memberId             OK  -> numeric, from objectUrn');

const dup = mod.parseLeads({ elements: [...fixture.elements, ...fixture.elements] }, src);
a(dup.leads.length === 6, `dedupe failed: ${dup.leads.length}`);
console.log('dedupe               OK  -> 12 elements -> 6 unique');

a(mod.parseLeads({ elements: [] }, src).leads.length === 0, 'empty');
a(mod.parseLeads(null, src).leads.length === 0, 'null body');
console.log('empty/null input     OK  -> no throw');

console.log('\nSALESNAV TESTS PASSED (against real captured payload)');
