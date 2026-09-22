import sys, json, csv, os, tempfile
from pathlib import Path
from datetime import datetime, timedelta, timezone
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import stage1, enrich
from store import Store
from linkedin import Blocked, NotFound
from csv_io import lead_key

tmp = Path(tempfile.mkdtemp(prefix="lle-res-"))
a = lambda c, m: (_ for _ in ()).throw(AssertionError(m)) if not c else None

# --- 1. a null in the stage-1 export must not blank a value the CSV still has
idx = {"jane": {"publicIdentifier": "jane", "seniority": None,
                "industry": "", "yearsInRole": 3, "fullName": "Jané"}}
row = {"publicIdentifier": "jane", "seniority": "VP", "industry": "SaaS", "reason": "fit"}
merged, matched = stage1.merge(row, idx, "jane")
a(matched, "should match")
a(merged["seniority"] == "VP", f"null base blanked CSV value: {merged['seniority']}")
a(merged["industry"] == "SaaS", f"empty base blanked CSV value: {merged['industry']}")
a(merged["yearsInRole"] == 3, "base value applied where present")
a(merged["fullName"] == "Jané", "base value applied")
a(merged["reason"] == "fit", "csv-only column kept")
print("merge null-safety    OK  (export nulls no longer blank CSV values)")

# --- 2. staleness + incomplete gating
s = Store(tmp / "s1")
old = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
s.put_lead("fresh", {"stage": "enriched", "enrichedAt": datetime.now(timezone.utc).isoformat()})
s.put_lead("stale", {"stage": "enriched", "enrichedAt": old})
s.put_lead("partial", {"stage": "enriched", "incomplete": ["company"],
                       "profile": {"experience": []}, "enrichedAt": old})
a(s.is_done("fresh") and s.is_done("stale"), "no refresh window = both done")
a(s.is_done("stale", refresh_days=90) is False, "stale must refresh")
a(s.is_done("fresh", refresh_days=90) is True, "fresh must not refresh")
a(s.is_done("partial") is False, "incomplete record is not done")
a(s.banked_profile("partial") is not None, "banked profile recoverable")
a(s.banked_profile("fresh") is None, "complete record is not banked")
print("resume gating        OK  (stale refreshes, partial resumes, fresh skipped)")

# --- 3. integration: blocked during company fetch must not lose the profile
csv_path = tmp / "filtered.csv"
with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh); w.writerow(["row", "profileId", "salesUrn", "fullName"])
    w.writerow(["1", "ACwAAAjane",
                "urn:li:fs_salesProfile:(ACwAAAjane,NAME_SEARCH,TNTB)", "Jane"])

PROFILE = {"entityUrn": "urn:li:fs_salesProfile:(ACwAAAjane,NAME_SEARCH,TNTB)",
  "objectUrn": "urn:li:member:1", "fullName": "Jane", "summary": "Hi",
  "currentPositions": [{"title": "VP Eng", "companyName": "Acme", "current": True,
    "companyUrn": "urn:li:fs_salesCompany:1", "startedOn": {"year": 2021}}]}

class FakeClient:
    """Serves the profile, then blocks on the company call."""
    def __init__(self, *args, **kw): self.fetches = 0; self.profile_calls = 0
    def profile(self, ref): self.profile_calls += 1; self.fetches += 1; return PROFILE
    def insights(self, ref, count=3): raise NotFound("no insights")
    def company(self, cid): raise Blocked("HTTP 429 — rate limited")

out = tmp / "out"
os.environ["LI_AT"] = "x"; os.environ["LI_JSESSIONID"] = "y"
real = enrich.LinkedInClient
enrich.LinkedInClient = FakeClient
made = []
enrich.LinkedInClient = lambda *ar, **kw: made.append(FakeClient()) or made[-1]

argv = ["enrich.py", str(csv_path), "-o", str(out), "--min-delay", "0", "--max-delay", "0"]
sys.argv = argv
rc = enrich.main()
a(rc == 2, f"blocked run should exit 2, got {rc}")

leads = json.loads((out / "leads.json").read_text())["records"]
rec = leads["ACwAAAjane"]
a(rec["profile"]["headline"] == "Hi", "profile must be banked despite the block")
a(rec["incomplete"] == ["company"], f"outstanding work recorded: {rec.get('incomplete')}")
a(made[0].profile_calls == 1, "one profile fetch")
print("blocked mid-lead     OK  (profile banked, 'company' left outstanding)")

# --- 4. resume: company now succeeds, profile must NOT be refetched
class RecoveredClient(FakeClient):
    def company(self, cid):
        self.fetches += 1
        return {"entityUrn": "urn:li:fs_salesCompany:1", "name": "Acme",
                "industry": "Software", "employeeCount": 240}

made2 = []
enrich.LinkedInClient = lambda *ar, **kw: made2.append(RecoveredClient()) or made2[-1]
sys.argv = argv
rc = enrich.main()
a(rc == 0, f"resume should succeed, got {rc}")
a(made2[0].profile_calls == 0, "profile must be reused, not refetched")

leads = json.loads((out / "leads.json").read_text())["records"]
rec = leads["ACwAAAjane"]
a("incomplete" not in rec, "record completed")
a(rec["companyKey"] == "1", "company resolved on resume")
companies = json.loads((out / "companies.json").read_text())["records"]
a(companies["1"]["staffCount"] == 240, "company data stored")
print("resume after block   OK  (0 profile refetches, company completed)")

enrich.LinkedInClient = real
print("\nRESILIENCE TESTS PASSED")
