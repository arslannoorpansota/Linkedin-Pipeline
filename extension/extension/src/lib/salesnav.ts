import type { Lead, LeadSource, Position } from '../types';

function str(v: unknown): string | null {
  return typeof v === 'string' && v.length > 0 ? v : null;
}

function num(v: unknown): number | null {
  return typeof v === 'number' && Number.isFinite(v) ? v : null;
}

function obj(v: unknown): Record<string, unknown> {
  return v && typeof v === 'object' && !Array.isArray(v) ? v as Record<string, unknown> : {};
}

/** `urn:li:fs_salesProfile:(ACwAA...,NAME_SEARCH,TNTB)` — the three parts are
 *  what Sales Navigator's own profile endpoint is keyed by. */
export function parseSalesUrn(urn: string | null): {
  profileId: string | null; authType: string | null; authToken: string | null;
} {
  const m = urn?.match(/\(([^,]+),([^,]+),([^)]*)\)/);
  return m
    ? { profileId: m[1] ?? null, authType: m[2] ?? null, authToken: m[3] || null }
    : { profileId: null, authType: null, authToken: null };
}

function tenureYears(v: unknown): number | null {
  const t = obj(v);
  const years = num(t['numYears']);
  const months = num(t['numMonths']);
  if (years === null && months === null) return null;
  return Math.round(((years ?? 0) + (months ?? 0) / 12) * 10) / 10;
}

function startedOn(v: unknown): string | null {
  const s = obj(v);
  const year = num(s['year']);
  if (year === null) return null;
  const month = num(s['month']);
  return month === null ? String(year) : `${year}-${String(month).padStart(2, '0')}`;
}

function toPosition(raw: unknown): Position {
  const p = obj(raw);
  const company = obj(p['companyUrnResolutionResult']);
  return {
    title: str(p['title']),
    companyName: str(p['companyName']) ?? str(company['name']),
    companyUrn: str(p['companyUrn']) ?? str(company['entityUrn']),
    companyIndustry: str(company['industry']),
    companyLocation: str(company['location']),
    description: str(p['description']),
    current: p['current'] === true,
    startedOn: startedOn(p['startedOn']),
    yearsInRole: tenureYears(p['tenureAtPosition']),
    yearsAtCompany: tenureYears(p['tenureAtCompany']),
  };
}

function isLeadElement(v: unknown): boolean {
  const el = obj(v);
  return typeof el['entityUrn'] === 'string'
    && /salesProfile/i.test(el['entityUrn'] as string)
    && ('fullName' in el || 'firstName' in el);
}

function findElements(body: unknown, depth = 0): Record<string, unknown>[] {
  if (depth > 6 || !body || typeof body !== 'object') return [];
  if (Array.isArray(body)) {
    return body.some(isLeadElement)
      ? body.filter(isLeadElement).map(v => obj(v))
      : body.flatMap(v => findElements(v, depth + 1));
  }
  const container = obj(body);
  const direct = container['elements'];
  if (Array.isArray(direct) && direct.some(isLeadElement)) {
    return direct.filter(isLeadElement).map(v => obj(v));
  }
  return Object.values(container).flatMap(v => findElements(v, depth + 1));
}

export function parseLeads(body: unknown, source: LeadSource): {
  leads: Lead[]; unparsed: number;
} {
  const elements = findElements(body);
  const seen = new Set<string>();
  const leads: Lead[] = [];
  let unparsed = 0;

  for (const el of elements) {
    const salesUrn = str(el['entityUrn']);
    const { profileId, authType, authToken } = parseSalesUrn(salesUrn);
    const firstName = str(el['firstName']);
    const lastName = str(el['lastName']);
    const fullName = str(el['fullName'])
      ?? ([firstName, lastName].filter(Boolean).join(' ') || null);

    if (!profileId || !fullName) { unparsed++; continue; }
    if (seen.has(profileId)) continue;
    seen.add(profileId);

    const positions = Array.isArray(el['currentPositions'])
      ? (el['currentPositions'] as unknown[]).map(toPosition)
      : [];
    const primary = positions.find(p => p.current) ?? positions[0] ?? null;

    leads.push({
      salesUrn,
      profileId,
      authType,
      authToken,
      memberId: str(el['objectUrn'])?.match(/(\d+)$/)?.[1] ?? null,
      salesUrl: authToken
        ? `https://www.linkedin.com/sales/lead/${profileId},${authType},${authToken}`
        : null,
      firstName,
      lastName,
      fullName,
      headline: str(el['summary']),
      location: str(el['geoRegion']),
      degree: num(el['degree']),
      currentTitle: primary?.title ?? null,
      companyName: primary?.companyName ?? null,
      companyUrn: primary?.companyUrn ?? null,
      companyId: primary?.companyUrn?.match(/(\d+)$/)?.[1] ?? null,
      industry: primary?.companyIndustry ?? null,
      companyLocation: primary?.companyLocation ?? null,
      roleDescription: primary?.description ?? null,
      yearsInRole: primary?.yearsInRole ?? null,
      yearsAtCompany: primary?.yearsAtCompany ?? null,
      startedOn: primary?.startedOn ?? null,
      positions,
      stage: 'discovered',
      source,
      discoveredAt: new Date().toISOString(),
    });
  }

  return { leads, unparsed };
}
