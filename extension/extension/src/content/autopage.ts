export interface AutoPageConfig {
  maxPages: number;
  minDelay: number;
  maxDelay: number;
}

export type AutoPageEvent =
  | { kind: 'progress'; page: number; maxPages: number }
  | { kind: 'stopped'; reason: string; pages: number };

const NEXT_SELECTORS = [
  'button[aria-label="Next"]',
  'button[aria-label="Next page"]',
  '.artdeco-pagination__button--next',
  'button.search-results__pagination-next-button',
  '[data-test-pagination-page-btn="next"] button',
];

const BLOCK_MARKERS = [
  'commercial use limit',
  'you’ve reached the',
  'unusual activity',
  'verify your identity',
];

function findNext(): HTMLButtonElement | null {
  for (const selector of NEXT_SELECTORS) {
    const el = document.querySelector<HTMLButtonElement>(selector);
    if (el) return el;
  }
  return null;
}

function pageIsBlocked(): boolean {
  const text = document.body.innerText.slice(0, 4000).toLowerCase();
  return BLOCK_MARKERS.some(marker => text.includes(marker));
}

export class AutoPager {
  private running = false;
  private pages = 0;
  private timer: number | null = null;

  constructor(
    private readonly config: AutoPageConfig,
    private readonly emit: (event: AutoPageEvent) => void,
  ) {}

  get active(): boolean {
    return this.running;
  }

  start(): void {
    if (this.running) return;
    this.running = true;
    this.pages = 0;
    this.schedule();
  }

  stop(reason = 'stopped by you'): void {
    if (!this.running) return;
    this.running = false;
    if (this.timer !== null) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    this.emit({ kind: 'stopped', reason, pages: this.pages });
  }

  private schedule(): void {
    const { minDelay, maxDelay } = this.config;
    const wait = minDelay + Math.random() * Math.max(0, maxDelay - minDelay);
    this.timer = window.setTimeout(() => this.step(), wait);
  }

  private step(): void {
    if (!this.running) return;

    if (pageIsBlocked()) {
      this.stop('LinkedIn showed a limit or verification notice — stop for today');
      return;
    }
    if (this.pages >= this.config.maxPages) {
      this.stop(`reached the ${this.config.maxPages}-page limit`);
      return;
    }

    const next = findNext();
    if (!next) {
      this.stop('no Next button on this page');
      return;
    }
    if (next.disabled || next.getAttribute('aria-disabled') === 'true') {
      this.stop('reached the last page of results');
      return;
    }

    next.click();
    this.pages++;
    this.emit({ kind: 'progress', page: this.pages, maxPages: this.config.maxPages });
    this.schedule();
  }
}
