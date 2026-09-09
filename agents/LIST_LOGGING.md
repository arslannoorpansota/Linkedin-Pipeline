# LIST_LOGGING.md — Full-List Logging Protocol

> **Standing rule, set by Faizan 2026-09-10. Applies to EVERY Sales Navigator list we triage, not just the one it was created for.**
> Every lead in a saved list gets a sheet row. Nothing is discarded silently.

---

## Why this exists

Before this rule, only shortlisted leads were logged and the other ~110 per list vanished
with no record. That meant: no dedupe protection on the leads we passed over, no audit trail
of *why* they were passed over, and the same names resurfacing in later pulls with nobody
able to tell they had already been judged.

---

## The two-pass protocol

### Pass 0 — Dedupe (always first)
Normalize name (col C) and company (col E) with `re.sub(r'[^a-z0-9]','',s.lower())` and check
**every** lead in the list against the sheet, shortlist and non-shortlist alike. Drop collisions
before writing anything. Report which ones collided.

### Pass 1 — Non-shortlisted leads (written FIRST)
Append one row per non-shortlisted lead, in list order:

- `B` date · `C` name · `D` title · `E` company · `G` geo · `M` Direct Client
- `AV` source (e.g. `Sales Nav - sep 9 list 3 (v11)`) · `AX` name · `AY` company
- `Q` Low · `R` score · `AZ` profile rating · `BA` company rating
- `T` = `Skip` · `AB` = `Skipped` · `AT` = `None - do not contact (skip)`
- `AW` internal note **AND** `BB` full reason — both, always

**Every Pass-1 reason MUST be prefixed `[LIST-VIEW ONLY]`** so no one later mistakes a
list-view judgement for a full-profile verdict. The rating is from a single line of text
(name, title, company, geo). Say so in the row.

### Pass 2 — Shortlist (written AFTER Pass 1)
Append shortlisted leads after the Pass-1 block. These are **staged, not rated**:

- Identity fields as above, plus `BB` = `STAGED (v-- shortlist) - awaiting full profile`
- Leave `Q/R/T/AZ/BA` empty until the full profile is read
- Then rate two-at-a-time off full profiles, draft humanized notes for keeps

---

## THE CONFIDENCE RULE (most important)

> **Never skip a lead on a guess. Confidence gates the skip, not lead quality.**

- Skip at list view **only** when the line itself is conclusive.
- If you are **not sure** the lead is skippable, it goes to the **shortlist** for a full-profile read.
- Rationale: a wrong skip silently loses a real lead forever; a wrong shortlist costs one profile read.
  The costs are not symmetric, so bias toward the shortlist.

### Conclusive at list view (safe to skip)
- **Non-founder title** — Grant Coordinator, Teacher Assistant, Professor, Lecturer, Board
  Member/Trustee, Analyst, Studio Manager, VP/CIO/CSO/SVP, Client Executive, Realtor,
  Software Engineer, Program Manager, Organizer, Director of X at a company they don't own.
- **Explicit CTO / technical-founder title** — "Co-Founder & CTO", "Founder CTO", "Chief AI Officer".
- **Geo auto-skip** — India, Pakistan, China, Thailand, UK (per `CADENCE.md` §5).
- **Obvious non-software business** named in the company line — plastic surgery / aesthetics /
  med-spa, pharmacy, bookkeeping, landscaping, staffing/outsourcing/recruiting agency,
  marketing/creative agency, nonprofit / association / foundation / institute / federation / TEDx.
- **Already a connection** or already handled in the sheet (dedupe catches most).

### NOT conclusive (must go to shortlist)
- Founder/Co-Founder at a company whose business you cannot identify from its name.
- A PhD/MD founder — the credential alone does not prove they are technical.
- Ambiguous names ("Flou", "Expa", "Hana", "The Lab") with a founder title.
- Anything where the skip reasoning would start with "probably", "likely", or "reads as".

---

## Ordering

Pass 1 rows go in **before** Pass 2 rows. Non-shortlisted first, shortlist after.

---

## Channel by PROFILE rating (Faizan, reaffirmed 2026-09-10)

The outreach channel is keyed off the **PROFILE rating in column AZ**, never the overall
lead score in column R.

| Profile rating (AZ) | Channel |
|---|---|
| **7 or above** | **BOTH** a connection note (<200 chars) **AND** an InMail |
| **6** | Connection note ONLY |
| **Below 6** | Skip (log fully, `T=Skip`) |

A lead can carry a low overall lead score (company docked for budget, services model, etc.)
and still be a Profile 7 that earns note + InMail. Rate the profile, then apply the table.

> ⚠️ **This overrides `agents/CADENCE.md` §2a**, which frames InMail as a fallback-only channel
> on the strength of reply-rate data (note 27.3%, InMail 5.3%). Faizan has overruled that for
> P7+. Never withhold an InMail from a P7 lead by citing CADENCE §2a or those stats.
> Where the two documents conflict, this rule wins.

---

## Handing over the next pair to rate

When asking Faizan for the next profiles, always give **two** leads in a table carrying
**page number**, list position, company, and sheet row:

| Page | List # | Name | Company | Sheet row |
|---|---|---|---|---|
| p1 | 4 | Kim Crosbie | NEXT\|HEALTH | 1999 |
| p2 | 13 | Jacqui Falco, RN | School Nurse Compass | 2000 |

The **page number is required** — a Sales Nav list paginates at ~25 per page, so without it
he has to sweep every page to find one name. Record each shortlisted lead's page and position
during triage. If a page is genuinely unknown, say so rather than guessing.

---

Relates to `agents/CADENCE.md` (dedupe gate, geo table), `agents/LEAD_RESEARCH.md`,
`sheets/SCHEMA.md`, and the memory notes `sheet-write-schema`, `icp-triage-engineering-gate`.
