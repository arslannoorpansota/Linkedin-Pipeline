# Cadence & Channel Routing — enforced rules

> **This file is the single source of truth for: which channel a lead gets, when
> the next touch is due, and when a lead is dead.** It overrides any older
> channel/follow-up guidance in `SALES_NAV_PLAYBOOK.md`, `FOLLOW_UP.md`, or memory.
>
> Written 2026-08-06 after a full read of the live pipeline (1,139 rows). Every
> number below is measured from that sheet, not assumed.

---

## 1. What the data forced these rules

Reply rate by channel, all rows with an outreach channel set (channel labels
normalised — the sheet had 12 spellings for 4 real channels):

| Channel | Sent | Replied | Reply rate |
|---|---|---|---|
| Both (DM + email) | 11 | 4 | **36.4%** |
| Connection note | 44 | 12 | **27.3%** |
| LinkedIn DM | 102 | 24 | **23.5%** |
| InMail | 38 | 2 | **5.3%** |

**InMail converts at roughly one-fifth of a free connection note, and it costs a
credit.** The old rule ("rating 7+ → InMail") routed our *highest-rated* leads
into our *worst* channel: 38 of the best leads went out by InMail and 36 of them
never replied. Gerry Blass, Pat Zingarella, and Alan Fenn all declined via InMail.

**InMail is not a reward for a high rating. It is a fallback for having no other
route in.**

Also measured, and the reason §3 exists:
- **124 contacted leads had no reply and no touch in >5 days.** Oldest was 43 days
  (Ryan Brucker/GeoWealth, Jon Darbyshire/SmartSuite, Harald Collet/Alkymi, and 14
  others all sat 42–43 days at `Connection Requested`).
- **53 leads had Follow-up 1 and nothing after it** — 48 of them never got a FU2.
- **381 rows sat at status `New`** — research finished, no decision attached.

---

## 2. Channel routing — by rating

| Profile rating | Default channel | InMail allowed? |
|---|---|---|
| **7+** | **Connection note** (≤200 chars, lead channel) → DM the proof point on accept, **and draft an InMail alongside it** | InMail drafted proactively for 7+ (Arslan 2026-08-10) — send the note first; the InMail is a ready backup |
| **6** | **Connection note** (≤200 chars) | Only via §2a |
| **<6** | **Skip** — set status `Skip` the same day, do not leave at `New` | Never |

A high rating buys **more personalisation effort and a faster follow-up**. The
connection note stays the lead channel at every rating (it out-converts InMail
5x). **New (Arslan 2026-08-10): for a 7+ lead, also draft an InMail so it is
ready** — send the free connection note first, keep the InMail as a prepared
fallback if no free route lands. Do not lead with the InMail.

### 2a. When InMail is actually correct

Only when *every* free route is closed. Check in this order and stop at the first hit:

1. 1st-degree → **direct DM** (free)
2. Mutual connection → **ask for the intro** (free, best converting path we have)
3. **"Open Profile" badge → InMail is free** — use it, costs 0 credits
4. Shared LinkedIn Group → **group message** (free)
5. Verified work email → **cold email** from `arslan@` (free, uncapped)
6. Connection note sent and ignored **7+ days**, still 7+ fit, and *none* of 1–5 apply → **InMail** (1 credit)

If a lead reaches step 6 with a rating of 6, it is a park, not an InMail.

---

## 3. The 4-touch cadence — enforced dates

**Cadence is Profile-7+ only (Arslan 2026-08-11).** The enforced T2/T3 chase runs
only for leads rated **Profile 7 or above** (our InMail leads). A **P6** keep gets its
T1 connection note but is *not* put on the enforced cadence — no T2/T3 chase, its
cadence columns stay blank. **Carve-out:** any lead that has **replied or accepted**
stays on the cadence radar regardless of rating, so a warm/in-conversation lead
below 7 (e.g. an unrated referral who accepted) still shows `REPLIED`/its stage and
does not fall off. The live `Cadence Stage` column enforces this
(`show = OR(profile>=7, replied, accepted)`).

Every contacted **P7+** lead is on this cadence until it replies, parks, or dies. Gaps are
capped at 5 days early on because that is where we were leaking: follow-ups
stopped happening after day 5.

| Touch | Due | Channel | Purpose |
|---|---|---|---|
| **T1** | Day 0 | Connection note (or DM if 1st-degree) | Hook only — what we noticed about them. No pitch. |
| **T2** | Day +3, or **immediately on accept** | LinkedIn DM | One concrete proof point, then the soft ask |
| **T3** | Day +8 | DM, or email if we have one | A **new angle** — a teardown observation or relevant case. Never "just bumping this" |
| **T4** | Day +15 | Email (InMail only per §2a) | Close the loop: "I'll stop here unless the timing changes" |
| **Park** | Day +45 | — | Status → `On Hold`, into the re-engagement pool |

Rules:
- **`Next Action Date` is never blank while a lead is on cadence.** Set it to
  last-touch + the gap for the next touch, at the moment you log the touch.
- **A reply ends the cadence.** Hand off to `FOLLOW_UP.md` — that is a
  conversation now, not a sequence.
- **Vary structure, not just the first line** across T2–T4 (`CLAUDE.md` §9).
- **T4 is the last touch.** No touch 5. Park it and move on.

### Sent dates vs planned dates (do not mix these up)

- **`Follow-up N Date` = the date that follow-up was actually SENT.** Past dates only.
- **`Next Action Date` = when the next touch is DUE.** This is where a planned date goes.

Putting a planned date in `Follow-up 1 Date` makes the lead look like it has an
extra completed touch, which pushes it to the wrong cadence stage and drives
`Days Since Last Touch` negative. It happened on 16 rows (planned FU1 of
2026-08-07 / 08-13 while the note had only just gone out). The formulas now ignore
future dates and show `SCHEDULED <date>` instead, but log the date in the right
column. `--fix-planned-fu` cleans up existing cases.

### Overdue definition (what the sheet flags red)

A lead is **overdue** when it has no reply and
`Days Since Last Touch > the gap for its current stage` (3 after T1, 5 after T2,
7 after T3). Work the overdue queue before adding any new leads — a stale
pipeline is worth more than a bigger one.

---

## 4. Pre-research dedupe gate (run BEFORE analysing anything)

Five rows were fully researched and only then flagged `dup list.7` (Theodore
Sprink, Craig Caryl, Keith Hovan, and others). That is analysis spent on leads
already decided.

**Before rating any pasted lead, check the sheet for:**
1. **LinkedIn URL** — exact match (strongest signal)
2. **Name** — normalised, case/punctuation-insensitive
3. **Company** — if it already has a live contact, this is the *same account*, not a new lead

Then:
- **Already `Skip`/`Not Relevant`** → reply `dup — already skipped [date]`. Do not re-research.
- **Already live (contacted/replied)** → reply `dup — already in play, status X`. Do not open a second thread.
- **Company already has a live contact** → do not contact a second person at that
  company cold. Note it on the existing row instead. (Inspiren had Alexander
  Hejnosz *and* Justin Oblak; Seen Health had Lori Evans Bernstein *and* Xing S.)

Run `python scripts/pipeline_health.py --check-dupes` to see current collisions.

### Company-identity trap

Match the *entity*, not the name. The sheet already caught one: "her Seen NYC =
1-emp stealth co; **NOT** the 53-emp Seen Health LA PACE co." Confirm headcount +
location + domain before treating two same-named companies as one.

---

## 5. Canonical target geography

The pipeline was applying opposite rules to the same country — Australia was
`SKIP: skip-geo` on 9 rows and `AU (target geo)` on 8; Canada was skip on 12 and
target on 10. That forces a judgement call on every row instead of a filter.

**This table is the filter. No per-row judgement.**

**Confirmed by Arslan 2026-08-06.** Target = US, Canada, Australia, Singapore, Gulf. UK excluded.

| Geo | Verdict |
|---|---|
| United States | ✅ Target |
| Canada | ✅ Target |
| Australia | ✅ Target |
| Singapore | ✅ Target |
| **Gulf** — UAE, Saudi Arabia, Qatar, Kuwait, Bahrain, Oman | ✅ Target |
| **United Kingdom** | ❌ **Excluded** — settled 2026-08-06, no longer an open question |
| New Zealand, Ireland | ❌ Not in target (were listed as widen options before 2026-08-06; no rows affected) |
| India, Pakistan, Israel, LATAM, mainland Europe, everywhere else | ❌ Skip on geo |

> ⚠️ **Never match on the bare word "wales"** when filtering out the UK — it would
> exclude **New South Wales, Australia** (Dom Gattellari, Leigh Caprile are both
> Sydney/NSW and in target). Match `united kingdom`, `london`, `england`, `scotland`.

Geo is a **company-HQ** test, not a personal-location test. A founder living
elsewhere while running a US-HQ'd company is in target.
