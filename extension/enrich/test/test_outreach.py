import sys, json, subprocess, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

tmp = Path(tempfile.mkdtemp(prefix="lle-out-"))

flat = tmp / "leads_flat.json"
flat.write_text(json.dumps({"schemaVersion": 1, "leads": [
  {"salesUrn": "urn:li:fs_salesProfile:(ACwAAAjane,NAME_SEARCH,TNTB)", "profileId": "ACwAAAjane",
   "salesUrl": "https://www.linkedin.com/sales/lead/ACwAAAjane,NAME_SEARCH,TNTB",
   "fullName": "Jané <script>Döe</script>", "currentTitle": "VP Engineering",
   "activity": [{"text": "We just shipped our new pricing model."}],
   "profile": {"location": "Berlin, Germany", "headline": "VP Eng"},
   "company": {"name": "Acme & Co", "staffRange": "201-500"}},
  {"profileId": "ACwAAAbob", "salesUrl": "https://www.linkedin.com/sales/lead/ACwAAAbob,NAME_SEARCH,DGLL",
   "fullName": "Bob Smith", "currentTitle": "CTO", "profile": {}, "company": None},
]}), encoding="utf-8")

shortlist = tmp / "shortlist.json"
shortlist.write_text(json.dumps([
  {"key": "ACwAAAjane", "keep": True, "reason": "VP eng, right size, posting about pricing",
   "note": "Saw your post on the pricing rework — we hit the same wall at 200 seats."},
  {"key": "ACwAAAbob", "keep": True, "reason": "CTO at target account",
   "note": "x" * 320},
  {"key": "ACwAAAcarol", "keep": True, "note": "no match"},
  {"key": "ACwAAAdave", "keep": False, "note": "dropped"},
]), encoding="utf-8")

out = tmp / "outreach.html"
r = subprocess.run([sys.executable, str(ROOT / "outreach.py"), str(shortlist),
                    "-e", str(flat), "-o", str(out)], capture_output=True, text=True)
assert r.returncode == 0, r.stdout + r.stderr
h = out.read_text(encoding="utf-8")

a = lambda c, m: (_ for _ in ()).throw(AssertionError(m)) if not c else None
a("2 cards" in r.stdout, r.stdout)
a("1 entry(s) marked keep:false" in r.stdout, "keep:false omitted: " + r.stdout)
a("1 shortlist entry(s) matched no enriched lead" in r.stdout, "unmatched flagged: " + r.stdout)
print("join + counts        OK  (2 kept, 1 dropped, 1 unmatched flagged)")

a("&lt;script&gt;" in h and "<script>Döe" not in h, "name must be HTML-escaped")
a("Acme &amp; Co" in h, "ampersand escaped")
print("html escaping        OK  (script tag and & neutralised)")

a('href="https://www.linkedin.com/sales/lead/ACwAAAjane,NAME_SEARCH,TNTB"' in h, 'profile link present')
a('target="_blank" rel="noopener"' in h, "links open safely")
print("profile links        OK")

a("over the 300 connection-note limit" in h, "long note must be flagged")
a(h.count('class="count') >= 2, "char counts rendered")
print("note length warning  OK  (320-char note flagged)")

a("recent post(s)" in h and "pricing model" in h, "activity surfaced")
print("activity surfaced    OK  (posts shown as context)")

a("contacted.csv" in h and "localStorage" in h, "progress + export wired")
a("prefers-color-scheme: dark" in h, "dark mode")
print("worksheet features   OK  (progress, export, dark mode)")
print("\nOUTREACH TESTS PASSED")
