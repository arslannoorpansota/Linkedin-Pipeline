#!/usr/bin/env python3
"""
Append manually-qualified leads to the BD Pipeline sheet (Pipeline tab).

Reads a JSON array of lead objects (keys match sheet columns, see MAPPING)
and appends one row each. Reuses OAuth token + Sheets helpers from
sync_reports_to_sheet.py. Idempotent via .manual_leads_state.json keyed by
lowercased "name|company".

Usage:
    python add_leads_to_sheet.py leads.json            # push
    python add_leads_to_sheet.py leads.json --dry-run  # print rows, no write
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import sync_reports_to_sheet as sync

SCRIPT_DIR = Path(__file__).resolve().parent
STATE_FILE = SCRIPT_DIR / ".manual_leads_state.json"

# JSON key -> sheet column. Any missing key -> blank cell. Extra keys in the lead
# dict that match a live header are also written (e.g. rating columns), so the set
# of writable columns is really "live header ∩ lead keys" — see lead_to_row.
PASSTHROUGH = [
    "Date Added", "Full Name", "Title", "Company", "Industry", "Location",
    "LinkedIn URL", "Email", "Connection Degree", "Mutual Connections",
    "Lead Type", "Service Interest", "Deal Type", "Estimated Budget",
    "Priority", "Lead Score", "Hook / Why Outreach", "Outreach Channel",
    "Assigned To", "Status", "Next Action", "Lead Source", "Internal Notes",
    # Extra columns present on the "ElectroCom Linkedin Pipeline" sheet:
    "Lead Name", "Company Name", "Profile Rating (/10)", "Company Rating (/10)",
    "Rating Reason",
]


def load_state() -> set[str]:
    if STATE_FILE.exists():
        try:
            return set(json.loads(STATE_FILE.read_text()).get("pushed", []))
        except Exception:
            return set()
    return set()


def save_state(keys: set[str]) -> None:
    STATE_FILE.write_text(json.dumps({"pushed": sorted(keys)}, indent=2))


def key_of(lead: dict) -> str:
    return f"{lead.get('Full Name', '').strip().lower()}|{lead.get('Company', '').strip().lower()}"


def lead_to_row(lead: dict, headers: list[str]) -> list[str]:
    row = {h: "" for h in headers}
    for k in PASSTHROUGH:
        if k in row and lead.get(k) not in (None, ""):
            row[k] = str(lead[k])
    if "Status" in row and not row["Status"]:
        row["Status"] = "New"
    if "Assigned To" in row and not row["Assigned To"]:
        row["Assigned To"] = "Arslan"
    if "Lead Source" in row and not row["Lead Source"]:
        row["Lead Source"] = "LinkedIn Sales Nav (manual)"
    return [row[h] for h in headers]


def live_headers(service, sid: str) -> list[str]:
    res = service.spreadsheets().values().get(
        spreadsheetId=sid, range=f"'{sync.PIPELINE_TAB}'!1:1").execute()
    vals = res.get("values", [])
    return vals[0] if vals else list(sync.PIPELINE_HEADERS)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("leads_json")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    leads = json.loads(Path(args.leads_json).read_text())
    state = load_state()
    new = [l for l in leads if key_of(l) not in state]
    print(f"{len(leads)} leads in file; {len(new)} new to push.")

    if args.dry_run:
        for l in new:
            print(f"  [{l.get('Company')}] {l.get('Full Name')} - {l.get('Title')} "
                  f"(score {l.get('Lead Score')}, {l.get('Priority')})")
        return 0

    if not new:
        print("Nothing new to push.")
        return 0

    cfg = sync.load_config()
    service = sync.get_service()
    sid = sync.ensure_spreadsheet(service, cfg)
    sync.ensure_tab_and_header(service, sid, sync.PIPELINE_TAB, sync.PIPELINE_HEADERS)
    headers = live_headers(service, sid)
    sync.append_rows(service, sid, sync.PIPELINE_TAB, [lead_to_row(l, headers) for l in new])

    for l in new:
        state.add(key_of(l))
    save_state(state)

    print(f"Pushed {len(new)} lead rows to Pipeline tab.")
    print(f"Sheet: {cfg.get('spreadsheet_url', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
