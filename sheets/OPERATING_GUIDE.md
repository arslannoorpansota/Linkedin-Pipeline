# BD Pipeline — daily operating guide

> How to read the sheet and what to do each day. Companion to `SCHEMA.md`
> (column definitions) and `../agents/CADENCE.md` (the rules behind it).
> Sheet: **ElectroCom Linkedin Pipeline**, Pipeline tab.

---

## 1. The one thing to look at: column BE

Three new columns were added at the far right (BC, BD, BE). They fill themselves —
you never type in them.

| Col | Name | What it means |
|---|---|---|
| **BC** | Days Since Last Touch | Days since the most recent *completed* contact. Range today: 0–43 |
| **BD** | Cadence Due | The date the next touch is due |
| **BE** | **Cadence Stage** | **The verdict — this is the column you work from** |

### What BE tells you

| Value | Meaning | Do what |
|---|---|---|
| `ACCEPTED - SEND T2` | They accepted, no DM sent yet | **Highest priority — send now** |
| `OVERDUE T2` | Touch 2 is late | **Send it today** |
| `OVERDUE T3` | Touch 3 is late | **Send it today** |
| `T3 due Aug 11` | On track, not due yet | Nothing — come back on that date |
| `SCHEDULED Aug 13` | Next touch already booked | Nothing — it's planned |
| `REPLIED` | They answered | Off cadence. Handle as a conversation (`FOLLOW_UP.md`) |
| `PARK` | All 4 touches used | Stop. Re-engagement pool |
| `—` | Skipped / closed | Nothing |
| *(blank)* | Never contacted | Not on cadence yet |

**Your daily routine:** filter BE on `OVERDUE`, sort BC descending, work top-down.
Do this *before* adding new leads.

Today: **147 overdue** — 15 `ACCEPTED - SEND T2` (work these first), 117 `OVERDUE T2`,
15 `OVERDUE T3`. Oldest untouched is 43 days.

**An accept is not a reply.** Someone accepting your connection request is the
trigger for touch 2, not the end of the sequence. 14 leads had accepted and never
received a DM, two of them sitting 42 days.

---

## 2. What the 4 touches are

From `../agents/CADENCE.md` §3. Gaps are short on purpose — follow-ups were dying
after day 5.

| Touch | When | What |
|---|---|---|
| T1 | Day 0 | Connection note, hook only, no pitch |
| T2 | Day +3, or the moment they accept | DM with one proof point + soft ask |
| T3 | Day +8 | A **new angle**, not "just bumping this" |
| T4 | Day +15 | Close-the-loop email |
| Park | Day +45 | Status → `On Hold` |

**Channel rule that changed:** connection note is the default at **every** rating.
A 7+ no longer means InMail — InMail replies at 5.3% vs 27.3% for a free
connection note. InMail is only for when there's no free route in.

---

## 3. Two columns people mix up

- **`Follow-up N Date`** = the date that follow-up **was sent**. Past dates only.
- **`Next Action Date`** = when the next touch is **due**. Planned dates go here.

Putting a planned date in `Follow-up 1 Date` makes a lead look like it has an extra
completed touch — it lands in the wrong cadence stage and drives BC negative. This
happened on 16 rows. The formulas now ignore future dates and show `SCHEDULED`
instead, but log dates in the right column.

---

## 4. Commands (run from `scripts/`)

```bash
python pipeline_health.py --all          # overdue + undecided + duplicate report
python pipeline_health.py --overdue      # just the work queue
python pipeline_health.py --check-dupes  # before researching a new list
```

Read-only. These two write, and are dry-run until you add `--apply`:

```bash
python pipeline_health.py --fix-planned-fu --apply   # clears 16 misplaced dates
python pipeline_health.py --decide --apply           # decides all 381 New rows
```

If the formula columns ever look wrong, re-run:

```bash
python pipeline_health.py --install-formulas
```

---

## 5. Known issue: the dropdowns are wrong

26 columns have strict data validation that was auto-generated from whatever was
in the cells. It is inconsistent with reality:

- **`Status` allows only 3 values** (`DM Sent`, `New`, `Connection Requested`) while
  the sheet contains ~20. Most rows already violate their own dropdown.
- `Internal Notes`, `Rating Reason`, `Lead Name`, `Company Name` have dropdowns
  whose options are whole pasted message blobs.
- `Date Added`, `Next Action Date`, `Response Date` are dropdowns of literal dates.
- `Outreach Channel` has 12 spellings for 4 real channels, which is why reply-rate
  analysis needs normalising before it reads correctly.

**Do not put a dropdown on BC/BD/BE.** A dropdown is for typing in; picking a value
**overwrites the formula** and that row stops updating forever.

Fix pending: strip validation from formula/free-text/date columns, install canonical
lists on the real dropdowns (Status, Outreach Channel, Response Type, Priority),
and protect BC–BE. This should happen **before** `--decide --apply`, otherwise the
`Skip` / `On Hold` values it writes land flagged as invalid.
