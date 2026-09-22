/** Parsers for the Sales Navigator company (account) page.
 *
 *  The account page renders the three things the founder gate needs and the
 *  lead-search API never returns: how many people work there, how many sit in
 *  the C suite, and — once the CXO persona is expanded — what those people do.
 *  We read the rendered DOM rather than the API because /sales-api/salesApiCompanies
 *  answers 403 SALES_SEAT_REQUIRED to anything that is not the page itself.
 */

export interface CompanyFacts {
  companyId: string | null;
  name: string | null;
  headcount: number | null;
  revenue: string | null;
  industry: string | null;
  location: string | null;
  website: string | null;
  description: string | null;
  /** Counts straight off the "Common searches" row. */
  employeesListed: number | null;
  decisionMakers: number | null;
  cxoCount: number | null;
  /** Every job title we could see anywhere on the page. */
  titles: string[];
  /** Trimmed HTML of the people areas, so we can see what actually rendered. */
  domSample: string;
  capturedAt: string;
}

const num = (s: string | null | undefined): number | null => {
  if (!s) return null;
  const m = s.replace(/,/g, '').match(/\d+/);
  return m ? Number(m[0]) : null;
};

const clean = (s: string | null | undefined): string | null => {
  const t = (s ?? '').replace(/\s+/g, ' ').trim();
  return t.length ? t : null;
};

/** "All employees (15)" -> 15, "CXO (2)" -> 2 */
function labelledCount(text: string, label: RegExp): number | null {
  const m = text.match(new RegExp(label.source + String.raw`[^(]*\((\d[\d,]*)\)`, 'i'));
  return m ? num(m[1]) : null;
}

/** The same counts, read off the links that carry them. */
function countFromLinks(doc: Document, label: RegExp): number | null {
  for (const a of doc.querySelectorAll('a, button')) {
    const t = clean(a.textContent) ?? '';
    if (label.test(t)) {
      const n = t.match(/\((\d[\d,]*)\)/);
      if (n) return num(n[1]);
    }
  }
  return null;
}

/** True once the account page has painted the parts we read. */
export function pageIsReady(doc: Document): boolean {
  const t = doc.body?.textContent ?? '';
  return /All employees\s*\(/i.test(t)
      || /\d[\d,]*\s+employees?\b/i.test(t)
      || /Relationship explorer/i.test(t);
}

export function companyIdFromUrl(url: string): string | null {
  return url.match(/\/sales\/company\/(\d+)/)?.[1] ?? null;
}

/** Job titles carry the signal; we only ever ask whether an engineer exists. */
export function collectTitles(root: ParentNode): string[] {
  const out = new Set<string>();
  const sel = [
    '[data-anonymize="job-title"]',
    '[data-anonymize="headline"]',
    '.artdeco-entity-lockup__subtitle',
    '._subtitle_a3bcnb',
  ].join(',');
  for (const el of root.querySelectorAll(sel)) {
    const t = clean(el.textContent);
    if (t && t.length < 160) out.add(t);
  }
  return [...out];
}

/** A slice of the page around anything that looks like a person, capped so the
 *  store stays small. Diagnostic only. */
function sampleDom(doc: Document): string {
  const bits: string[] = [];
  const marks = ['employee', 'people', 'decision', 'cxo', 'persona', 'relationship'];
  for (const el of doc.querySelectorAll('section, div[class*="card"], a[href*="/sales/lead/"]')) {
    const t = (el.textContent ?? '').toLowerCase();
    if (marks.some(m => t.includes(m)) && el.innerHTML.length < 6000) {
      bits.push(el.outerHTML.slice(0, 3000));
      if (bits.length >= 4) break;
    }
  }
  return bits.join('\n<!-- ---- -->\n').slice(0, 12000);
}

export function parseCompanyPage(doc: Document, url: string): CompanyFacts {
  const text = (doc.body?.innerText ?? doc.body?.textContent ?? '').slice(0, 20000);

  const pick = (sel: string): string | null =>
    clean(doc.querySelector(sel)?.textContent);

  // Headcount appears as "15 employees" next to a people icon, and again in
  // "All employees (15)". Prefer the explicit line, fall back to the link.
  const headcount =
    num(text.match(/([\d,]+)\s+employees?\b/i)?.[1]) ??
    countFromLinks(doc, /All employees/i) ??
    labelledCount(text, /All employees/);

  const website = doc.querySelector<HTMLAnchorElement>(
    'a[data-control-name="visit_company_website"], a[href^="http"][target="_blank"]',
  );

  return {
    companyId: companyIdFromUrl(url),
    name: pick('[data-anonymize="company-name"]') ?? pick('h1'),
    headcount,
    revenue: clean(text.match(/(\$[\d.,]+\s*[KMB]?\s*-\s*\$[\d.,]+\s*[KMB]?\s+in revenue)/i)?.[1]),
    industry: pick('[data-anonymize="industry"]'),
    location: pick('[data-anonymize="location"]'),
    website: website?.href ?? null,
    description: clean(doc.querySelector('[data-anonymize="company-blurb"], .about__description')?.textContent),
    employeesListed: countFromLinks(doc, /All employees/i) ?? labelledCount(text, /All employees/),
    decisionMakers: countFromLinks(doc, /Decision makers/i) ?? labelledCount(text, /Decision makers/),
    cxoCount: countFromLinks(doc, /^CXO/i) ?? labelledCount(text, /CXO/),
    titles: collectTitles(doc),
    domSample: sampleDom(doc),
    capturedAt: new Date().toISOString(),
  };
}

/* ---- the founder gate ------------------------------------------------ */

/** Titles that mean the company already owns its engineering. */
const ENGINEER = new RegExp([
  String.raw`\bcto\b`, 'chief technology officer', 'chief technical officer',
  'chief information officer', 'chief product officer', 'chief architect',
  'chief digital officer', 'chief innovation officer',
  'vp of engineering', 'vp engineering', 'head of engineering',
  'engineering manager', 'director of engineering', 'engineering lead',
  String.raw`\bengineer\b`, 'engineering', 'developer', String.raw`\bdev\b`,
  'programmer', 'architect', 'devops', 'full.?stack', 'backend', 'back.end',
  'frontend', 'front.end', 'software', 'data scientist', 'machine learning',
  String.raw`\bml\b`, 'technical lead', 'tech lead', 'principal engineer',
].join('|'), 'i');

/** A CTO or equivalent specifically — the hard skip. */
const CTO = new RegExp([
  String.raw`\bcto\b`, 'chief technology officer', 'chief technical officer',
  'chief information officer', 'chief product officer', 'chief architect',
  'chief digital officer', 'vp of engineering', 'vp engineering',
  'head of engineering', 'director of engineering',
].join('|'), 'i');

export interface GateResult {
  /** null when the page did not give us enough to judge. */
  keep: boolean | null;
  reason: string;
  hasCto: boolean;
  engineerTitles: string[];
  confident: boolean;
}

/**
 * The only question: does this company have a CTO or any engineer?
 * No -> they have to buy the build. Yes -> they already own it, skip.
 */
export function founderGate(facts: CompanyFacts): GateResult {
  const engineers = facts.titles.filter(t => ENGINEER.test(t));
  const ctos = facts.titles.filter(t => CTO.test(t));

  if (ctos.length) {
    return {
      keep: false, hasCto: true, engineerTitles: ctos, confident: true,
      reason: `CTO or engineering leader on the account: ${ctos.slice(0, 3).join('; ')}`,
    };
  }
  if (engineers.length) {
    return {
      keep: false, hasCto: false, engineerTitles: engineers, confident: true,
      reason: `${engineers.length} engineering staff on the account: ${engineers.slice(0, 3).join('; ')}`,
    };
  }

  // No engineer seen. That is only meaningful if we actually saw the staff.
  const sawPeople = facts.titles.length > 0;
  const small = facts.headcount !== null && facts.headcount <= 200;

  if (!sawPeople) {
    return {
      keep: null, hasCto: false, engineerTitles: [], confident: false,
      reason: 'no job titles rendered on the page — cannot judge, needs a manual look',
    };
  }
  if (!small && facts.headcount !== null) {
    return {
      keep: null, hasCto: false, engineerTitles: [], confident: false,
      reason: `no engineer among ${facts.titles.length} visible titles, but headcount `
            + `${facts.headcount} is too large to trust a partial list`,
    };
  }
  return {
    keep: true, hasCto: false, engineerTitles: [], confident: true,
    reason: `no CTO and no engineer among ${facts.titles.length} visible titles`
          + (facts.headcount !== null ? ` at ${facts.headcount} staff` : '')
          + ' — they cannot build it in house',
  };
}
