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
| `—` | Skipped / closed / declined | Nothing |
| *(blank)* | Never contacted | Not on cadence yet |

**Your daily routine:** filter BE on `OVERDUE`, sort BC descending, work top-down.
Do this *before* adding new leads.

Today: **155 need action** — 15 `ACCEPTED - SEND T2` (work these first),
125 `OVERDUE T2`, 15 `OVERDUE T3`. Oldest untouched is 43 days.

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

## 5. Dropdowns (fixed 2026-08-06)

The sheet used to carry auto-generated dropdowns built from whatever happened to be
in the cells — `Status` permitted only 3 values while 24 were in use, and
`Internal Notes` / `Rating Reason` had whole message blobs as options. That is fixed:

- **Dropdowns removed** from every free-text, date and formula column (14 of them).
- **Canonical lists installed** on the 6 real dropdown columns: Status (17 values in
  use), Outreach Channel (5), Response Type, Priority, Lead Type, Assigned To.
- Lists are **warn-not-reject**, so a legitimate value is never blocked — you get a
  flag, not a wall.
- **Label variants collapsed** — 436 cells. Outreach Channel went from 18 spellings
  to 5, so reply rates read correctly with no normalising:
  Connection Note **27.3%**, LinkedIn DM **23.5%**, InMail **7.9%**, Both 36.4%.

Every original value is recorded in `scripts/label_normalization_log.csv`.

Re-run the checks any time:

```bash
python sheet_audit.py            # every consistency check, worst first
python sheet_fix.py --all        # dry-run of any dropdown/label repair needed
```

**Do not put a dropdown on BC/BD/BE.** A dropdown is for typing in; picking a value
**overwrites the formula** and that row stops updating forever.

### If you click into BC/BD/BE

Those cells hold a formula, so clicking one shows a long expression in the formula
bar. That is normal — it is the source, not a value. **Press `Esc` to leave, never
`Enter`**: Enter commits whatever is in the edit box and can wipe the formula. It
already happened once to BE808, which sat empty until it was restored.

BC:BE now carry warn-on-edit protection, so Sheets prompts before an edit lands.
To repair a damaged column at any time:

```bash
python pipeline_health.py --install-formulas   # rewrites all three columns
```

Fix pending: strip validation from formula/free-text/date columns, install canonical
lists on the real dropdowns (Status, Outreach Channel, Response Type, Priority),
and protect BC–BE. This should happen **before** `--decide --apply`, otherwise the
`Skip` / `On Hold` values it writes land flagged as invalid.

---

## 6. What this means for NEW leads

The columns are calculated for every row, including rows added later — the array
formula covers the whole column, so a new lead is picked up automatically. What you
must fill by hand is the input that drives them:

| You fill | Then BC/BD/BE do this |
|---|---|
| Nothing yet (just researched) | All three stay blank — the lead is not on cadence |
| `DM / Email Sent Date` = the day you sent T1 | Cadence starts. BD = that date + 3, BE counts down to T2 |
| `Response Type` = `Accepted` (they accepted) | BE flips to **`ACCEPTED - SEND T2`** — send the DM now |
| `Follow-up 1 Date` = the day you actually sent T2 | Touch count goes to 2, BD = that date + 5, BE tracks T3 |
| `Response Type` = `Positive` / `Negative` / `Neutral` | BE reads `REPLIED` — off cadence, it is a conversation |
| `Status` = `Skip` / `Closed - Not Interested` | BE reads `—`, the lead leaves the queue |

Three rules keep it accurate:

1. **Log the date on the day you send.** A blank sent date means the lead never
   enters the queue and gets silently forgotten.
2. **Follow-up columns take the date it was SENT.** Planned dates go in
   `Next Action Date`, or the lead reads as having an extra touch (§3).
3. **An accept is not a reply.** Mark `Accepted`, not `Positive`, or the lead drops
   off cadence before it has been pitched.

Adding rows below the last row is fine. If you ever add a row *above* the current
last row or extend past it, re-run `--install-formulas` to restretch the columns.
