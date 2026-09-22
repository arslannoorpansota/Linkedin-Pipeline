#!/usr/bin/env python3
"""Verify the filter step accounted for every lead.

Between export and enrichment a lead can go missing without anyone noticing.
This compares the original CSV against the filtered one (and decisions.json if
present) and fails loudly when the numbers do not reconcile.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from csv_io import lead_key


def identifiers(path: Path) -> tuple[list[str], int, int]:
    """Returns (identifiers, row count, rows with no identifier at all)."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    keys, anonymous = [], 0
    for row in rows:
        key = lead_key(row)
        if key:
            keys.append(key)
        else:
            anonymous += 1
    return keys, len(rows), anonymous


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("original", type=Path, help="leads.csv from the extension")
    parser.add_argument("filtered", type=Path, help="leads_filtered.csv from the filter step")
    parser.add_argument("-d", "--decisions", type=Path, help="decisions.json, if written")
    args = parser.parse_args()

    before, n_before, anon_before = identifiers(args.original)
    after, n_after, anon_after = identifiers(args.filtered)

    before_set, after_set = set(before), set(after)
    problems: list[str] = []

    for name, keys, unique, anonymous in (
        (args.original.name, before, len(before_set), anon_before),
        (args.filtered.name, after, len(set(after)), anon_after),
    ):
        if len(keys) != unique:
            problems.append(f"{len(keys) - unique} duplicate identifier(s) in {name}")
        if anonymous:
            problems.append(f"{anonymous} row(s) in {name} have no identifier at all")

    invented = after_set - before_set
    if invented:
        problems.append(
            f"{len(invented)} row(s) in {args.filtered.name} are not in the original "
            f"— the filter altered identifiers: {', '.join(list(invented)[:3])}")

    print(f"original : {n_before}")
    print(f"filtered : {n_after}  (kept {len(after_set & before_set)}, "
          f"dropped {len(before_set - after_set)})")

    if args.decisions and args.decisions.exists():
        decisions = json.loads(args.decisions.read_text(encoding="utf-8"))
        rows = {d.get("row") for d in decisions if isinstance(d, dict)}
        missing = set(range(1, n_before + 1)) - rows
        keeps = sum(1 for d in decisions if d.get("keep"))
        print(f"decisions: {len(decisions)} entries, {keeps} keep")
        if missing:
            preview = ", ".join(map(str, sorted(missing)[:10]))
            problems.append(
                f"{len(missing)} row(s) have no decision — rows {preview}"
                f"{' ...' if len(missing) > 10 else ''}")
        if keeps != n_after:
            problems.append(f"decisions say keep {keeps} but filtered CSV has {n_after} rows")

    if problems:
        print("\nFAILED:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    print("\nOK — every lead accounted for.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
