#!/usr/bin/env python3
"""
Backfill send dates that were never logged, so those leads enter the cadence.

Confirmed by the user 2026-08-06: for the rows whose Status says a follow-up was
sent, the DM WAS sent — only the date was never recorded. Until it is filled in,
`Days Since Last Touch` reads from the wrong event and the lead sits in the wrong
cadence stage.

Every value here is sourced from the daily reports, not invented, and the basis is
written into Internal Notes so nothing looks like captured data when it is a
reconstruction. Dry-run unless --apply.

Sources:
  reports/2026-07-22.md — "8 rows still showed 'Connected (No DM yet)' though
      messages were sent (Irosha de Silva, Kiran Jain, Sam Bigdeli, Waqar A.,
      Charley Dehoney, Manju Devadas, Stephen Weis, Diego Serrano). Corrected all 8
      ... with an internal note that content was not captured in the sheet."
  reports/2026-07-01.md — post-accept DMs drafted the same day the accept was
      logged, so the accept date is the best available send date.

Usage:
    python backfill_dates.py
    python backfill_dates.py --apply
"""
from __future__ import annotations

import argparse
import sys

import pipeline_health as ph
import sync_reports_to_sheet as sync

TAB = "Pipeline"
BASIS = "Date reconstructed 2026-08-06 from reports/2026-07-22.md reconciliation"

# (row, column, value, basis) — DM confirmed sent; date taken from the accept, which
# the 07-01 report shows was the same day the post-accept DM went out.
PLAN: list[tuple[int, str, str, str]] = [
    (35,  "Follow-up 1 Date", "2026-07-01", "accept 07-01, post-accept DM same day"),
    (70,  "Follow-up 1 Date", "2026-07-03", "accept 07-03, post-accept DM same day"),
    (71,  "Follow-up 1 Date", "2026-07-03", "accept 07-03, post-accept DM same day"),
    (72,  "Follow-up 1 Date", "2026-07-03", "no accept logged; batch accepted 07-03"),
    (73,  "Follow-up 1 Date", "2026-07-03", "accept 07-03, post-accept DM same day"),
    (80,  "Follow-up 1 Date", "2026-07-02", "accept 07-02, post-accept DM same day"),
    (81,  "Follow-up 1 Date", "2026-07-03", "accept 07-03, post-accept DM same day"),
    # Diego Serrano: connection note 07-11 (reports/2026-07-10.md), DM confirmed by
    # the 07-22 reconciliation; no send date was ever recorded for either touch.
    (459, "DM / Email Sent Date", "2026-07-11", "connection note 07-11 per report"),
    (459, "Follow-up 1 Date",     "2026-07-22", "DM confirmed sent by 07-22 reconciliation"),
    # These three claim a follow-up was sent but have no dates at all. Date Added is
    # the only anchor, and in this batch Date Added == the day the note went out.
    (92,  "DM / Email Sent Date", "2026-07-03", "Date Added; batch sent same day"),
    (92,  "Follow-up 1 Date",     "2026-07-22", "DM confirmed sent by 07-22 reconciliation"),
    (104, "DM / Email Sent Date", "2026-07-03", "Date Added; batch sent same day"),
    (104, "Follow-up 1 Date",     "2026-07-22", "DM confirmed sent by 07-22 reconciliation"),
    (188, "DM / Email Sent Date", "2026-07-03", "Date Added; batch sent same day"),
    (188, "Follow-up 1 Date",     "2026-07-22", "DM confirmed sent by 07-22 reconciliation"),
    # Status "Connection Requested" with no send date: the request went out, only the
    # date is missing. Without it these never enter the cadence at all.
    (85,  "DM / Email Sent Date", "2026-07-03", "Date Added; batch sent same day"),
    (95,  "DM / Email Sent Date", "2026-07-03", "Date Added; batch sent same day"),
    (108, "DM / Email Sent Date", "2026-07-03", "Date Added; batch sent same day"),
    (113, "DM / Email Sent Date", "2026-07-03", "Date Added; batch sent same day"),
    (200, "DM / Email Sent Date", "2026-07-03", "Date Added; batch sent same day"),
    # Inbound: he requested, we accepted. No outbound send, but the connection exists,
    # so T2 is due from the date the connection was established.
    (623, "DM / Email Sent Date", "2026-07-24", "inbound accept 07-24; no outbound send"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    svc = ph.read_service()
    sid = sync.load_config()["spreadsheet_id"]
    headers, rows = ph.fetch_rows(svc, sid)
    sh = ph.Sheet(headers, rows)

    print(f"=== BACKFILL SEND DATES ({'APPLYING' if args.apply else 'DRY RUN'}) "
          f"— {len(PLAN)} cells ===")
    data, notes = [], {}
    for row_n, col, val, why in PLAN:
        row = sh.rows[row_n - 2]
        cur = sh.get(row, col)
        flag = "" if not cur else f"  !! already holds {cur!r}, skipping"
        print(f"  row {row_n:>4} {sh.name(row)[:22]:22} {col:22} <- {val}  ({why}){flag}")
        if cur:
            continue
        data.append({"range": f"{TAB}!{ph.col_letter(sh.idx[col])}{row_n}",
                     "values": [[val]]})
        notes.setdefault(row_n, []).append(f"{col} = {val} ({why})")

    for row_n, items in notes.items():
        row = sh.rows[row_n - 2]
        existing = sh.get(row, "Internal Notes")
        add = f"{BASIS}: " + "; ".join(items)
        data.append({"range": f"{TAB}!{ph.col_letter(sh.idx['Internal Notes'])}{row_n}",
                     "values": [[(existing + " | " + add).strip(" |")]]})

    if not args.apply:
        print(f"\n  {len(data)} cells would be written (incl. {len(notes)} Internal "
              f"Notes entries recording the basis)")
        print("  (no write — add --apply)")
        return 0
    svc.spreadsheets().values().batchUpdate(
        spreadsheetId=sid,
        body={"valueInputOption": "USER_ENTERED", "data": data}).execute()
    print(f"\n  wrote {len(data)} cells across {len(notes)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
