/** Parser for a Sales Navigator lead profile page.
 *
 *  The account page hides its people behind lazily rendered sections, which is
 *  why the company scrape could never answer "is there a CTO". A profile page
 *  is different: the person's own headline, about text and experience are in
 *  the main body, so a background tab does render them.
 *
 *  We only ask one thing of it: can this person build the software themselves?
 */

export interface ProfileFacts {
  profileId: string | null;
  name: string | null;
  headline: string | null;
  about: string | null;
  currentTitle: string | null;
  /** Every past and present role title we can see. */
  experience: string[];
  education: string[];
  /** Diagnostic, so selectors can be checked against the real page. */
  domSample: string;
  capturedAt: string;
}

const clean = (s: string | null | undefined): string | null => {
  const t = (s ?? '').replace(/\s+/g, ' ').trim();
  return t.length ? t : null;
};

export function profileIdFromUrl(url: string): string | null {
  return url.match(/\/sales\/lead\/([^,/?]+)/)?.[1] ?? null;
}

/** Ready once the person's own text has painted. */
export function profileIsReady(doc: Document): boolean {
  const t = doc.body?.textContent ?? '';
  return /About|Experience|Current role|Highlights/i.test(t) && t.length > 1500;
}

function textList(doc: Document, selectors: string[], cap = 40): string[] {
  const out = new Set<string>();
  for (const el of doc.querySelectorAll(selectors.join(','))) {
    const t = clean(el.textContent);
    if (t && t.length < 200) out.add(t);
    if (out.size >= cap) break;
  }
  return [...out];
}

function sampleDom(doc: Document): string {
  const bits: string[] = [];
  for (const el of doc.querySelectorAll('section, article, div[class*="profile"]')) {
    const t = (el.textContent ?? '').toLowerCase();
    if (/experience|about|education|current/.test(t) && el.innerHTML.length < 6000) {
      bits.push(el.outerHTML.slice(0, 2500));
      if (bits.length >= 4) break;
    }
  }
  return bits.join('\n<!-- ---- -->\n').slice(0, 12000);
}

export function parseProfilePage(doc: Document, url: string): ProfileFacts {
  const pick = (sel: string) => clean(doc.querySelector(sel)?.textContent);
  return {
    profileId: profileIdFromUrl(url),
    name: pick('[data-anonymize="person-name"]') ?? pick('h1'),
    headline: pick('[data-anonymize="headline"]'),
    about: pick('[data-anonymize="person-blurb"], .about__summary-text'),
    currentTitle: pick('[data-anonymize="job-title"]'),
    experience: textList(doc, ['[data-anonymize="job-title"]', '.experience__title',
                               'h3[class*="title"]']),
    education: textList(doc, ['[data-anonymize="education"]', '.education__school',
                              '[data-anonymize="degree"]'], 10),
    domSample: sampleDom(doc),
    capturedAt: new Date().toISOString(),
  };
}

/* ---- can this person build it themselves? --------------------------- */

/** Titles or claims that mean the founder can ship software without us. */
const TECHNICAL = new RegExp([
  String.raw`\bcto\b`, 'chief technology officer', 'chief technical officer',
  'chief information officer', 'chief product officer', 'chief architect',
  'vp of engineering', 'head of engineering', 'director of engineering',
  String.raw`\bsoftware engineer\b`, 'senior engineer', 'founding engineer',
  'full.?stack', 'backend', 'front.?end', String.raw`\bdeveloper\b`,
  String.raw`\bprogrammer\b`, 'data scientist', 'machine learning',
  'devops', String.raw`\bsre\b`, 'computer science', String.raw`\bcs degree\b`,
  'i built', 'i coded', 'i developed', 'technologist', 'solutions architect',
].join('|'), 'i');

/** Non technical backgrounds: the profile we actually want. */
const NON_TECHNICAL = new RegExp([
  '\\bmd\\b', 'physician', 'surgeon', 'nurse', 'rn\\b', 'psychologist',
  'therapist', 'counselor', 'counsellor', 'clinician', 'dentist', 'pharmacist',
  'dietitian', 'physical therapist', 'social worker', 'mba\\b', 'sales',
  'marketing', 'operations', 'finance', 'attorney', 'educator', 'teacher',
].join('|'), 'i');

export interface ProfileVerdict {
  /** 1-10; null when the page gave us nothing to judge. */
  rating: number | null;
  reason: string;
  technical: boolean;
  evidence: string[];
}

export function rateProfile(p: ProfileFacts): ProfileVerdict {
  const blob = [p.headline, p.about, p.currentTitle, ...p.experience, ...p.education]
    .filter(Boolean).join(' ');

  if (blob.trim().length < 40) {
    return { rating: null, technical: false, evidence: [],
             reason: 'profile did not render enough text to judge' };
  }

  const tech = blob.match(TECHNICAL);
  const nonTech = blob.match(NON_TECHNICAL);

  if (tech) {
    return {
      rating: 3, technical: true, evidence: [tech[0]],
      reason: `technical background on the profile (${tech[0]}), so they can build in house`,
    };
  }

  // Non technical founder with no engineering history: the target.
  let rating = 7;
  const ev: string[] = [];
  if (nonTech) { rating += 1; ev.push(nonTech[0]); }
  if (p.about && p.about.length > 200) { rating += 1; ev.push('detailed about section'); }
  rating = Math.min(10, rating);

  return {
    rating, technical: false, evidence: ev,
    reason: nonTech
      ? `non technical founder (${nonTech[0]}), no engineering background on the profile`
      : 'no engineering background visible on the profile',
  };
}
