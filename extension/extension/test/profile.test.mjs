import assert from 'node:assert/strict';
import { execSync } from 'node:child_process';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const out = join(mkdtempSync(join(tmpdir(),'lle-')),'p.mjs');
execSync(`npx esbuild src/lib/profile.ts --bundle --format=esm --outfile=${out}`,{stdio:'pipe'});
const { rateProfile } = await import(out);

const base={profileId:'x',name:'A',headline:'',about:'',currentTitle:'',
            experience:[],education:[],domSample:'',capturedAt:''};

// technical founder -> low, must not be contacted as a build lead
for (const h of ['Co-Founder & CTO','Founding Engineer','Full Stack Developer',
                 'Data Scientist and founder','I built the platform myself',
                 'BS Computer Science, founder']) {
  const v=rateProfile({...base, headline:h, about:'Building things for years.'});
  assert.equal(v.technical, true, `${h} should read technical`);
  assert.ok(v.rating <= 3, `${h} should rate low`);
}

// non technical clinician founder -> the target profile
const md=rateProfile({...base, headline:'Founder & CEO, board certified MD',
  about:'I practiced medicine for twenty years before founding this company to fix intake. '.repeat(4)});
assert.equal(md.technical, false);
assert.ok(md.rating >= 8, `clinician founder should rate high, got ${md.rating}`);

// empty page -> null, never a silent guess
assert.equal(rateProfile({...base}).rating, null);

// a CMO is not an engineer
const cmo=rateProfile({...base, headline:'Chief Marketing Officer and co-founder',
                       about:'Twenty years in healthcare marketing and brand.'});
assert.equal(cmo.technical, false);

console.log('profile rating: all assertions passed');
