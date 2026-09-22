import sys, json, csv, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from parsers import parse_profile, parse_company, current_company, parse_insights
from csv_io import read_filtered, lead_key, lead_ref
from store import Store

a = lambda c, m: (_ for _ in ()).throw(AssertionError(m)) if not c else None
tmp = Path(tempfile.mkdtemp(prefix="lle-parse-"))

PROFILE = {"entityUrn": "urn:li:fs_salesProfile:(ACwAAAU0K_ABe1k,NAME_SEARCH,TNTB)",
  "objectUrn": "urn:li:member:87305200", "fullName": "Erik Abel",
  "summary": "Healthcare strategy", "geoRegion": "Greater Pittsburgh Region",
  "industry": "Hospitals", "numOfConnections": 500, "degree": 2,
  "currentPositions": [{"title": "Founder and Principal", "companyName": "OneAnother Health, LLC",
    "companyUrn": "urn:li:fs_salesCompany:105823183", "current": True,
    "tenureAtPosition": {"numYears": 5, "numMonths": 6},
    "tenureAtCompany": {"numYears": 5, "numMonths": 6},
    "startedOn": {"month": 4, "year": 2021}, "description": "Advisor to startups.",
    "companyUrnResolutionResult": {"entityUrn": "urn:li:fs_salesCompany:105823183",
      "name": "OneAnother Health", "industry": "Business Consulting and Services",
      "location": "Wexford, Pennsylvania, United States"}}],
  "pastPositions": [{"title": "VP Strategy", "companyName": "Acme",
    "companyUrn": "urn:li:fs_salesCompany:1", "current": False,
    "startedOn": {"year": 2015}, "endedOn": {"year": 2021}}]}

p = parse_profile(PROFILE)
a(p["fullName"] == "Erik Abel", p["fullName"])
a(p["memberId"] == "87305200", p["memberId"])
a(p["profileId"] == "ACwAAAU0K_ABe1k", p["profileId"])
a(p["location"] == "Greater Pittsburgh Region", p["location"])
a(p["connections"] == 500 and p["degree"] == 2, "counts")
a(len(p["experience"]) == 2, p["experience"])
a(p["experience"][0]["current"] is True, "current role first")
a(p["experience"][0]["yearsInRole"] == 5.5, p["experience"][0]["yearsInRole"])
a(p["experience"][0]["companyIndustry"] == "Business Consulting and Services", "industry")
print("parse_profile        OK  (current role first, tenure 5.5y, industry resolved)")

c = current_company(p)
a(c["id"] == "105823183" and c["name"] == "OneAnother Health, LLC", c)
print("current_company      OK  -> id", c["id"])

COMPANY = {"entityUrn": "urn:li:fs_salesCompany:105823183", "name": "OneAnother Health",
  "industry": "Business Consulting", "employeeCount": 12,
  "employeeCountRange": {"start": 11, "end": 50}, "website": "https://example.com",
  "foundedOn": {"year": 2021}, "description": "We advise.",
  "headquarters": {"city": "Wexford", "country": "US"}}
cc = parse_company(COMPANY)
a(cc["staffCount"] == 12 and cc["staffRange"] == "11-50", cc)
a(cc["industry"] == "Business Consulting" and cc["founded"] == 2021, cc)
print("parse_company        OK  ->", cc["staffRange"], "|", cc["industry"])

ins = parse_insights({"elements": [
  {"commentary": "We just shipped a new pricing model after months of research."},
  {"commentary": "We just shipped a new pricing model after months of research."},
  {"text": "short"},
  {"text": "Hiring two senior backend engineers in Berlin, DM me if interested."}]})
a(len(ins) == 2, ins)
print("parse_insights       OK  (2 posts, dupe + noise dropped)")

# --- identifiers -----------------------------------------------------------
ref = lead_ref({"salesUrn": "urn:li:fs_salesProfile:(ACwAAAU0K_ABe1k,NAME_SEARCH,TNTB)"})
a(ref.profile_id == "ACwAAAU0K_ABe1k" and ref.auth_type == "NAME_SEARCH", ref)
a(ref.path_key == "(profileId:ACwAAAU0K_ABe1k,authType:NAME_SEARCH,authToken:TNTB)", ref.path_key)
print("lead_ref from urn    OK  ->", ref.path_key[:46] + "...")

ref2 = lead_ref({"salesUrl": "https://www.linkedin.com/sales/lead/ACwAAB1x,NAME_SEARCH,DGLL"})
a(ref2.profile_id == "ACwAAB1x" and ref2.auth_token == "DGLL", ref2)
print("lead_ref from url    OK  ->", ref2.profile_id)

a(lead_ref({"fullName": "nobody"}) is None, "row with no identifier must be rejected")
print("no identifier        OK  (rejected, not guessed)")

# --- CSV round trip --------------------------------------------------------
csv_path = tmp / "filtered.csv"
with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["row","profileId","salesUrn","memberId","salesUrl","fullName","industry"])
    w.writerow(["1","ACwAAAU0K_ABe1k","urn:li:fs_salesProfile:(ACwAAAU0K_ABe1k,NAME_SEARCH,TNTB)",
                "87305200","https://www.linkedin.com/sales/lead/ACwAAAU0K_ABe1k,NAME_SEARCH,TNTB",
                "Jané Döe-Müller","Insurance"])
    w.writerow(["2","","","","https://www.linkedin.com/sales/lead/ACwAAB1x,NAME_SEARCH,DGLL","Bob",""])
    w.writerow(["3","","","","","No Identifier",""])

rows, skipped = read_filtered(csv_path)
a(len(rows) == 2 and skipped == [4], f"{len(rows)} usable, skipped {skipped}")
a(rows[0]["fullName"] == "Jané Döe-Müller", "unicode survived")
a(lead_key(rows[1]) == "ACwAAB1x", lead_key(rows[1]))
print("read_filtered        OK  (2 usable, 1 skipped, unicode intact, url fallback)")

store = Store(tmp / "out")
store.put_lead(lead_key(rows[0]), {**rows[0], "stage": "enriched", "companyKey": "105823183"})
store.put_company("105823183", cc)
store.flush()
s2 = Store(tmp / "out")
a(s2.is_done(lead_key(rows[0])) and s2.has_company("105823183"), "resume")
flat = json.loads(s2.write_flat().read_text(encoding="utf-8"))
a(flat["leads"][0]["company"]["name"] == "OneAnother Health", "flat join")
print("store + flat export  OK  (resume works, company joined)")
print("\nPARSING TESTS PASSED")
