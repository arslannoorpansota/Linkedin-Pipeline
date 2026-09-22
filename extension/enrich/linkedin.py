"""Authenticated Sales Navigator client with pacing and block detection.

Sales Navigator search results carry no public profile id, so enrichment goes
through the same sales-api endpoints the web app itself uses.
"""
from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

SALES_API = "https://www.linkedin.com/sales-api"

BLOCK_MARKERS = ("/checkpoint/challenge", "/authwall", "/uas/login")

PROFILE_DECORATION = (
    "(entityUrn,objectUrn,firstName,lastName,fullName,headline,summary,"
    "geoRegion,industry,vanityName,publicProfileUrl,flagshipProfileUrl,"
    "positions*,educations*,skills*,fullPositions*,"
    "currentPositions*,pastPositions*,numOfConnections,degree)"
)


class Blocked(Exception):
    """LinkedIn refused the request in a way that must stop the run."""


class NotFound(Exception):
    """Target does not exist or is not visible to this account."""


@dataclass
class Pacing:
    min_delay: float = 4.0
    max_delay: float = 9.0
    max_fetches: int = 400

    def sleep(self) -> None:
        time.sleep(random.uniform(self.min_delay, self.max_delay))


class LinkedInClient:
    def __init__(self, li_at: str, jsessionid: str, pacing: Pacing | None = None,
                 budget: Any = None, dump_dir: Path | None = None) -> None:
        csrf = jsessionid.strip('"')
        self.pacing = pacing or Pacing()
        self.budget = budget
        self.fetches = 0
        self.dump_dir = dump_dir
        self._dumped: set[str] = set()
        self.session = requests.Session()
        self.session.cookies.set("li_at", li_at, domain=".linkedin.com")
        self.session.cookies.set("JSESSIONID", f'"{csrf}"', domain=".linkedin.com")
        self.session.headers.update({
            "csrf-token": csrf,
            "accept": "application/json",
            "x-restli-protocol-version": "2.0.0",
            "x-li-lang": "en_US",
            "user-agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
            ),
            "referer": "https://www.linkedin.com/sales/search/people",
        })

    def _dump(self, label: str, payload: Any) -> None:
        """Keep the first response of each kind so its shape can be inspected."""
        if self.dump_dir is None or label in self._dumped:
            return
        self._dumped.add(label)
        self.dump_dir.mkdir(parents=True, exist_ok=True)
        (self.dump_dir / f"{label}.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def get(self, path: str, params: dict[str, Any] | None = None,
            label: str = "response") -> Any:
        if self.fetches >= self.pacing.max_fetches:
            raise Blocked(f"fetch budget of {self.pacing.max_fetches} reached for this run")
        if self.budget is not None:
            self.budget.check()
        if self.fetches:
            self.pacing.sleep()
        self.fetches += 1
        if self.budget is not None:
            self.budget.record()

        url = path if path.startswith("http") else f"{SALES_API}{path}"
        try:
            res = self.session.get(url, params=params, timeout=30, allow_redirects=False)
        except requests.RequestException as exc:
            raise Blocked(f"network failure: {exc}") from exc

        location = res.headers.get("location", "")
        if any(marker in location for marker in BLOCK_MARKERS):
            raise Blocked(f"redirected to {location} — session is challenged or expired")
        if res.status_code in (401, 403):
            raise Blocked(f"HTTP {res.status_code} — session rejected "
                          "(is the Sales Navigator seat still active?)")
        if res.status_code == 429:
            raise Blocked("HTTP 429 — rate limited")
        if res.status_code == 404:
            raise NotFound(url)
        if res.status_code >= 500:
            raise Blocked(f"HTTP {res.status_code} — upstream error")
        if res.status_code != 200:
            raise Blocked(f"unexpected HTTP {res.status_code}")

        try:
            payload = res.json()
        except ValueError as exc:
            raise Blocked("response was not JSON — likely an interstitial page") from exc

        self._dump(label, payload)
        return payload

    def profile(self, ref: Any) -> Any:
        return self.get(f"/salesApiProfiles/{ref.path_key}",
                        {"decoration": PROFILE_DECORATION}, label="profile")

    def company(self, company_id: str) -> Any:
        return self.get(f"/salesApiCompanies/{company_id}", {
            "decoration": "(entityUrn,name,description,industry,employeeCount,"
                          "employeeDisplayCount,employeeCountRange,location,"
                          "headquarters,website,revenue,specialties,foundedOn)",
        }, label="company")

    def insights(self, ref: Any, count: int = 3) -> Any:
        now_ms = int(time.time() * 1000)
        return self.get("/salesApiInsightsV2", {
            "insightTypes": "List(LEAD_POST,LEAD_COMMENT)",
            "q": "findByMember",
            "profile": ref.urn,
            "timeRange": f"(start:{now_ms - 90 * 86400_000},end:{now_ms})",
            "start": 0,
            "count": count,
        }, label="insights")
