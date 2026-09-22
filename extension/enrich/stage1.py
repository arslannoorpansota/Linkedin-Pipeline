"""Join filtered rows back to the stage-1 export.

The CSV's job is to say *which* leads survived filtering. The data itself comes
from the extension's JSON export, so a filter step that drops or rewrites
columns cannot quietly degrade the final output.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_PUBLIC_ID = re.compile(r"linkedin\.com/in/([^/?#]+)", re.I)

INDEX_FIELDS = ("profileId", "salesUrn", "memberId", "salesUrl")


def load_index(path: Path) -> dict[str, dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    leads = raw.get("leads", raw) if isinstance(raw, dict) else raw
    if not isinstance(leads, list):
        raise SystemExit(f"{path} does not look like a stage-1 export (no 'leads' array)")

    index: dict[str, dict] = {}
    for lead in leads:
        if not isinstance(lead, dict):
            continue
        for field in INDEX_FIELDS:
            value = lead.get(field)
            if isinstance(value, str) and value:
                index.setdefault(value, lead)
                match = _PUBLIC_ID.search(value)
                if match:
                    index.setdefault(match.group(1), lead)
    return index


def merge(row: dict[str, str], index: dict[str, dict], key: str | None) -> tuple[dict[str, Any], bool]:
    """Stage-1 values win where it has them; CSV fills the gaps.

    A null in the export must not blank out a value the CSV still carries.
    """
    base: dict | None = None
    for field in INDEX_FIELDS:
        value = (row.get(field) or "").strip()
        if value and value in index:
            base = index[value]
            break
    if base is None and key:
        base = index.get(key)

    if base is None:
        return dict(row), False

    merged = dict(row)
    merged.update({k: v for k, v in base.items() if v is not None and v != ""})
    return merged, True
