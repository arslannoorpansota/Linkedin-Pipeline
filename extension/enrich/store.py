"""Resumable JSON store. Every write is atomic so a kill mid-run loses nothing."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1

# A profile that does not exist will not start existing on the next run.
# Retrying these forever silently burns the daily budget.
PERMANENT_ERRORS = {"profile_not_found"}


def _atomic_write(path: Path, payload: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


class Store:
    def __init__(self, outdir: Path) -> None:
        self.outdir = outdir
        self.outdir.mkdir(parents=True, exist_ok=True)
        self.leads_path = outdir / "leads.json"
        self.companies_path = outdir / "companies.json"
        self.leads: dict[str, dict] = self._load(self.leads_path)
        self.companies: dict[str, dict] = self._load(self.companies_path)

    @staticmethod
    def _load(path: Path) -> dict[str, dict]:
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("records", data) if isinstance(data, dict) else {}

    def is_enriched(self, key: str) -> bool:
        return self.leads.get(key, {}).get("stage") == "enriched"

    def is_done(self, key: str, retry_failed: bool = False, refresh_days: int = 0) -> bool:
        record = self.leads.get(key)
        if not record:
            return False
        if record.get("stage") == "enriched":
            if record.get("incomplete"):
                return False
            return not self._is_stale(record, refresh_days)
        if retry_failed:
            return False
        return record.get("error") in PERMANENT_ERRORS

    @staticmethod
    def _is_stale(record: dict, refresh_days: int) -> bool:
        if refresh_days <= 0:
            return False
        stamp = record.get("enrichedAt")
        if not isinstance(stamp, str):
            return True
        try:
            enriched = datetime.fromisoformat(stamp)
        except ValueError:
            return True
        if enriched.tzinfo is None:
            enriched = enriched.replace(tzinfo=timezone.utc)
        return enriched < datetime.now(timezone.utc) - timedelta(days=refresh_days)

    def banked_profile(self, key: str) -> dict | None:
        """A profile already paid for on an earlier run that stopped part-way."""
        record = self.leads.get(key) or {}
        if record.get("incomplete") and isinstance(record.get("profile"), dict):
            return record
        return None

    def failed_keys(self) -> list[str]:
        return [k for k, v in self.leads.items() if v.get("stage") == "failed"]

    def has_company(self, key: str) -> bool:
        return key in self.companies

    def put_lead(self, key: str, record: dict) -> None:
        self.leads[key] = record

    def put_company(self, key: str, record: dict) -> None:
        self.companies[key] = record

    def flush(self) -> None:
        _atomic_write(self.leads_path, {
            "schemaVersion": SCHEMA_VERSION,
            "count": len(self.leads),
            "records": self.leads,
        })
        _atomic_write(self.companies_path, {
            "schemaVersion": SCHEMA_VERSION,
            "count": len(self.companies),
            "records": self.companies,
        })

    def write_flat(self) -> Path:
        """Denormalised one-object-per-lead export for CRM import."""
        flat = []
        for key, lead in self.leads.items():
            company_key = lead.get("companyKey")
            flat.append({**lead, "company": self.companies.get(company_key) if company_key else None})
        path = self.outdir / "leads_flat.json"
        _atomic_write(path, {
            "schemaVersion": SCHEMA_VERSION,
            "count": len(flat),
            "leads": flat,
        })
        return path
