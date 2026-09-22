import type { Lead } from '../types';

export const FILTER_COLUMNS = [
  'row',
  'profileId',
  'salesUrn',
  'memberId',
  'salesUrl',
  'fullName',
  'headline',
  'currentTitle',
  'companyName',
  'industry',
  'location',
  'companyLocation',
  'degree',
  'yearsInRole',
  'yearsAtCompany',
  'startedOn',
  'roleDescription',
] as const;

function cell(value: unknown): string {
  if (value === null || value === undefined) return '""';
  return `"${String(value).replace(/"/g, '""')}"`;
}

export function toCsv(leads: Lead[]): string {
  const header = FILTER_COLUMNS.map(cell).join(',');
  const rows = leads.map((lead, i) => {
    const record: Record<string, unknown> = { ...lead, row: i + 1 };
    return FILTER_COLUMNS.map(c => cell(record[c])).join(',');
  });
  return '﻿' + [header, ...rows].join('\r\n') + '\r\n';
}

export function toJson(leads: Lead[]): string {
  return JSON.stringify({
    schemaVersion: 1,
    exportedAt: new Date().toISOString(),
    leadCount: leads.length,
    leads,
  }, null, 2);
}

export function download(filename: string, content: string, mime: string): void {
  const blob = new Blob([content], { type: `${mime};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
