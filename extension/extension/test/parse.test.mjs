import { execSync } from 'node:child_process';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import assert from 'node:assert/strict';

const dir = mkdtempSync(join(tmpdir(), 'lle-'));
const out = join(dir, 'c.mjs');
execSync(`npx esbuild src/lib/company.ts --bundle --format=esm --outfile=${out}`, {stdio:'pipe'});
const { parseCompanyPage, founderGate, pageIsReady } = await import(out);

// the Space Capital page, as rendered
const html = `<html><body>
  <h1 data-anonymize="company-name">Space Capital</h1>
  <span data-anonymize="industry">Venture Capital and Private Equity Principals</span>
  <span data-anonymize="location">New York, New York, United States</span>
  <div>15 employees</div>
  <div>$500,000 - $1M in revenue</div>
  <a href="https://spacecapital.com" target="_blank">Visit website</a>
  <div>Common searches
    <a href="#">All employees (15)</a>
    <a href="#">Decision makers (3)</a>
  </div>
  <div>Your personas <a href="#">CXO (2)</a> <a href="#">Director+ (3)</a></div>
  <div>Relationship explorer</div>
  <div class="card"><a href="/sales/lead/ACwAAA1"><span data-anonymize="person-name">Jane Doe</span>
    <span data-anonymize="job-title">Chief Technology Officer</span></a></div>
</body></html>`;

const { JSDOM } = await import('jsdom').catch(() => ({ JSDOM: null }));
if (!JSDOM) { console.log('SKIP: jsdom not installed'); process.exit(0); }
const doc = new JSDOM(html).window.document;

assert.equal(pageIsReady(doc), true, 'should detect a rendered page');
const f = parseCompanyPage(doc, 'https://www.linkedin.com/sales/company/27126726');
console.log('  companyId      ', f.companyId);
console.log('  name           ', f.name);
console.log('  headcount      ', f.headcount);
console.log('  revenue        ', f.revenue);
console.log('  employeesListed', f.employeesListed);
console.log('  decisionMakers ', f.decisionMakers);
console.log('  cxoCount       ', f.cxoCount);
console.log('  titles         ', f.titles);
assert.equal(f.headcount, 15);
assert.equal(f.employeesListed, 15);
assert.equal(f.decisionMakers, 3);
assert.equal(f.cxoCount, 2);
assert.equal(f.companyId, '27126726');
const g = founderGate(f);
console.log('  gate           ', g.keep, '|', g.reason);
assert.equal(g.keep, false, 'a CTO on the page must be a skip');
console.log('\nall parser assertions passed');
