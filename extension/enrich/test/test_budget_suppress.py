import sys, json, csv, shutil, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from budget import Budget, BudgetExhausted
from store import Store
import suppress
from parsers import parse_insights
from csv_io import lead_key

tmp = Path(tempfile.mkdtemp(prefix="lle-test-"))
shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)

# 1. permanent failure is not retried, but --retry-failed overrides
s = Store(tmp / "out")
s.put_lead("k1", {"stage": "enriched"})
s.put_lead("k2", {"stage": "failed", "error": "profile_not_found"})
s.put_lead("k3", {"stage": "failed", "error": "network_hiccup"})
s.flush()
s2 = Store(tmp / "out")
assert s2.is_done("k1") is True
assert s2.is_done("k2") is True,  "permanent failure should be done"
assert s2.is_done("k3") is False, "transient failure should retry"
assert s2.is_done("k2", retry_failed=True) is False, "--retry-failed overrides"
assert s2.is_done("nope") is False
print("permanent failures   OK  (not_found skipped, transient retried, override works)")

# 2. budget persists across Budget instances (i.e. across runs)
b = Budget(tmp / "budget.json", daily_cap=5)
for _ in range(3): b.record()
assert b.used() == 3 and b.remaining() == 2
b2 = Budget(tmp / "budget.json", daily_cap=5)
assert b2.used() == 3, "budget survived a fresh run"
b2.record(); b2.record()
assert b2.remaining() == 0
try:
    b2.check(); raise SystemExit("FAIL: check() should have raised")
except BudgetExhausted as e:
    assert "daily cap of 5" in str(e), e
print("daily budget         OK  (persists across runs, halts at cap)")

# 3. suppression from CSV and text, incl. URL -> public id
sup_csv = tmp / "contacted.csv"
with sup_csv.open("w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh); w.writerow(["salesUrl"])
    w.writerow(["https://www.linkedin.com/sales/lead/ACwAAAU0K_ABe1k,NAME_SEARCH,TNTB"])
sup_txt = tmp / "exclude.txt"
sup_txt.write_text("# manual excludes\nACwAAB1xBobSmith\n", encoding="utf-8")
sset = suppress.load([sup_csv, sup_txt])
jane = {"salesUrl": "https://www.linkedin.com/sales/lead/ACwAAAU0K_ABe1k,NAME_SEARCH,TNTB"}
bob  = {"profileId": "ACwAAB1xBobSmith"}
new  = {"profileId": "ACwAAC9qFreshLead"}
assert suppress.is_suppressed(jane, sset, lead_key(jane)) is True
assert suppress.is_suppressed(bob,  sset, lead_key(bob))  is True, "text list by profileId"
assert suppress.is_suppressed(new,  sset, lead_key(new))  is False
print("suppression          OK  (csv salesUrl + text profileId both match, new passes)")

# 4. activity parsing + dedup + noise rejection
feed = {"elements": [
  {"entityUrn": "urn:li:activity:1", "insightType": "LEAD_POST",
   "commentary": "We just shipped our new pricing model after six months of research."},
  {"entityUrn": "urn:li:activity:1",
   "commentary": "We just shipped our new pricing model after six months of research."},
  {"commentary": "short"},
  {"text": "Hiring two senior backend engineers in Berlin, DM me if interested."},
]}
acts = parse_insights(feed)
assert len(acts) == 2, acts
assert acts[0]["type"] == "LEAD_POST", acts[0]
assert "pricing model" in acts[0]["text"]
assert "Hiring two senior" in acts[1]["text"]
print("activity parsing     OK  (2 posts, dupe dropped, 'short' noise rejected)")
print("\nALL NEW-FEATURE TESTS PASSED")
