import sys, json, csv, subprocess, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import stage1
from csv_io import lead_key

tmp = Path(tempfile.mkdtemp(prefix="lle-join-"))
ROOT = Path(__file__).resolve().parent.parent

# stage-1 export: rich signals the filter step may not preserve
leads_json = tmp / "leads.json"
leads_json.write_text(json.dumps({"schemaVersion": 1, "leads": [
  {"salesUrn": "urn:li:fs_salesProfile:(ACwAAAjane,NAME_SEARCH,TNTB)", "memberId": "87305200",
   "profileId": "ACwAAAjane", "salesUrl": "https://www.linkedin.com/sales/lead/ACwAAAjane,NAME_SEARCH,TNTB",
   "fullName": "Jané Döe-Müller", "seniority": "VP", "yearsInRole": 3,
   "companyStaffRange": "201-500", "industry": "Software"},
  {"salesUrn": "urn:li:fs_salesProfile:(ACwAAAbob,NAME_SEARCH,DGLL)", "memberId": "87305201",
   "profileId": "ACwAAAbob", "salesUrl": "https://www.linkedin.com/sales/lead/ACwAAAbob,NAME_SEARCH,DGLL",
   "fullName": "Bob Smith", "seniority": "CTO", "yearsInRole": 7,
   "companyStaffRange": "51-200", "industry": "Fintech"},
]}), encoding="utf-8")

index = stage1.load_index(leads_json)

# a filter step that kept only two columns and added its own
lossy = {"profileId": "ACwAAAjane", "reason": "VP eng at target-size SaaS"}
merged, matched = stage1.merge(lossy, index, lead_key(lossy))
assert matched is True
assert merged["seniority"] == "VP", "signal recovered from stage-1"
assert merged["yearsInRole"] == 3, "signal recovered from stage-1"
assert merged["companyStaffRange"] == "201-500"
assert merged["fullName"] == "Jané Döe-Müller"
assert merged["reason"] == "VP eng at target-size SaaS", "filter's own column preserved"
print("lossy filter recovery OK  (dropped columns restored, new column kept)")

# match by URL alone
url_only = {"salesUrl": "https://www.linkedin.com/sales/lead/ACwAAAbob,NAME_SEARCH,DGLL"}
merged2, matched2 = stage1.merge(url_only, index, lead_key(url_only))
assert matched2 is True and merged2["seniority"] == "CTO"
print("match by URL          OK  ->", merged2["fullName"])

# a row that isn't in the export falls back to CSV values, flagged
stranger = {"profileId": "ACwAAAghost", "fullName": "Ghost"}
merged3, matched3 = stage1.merge(stranger, index, lead_key(stranger))
assert matched3 is False and merged3["fullName"] == "Ghost"
print("unmatched row         OK  (falls back to CSV, reported)")

# --- check_filter.py ---
def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh); w.writerow(["row", "profileId", "fullName"])
        for r in rows: w.writerow(r)

orig = tmp / "leads.csv"
write_csv(orig, [[1, "ACwAAAjane", "Jane"], [2, "ACwAAAbob", "Bob"], [3, "ACwAAAcarol", "Carol"]])

def run(*args):
    return subprocess.run([sys.executable, str(ROOT / "check_filter.py"), *map(str, args)],
                          capture_output=True, text=True)

good = tmp / "good.csv"; write_csv(good, [[1, "ACwAAAjane", "Jane"]])
dec = tmp / "decisions.json"
dec.write_text(json.dumps([{"row":1,"keep":True},{"row":2,"keep":False},{"row":3,"keep":False}]))
r = run(orig, good, "-d", dec)
assert r.returncode == 0, r.stdout + r.stderr
print("check_filter clean    OK  (exit 0, all rows accounted for)")

incomplete = tmp / "inc.json"
incomplete.write_text(json.dumps([{"row":1,"keep":True},{"row":2,"keep":False}]))
r = run(orig, good, "-d", incomplete)
assert r.returncode == 1 and "no decision" in r.stderr, r.stderr
print("missing decision      OK  (exit 1: 'row 3 has no decision')")

corrupt = tmp / "corrupt.csv"; write_csv(corrupt, [[1, "ACwAAATYPO", "Jane"]])
r = run(orig, corrupt)
assert r.returncode == 1 and "altered identifiers" in r.stderr, r.stderr
print("altered identifier    OK  (exit 1: filter rewrote an ID)")

mismatch = tmp / "mm.csv"; write_csv(mismatch, [[1,"ACwAAAjane","Jane"],[2,"ACwAAAbob","Bob"]])
r = run(orig, mismatch, "-d", dec)
assert r.returncode == 1 and "keep 1 but filtered CSV has 2" in r.stderr, r.stderr
print("keep/row mismatch     OK  (exit 1: counts disagree)")
print("\nSTAGE-1 JOIN + FILTER CHECK TESTS PASSED")
