import assert from 'node:assert/strict';
import { execSync } from 'node:child_process';
import { writeFileSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

// bundle the module so we can import the TS from plain node
const dir = mkdtempSync(join(tmpdir(), 'lle-'));
const out = join(dir, 'company.mjs');
execSync(`npx esbuild src/lib/company.ts --bundle --format=esm --outfile=${out}`,
         { stdio: 'pipe' });
const { founderGate } = await import(out);

const base = { companyId:'1', name:'X', headcount:12, revenue:null, industry:null,
  location:null, website:null, description:null, employeesListed:12,
  decisionMakers:3, cxoCount:2, titles:[], capturedAt:'' };

// a CTO is a hard skip
let g = founderGate({ ...base, titles:['Founder & CEO','Chief Technology Officer'] });
assert.equal(g.keep, false); assert.equal(g.hasCto, true);

// so is any engineer, even without a CTO
g = founderGate({ ...base, titles:['Founder','Senior Software Engineer'] });
assert.equal(g.keep, false); assert.equal(g.hasCto, false);
assert.match(g.reason, /engineering staff/);

// the keep case: people visible, none of them technical
g = founderGate({ ...base, titles:['Founder & CEO','Office Manager','Nurse Practitioner'] });
assert.equal(g.keep, true); assert.equal(g.confident, true);

// no titles rendered -> cannot judge, must not silently keep
g = founderGate({ ...base, titles:[] });
assert.equal(g.keep, null); assert.equal(g.confident, false);

// big company with a partial title list -> also undecidable
g = founderGate({ ...base, headcount:5000, titles:['Founder & CEO','Receptionist'] });
assert.equal(g.keep, null); assert.equal(g.confident, false);

// title variants that must all register as engineering
for (const t of ['CTO','VP of Engineering','Full Stack Developer','DevOps Lead',
                 'Head of Engineering','Machine Learning Engineer','Chief Product Officer']) {
  const r = founderGate({ ...base, titles:['Founder', t] });
  assert.equal(r.keep, false, `${t} should block`);
}

// and ones that must NOT (no false skips on clinical or ops roles)
for (const t of ['Chief Nursing Officer','Operations Manager','Chief Medical Officer',
                 'Practice Administrator','Chief Financial Officer']) {
  const r = founderGate({ ...base, titles:['Founder', t] });
  assert.equal(r.keep, true, `${t} should not block`);
}

console.log('company gate: all assertions passed');
