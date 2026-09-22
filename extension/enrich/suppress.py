"""Identifiers to skip — people already contacted, or explicitly excluded."""
from __future__ import annotations

import csv
import re
from pathlib import Path

_PROFILE_ID = re.compile(r"(?:lead/|\()(AC[A-Za-z0-9_-]{10,})", re.I)


def load(paths: list[Path]) -> set[str]:
    """Accepts .csv (any column named like an identifier) or newline-delimited text."""
    out: set[str] = set()
    for path in paths:
        if not path.exists():
            raise SystemExit(f"suppression file not found: {path}")
        if path.suffix.lower() == ".csv":
            with path.open(encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    for column in ("profileId", "salesUrn", "memberId", "salesUrl"):
                        value = (row.get(column) or "").strip()
                        if value:
                            out.add(value)
                            match = _PROFILE_ID.search(value)
                            if match:
                                out.add(match.group(1))
        else:
            for line in path.read_text(encoding="utf-8").splitlines():
                value = line.strip()
                if value and not value.startswith("#"):
                    out.add(value)
                    match = _PROFILE_ID.search(value)
                    if match:
                        out.add(match.group(1))
    return out


def is_suppressed(row: dict[str, str], suppressed: set[str], key: str | None) -> bool:
    if key and key in suppressed:
        return True
    return any(
        (row.get(c) or "").strip() in suppressed
        for c in ("profileId", "salesUrn", "memberId", "salesUrl")
        if (row.get(c) or "").strip()
    )
