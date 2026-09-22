"""Read the filtered CSV back, keyed on Sales Navigator identifiers.

Sales Navigator search results never carry a public vanity id, so the durable
key is the profileId/authType/authToken triple embedded in the lead's URN.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import NamedTuple

KEY_COLUMNS = ("profileId", "salesUrn", "salesUrl", "memberId")

_URN = re.compile(r"\(([^,]+),([^,]+),([^)]*)\)")
_SALES_URL = re.compile(r"/sales/lead/([^,/?#]+),([^,/?#]+),([^,/?#]+)", re.I)


class LeadRef(NamedTuple):
    profile_id: str
    auth_type: str
    auth_token: str

    @property
    def urn(self) -> str:
        return f"urn:li:fs_salesProfile:({self.profile_id},{self.auth_type},{self.auth_token})"

    @property
    def path_key(self) -> str:
        return f"(profileId:{self.profile_id},authType:{self.auth_type},authToken:{self.auth_token})"


def lead_ref(row: dict[str, str]) -> LeadRef | None:
    """profileId alone is not enough — the API needs the auth pair alongside it."""
    for column in ("salesUrn", "salesUrl"):
        value = (row.get(column) or "").strip()
        if not value:
            continue
        match = _URN.search(value) or _SALES_URL.search(value)
        if match:
            return LeadRef(match.group(1), match.group(2), match.group(3))

    profile_id = (row.get("profileId") or "").strip()
    if profile_id:
        return LeadRef(profile_id, "NAME_SEARCH", "")
    return None


def lead_key(row: dict[str, str]) -> str | None:
    ref = lead_ref(row)
    if ref:
        return ref.profile_id
    for column in KEY_COLUMNS:
        value = (row.get(column) or "").strip()
        if value:
            return value
    return None


def read_filtered(path: Path) -> tuple[list[dict[str, str]], list[int]]:
    """Returns (usable rows, line numbers of rows with no usable identifier)."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    if rows and not any(c in rows[0] for c in KEY_COLUMNS):
        raise SystemExit(
            f"{path} has no identifier column. Expected one of: {', '.join(KEY_COLUMNS)}.\n"
            f"Found: {', '.join(rows[0].keys())}"
        )

    usable, skipped = [], []
    for index, row in enumerate(rows, start=2):
        if lead_ref(row):
            usable.append(row)
        else:
            skipped.append(index)
    return usable, skipped
