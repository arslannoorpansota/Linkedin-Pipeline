"""Fetch budget that persists across runs.

A per-run ceiling is not enough on its own: re-running the command four times
resets it four times. This counter is keyed by UTC date and lives on disk.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


class BudgetExhausted(Exception):
    pass


class Budget:
    def __init__(self, path: Path, daily_cap: int) -> None:
        self.path = path
        self.daily_cap = daily_cap
        self.counts: dict[str, int] = {}
        if path.exists():
            try:
                self.counts = json.loads(path.read_text(encoding="utf-8"))
            except ValueError:
                self.counts = {}

    @staticmethod
    def today() -> str:
        return datetime.now(timezone.utc).date().isoformat()

    def used(self) -> int:
        return self.counts.get(self.today(), 0)

    def remaining(self) -> int:
        return max(0, self.daily_cap - self.used())

    def check(self) -> None:
        if self.remaining() <= 0:
            raise BudgetExhausted(
                f"daily cap of {self.daily_cap} requests reached "
                f"({self.used()} used on {self.today()} UTC)"
            )

    def record(self, n: int = 1) -> None:
        self.counts[self.today()] = self.used() + n
        self._save()

    def _save(self) -> None:
        recent = sorted(self.counts)[-30:]
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({k: self.counts[k] for k in recent}, indent=2),
                       encoding="utf-8")
        os.replace(tmp, self.path)
