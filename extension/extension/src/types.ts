export type Stage = 'discovered' | 'selected' | 'enriched' | 'failed';

export interface LeadSource {
  kind: 'salesnav';
  searchUrl: string;
  page: number;
  capturedAt: string;
}

export interface Position {
  title: string | null;
  companyName: string | null;
  companyUrn: string | null;
  companyIndustry: string | null;
  companyLocation: string | null;
  description: string | null;
  current: boolean;
  startedOn: string | null;
  yearsInRole: number | null;
  yearsAtCompany: number | null;
}

export interface Lead {
  salesUrn: string | null;
  profileId: string;
  authType: string | null;
  authToken: string | null;
  memberId: string | null;
  salesUrl: string | null;
  firstName: string | null;
  lastName: string | null;
  fullName: string | null;
  headline: string | null;
  location: string | null;
  degree: number | null;
  currentTitle: string | null;
  companyName: string | null;
  companyUrn: string | null;
  companyId: string | null;
  industry: string | null;
  companyLocation: string | null;
  roleDescription: string | null;
  yearsInRole: number | null;
  yearsAtCompany: number | null;
  startedOn: string | null;
  positions: Position[];
  stage: Stage;
  source: LeadSource;
  discoveredAt: string;
}

export interface CaptureStats {
  pages: number;
  leads: number;
  lastCapturedAt: string | null;
  unparsed: number;
}

export interface Settings {
  captureRaw: boolean;
  autoRun: boolean;
}
