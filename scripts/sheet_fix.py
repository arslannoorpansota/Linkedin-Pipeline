#!/usr/bin/env python3
"""
Repair sheet hygiene: bad dropdowns and fragmented label values.

  --validation   remove auto-generated dropdowns from free-text / date / formula
                 columns, and install canonical lists on the real dropdown columns
  --labels       collapse label variants to one canonical value per meaning
  --all          both

Dry-run unless --apply. Run --labels BEFORE --validation so no value is left
outside its new list.

Usage:
    python sheet_fix.py --all
    python sheet_fix.py --all --apply
"""
from __future__ import annotations

import argparse
import collections
import csv
import re
import sys
from pathlib import Path

import pipeline_health as ph
import sync_reports_to_sheet as sync

SCRIPT_DIR = Path(__file__).resolve().parent
TAB = "Pipeline"

# Columns that must never carry a dropdown: calculated, free text, or a date.
NO_DROPDOWN = re.compile(
    r"date|notes|reason|hook|content|^lead name$|^company name$|"
    r"days since last touch|cadence due|cadence stage|interested in|"
    r"mutual connections|^title$|^location$|^linkedin url$|^email$", re.I)

# Canonical lists for the columns that genuinely are dropdowns. Every value the
# sheet uses after --labels must appear here.
DROPDOWNS = {
    "Status": [
        "New", "To Review - pull full profile", "Connection note drafted (USER TO SEND)",
        "Connection Requested", "Connected (No DM yet)", "DM Sent", "InMail Sent",
        "Email Sent", "Connected - follow-up sent", "Replied", "In Conversation",
        "Interested", "Call Scheduled", "RFI in progress", "Proposal Sent",
        "Negotiating", "Won", "Lost", "Closed - Not Interested", "On Hold",
        "Nurture", "Not Relevant", "Skip",
    ],
    "Outreach Channel": [
        "Connection Note", "LinkedIn DM", "InMail", "Email", "Both",
        "Referral", "Inbound", "Skip",
    ],
    "Response Type": [
        "Accepted", "Positive", "Neutral", "Negative", "Declined",
        "Not a fit", "No Response",
    ],
    "Priority": ["High", "Medium", "Low"],
    "Lead Type": ["Direct Client", "Agency Partner", "Anthropic Partner", "Hire (Arslan)"],
    "Assigned To": ["Arslan", "Faizan", "Both"],
}

# value -> canonical. Matched case-insensitively on the whole cell.
LABELS: dict[str, dict[str, str]] = {
    "Outreach Channel": {},     # filled by rules below
    "Status": {
        "connection send": "Connection Requested",
        "inmail sent": "InMail Sent",
        "connected": "Connected (No DM yet)",
        "connected - accepted": "Connected (No DM yet)",
        "connected - inbound (he requested, we accepted)": "Connected (No DM yet)",
        "replied - not a fit (network-only)": "Closed - Not Interested",
        "closed - inmail declined": "Closed - Not Interested",
        "in conversation - pitched meta auto-post agent (distribution)": "In Conversation",
        "call scheduling": "Call Scheduled",
    },
    "Response Type": {
        "accepted (connection)": "Accepted",
        "accepted connection (network only)": "Accepted",
        "connection accepted": "Accepted",
        "accepted + viewed profile": "Accepted",
        "positive - rfi materials sent": "Positive",
        "positive - not a services fit now": "Positive",
        "interested (not near-term dev buyer)": "Positive",
        "not interested (keep-warm)": "Declined",
        "not a fit - builds in-house (network-only)": "Not a fit",
    },
    "Lead Type": {
        "type a": "Direct Client",
        "direct client (type a)": "Direct Client",
        "type b": "Agency Partner",
        "skip": "",
    },
}


def canon_channel(v: str) -> str:
    """Channel variants all clearly name one channel; degree/mutuals live in their
    own columns, so the extra detail in the label is redundant."""
    s = v.strip().lower()
    if not s:
        return ""
    if "inmail" in s:
        return "InMail"
    if "connection note" in s:
        return "Connection Note"
    if s == "both":
        return "Both"
    if "skip" in s:
        return "Skip"
    if "email" in s:
        return "Email"
    if "dm" in s or s == "linkedin":
        return "LinkedIn DM"
    if "referral" in s:
        return "Referral"
    if "inbound" in s:
        return "Inbound"
    return v


def fix_labels(svc, sid, sh, apply: bool) -> None:
    changes = []
    for col, mapping in LABELS.items():
        if col not in sh.idx:
            continue
        letter = ph.col_letter(sh.idx[col])
        for i, row in enumerate(sh.rows, start=2):
            cur = sh.get(row, col)
            if not cur:
                continue
            new = canon_channel(cur) if col == "Outreach Channel" \
                else mapping.get(cur.strip().lower(), cur)
            if new != cur:
                changes.append((f"{TAB}!{letter}{i}", col, cur, new))

    print(f"\n=== NORMALISE LABELS ({'APPLYING' if apply else 'DRY RUN'}) "
          f"— {len(changes)} cells ===")
    summary = collections.Counter((c[1], c[2], c[3]) for c in changes)
    for (col, old, new), n in summary.most_common():
        print(f"  {n:4}  {col:17} {old[:44]!r} -> {new!r}")
    if not changes or not apply:
        if changes:
            print("  (no write — add --apply)")
        return
    # Audit trail: some mappings drop detail (e.g. "In conversation - pitched Meta
    # auto-post agent" -> "In Conversation"), so record every original value.
    log = SCRIPT_DIR / "label_normalization_log.csv"
    with log.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["cell", "column", "old_value", "new_value"])
        w.writerows(changes)
    print(f"  audit trail -> {log}")
    data = [{"range": r, "values": [[new]]} for r, _, _, new in changes]
    for i in range(0, len(data), 900):
        svc.spreadsheets().values().batchUpdate(
            spreadsheetId=sid,
            body={"valueInputOption": "USER_ENTERED", "data": data[i:i + 900]}).execute()
    print(f"  wrote {len(data)} cells")


def fix_validation(svc, sid, sh, apply: bool) -> None:
    meta = svc.spreadsheets().get(
        spreadsheetId=sid, ranges=[f"{TAB}!A1:BI2"], includeGridData=True,
        fields="sheets(properties(title,sheetId),data(rowData(values(dataValidation))))").execute()
    tab = meta["sheets"][0]
    gid = tab["properties"]["sheetId"]
    vrow = tab["data"][0].get("rowData", [{}])[-1].get("values", [])
    last_row = len(sh.rows) + 1

    strip, install = [], []
    for i, hdr in enumerate(sh.headers):
        name = hdr.strip()
        has_dv = i < len(vrow) and vrow[i].get("dataValidation")
        if name in DROPDOWNS:
            install.append((i, name))
        elif has_dv and (NO_DROPDOWN.search(name) or not name):
            strip.append((i, name or "(blank)"))

    print(f"\n=== FIX DATA VALIDATION ({'APPLYING' if apply else 'DRY RUN'}) ===")
    print(f"  strip dropdown from {len(strip)} columns:")
    for i, n in strip:
        print(f"      {ph.col_letter(i):3} {n}")
    print(f"  install canonical list on {len(install)} columns:")
    for i, n in install:
        print(f"      {ph.col_letter(i):3} {n:17} ({len(DROPDOWNS[n])} options)")
    if not apply:
        print("  (no write — add --apply)")
        return

    reqs = []
    for i, _ in strip:
        reqs.append({"setDataValidation": {"range": {
            "sheetId": gid, "startRowIndex": 1, "endRowIndex": last_row,
            "startColumnIndex": i, "endColumnIndex": i + 1}}})   # no rule = clear
    for i, name in install:
        reqs.append({"setDataValidation": {
            "range": {"sheetId": gid, "startRowIndex": 1, "endRowIndex": last_row,
                      "startColumnIndex": i, "endColumnIndex": i + 1},
            "rule": {
                "condition": {"type": "ONE_OF_LIST",
                              "values": [{"userEnteredValue": v} for v in DROPDOWNS[name]]},
                "showCustomUi": True,
                "strict": False,   # warn, don't reject: never block a legitimate write
            }}})
    for i in range(0, len(reqs), 100):
        svc.spreadsheets().batchUpdate(spreadsheetId=sid,
                                       body={"requests": reqs[i:i + 100]}).execute()
    print(f"  applied {len(reqs)} validation changes")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--validation", action="store_true")
    ap.add_argument("--labels", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not any([args.validation, args.labels, args.all]):
        ap.print_help()
        return 1

    svc = ph.read_service()
    sid = sync.load_config()["spreadsheet_id"]
    headers, rows = ph.fetch_rows(svc, sid)
    sh = ph.Sheet(headers, rows)
    print(f"Pipeline: {len(rows)} leads, {len(headers)} columns")

    if args.labels or args.all:
        fix_labels(svc, sid, sh, args.apply)
    if args.validation or args.all:
        if args.apply and (args.labels or args.all):
            headers, rows = ph.fetch_rows(svc, sid)      # re-read after label writes
            sh = ph.Sheet(headers, rows)
        fix_validation(svc, sid, sh, args.apply)
    return 0


if __name__ == "__main__":
    sys.exit(main())
