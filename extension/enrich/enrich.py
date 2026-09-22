#!/usr/bin/env python3
"""Stage 3 — enrich filtered leads with profile, activity and company detail.

Reads the CSV that came back from filtering, fetches each profile, resolves and
caches each company once, and writes JSON. Safe to re-run: already-enriched
leads, permanently-failed leads and cached companies are all skipped.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import stage1
import suppress
from budget import Budget, BudgetExhausted
from csv_io import lead_key, lead_ref, read_filtered
from linkedin import Blocked, LinkedInClient, NotFound, Pacing
from parsers import current_company, parse_company, parse_insights, parse_profile
from store import Store

ACTIVITY_GIVE_UP_AFTER = 3


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_dotenv(path: Path) -> None:
    """Keeps session cookies out of shell history. Real env vars still win."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def load_cookies(args: argparse.Namespace) -> tuple[str, str]:
    load_dotenv(args.env)
    li_at = args.li_at or os.environ.get("LI_AT", "")
    jsessionid = args.jsessionid or os.environ.get("LI_JSESSIONID", "")
    if not li_at or not jsessionid:
        sys.exit(
            f"Missing cookies. Put them in {args.env}, export LI_AT and LI_JSESSIONID,\n"
            "or pass --li-at/--jsessionid.\n"
            "Get them from a logged-in linkedin.com tab: DevTools > Application > Cookies."
        )
    return li_at, jsessionid


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input", type=Path, help="filtered CSV")
    p.add_argument("-o", "--outdir", type=Path, default=Path("out"))
    p.add_argument("--leads", type=Path, metavar="JSON",
                   help="stage-1 leads.json; lead data is taken from here and the "
                        "CSV is used only to select rows")
    p.add_argument("--env", type=Path, default=Path(".env"),
                   help="file holding LI_AT / LI_JSESSIONID (default: .env)")
    p.add_argument("--min-delay", type=float, default=4.0)
    p.add_argument("--max-delay", type=float, default=9.0)
    p.add_argument("--max-fetches", type=int, default=400, help="ceiling for this run")
    p.add_argument("--daily-cap", type=int, default=500,
                   help="ceiling per UTC day, persisted across runs")
    p.add_argument("--limit", type=int, default=0, help="stop after N leads")
    p.add_argument("--suppress", type=Path, action="append", default=[],
                   metavar="FILE", help="CSV or text file of identifiers to skip; repeatable")
    p.add_argument("--retry-failed", action="store_true",
                   help="also retry leads that previously failed permanently")
    p.add_argument("--refresh-older-than", type=int, default=0, metavar="DAYS",
                   help="re-fetch leads enriched more than DAYS ago (0 = never)")
    p.add_argument("--activity", action="store_true",
                   help="also fetch recent posts (one extra request per lead)")
    p.add_argument("--dump-raw", action="store_true",
                   help="save the first response of each kind to out/raw/ for inspection")
    p.add_argument("--skip-companies", action="store_true")
    p.add_argument("--li-at")
    p.add_argument("--jsessionid")
    return p


def main() -> int:
    args = build_parser().parse_args()

    rows, skipped = read_filtered(args.input)
    if skipped:
        print(f"! {len(skipped)} row(s) had no usable identifier, lines: "
              f"{', '.join(map(str, skipped[:10]))}{' ...' if len(skipped) > 10 else ''}",
              file=sys.stderr)
    if not rows:
        sys.exit("No usable rows in the filtered CSV.")

    suppressed = suppress.load(args.suppress) if args.suppress else set()
    index = stage1.load_index(args.leads) if args.leads else {}
    store = Store(args.outdir)

    pending, n_suppressed, n_done, n_unmatched = [], 0, 0, 0
    for row in rows:
        if index:
            row, matched = stage1.merge(row, index, lead_key(row))
            if not matched:
                n_unmatched += 1
        key = lead_key(row) or ""
        if suppressed and suppress.is_suppressed(row, suppressed, lead_key(row)):
            n_suppressed += 1
        elif store.is_done(key, retry_failed=args.retry_failed,
                           refresh_days=args.refresh_older_than):
            n_done += 1
        else:
            pending.append(row)

    if index and n_unmatched:
        print(f"! {n_unmatched} filtered row(s) had no match in {args.leads.name} — "
              f"using CSV values for those", file=sys.stderr)

    if args.limit:
        pending = pending[:args.limit]

    budget = Budget(args.outdir / "budget.json", args.daily_cap)
    source = f" | joined to {args.leads.name}" if index else ""
    print(f"{len(rows)} filtered | {n_done} already done | {n_suppressed} suppressed "
          f"| {len(pending)} to fetch{source}")
    print(f"daily budget: {budget.used()}/{budget.daily_cap} used, {budget.remaining()} left")

    if not pending:
        print(f"Nothing to do. Flat export: {store.write_flat()}")
        return 0

    li_at, jsessionid = load_cookies(args)
    client = LinkedInClient(
        li_at, jsessionid,
        Pacing(min_delay=args.min_delay, max_delay=args.max_delay,
               max_fetches=args.max_fetches),
        budget=budget,
        dump_dir=(args.outdir / "raw") if args.dump_raw else None)

    done = failed = fetched = cached = reused = 0
    activity_on, activity_misses = args.activity, 0
    halted: str | None = None

    for index, row in enumerate(pending, start=1):
        key = lead_key(row) or ""
        ref = lead_ref(row)
        label = row.get("fullName") or key
        banked = store.banked_profile(key)

        try:
            if banked:
                profile = banked["profile"]
                company = banked.get("_companyRef")
                reused += 1
            else:
                profile = parse_profile(client.profile(ref))
                company = current_company(profile)
        except NotFound:
            store.put_lead(key, {**row, "stage": "failed", "error": "profile_not_found",
                                 "enrichedAt": now()})
            failed += 1
            store.flush()
            print(f"[{index}/{len(pending)}] {label} — not found (will not retry)",
                  file=sys.stderr)
            continue
        except (BudgetExhausted, Blocked) as exc:
            halted = str(exc)
            break

        # Bank the profile before spending anything further. If a later fetch is
        # blocked, the request already paid for is not thrown away.
        want_company = bool(company) and not args.skip_companies
        record = {
            **row,
            "linkedinUrl": profile.get("linkedinUrl") or row.get("linkedinUrl"),
            "vanityName": profile.get("vanityName"),
            "stage": "enriched",
            "companyKey": None,
            "profile": profile,
            "activity": banked.get("activity") if banked else None,
            "enrichedAt": now(),
            "error": None,
            "incomplete": (["activity"] if activity_on else []) + (["company"] if want_company else []),
            "_companyRef": company,
        }
        store.put_lead(key, record)
        store.flush()

        company_cached = False
        try:
            if activity_on and record["activity"] is None:
                try:
                    record["activity"] = parse_insights(client.insights(ref))
                    if not record["activity"]:
                        activity_misses += 1
                except NotFound:
                    activity_misses += 1
                if activity_misses >= ACTIVITY_GIVE_UP_AFTER:
                    activity_on = False
                    print(f"! no activity endpoint answered {activity_misses}x — "
                          f"disabling it for this run (see README: schema drift)",
                          file=sys.stderr)
            if "activity" in record["incomplete"]:
                record["incomplete"].remove("activity")

            if want_company:
                company_key = company["id"]
                record["companyKey"] = company_key
                company_cached = store.has_company(company_key)
                if company_cached:
                    cached += 1
                else:
                    try:
                        store.put_company(company_key, {
                            **parse_company(client.company(company_key)),
                            "fetchedAt": now(),
                        })
                        fetched += 1
                    except NotFound:
                        store.put_company(company_key, {
                            "id": company_key, "name": company.get("name"),
                            "error": "not_found", "fetchedAt": now(),
                        })
            if "company" in record["incomplete"]:
                record["incomplete"].remove("company")

        except (BudgetExhausted, Blocked) as exc:
            halted = str(exc)
            store.put_lead(key, record)
            store.flush()
            break

        record.pop("_companyRef", None)
        record.pop("incomplete", None)
        store.put_lead(key, record)
        store.flush()
        done += 1

        extras = ["profile reused"] if banked else []
        extras.append(f"{len(profile['experience'])} roles")
        if record["activity"]:
            extras.append(f"{len(record['activity'])} posts")
        if record["companyKey"]:
            extras.append("company cached" if company_cached else "company fetched")
        print(f"[{index}/{len(pending)}] {label} ({', '.join(extras)})")

    store.flush()
    flat = store.write_flat()

    reuse = f" | profiles reused {reused}" if reused else ""
    print(f"\nenriched {done} | failed {failed}{reuse} | "
          f"companies fetched {fetched}, cache hits {cached} | "
          f"requests {client.fetches} | daily {budget.used()}/{budget.daily_cap}")
    print(f"out: {store.leads_path}, {store.companies_path}, {flat}")

    if halted:
        print(f"\nHALTED: {halted}\n"
              "Progress is saved — re-run the same command to resume. "
              "Do not retry immediately.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
