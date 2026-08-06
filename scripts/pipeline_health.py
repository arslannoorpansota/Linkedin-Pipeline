#!/usr/bin/env python3
"""
Pipeline health — surface stalls, dupes and undecided rows without scanning the sheet.

Implements the enforcement side of agents/CADENCE.md:
  --overdue           leads with no reply whose next cadence touch is past due
  --undecided         status=New rows that still need a send/skip decision
  --check-dupes       name / LinkedIn-URL / company collisions (pre-research gate)
  --install-formulas  add the live "Days Since Last Touch" / "Cadence Due" /
                      "Cadence Stage" formula columns to the Pipeline tab
  --decide            attach a decision to every status=New row
  --fix-planned-fu    clear future dates parked in a "Follow-up N Date" column
  --all               every read-only report above

Read-only by default. --install-formulas writes; --decide and --fix-planned-fu
are dry-run until you add --apply.

Usage:
    python pipeline_health.py --all
    python pipeline_health.py --overdue --csv /tmp/overdue.csv
    python pipeline_health.py --install-formulas
    python pipeline_health.py --fix-planned-fu --apply
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime
import re
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import sync_reports_to_sheet as sync

SCRIPT_DIR = Path(__file__).resolve().parent
TAB = "Pipeline"
READ_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Cadence gaps from CADENCE.md §3: wait N days after touch #index before the next one.
# 1 touch done -> 3 days, 2 -> 5, 3 -> 7, 4 -> cadence complete (park).
CADENCE_GAPS = {1: 3, 2: 5, 3: 7}
PARK_AFTER_DAYS = 45

TOUCH_DATE_COLS = [
    "DM / Email Sent Date",
    "Follow-up 1 Date",
    "Follow-up 2 Date",
    "Follow-up 3 Date",
]
# Statuses that are off-cadence: decided, dead, or now a live conversation.
CLOSED_STATUSES = {
    "skip", "not relevant", "lost", "won", "on hold", "new", "",
}
REPLIED_MARKERS = {"replied", "interested", "call scheduled", "negotiating",
                   "proposal sent", "in conversation"}

# Canonical target geography — CADENCE.md §5. Matched against the Location column
# so an out-of-target lead can never reach the send queue on rating alone.
TARGET_GEO = [
    "united states", "usa", ", us", "u.s.", "canada", "australia", "new zealand",
    "singapore", "united arab emirates", "uae", "dubai", "abu dhabi",
    "saudi", "ksa", "riyadh", "ireland", "dublin",
]
OFF_TARGET_GEO = [
    "pakistan", "karachi", "lahore", "islamabad", "india", "bengaluru", "bangalore",
    "mumbai", "delhi", "israel", "tel aviv", "united kingdom", "london", "england",
    "germany", "berlin", "france", "paris", "spain", "netherlands", "amsterdam",
    "poland", "ukraine", "romania", "brazil", "mexico", "argentina", "colombia",
    "guatemala", "panama", "nigeria", "kenya", "egypt", "philippines", "indonesia",
    "vietnam", "malaysia", "china", "japan", "korea", "turkey", "italy", "sweden",
    "switzerland", "portugal", "greece", "czech", "hungary", "bulgaria",
]
# LinkedIn often gives a metro instead of a state ("Greater Boston", "SF Bay Area").
US_METROS = [
    "san francisco bay area", "greater boston", "greater cleveland", "greater chicago",
    "greater seattle", "greater houston", "greater philadelphia", "greater pittsburgh",
    "greater minneapolis", "greater indianapolis", "greater sacramento",
    "greater phoenix", "greater tampa", "greater orlando", "greater st. louis",
    "miami-fort lauderdale", "dallas-fort worth", "new york city metropolitan area",
    "washington dc-baltimore area", "los angeles metropolitan area",
    "atlanta metropolitan area", "denver metropolitan area", "austin, texas metropolitan",
    "greater toronto area", "greater vancouver", "greater montreal", "greater sydney",
    "greater melbourne", "greater brisbane", "greater perth",
]
# Two-letter US/CA state or province suffix, e.g. "Austin, TX" / "Toronto, ON".
US_CA_STATE = re.compile(
    r",\s*(a[klrzb]|c[aot]|d[ce]|fl|ga|hi|i[adln]|k[sy]|la|m[adeinost]|"
    r"n[cdehjmvy]|o[hkr]|pa|ri|s[cd]|t[nx]|ut|v[at]|w[aivy]|"
    r"ab|bc|mb|nb|nl|ns|nt|nu|on|pe|qc|sk|yt)\b", re.I)


def geo_verdict(location: str) -> str:
    """'target' | 'off-target' | 'unknown' — company-HQ test, per CADENCE.md §5."""
    loc = location.strip().lower()
    if not loc:
        return "unknown"
    # Word-boundary match: plain substrings put "Indiana"/"Indianapolis" in India
    # and "Greater Boston" nowhere.
    def hit(terms):
        return any(re.search(rf"(?<![a-z]){re.escape(t)}(?![a-z])", loc) for t in terms)
    if hit(OFF_TARGET_GEO):
        return "off-target"
    if hit(TARGET_GEO) or US_CA_STATE.search(loc) or hit(US_METROS):
        return "target"
    return "unknown"


# ---------------------------------------------------------------- sheet access

def read_service():
    creds = Credentials.from_authorized_user_file(str(sync.TOKEN_FILE), READ_SCOPES)
    if not creds.valid:
        creds.refresh(Request())
        sync.TOKEN_FILE.write_text(creds.to_json())
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def fetch_rows(service, sid: str) -> tuple[list[str], list[list[str]]]:
    resp = service.spreadsheets().values().get(spreadsheetId=sid, range=TAB).execute()
    rows = resp.get("values", [])
    return rows[0], rows[1:]


def col_letter(idx: int) -> str:
    """0-based column index -> A1 letter (0 -> A, 26 -> AA)."""
    out = ""
    n = idx + 1
    while n:
        n, rem = divmod(n - 1, 26)
        out = chr(65 + rem) + out
    return out


# ---------------------------------------------------------------- row helpers

class Sheet:
    def __init__(self, headers: list[str], rows: list[list[str]]):
        self.headers = headers
        self.rows = rows
        self.idx = {h.strip(): i for i, h in enumerate(headers) if h.strip()}

    def get(self, row: list[str], key: str) -> str:
        i = self.idx.get(key)
        if i is None or i >= len(row):
            return ""
        return row[i].strip()

    def name(self, row) -> str:
        return self.get(row, "Full Name") or self.get(row, "Lead Name")

    def company(self, row) -> str:
        return self.get(row, "Company") or self.get(row, "Company Name")

    def rating(self, row):
        for k in ("Profile Rating (/10)", "Lead Score"):
            m = re.search(r"\d+", self.get(row, k))
            if m:
                return int(m.group())
        return None


def parse_date(s: str):
    s = s.strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%b %d, %Y"):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def touches(sh: Sheet, row, today: datetime.date | None = None) -> list[datetime.date]:
    """Completed touches only. A future date in a 'sent' column is a PLANNED touch
    (it belongs in Next Action Date) and must not count, or last-touch lands in the
    future and days-since-touch goes negative."""
    today = today or datetime.date.today()
    got = [parse_date(sh.get(row, c)) for c in TOUCH_DATE_COLS]
    return sorted(d for d in got if d and d <= today)


def planned_touch(sh: Sheet, row, today: datetime.date | None = None):
    """A future-dated follow-up column = a scheduled touch that hasn't happened."""
    today = today or datetime.date.today()
    got = [parse_date(sh.get(row, c)) for c in TOUCH_DATE_COLS]
    future = [d for d in got if d and d > today]
    return max(future) if future else None


def last_touch(sh: Sheet, row, today: datetime.date | None = None):
    t = touches(sh, row, today)
    resp = parse_date(sh.get(row, "Response Date"))
    if resp and resp <= (today or datetime.date.today()):
        t.append(resp)
    return max(t) if t else None


REAL_REPLY_RE = re.compile(r"positive|negative|neutral|not a fit", re.I)
REPLIED_STATUS_RE = re.compile(
    r"replied|interested|call scheduled|negotiating|proposal|in conversation", re.I)
ACCEPTED_RE = re.compile(r"accept|^connected", re.I)


def has_replied(sh: Sheet, row) -> bool:
    """A genuine message reply. A connection ACCEPT is not a reply — it is the
    trigger for touch 2. Treating any Response Date as a reply hid 14 leads that
    accepted and never got a DM (some for 42 days)."""
    if REAL_REPLY_RE.search(sh.get(row, "Response Type")):
        return True
    return bool(REPLIED_STATUS_RE.search(sh.get(row, "Status")))


def is_accepted(sh: Sheet, row) -> bool:
    """They accepted the connection request -> T2 is due immediately (CADENCE.md §3)."""
    blob = f"{sh.get(row, 'Response Type')} {sh.get(row, 'Status')}"
    return bool(ACCEPTED_RE.search(blob.strip()))


# A rating justified mainly by network/referral value is a Type-B/C partner lead, not
# a direct client. CLAUDE.md §5's single-motion rule says don't run that track next to
# Type A — so these must not silently enter the direct-client send queue.
CONNECTOR_RE = re.compile(
    r"connector|referral|gateway|ecosystem|community-build|type-b|"
    r"\bvc\b|angel investor|portfolio", re.I)


def is_connector_rated(sh: "Sheet", row) -> bool:
    return bool(CONNECTOR_RE.search(sh.get(row, "Rating Reason")))


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def norm_url(s: str) -> str:
    s = s.strip().lower().split("?")[0].rstrip("/")
    m = re.search(r"linkedin\.com/(?:in|sales/lead)/([^/]+)", s)
    return m.group(1) if m else ""


# ---------------------------------------------------------------- reports

def report_overdue(sh: Sheet, today: datetime.date, out_csv: Path | None):
    late = []
    for n, row in enumerate(sh.rows, start=2):
        status = sh.get(row, "Status")
        if status.strip().lower() in CLOSED_STATUSES or has_replied(sh, row):
            continue
        if planned_touch(sh, row, today):
            continue          # next touch already scheduled — not overdue
        lt = last_touch(sh, row, today)
        if not lt:
            continue
        done = len(touches(sh, row, today))
        accepted = is_accepted(sh, row)
        age = (today - lt).days
        if done >= 4 or age >= PARK_AFTER_DAYS:
            stage, due_in = "PARK", 0
        elif accepted and done <= 1:
            stage, due_in = "T2 (ACCEPTED)", 0   # accept means send it now
        else:
            gap = CADENCE_GAPS.get(done, 7)
            stage, due_in = f"T{done + 1}", gap
        if age > due_in:
            late.append({
                "row": n, "days_since_touch": age, "next_touch": stage,
                "name": sh.name(row), "company": sh.company(row),
                "rating": sh.rating(row) or "", "status": status,
                "linkedin": sh.get(row, "LinkedIn URL"),
            })
    # Accepted-and-never-DM'd first: warmest leads in the pipeline.
    late.sort(key=lambda r: (r["next_touch"] != "T2 (ACCEPTED)",
                             -(r["rating"] or 0), -r["days_since_touch"]))

    print(f"\n=== OVERDUE — no reply, next touch past due ({len(late)} leads) ===")
    print(f"{'row':>5} {'days':>5} {'next':>5} {'r':>2}  {'name':26} {'company':24} status")
    for r in late[:40]:
        print(f"{r['row']:>5} {r['days_since_touch']:>5} {r['next_touch']:>5} "
              f"{r['rating'] or '-':>2}  {r['name'][:26]:26} {r['company'][:24]:24} {r['status']}")
    if len(late) > 40:
        print(f"  … {len(late) - 40} more")
    by_stage = collections.Counter(r["next_touch"] for r in late)
    print("  by next touch:", dict(sorted(by_stage.items())))
    if out_csv and late:
        write_csv(out_csv, late)
    return late


def report_undecided(sh: Sheet, out_csv: Path | None):
    buckets = collections.defaultdict(list)
    for n, row in enumerate(sh.rows, start=2):
        if sh.get(row, "Status") != "New":
            continue
        r = sh.rating(row)
        geo = geo_verdict(sh.get(row, "Location"))
        rec = {
            "row": n, "rating": r or "", "name": sh.name(row),
            "company": sh.company(row), "title": sh.get(row, "Title"),
            "location": sh.get(row, "Location"), "geo": geo,
            "degree": sh.get(row, "Connection Degree"),
            "has_hook": "yes" if sh.get(row, "Hook / Why Outreach").strip() else "NO",
            "hook": sh.get(row, "Hook / Why Outreach")[:80],
            "linkedin": sh.get(row, "LinkedIn URL"),
        }
        if r is None:
            buckets["unrated"].append(rec)
        elif r < 6:
            buckets["<6"].append(rec)
        elif geo == "off-target":
            buckets["geo-skip"].append(rec)   # rating can't override geo
        elif is_connector_rated(sh, row):
            buckets["connector"].append(rec)  # Type-B/C — not this motion
        else:
            buckets["7+" if r >= 7 else "6"].append(rec)

    total = sum(len(v) for v in buckets.values())
    print(f"\n=== UNDECIDED — status=New, research done, no decision ({total} leads) ===")
    print(f"  7+ direct-client (send note now): {len(buckets['7+'])}")
    print(f"  6  direct-client (send note):     {len(buckets['6'])}")
    print(f"  <6 (mark Skip today):             {len(buckets['<6'])}")
    print(f"  6+ but OFF-TARGET GEO (skip):     {len(buckets['geo-skip'])}")
    print(f"  6+ rated for CONNECTOR value:     {len(buckets['connector'])}  <- Type-B/C, not this motion")
    print(f"  unrated (needs rating):           {len(buckets['unrated'])}")
    if buckets["geo-skip"]:
        print("    geo: " + "; ".join(f"{r['name']} ({r['location']})" for r in buckets["geo-skip"][:6]))

    send = sorted(buckets["7+"] + buckets["6"], key=lambda r: -(r["rating"] or 0))
    no_hook = sum(1 for r in send if r["has_hook"] == "NO")
    print(f"\n  --- SEND QUEUE (direct client, in geo): {len(send)} ---")
    print(f"      {no_hook} of {len(send)} have NO hook recorded — hooks must be verifiable")
    print(f"      (CLAUDE.md §9), so gather the hook before writing the note.")
    for r in send[:40]:
        flag = "" if r["geo"] == "target" else f"  [geo?{r['location'][:14]}]"
        hk = "" if r["has_hook"] == "yes" else "  [no hook]"
        print(f"  {r['row']:>5} r{r['rating']:<2} {r['name'][:22]:22} {r['company'][:20]:20} "
              f"{r['location'][:16]:16} {r['degree'][:3]:3}{hk}{flag}")
    if len(send) > 40:
        print(f"  … {len(send) - 40} more")
    if out_csv and send:
        write_csv(out_csv, send)
    return send


def report_dupes(sh: Sheet):
    by_name, by_url, by_company = (collections.defaultdict(list) for _ in range(3))
    for n, row in enumerate(sh.rows, start=2):
        rec = (n, sh.name(row), sh.company(row), sh.get(row, "Status"))
        if sh.name(row):
            by_name[norm(sh.name(row))].append(rec)
        u = norm_url(sh.get(row, "LinkedIn URL"))
        if u:
            by_url[u].append(rec)
        if sh.company(row) and sh.get(row, "Status").strip().lower() not in ("skip", "not relevant"):
            by_company[norm(sh.company(row))].append(rec)

    print("\n=== DUPLICATE / COLLISION CHECK ===")
    for label, d, note in (
        ("same person, >1 row (by name)", by_name, "merge — keep the decided row"),
        ("same LinkedIn URL, >1 row", by_url, "merge — same profile"),
        ("same company, >1 live contact", by_company, "do NOT cold-contact both"),
    ):
        hits = {k: v for k, v in d.items() if len(v) > 1}
        print(f"\n  {label}: {len(hits)}  ({note})")
        for k, v in sorted(hits.items(), key=lambda x: -len(x[1]))[:12]:
            who = ", ".join(sorted({x[1] for x in v}))
            print(f"    rows {[x[0] for x in v]}  {who[:60]}")
    return None


def decide_undecided(service, sid: str, sh: Sheet, today: datetime.date, apply: bool):
    """Attach a decision to every status=New row so nothing sits undecided.

    <6 / off-geo -> Skip.  6+ direct client -> queued for a connection note.
    6+ connector-rated -> parked as Type-B/C (single-motion rule, CLAUDE.md §5).
    Writes only Status / Next Action / Next Action Date. Dry-run unless apply=True.
    """
    plan = []
    for n, row in enumerate(sh.rows, start=2):
        if sh.get(row, "Status") != "New":
            continue
        r = sh.rating(row)
        geo = geo_verdict(sh.get(row, "Location"))
        if r is None:
            continue
        if r < 6:
            new = ("Skip", "None - skip, do not contact (rating <6)", today)
        elif geo == "off-target":
            new = ("Skip", f"None - skip, off-target geo ({sh.get(row, 'Location')})", today)
        elif is_connector_rated(sh, row):
            new = ("On Hold", "Type-B/C connector - park, single-motion rule", today)
        else:
            new = ("New", "Send connection request", today)
        plan.append((n, new))

    counts = collections.Counter(p[1][0] + " / " + p[1][1][:34] for p in plan)
    print(f"\n=== DECIDE UNDECIDED ({'APPLYING' if apply else 'DRY RUN'}) — {len(plan)} rows ===")
    for k, v in counts.most_common():
        print(f"  {v:5}  {k}")
    if not apply:
        print("  (no write — add --apply to commit these decisions)")
        return

    sc, nac, nad = (col_letter(sh.idx[k]) for k in ("Status", "Next Action", "Next Action Date"))
    data = []
    for n, (status, action, date) in plan:
        data.append({"range": f"{TAB}!{sc}{n}", "values": [[status]]})
        data.append({"range": f"{TAB}!{nac}{n}", "values": [[action]]})
        data.append({"range": f"{TAB}!{nad}{n}", "values": [[date.isoformat()]]})
    for i in range(0, len(data), 900):   # keep each batch well under API limits
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=sid,
            body={"valueInputOption": "USER_ENTERED", "data": data[i:i + 900]},
        ).execute()
        print(f"  wrote {min(i + 900, len(data))}/{len(data)} cells")
    print("  done")


def fix_planned_fu(service, sid: str, sh: Sheet, today: datetime.date, apply: bool):
    """Clear future dates wrongly parked in a 'Follow-up N Date' column.

    Those columns mean "FU was SENT on this date". A planned date there makes the
    lead look like it has an extra completed touch. Only clears when the same date
    is already recorded in Next Action Date, so no information is lost. Follow-up
    Notes are left untouched.
    """
    plan = []
    for n, row in enumerate(sh.rows, start=2):
        nad = parse_date(sh.get(row, "Next Action Date"))
        for c in TOUCH_DATE_COLS:
            if c == "DM / Email Sent Date":
                continue
            d = parse_date(sh.get(row, c))
            if d and d > today and nad == d:      # safe: date preserved elsewhere
                plan.append((n, c, d, sh.name(row)))

    print(f"\n=== FIX PLANNED FOLLOW-UP DATES ({'APPLYING' if apply else 'DRY RUN'}) "
          f"— {len(plan)} cells ===")
    for n, c, d, nm in plan:
        print(f"  row {n:5} clear {c} = {d}  ({nm[:24]}) — kept in Next Action Date")
    if not plan:
        return
    if not apply:
        print("  (no write — add --apply to clear these cells)")
        return
    data = [{"range": f"{TAB}!{col_letter(sh.idx[c])}{n}", "values": [[""]]}
            for n, c, _, _ in plan]
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=sid,
        body={"valueInputOption": "USER_ENTERED", "data": data},
    ).execute()
    print(f"  cleared {len(data)} cells")


def write_csv(path: Path, records: list[dict]):
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(records[0].keys()))
        w.writeheader()
        w.writerows(records)
    print(f"  -> wrote {len(records)} rows to {path}")


# ---------------------------------------------------------------- formulas

def install_formulas(service, sid: str, sh: Sheet, dry_run: bool):
    """Append three live formula columns so stalls surface without scanning rows."""
    need = ["Days Since Last Touch", "Cadence Due", "Cadence Stage"]
    existing = {h.strip(): i for i, h in enumerate(sh.headers) if h.strip()}
    start = len(sh.headers)
    plan = []
    for i, h in enumerate(need):
        plan.append((h, existing[h] if h in existing else start + len(plan)))

    def cell(key: str, r: int) -> str:
        return f"{col_letter(sh.idx[key])}{r}"

    # A date column may hold a real date OR ISO text, so take the max of both readings.
    def dnum(key: str, r: int) -> str:
        c = cell(key, r)
        return f"MAX(N({c}),IFERROR(DATEVALUE({c}),0))"

    last_row = len(sh.rows) + 1
    updates = []
    for header, cidx in plan:
        letter = col_letter(cidx)
        updates.append({"range": f"{TAB}!{letter}1", "values": [[header]]})
        col = []
        for r in range(2, last_row + 1):
            # A future date in a "sent" column is a PLANNED touch, not a completed
            # one. Counting it made last-touch land in the future and BC go negative
            # (16 rows had a planned FU1 of 2026-08-07/08-13). Only elapsed dates
            # count as touches; the planned date surfaces as SCHEDULED instead.
            def past(k, _r=r):
                d = dnum(k, _r)
                return f"IF({d}>TODAY(),0,{d})"

            resp = dnum("Response Date", r)
            status = cell("Status", r)
            # last  = OUR last send — drives the cadence gap (BD/BE).
            # last_any = last activity on the thread, including THEIR reply — drives
            # BC. A reply is the most recent event, so it sets the staleness clock;
            # 12 rows were counting from our older send date instead (Ryan Fortin
            # showed 43 when the reply was 37 days ago).
            last = f"MAX({','.join(past(k) for k in TOUCH_DATE_COLS)})"
            last_any = f"MAX({last},{past('Response Date')})"
            n_touch = "+".join(f"IF({past(k)}>0,1,0)" for k in TOUCH_DATE_COLS)
            planned = f"MAX({','.join(dnum(k, r) for k in TOUCH_DATE_COLS)})"
            rtype = cell("Response Type", r)
            # A connection ACCEPT is not a reply. Keying off "any Response Date"
            # marked 26 accepts as REPLIED and hid 14 leads that accepted and never
            # got a DM. Only a real message reply takes a lead off cadence.
            replied = (f'OR(REGEXMATCH(LOWER({rtype}&""),"positive|negative|neutral|not a fit"),'
                       f'REGEXMATCH(LOWER({status}&""),'
                       f'"replied|interested|call scheduled|negotiating|proposal|in conversation"))')
            accepted = f'REGEXMATCH(LOWER({rtype}&" "&{status}&""),"accept|connected")'
            closed = f"REGEXMATCH(LOWER({status}&\"\"),\"^(skip|not relevant|lost|won|on hold|new)?$|^skip|not relevant|lost|won|on hold\")"

            if header == "Days Since Last Touch":
                f = f'=IF({last_any}=0,"",TODAY()-{last_any})'
            elif header == "Cadence Due":
                # A planned date beats the computed one — it's the operator's intent.
                # An accept with no DM yet is due immediately (gap 0).
                f = (f'=IF({planned}>TODAY(),{planned},'
                     f'IF(OR({last}=0,{replied},{closed},({n_touch})>=4),"",'
                     f'IF(AND({accepted},({n_touch})<=1),{last_any},'
                     f'{last}+IFS(({n_touch})=1,3,({n_touch})=2,5,TRUE,7))))')
            else:  # Cadence Stage
                f = (f'=IF(AND({last}=0,NOT({planned}>TODAY())),"",'
                     f'IF({replied},"REPLIED",IF({closed},"—",'
                     f'IF({planned}>TODAY(),"SCHEDULED "&TEXT({planned},"mmm d"),'
                     f'IF(({n_touch})>=4,"PARK",'
                     # Accepted but no DM yet: T2 is due now, however long it has sat.
                     f'IF(AND({accepted},({n_touch})<=1),"ACCEPTED - SEND T2",'
                     f'IF(TODAY()-{last}>IFS(({n_touch})=1,3,({n_touch})=2,5,TRUE,7),'
                     f'"OVERDUE T"&(({n_touch})+1),"T"&(({n_touch})+1)&" due "&TEXT({last}+IFS(({n_touch})=1,3,({n_touch})=2,5,TRUE,7),"mmm d"))))))))')
            col.append([f])
        updates.append({"range": f"{TAB}!{letter}2:{letter}{last_row}", "values": col})

    cols = ", ".join(f"{h} -> {col_letter(i)}" for h, i in plan)
    print(f"\n=== INSTALL FORMULAS ({'DRY RUN' if dry_run else 'WRITING'}) ===")
    print(f"  columns: {cols}")
    print(f"  rows 2..{last_row}")
    print(f"  sample: {updates[1]['values'][0][0][:150]}…")
    if dry_run:
        print("  (no write — drop --dry-run to apply)")
        return
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=sid,
        body={"valueInputOption": "USER_ENTERED", "data": updates},
    ).execute()
    set_number_formats(service, sid, {h: i for h, i in plan}, last_row)
    print("  done — sort or filter on 'Cadence Stage' to work the queue")


def set_number_formats(service, sid: str, cols: dict[str, int], last_row: int):
    """Without this, the day-count in 'Days Since Last Touch' inherits a date format
    and renders as 2/10/1900, and 'Cadence Due' renders as the raw serial 46201."""
    meta = service.spreadsheets().get(spreadsheetId=sid, fields="sheets.properties").execute()
    gid = next(s["properties"]["sheetId"] for s in meta["sheets"]
               if s["properties"]["title"] == TAB)
    want = {
        "Days Since Last Touch": {"type": "NUMBER", "pattern": "0"},
        "Cadence Due": {"type": "DATE", "pattern": "yyyy-mm-dd"},
        "Cadence Stage": {"type": "TEXT", "pattern": "@"},
    }
    reqs = []
    for header, fmt in want.items():
        if header not in cols:
            continue
        reqs.append({"repeatCell": {
            "range": {"sheetId": gid, "startRowIndex": 1, "endRowIndex": last_row,
                      "startColumnIndex": cols[header], "endColumnIndex": cols[header] + 1},
            "cell": {"userEnteredFormat": {"numberFormat": fmt}},
            "fields": "userEnteredFormat.numberFormat",
        }})
    if reqs:
        service.spreadsheets().batchUpdate(
            spreadsheetId=sid, body={"requests": reqs}).execute()
        print(f"  number formats applied to {len(reqs)} columns")


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--overdue", action="store_true")
    ap.add_argument("--undecided", action="store_true")
    ap.add_argument("--check-dupes", action="store_true")
    ap.add_argument("--install-formulas", action="store_true")
    ap.add_argument("--fix-planned-fu", action="store_true",
                    help="clear future dates parked in Follow-up N Date (dry-run unless --apply)")
    ap.add_argument("--decide", action="store_true",
                    help="attach a decision to every status=New row (dry-run unless --apply)")
    ap.add_argument("--apply", action="store_true", help="with --decide: actually write")
    ap.add_argument("--all", action="store_true", help="all read-only reports")
    ap.add_argument("--dry-run", action="store_true", help="with --install-formulas")
    ap.add_argument("--csv", type=Path, help="write the queue to CSV")
    ap.add_argument("--today", help="override today (YYYY-MM-DD)")
    args = ap.parse_args()

    if not any([args.overdue, args.undecided, args.check_dupes,
                args.install_formulas, args.decide, args.fix_planned_fu, args.all]):
        ap.print_help()
        return 1

    today = parse_date(args.today) if args.today else datetime.date.today()
    cfg = sync.load_config()
    service = read_service()
    headers, rows = fetch_rows(service, cfg["spreadsheet_id"])
    sh = Sheet(headers, rows)
    print(f"Pipeline: {len(rows)} leads, {len(headers)} columns, as of {today}")

    if args.overdue or args.all:
        report_overdue(sh, today, args.csv if args.overdue else None)
    if args.undecided or args.all:
        report_undecided(sh, args.csv if args.undecided else None)
    if args.check_dupes or args.all:
        report_dupes(sh)
    if args.install_formulas:
        install_formulas(service, cfg["spreadsheet_id"], sh, args.dry_run)
    if args.fix_planned_fu:
        fix_planned_fu(service, cfg["spreadsheet_id"], sh, today, args.apply)
    if args.decide:
        decide_undecided(service, cfg["spreadsheet_id"], sh, today, args.apply)
    return 0


if __name__ == "__main__":
    sys.exit(main())
