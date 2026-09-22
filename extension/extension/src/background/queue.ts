/** A queue that drives one tab through a list of Sales Navigator pages.
 *
 *  The search autopager lives in the content script because it only ever
 *  clicks Next on the page it is already on. This queue navigates, so it has
 *  to outlive the page: every navigation tears the content script down.
 *  It therefore runs in the service worker and keeps its state in
 *  chrome.storage.local, which survives the worker being suspended.
 */

export interface QueueItem {
  row: string;
  company: string;
  companyUrl: string;
  profileUrl: string;
}

export interface QueueState {
  running: boolean;
  items: QueueItem[];
  index: number;
  /** Wall-clock ms to wait between navigations, randomised per step. */
  minDelay: number;
  maxDelay: number;
  startedAt: string | null;
  stoppedReason: string | null;
  visited: string[];
  failed: { url: string; reason: string }[];
}

const KEY = 'visitQueue';

const EMPTY: QueueState = {
  running: false, items: [], index: 0,
  minDelay: 6000, maxDelay: 12000,
  startedAt: null, stoppedReason: null, visited: [], failed: [],
};

export async function getState(): Promise<QueueState> {
  const got = await chrome.storage.local.get(KEY);
  return { ...EMPTY, ...(got[KEY] as Partial<QueueState> | undefined) };
}

export async function setState(patch: Partial<QueueState>): Promise<QueueState> {
  const next = { ...(await getState()), ...patch };
  await chrome.storage.local.set({ [KEY]: next });
  return next;
}

export async function reset(): Promise<void> {
  await chrome.storage.local.set({ [KEY]: EMPTY });
}

/** LinkedIn tells us to stop in prose; believe it immediately. */
export const BLOCK_MARKERS = [
  'commercial use limit',
  'you’ve reached the',
  "you've reached the",
  'unusual activity',
  'verify your identity',
  'please verify',
  'temporarily restricted',
];

export function jitter(min: number, max: number): number {
  return Math.round(min + Math.random() * Math.max(0, max - min));
}
