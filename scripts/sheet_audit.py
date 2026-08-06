#!/usr/bin/env python3
"""
Full-sheet audit — every consistency check we know about, in one pass.

Read-only. Prints a numbered list of findings, worst first, and exits non-zero if
anything is wrong so it can be used as a gate.

Usage:
    python sheet_audit.py
    python sheet_audit.py --today 2026-08-06     # pin "today" for reproducibility
"""
from __future__ import annotations

import argparse
import collections
import datetime
import re
import sys

import pipeline_health as ph
import sync_reports_to_sheet as sync

FORMULA_COLS = ["Days Since Last Touch", "Cadence Due", "Cadence Stage"]
ERROR_VALUES = ("#REF!", "#N/A", "#VALUE!", "#DIV/0!", "#NAME?", "#ERROR!", "#NUM!")

CANONICAL_CHANNELS = {"LinkedIn DM", "Connection Note", "InMail", "Email", "Both",
                      "Referral", "Inbound", "Skip"}

findings: list[tuple[str, str, list[str]]] = []


def finding(sev: str, title: str, detail: list[str]):
    findings.append((sev, title, detail))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--today")
    args = ap.parse_args()
    today = ph.parse_date(args.today) if args.today else datetime.date.today()

    svc = ph.read_service()
    sid = sync.load_config()["spreadsheet_id"]
    headers, rows = ph.fetch_rows(svc, sid)
    sh = ph.Sheet(headers, rows)
    n_rows = len(rows)
    print(f"Auditing {n_rows} leads x {len(headers)} columns, as of {today}\n")

    # ---------------------------------------------------------------- 1. formulas
    last = n_rows + 1
    bc, be = ph.col_letter(sh.idx[FORMULA_COLS[0]]), ph.col_letter(sh.idx[FORMULA_COLS[2]])
    raw = svc.spreadsheets().values().get(
        spreadsheetId=sid, range=f"Pipeline!{bc}2:{be}{last}",
        valueRenderOption="FORMULA").execute().get("values", [])
    val = svc.spreadsheets().values().get(
        spreadsheetId=sid, range=f"Pipeline!{bc}2:{be}{last}").execute().get("values", [])

    missing = [i + 2 for i, r in enumerate(raw)
               if len([x for x in (list(r) + ["", "", ""])[:3] if str(x).startswith("=")]) < 3]
    if missing:
        finding("HIGH", f"{len(missing)} rows missing a formula in {bc}:{be} "
                        f"(a wiped cell stops that row reporting)",
                [f"rows: {missing[:20]}"])

    errs = [(i + 2, c) for i, r in enumerate(val)
            for c in (list(r) + ["", "", ""])[:3] if str(c).strip() in ERROR_VALUES]
    if errs:
        finding("HIGH", f"{len(errs)} formula cells showing an error value", [str(errs[:10])])

    # ------------------------------------------------- 2. recompute BC / BD / BE
    mism_bc, mism_bd, mism_be = [], [], []
    for i, row in enumerate(sh.rows, start=2):
        got = (list(val[i - 2]) + ["", "", ""])[:3] if i - 2 < len(val) else ["", "", ""]
        lt = ph.last_touch(sh, row, today)
        exp_bc = str((today - lt).days) if lt else ""
        if got[0].strip() != exp_bc:
            mism_bc.append((i, sh.name(row), got[0], exp_bc))
        # BE: only verify the states we can derive unambiguously
        if ph.planned_touch(sh, row, today):
            exp_be = "SCHEDULED"
        elif ph.has_replied(sh, row):
            exp_be = "REPLIED"
        elif not lt:
            exp_be = ""
        elif ph.is_accepted(sh, row) and len(ph.touches(sh, row, today)) <= 1:
            exp_be = "ACCEPTED"
        else:
            exp_be = None                      # OVERDUE/T-due: covered by --overdue
        if exp_be is not None and exp_be not in got[2] and not (exp_be == "" and not got[2]):
            # a closed/skip row legitimately renders as an em dash
            if not (got[2].strip() in ("—", "") and exp_be == ""):
                mism_be.append((i, sh.name(row), got[2], exp_be))
    if mism_bc:
        finding("HIGH", f"{len(mism_bc)} rows where Days Since Last Touch disagrees "
                        f"with a recompute", [str(m) for m in mism_bc[:10]])
    if mism_be:
        finding("MED", f"{len(mism_be)} rows where Cadence Stage disagrees with a recompute",
                [str(m) for m in mism_be[:10]])

    negs = [(i + 2, c) for i, r in enumerate(val)
            for c in [(list(r) + [""])[0]] if c.strip().startswith("-")]
    if negs:
        finding("HIGH", f"{len(negs)} negative day counts", [str(negs[:10])])

    # ---------------------------------------------------- 3. date column hygiene
    unparseable, mixed = [], collections.Counter()
    for i, row in enumerate(sh.rows, start=2):
        for c in ph.TOUCH_DATE_COLS + ["Response Date", "Next Action Date", "Date Added"]:
            v = sh.get(row, c)
            if v and not ph.parse_date(v):
                unparseable.append((i, c, v[:24]))
    if unparseable:
        finding("MED", f"{len(unparseable)} date cells that do not parse as a date",
                [str(u) for u in unparseable[:10]])

    planned = [(i, sh.name(row)) for i, row in enumerate(sh.rows, start=2)
               if ph.planned_touch(sh, row, today)]
    if planned:
        finding("MED", f"{len(planned)} rows with a FUTURE date in a 'Follow-up N Date' "
                       f"column (belongs in Next Action Date)",
                [f"{i}: {n}" for i, n in planned[:8]] + ["fix: --fix-planned-fu --apply"])

    # ------------------------------------------------------- 4. status coherence
    contacted_no_date, sent_but_new, fu_claim_no_date, resp_no_send = [], [], [], []
    for i, row in enumerate(sh.rows, start=2):
        st, sent = sh.get(row, "Status"), sh.get(row, "DM / Email Sent Date")
        stl = st.lower()
        if re.search(r"sent|requested|connected|replied|interested", stl) and not sent:
            contacted_no_date.append((i, sh.name(row), st))
        if st == "New" and sent:
            sent_but_new.append((i, sh.name(row)))
        if "follow-up sent" in stl and not sh.get(row, "Follow-up 1 Date"):
            fu_claim_no_date.append((i, sh.name(row), st))
        if sh.get(row, "Response Date") and not sent:
            resp_no_send.append((i, sh.name(row), st))
    if contacted_no_date:
        finding("MED", f"{len(contacted_no_date)} rows whose status implies contact but "
                       f"DM / Email Sent Date is empty",
                [str(x) for x in contacted_no_date[:8]])
    if sent_but_new:
        finding("MED", f"{len(sent_but_new)} rows with a sent date but status still 'New'",
                [str(x) for x in sent_but_new[:8]])
    if fu_claim_no_date:
        finding("MED", f"{len(fu_claim_no_date)} rows whose status says a follow-up was "
                       f"sent but Follow-up 1 Date is empty (needs a human to confirm)",
                [str(x) for x in fu_claim_no_date[:12]])
    if resp_no_send:
        finding("LOW", f"{len(resp_no_send)} rows with a Response Date but no send date",
                [str(x) for x in resp_no_send[:8]])

    # --------------------------------------------------------- 5. undecided rows
    undecided = [i for i, row in enumerate(sh.rows, start=2)
                 if sh.get(row, "Status") == "New" and not sh.get(row, "Next Action")]
    if undecided:
        finding("MED", f"{len(undecided)} rows still at status 'New' with no decision "
                       f"attached", ["fix: --decide --apply"])

    # -------------------------------------------------------------- 6. dupes
    by_name, by_url, by_comp = (collections.defaultdict(list) for _ in range(3))
    for i, row in enumerate(sh.rows, start=2):
        if sh.name(row):
            by_name[ph.norm(sh.name(row))].append(i)
        u = ph.norm_url(sh.get(row, "LinkedIn URL"))
        if u:
            by_url[u].append(i)
        if sh.company(row) and sh.get(row, "Status").lower() not in (
                "skip", "not relevant", "on hold", "lost", "closed - not interested"):
            by_comp[ph.norm(sh.company(row))].append(i)
    for label, d, sev in (("duplicate person rows (same name)", by_name, "MED"),
                          ("duplicate LinkedIn URLs", by_url, "MED"),
                          ("companies with >1 live contact", by_comp, "LOW")):
        hits = {k: v for k, v in d.items() if len(v) > 1}
        if hits:
            finding(sev, f"{len(hits)} {label}",
                    [f"{k}: rows {v}" for k, v in list(hits.items())[:8]])

    # ------------------------------------------------------- 7. field validity
    bad_rating, bad_geo = [], []
    for i, row in enumerate(sh.rows, start=2):
        for c in ("Profile Rating (/10)", "Company Rating (/10)"):
            v = sh.get(row, c)
            if v and (not v.isdigit() or not 1 <= int(v) <= 10):
                bad_rating.append((i, c, v[:16]))
        r = sh.rating(row)
        if (r or 0) >= 6 and ph.geo_verdict(sh.get(row, "Location")) == "off-target" \
                and sh.get(row, "Status") == "New":
            bad_geo.append((i, sh.name(row), sh.get(row, "Location")))
    if bad_rating:
        finding("LOW", f"{len(bad_rating)} rating cells that are not a number 1-10",
                [str(x) for x in bad_rating[:8]])
    if bad_geo:
        finding("MED", f"{len(bad_geo)} undecided rows rated 6+ but out of target geo",
                [str(x) for x in bad_geo[:8]])

    # ---------------------------------------------- 8. channel label consistency
    chans = collections.Counter(sh.get(r, "Outreach Channel") for r in sh.rows
                                if sh.get(r, "Outreach Channel"))
    noncanon = {k: v for k, v in chans.items() if k not in CANONICAL_CHANNELS}
    if len(chans) > len(CANONICAL_CHANNELS) or noncanon:
        finding("MED", f"Outreach Channel has {len(chans)} distinct labels for "
                       f"{len(CANONICAL_CHANNELS)} real channels — breaks reply-rate analysis",
                [f"{k!r} x{v}" for k, v in sorted(noncanon.items(), key=lambda x: -x[1])[:10]])

    # ------------------------------------------------------ 9. data validation
    meta = svc.spreadsheets().get(
        spreadsheetId=sid, ranges=["Pipeline!A1:BE2"], includeGridData=True,
        fields="sheets(data(rowData(values(dataValidation))),protectedRanges)").execute()
    tab = meta["sheets"][0]
    vrow = tab["data"][0].get("rowData", [{}])[-1].get("values", [])
    dv_cols = []
    for i, v in enumerate(vrow):
        dv = v.get("dataValidation")
        if not dv:
            continue
        cond = dv.get("condition", {})
        opts = [x.get("userEnteredValue", "") for x in cond.get("values", [])]
        hdr = headers[i].strip() if i < len(headers) else ""
        # A dropdown is wrong on: free text, dates, formulas, or a list of long blobs
        junk = (any(len(o) > 60 for o in opts)
                or hdr in FORMULA_COLS
                or re.search(r"date|notes|reason|hook|name$|content", hdr, re.I)
                or len(opts) > 25)
        if junk:
            dv_cols.append(f"{ph.col_letter(i)} {hdr!r} ({len(opts)} options)")
    if dv_cols:
        finding("HIGH", f"{len(dv_cols)} columns carry a bad dropdown (free-text, date or "
                        f"formula columns should not have one)", dv_cols[:14])

    statuses = collections.Counter(sh.get(r, "Status") for r in sh.rows if sh.get(r, "Status"))
    status_dv = None
    for i, v in enumerate(vrow):
        if i < len(headers) and headers[i].strip() == "Status":
            dv = v.get("dataValidation") or {}
            status_dv = [x.get("userEnteredValue") for x in dv.get("condition", {}).get("values", [])]
    if status_dv is not None:
        outside = {s: c for s, c in statuses.items() if s not in status_dv}
        if outside:
            finding("HIGH", f"Status dropdown allows {len(status_dv)} values but "
                            f"{sum(outside.values())} rows across {len(outside)} other values "
                            f"violate it",
                    [f"allowed: {status_dv}"] +
                    [f"{k!r} x{v}" for k, v in sorted(outside.items(), key=lambda x: -x[1])[:8]])

    if not tab.get("protectedRanges"):
        finding("MED", "formula columns are not protected", ["fix: --protect --apply"])

    # -------------------------------------------------------------- 10. report
    order = {"HIGH": 0, "MED": 1, "LOW": 2}
    findings.sort(key=lambda f: order[f[0]])
    if not findings:
        print("No issues found.")
        return 0
    print(f"{len(findings)} issue groups found\n" + "=" * 74)
    for n, (sev, title, detail) in enumerate(findings, 1):
        print(f"\n{n}. [{sev}] {title}")
        for d in detail:
            print(f"      {d}")
    print("\n" + "=" * 74)
    print(collections.Counter(s for s, _, _ in findings))
    return 1


if __name__ == "__main__":
    sys.exit(main())
