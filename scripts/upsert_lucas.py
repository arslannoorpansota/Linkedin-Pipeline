#!/usr/bin/env python3
"""Upsert the Lucas Health Tech / Casi Vician lead into the BD Pipeline sheet.

Finds an existing row (Company == 'Lucas Health Tech' or name contains 'Casi'),
updates the given fields in place; if none exists, appends a new aligned row.

    scripts/.venv/bin/python scripts/upsert_lucas.py            # dry-run (no write)
    scripts/.venv/bin/python scripts/upsert_lucas.py --commit   # write
"""
from __future__ import annotations
import sys
import sync_reports_to_sheet as sync

TAB = "Pipeline"

# Canonical field values. Keys are matched to live headers (exact, case-insensitive,
# with a few aliases). Unmatched keys are reported in the dry-run.
LEAD = {
    "Date Added": "2026-07-24",
    "Full Name": "Casi M. Vician",
    "Lead Name": "Casi M. Vician",
    "Title": "Founder & CEO",
    "Company": "Lucas Health Tech",
    "Company Name": "Lucas Health Tech",
    "Industry": "Healthcare",
    "Location": "Painesville, OH, USA",
    "Email": "casi@lucashealthtech.com",
    "Phone": "+1 440-343-0399",
    "Connection Degree": "3rd",
    "Lead Type": "Direct Client",
    "Service Interest": "AI/ML, Full-stack",
    "Deal Type": "Project",
    "Estimated Budget": "$100k+",
    "Priority": "High",
    "Lead Score": "9",
    "Hook / Why Outreach": "Inbound RFI: LORiMDT clinical-governance platform (HCC tumor board); FHIR + tumor-board workflow build",
    "Outreach Channel": "Both",
    "From Email": "arslan@electrocomit.com",
    "Outreach by": "Arslan",
    "Status": "Proposal Sent",
    "Response Date": "2026-08-01",
    "Response Type": "Neutral",
    "Response Summary": "Group status email: submission under review; demos moved to week of Aug 10; shortlist invites sent individually.",
    "Proposal Sent Date": "2026-08-01",
    "Deal Value (USD)": "385000",
    "Assigned To": "Both",
    "Next Action": "Submit demo-process questions (due Aug 5, 5PM MT); prep working Tier-1 demo for wk of Aug 10; brief references (Iftikhar, John Linss)",
    "Next Action Date": "2026-08-05",
    "Lead Source": "Inbound",
    "Internal Notes": ("RFI response submitted 2026-08-01 02:53 (before 7/31 5PM MT deadline). "
                       "Bid Tier 1 $385K one-time + phased Tier 2; $20K fixed-scope discovery sprint credited to kickoff. "
                       "Refs: confidential clinical-platform client (multi-hospital, at demo under NDA), Sonostat / Iftikhar Saeed Khan, IUB; "
                       "CoreSpeed+PharmaBuilt / John Linss labeled as non-clinical systems work. Clinical lead Dr. Talia Baker. "
                       "Demos moved to wk of Aug 10; demo-questions due Aug 5, Demo FAQ Aug 6."),
}

ALIASES = {
    "full name": ["lead name"], "lead name": ["full name"],
    "company": ["company name"], "company name": ["company"],
    "deal value (usd)": ["deal value"], "deal value": ["deal value (usd)"],
}


def norm(s: str) -> str:
    return s.strip().lower()


def build_header_index(headers):
    idx = {norm(h): i for i, h in enumerate(headers)}
    return idx


def col_letter(n0):  # 0-based -> A1 letter
    n = n0 + 1
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def main():
    commit = "--commit" in sys.argv
    cfg = sync.load_config()
    svc = sync.get_service()
    sid = cfg["spreadsheet_id"]

    res = svc.spreadsheets().values().get(spreadsheetId=sid, range=f"'{TAB}'!A1:BB500").execute()
    vals = res.get("values", [])
    if not vals:
        print("Pipeline tab is empty; aborting (unexpected)."); return 1
    headers = vals[0]
    hidx = build_header_index(headers)

    # map LEAD keys -> column index
    mapped, unmatched = {}, []
    for k, v in LEAD.items():
        col = hidx.get(norm(k))
        if col is None:
            for alt in ALIASES.get(norm(k), []):
                if norm(alt) in hidx:
                    col = hidx[norm(alt)]; break
        if col is None:
            unmatched.append(k)
        else:
            mapped[col] = v  # later duplicate cols (alias) overwrite; fine

    # find existing row
    ci = hidx.get("company") or hidx.get("company name")
    ni = hidx.get("full name") if "full name" in hidx else hidx.get("lead name")
    found_row = None
    for r, row in enumerate(vals[1:], start=2):
        comp = row[ci].strip().lower() if (ci is not None and ci < len(row)) else ""
        name = row[ni].strip().lower() if (ni is not None and ni < len(row)) else ""
        if comp == "lucas health tech" or "casi" in name:
            found_row = r; existing = row; break

    print(f"Headers: {len(headers)} cols. Existing Lucas/Casi row: {found_row or 'NONE'}")
    if unmatched:
        print("!! Unmatched fields (won't be written):", unmatched)

    if found_row:
        # overlay onto existing row, update whole row range
        new_row = list(existing) + [""] * (len(headers) - len(existing))
        changes = []
        for col, v in mapped.items():
            if new_row[col] != v:
                changes.append((headers[col], new_row[col], v))
            new_row[col] = v
        print(f"\nUPDATE row {found_row}: {len(changes)} cell changes")
        for h, old, new in changes:
            print(f"  [{h}] '{old[:40]}' -> '{new[:60]}'")
        if commit:
            rng = f"'{TAB}'!A{found_row}:{col_letter(len(headers)-1)}{found_row}"
            svc.spreadsheets().values().update(
                spreadsheetId=sid, range=rng, valueInputOption="RAW",
                body={"values": [new_row]}).execute()
            print("Committed update.")
    else:
        row = [""] * len(headers)
        for col, v in mapped.items():
            row[col] = v
        print("\nAPPEND new row:")
        for col, v in mapped.items():
            print(f"  [{headers[col]}] = '{str(v)[:60]}'")
        if commit:
            sync.append_rows(svc, sid, TAB, [row])
            print("Committed append.")

    if not commit:
        print("\n(dry-run; re-run with --commit to write)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
