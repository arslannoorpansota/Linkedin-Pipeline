"""Emit leads_filtered.csv from leads.csv + decisions.json.

Judgement lives in decisions.json; this script only copies rows, so names,
URNs and encodings stay byte-identical to the export.
"""
import csv, json, sys

leads = sys.argv[1] if len(sys.argv) > 1 else 'data/leads.csv'
decs  = sys.argv[2] if len(sys.argv) > 2 else 'data/decisions.json'
out   = sys.argv[3] if len(sys.argv) > 3 else 'data/leads_filtered.csv'

keep = {d['row'] for d in json.load(open(decs)) if d['keep']}

with open(leads, newline='', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = [r for r in reader if int(r['row']) in keep]

with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

print(f'{len(rows)} kept -> {out}')
