# LinkedIn Lead Extractor

Three-stage lead pipeline: capture in the browser, filter with Claude Code,
enrich with Python.

```
Sales Navigator search
        │
        ▼
  [1] extension  ──►  leads.csv  +  leads.json
        │
        ▼
  [2] Claude Code  ──►  leads_filtered.csv      (see FILTER_PROMPT.md)
        │
        ▼
  [3] enrich.py  ──►  leads.json, companies.json, leads_flat.json
        │
        ▼
  [4] Claude Code  ──►  shortlist.json + drafted notes  (see OUTREACH_PROMPT.md)
        │
        ▼
  [5] outreach.py  ──►  outreach.html   — you send them by hand
```

Two filter passes, on purpose. Pass 1 (stage 2) is a **budget** decision — it
exists to stop you spending 800 profile fetches. Pass 2 (stage 4) is a
**quality** decision, and it's free, because by then you have the full profile,
the company, and what they've been posting about.

Stage 1 is cheap (one request per page of results). Stage 3 is expensive
(one profile fetch per lead), which is why the filter sits between them.

## How to use it

One command, run as often as you like. It works out what's been done and tells
you the single next thing:

```bash
./run.sh
```

That's the whole interface. It moves files out of Downloads, checks the filter,
looks up profiles, builds your worksheet, and stops with plain instructions at
the two points where it needs you.

```
  1. Collect      extension     press Start collecting, then Download leads
  2. Filter       Claude Code   narrow to your ideal customer
  3. Look up      ./run.sh      profiles + companies  (the slow part)
  4. Shortlist    Claude Code   pick the best, draft a note each
  5. Send         you           worksheet opens, you click through
```

Steps 2 and 4 are the judgement calls, so they're yours. Step 5 is manual on
purpose — automated connection notes are the fastest way to lose an account.

### First time

```bash
cd extension && npm install && npm run build
```

Load it in Chrome: `chrome://extensions` → Developer mode → **Load unpacked** →
pick `extension/dist`.

```bash
cp enrich/.env.example enrich/.env    # then paste in your LinkedIn cookies
pip install -r enrich/requirements.txt
```

### Before your first full run

```bash
cd enrich && python3 enrich.py ../data/leads_filtered.csv --limit 3 --dump-raw -o ../data/out
```

Three leads only, saving the raw responses. Step 3 talks to Sales Navigator's
API and has not yet been verified against live responses — check the output
looks right before running it against a full list.

## 1. Extension — capture

```bash
cd extension
npm install
npm run build          # -> extension/dist
npm test               # parser tests
```

Load it: `chrome://extensions` → Developer mode → **Load unpacked** →
select `extension/dist`.

Click the toolbar icon to open the dashboard, then open a Sales Navigator
search in another tab. Captures happen automatically — the dashboard tab must
stay open. Then **Export filter CSV**.

### Auto-paging

**Start auto-paging** clicks through result pages for you, 4-9s apart by
default, up to a page limit you set. It stops on its own when:

- it hits your page limit (default 20 ≈ 500 leads),
- the Next button is missing, disabled, or you're on the last page,
- LinkedIn shows a commercial-use limit or verification notice,
- no results are captured for 45s — meaning it's clicking but nothing is
  coming back,
- you navigate away, or press **Stop**.

Start with the default 20 pages. This is the one part of the pipeline that
automates clicks rather than just watching traffic, so it carries more risk
than the rest — raise the limit only once you've seen a few clean runs.

The CSV carries `salesUrn`, `memberId` and `publicIdentifier`. Those are the
keys stage 3 matches on, so keep at least one of them in the filtered file.

## 2. Claude Code — filter

See [FILTER_PROMPT.md](FILTER_PROMPT.md). Fill in your ICP and hand it the CSV.

The prompt deliberately has Claude write decisions to a separate file and copy
rows with a script, rather than regenerating the CSV by hand. That keeps the
lead data byte-identical and gives you a `decisions.json` you can audit.

Then confirm nothing vanished:

```bash
python3 enrich/check_filter.py leads.csv leads_filtered.csv -d decisions.json
```

It fails loudly on rows with no decision, identifiers the filter rewrote,
duplicates, and a keep-count that disagrees with the filtered file.

## 3. Python — enrich

```bash
cd enrich
pip install -r requirements.txt

cp .env.example .env        # then fill in LI_AT and LI_JSESSIONID
python3 enrich.py ../leads_filtered.csv --leads ../leads.json -o out

./test/run.sh               # tests
```

Cookies come from `.env` by default, so they stay out of `~/.bash_history`.
Real environment variables still take precedence.

### Pass `--leads`

`--leads leads.json` points at the **stage-1 export**. Lead data is then taken
from there and the CSV is used only to decide *which* rows to process.

Without it, stage 3 reads data straight out of the filtered CSV — so if the
filter step dropped a column, `seniority`, `yearsInRole` and `companyStaffRange`
quietly disappear from your final output. Rows with no match in the export fall
back to CSV values and are reported.

Output in `out/`:

| file | contents |
|---|---|
| `leads.json` | one record per lead, keyed by identifier, with `profile` |
| `companies.json` | one record per company, keyed by `universalName` |
| `leads_flat.json` | denormalised join of the two, for CRM import |
| `budget.json` | requests used per UTC day |

Both `.env` and `out/` hold sensitive data — `.gitignore` covers them.

Companies are stored separately and fetched **once**. On a list where many
leads share employers this is most of the saving — watch the `cache hits`
count in the summary.

### Resuming

Re-running skips already-enriched leads and cached companies. State is flushed
after every lead, so a crash or a `Ctrl-C` loses nothing.

Leads that failed *permanently* — a profile that no longer exists — are also
skipped, so they don't burn budget on every run. Transient failures do retry.
To force a retry of everything that failed:

```bash
python3 enrich.py leads_filtered.csv --retry-failed
```

### Refreshing stale data

```bash
python3 enrich.py ../data/leads_filtered.csv --refresh-older-than 90
```

People change jobs. Without this, a record enriched in March stays wrong
forever. Leads enriched more recently than the window are still skipped.

### Interrupted part-way through a lead

If a run is blocked *after* the profile fetch but *before* the company or
activity fetch, the profile is banked with the outstanding work recorded
(`"incomplete": ["company"]`). The next run picks the record up, reuses the
profile it already paid for, and only fetches what's missing — the summary
line reports `profiles reused`.

### Skipping people you've already contacted

```bash
python3 enrich.py leads_filtered.csv --suppress contacted.csv --suppress exclude.txt
```

A `.csv` is matched on any identifier column; a `.txt` is one identifier or
profile URL per line, `#` for comments. Repeatable.

### Recent posts

```bash
python3 enrich.py leads_filtered.csv --activity
```

Adds each lead's recent posts to their record — the strongest personalisation
hook available, and what [OUTREACH_PROMPT.md](OUTREACH_PROMPT.md) writes notes
from. Costs **one extra request per lead**, so it roughly doubles the run.

Which endpoint LinkedIn serves for this changes over time, so three known
shapes are tried until one answers; the winner is reused for the rest of the
run. If none answer three times running it disables itself and says so on
stderr, rather than quietly costing a request per lead (see *Schema drift*).

### Pacing

```bash
python3 enrich.py leads_filtered.csv --min-delay 6 --max-delay 14 --max-fetches 200
python3 enrich.py leads_filtered.csv --limit 10        # trial run first
```

Two ceilings apply:

- `--max-fetches` (default 400) caps a single run.
- `--daily-cap` (default 500) caps a UTC day and **persists in `out/budget.json`**,
  so re-running the command doesn't hand you a fresh allowance.

Default jitter is 4-9s. The client halts on 429, 401/403, and challenge
redirects rather than retrying — if it stops, **stop too**. Re-run later;
progress is saved.

## 4. Claude Code — shortlist and draft notes

See [OUTREACH_PROMPT.md](OUTREACH_PROMPT.md). Produces `data/shortlist.json`
with a reason and a drafted note per lead.

## 5. Worksheet — send by hand

```bash
cd enrich
python3 outreach.py ../data/shortlist.json -e ../data/out/leads_flat.json \
  -o ../data/outreach.html
```

Open `data/outreach.html` in a browser. One card per lead: their profile link,
why they were shortlisted, the drafted note with a copy button, their recent
posts for context, and a character count that turns red past LinkedIn's
300-character connection-note limit.

**Nothing is sent automatically, by design.** Automated connection notes are
the fastest way to get an account restricted, and LinkedIn caps you at roughly
100-200 requests a week regardless. You keep the personalisation and drop the
part that costs you the account.

Tick each lead off as you go — progress is saved in the browser. When you're
done, **Export contacted.csv** and feed it back:

```bash
python3 enrich.py ../data/leads_filtered.csv --suppress ../data/contacted.csv
```

That closes the loop: nobody gets contacted twice.

## Notes

- Automated collection is against LinkedIn's User Agreement, and the
  consequence lands on the account running it. Keep volumes low.
- A Python client carries an exported cookie and doesn't match a browser
  fingerprint, so it draws attention sooner than the in-browser path. If you
  start getting challenged, the fix is to move stage 3 into the extension.
- If leads are EU residents, GDPR applies to what you store — `out/` is
  personal data.

## Schema drift

The Sales Navigator and Voyager payload shapes change without notice. Both
parsers walk the response tree for recognisable records instead of indexing
fixed paths, and skip what they don't recognise.

If the dashboard reports captures with **0 leads matched**, the shape has
moved. Leave *Keep raw payloads* on, hit **Export raw payloads**, and the
saved JSON shows the current shape — `extension/test/salesnav.test.mjs` is
where to encode the fix.
# extension
