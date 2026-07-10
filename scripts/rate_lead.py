#!/usr/bin/env python3
"""Write lead Profile + Company ratings (and notes) to the BD Pipeline sheet.

Finds each row by Full Name and updates the 'Profile Rating (/10)',
'Company Rating (/10)', 'Internal Notes' and 'Rating Reason' columns.
Reuses the sync OAuth token.

Single lead:
    python rate_lead.py --name "Sam Garg" --profile 5 --company 3 --note "..."

Bulk (ONE API round-trip for the whole list) -- CSV with a header row
    name,profile,company,note
    Sam Garg,5,3,Series A, no in-house eng
    Jane Doe,8,7,Hiring 3 AI eng right now
    python rate_lead.py --batch ratings.csv          # or: --batch - (read stdin)

Dump every still-unrated lead as a ready-to-fill CSV template:
    python rate_lead.py --list-unrated > ratings.csv
"""
import argparse
import csv
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


def load_sheet(svc, sid):
    """Fetch header + all rows once. Returns (header, col indices, name->row map)."""
    hdr = svc.spreadsheets().values().get(
        spreadsheetId=sid, range="'Pipeline'!1:1").execute().get("values", [[]])[0]
    idx = {
        "profile": hdr.index("Profile Rating (/10)"),
        "company": hdr.index("Company Rating (/10)"),
        "note": hdr.index("Internal Notes"),
        "reason": hdr.index("Rating Reason") if "Rating Reason" in hdr else None,
    }
    name_i = hdr.index("Full Name")
    rows = svc.spreadsheets().values().get(
        spreadsheetId=sid, range="'Pipeline'!A2:BZ").execute().get("values", [])
    name_to_row = {}
    for offset, r in enumerate(rows, start=2):
        nm = r[name_i].strip().lower() if len(r) > name_i and r[name_i] else ""
        if nm and nm not in name_to_row:
            name_to_row[nm] = (offset, r)
    return hdr, idx, name_to_row


def build_updates(idx, row, profile, company, note):
    data = [
        {"range": f"'Pipeline'!{col(idx['profile'])}{row}", "values": [[profile]]},
        {"range": f"'Pipeline'!{col(idx['company'])}{row}", "values": [[company]]},
    ]
    if note:
        data.append({"range": f"'Pipeline'!{col(idx['note'])}{row}", "values": [[note]]})
        if idx["reason"] is not None:
            data.append({"range": f"'Pipeline'!{col(idx['reason'])}{row}", "values": [[note]]})
    return data


def read_batch(path):
    """Read a CSV of name,profile,company,note (header row required)."""
    f = sys.stdin if path == "-" else open(path, newline="", encoding="utf-8")
    try:
        rows = list(csv.DictReader(f))
    finally:
        if f is not sys.stdin:
            f.close()
    out = []
    for r in rows:
        name = (r.get("name") or "").strip()
        if not name:
            continue
        out.append({
            "name": name,
            "profile": int(r["profile"]) if r.get("profile", "").strip() else "",
            "company": int(r["company"]) if r.get("company", "").strip() else "",
            "note": (r.get("note") or "").strip(),
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name")
    ap.add_argument("--profile", type=int)
    ap.add_argument("--company", type=int)
    ap.add_argument("--note", default="")
    ap.add_argument("--batch", help="CSV file (or '-' for stdin) of name,profile,company,note")
    ap.add_argument("--list-unrated", action="store_true",
                    help="Print a CSV template of leads with no Profile Rating yet")
    a = ap.parse_args()

    svc = S.get_service()
    sid = S.load_config()["spreadsheet_id"]
    hdr, idx, name_to_row = load_sheet(svc, sid)

    if a.list_unrated:
        w = csv.writer(sys.stdout)
        w.writerow(["name", "profile", "company", "note"])
        for nm, (row, r) in sorted(name_to_row.items(), key=lambda kv: kv[1][0]):
            rated = len(r) > idx["profile"] and str(r[idx["profile"]]).strip()
            if not rated:
                w.writerow([r[hdr.index("Full Name")], "", "", ""])
        return

    if a.batch:
        leads = read_batch(a.batch)
    elif a.name:
        if a.profile is None or a.company is None:
            sys.exit("--profile and --company are required with --name")
        leads = [{"name": a.name, "profile": a.profile,
                  "company": a.company, "note": a.note}]
    else:
        sys.exit("Provide --name, --batch, or --list-unrated")

    data, done, missing = [], [], []
    for lead in leads:
        hit = name_to_row.get(lead["name"].strip().lower())
        if not hit:
            missing.append(lead["name"])
            continue
        row = hit[0]
        data += build_updates(idx, row, lead["profile"], lead["company"], lead["note"])
        done.append(f"{lead['name']} (row {row}) -> P{lead['profile']}/C{lead['company']}")

    if data:
        svc.spreadsheets().values().batchUpdate(
            spreadsheetId=sid,
            body={"valueInputOption": "RAW", "data": data}).execute()

    for d in done:
        print("Rated", d)
    if missing:
        print(f"\nNOT FOUND in sheet ({len(missing)}): " + ", ".join(missing),
              file=sys.stderr)


if __name__ == "__main__":
    main()



