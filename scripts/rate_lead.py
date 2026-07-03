#!/usr/bin/env python3
"""Write a lead's Profile + Company rating (and a note) to the BD Pipeline sheet.

Finds the row by Full Name and updates the 'Profile Rating (/10)',
'Company Rating (/10)', and 'Internal Notes' columns. Reuses the sync OAuth token.

    python rate_lead.py --name "Sam Garg" --profile 5 --company 3 --note "..."
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync_reports_to_sheet as S


def col(i):
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--profile", type=int, required=True)
    ap.add_argument("--company", type=int, required=True)
    ap.add_argument("--note", default="")
    a = ap.parse_args()

    svc = S.get_service()
    sid = S.load_config()["spreadsheet_id"]
    hdr = svc.spreadsheets().values().get(
        spreadsheetId=sid, range="'Pipeline'!1:1").execute().get("values", [[]])[0]
    pr, cr, nt = (hdr.index("Profile Rating (/10)"),
                  hdr.index("Company Rating (/10)"),
                  hdr.index("Internal Notes"))
    names = svc.spreadsheets().values().get(
        spreadsheetId=sid, range="'Pipeline'!C2:C").execute().get("values", [])
    row = next((i for i, v in enumerate(names, start=2)
                if v and v[0].strip().lower() == a.name.strip().lower()), None)
    if not row:
        sys.exit(f"NOT FOUND in sheet: {a.name}")
    data = [
        {"range": f"'Pipeline'!{col(pr)}{row}", "values": [[a.profile]]},
        {"range": f"'Pipeline'!{col(cr)}{row}", "values": [[a.company]]},
    ]
    if a.note:
        data.append({"range": f"'Pipeline'!{col(nt)}{row}", "values": [[a.note]]})
    svc.spreadsheets().values().batchUpdate(
        spreadsheetId=sid,
        body={"valueInputOption": "RAW", "data": data}).execute()
    print(f"Rated {a.name} (row {row}) -> Profile {a.profile}, Company {a.company}")


if __name__ == "__main__":
    main()
