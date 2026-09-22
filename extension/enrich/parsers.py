"""Tolerant extraction from Sales Navigator API payloads.

Shapes shift without notice, so these search the tree for recognisable records
rather than indexing fixed paths. Anything unrecognised is skipped, never
guessed at.
"""
from __future__ import annotations

from typing import Any, Iterator


def _walk(node: Any, depth: int = 0) -> Iterator[dict]:
    if depth > 10 or node is None:
        return
    if isinstance(node, list):
        for item in node:
            yield from _walk(item, depth + 1)
    elif isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value, depth + 1)


def _text(node: dict, *keys: str) -> str | None:
    for key in keys:
        value = node.get(key)
        if isinstance(value, str) and value:
            return value
        if isinstance(value, dict):
            inner = value.get("text")
            if isinstance(inner, str) and inner:
                return inner
    return None


def _num(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _tenure(node: Any) -> float | None:
    if not isinstance(node, dict):
        return None
    years, months = node.get("numYears"), node.get("numMonths")
    if years is None and months is None:
        return None
    return round((years or 0) + (months or 0) / 12, 1)


def _started(node: Any) -> str | None:
    if not isinstance(node, dict):
        return None
    year = node.get("year")
    if not year:
        return None
    month = node.get("month")
    return f"{year}-{int(month):02d}" if month else str(year)


def _position(node: dict) -> dict:
    company = node.get("companyUrnResolutionResult") or {}
    return {
        "title": _text(node, "title"),
        "companyName": _text(node, "companyName") or _text(company, "name"),
        "companyUrn": node.get("companyUrn") or company.get("entityUrn"),
        "companyIndustry": _text(company, "industry"),
        "companyLocation": _text(company, "location"),
        "description": _text(node, "description"),
        "location": _text(node, "location", "locationName"),
        "current": bool(node.get("current")),
        "startedOn": _started(node.get("startedOn")),
        "endedOn": _started(node.get("endedOn")),
        "yearsInRole": _tenure(node.get("tenureAtPosition")),
        "yearsAtCompany": _tenure(node.get("tenureAtCompany")),
    }


def _looks_like_position(node: dict) -> bool:
    return "title" in node and ("companyName" in node or "companyUrn" in node)


def _public_url(root: dict, payload: Any) -> tuple[str | None, str | None]:
    """The /in/ URL for connection requests. Sales Navigator search never
    returns it, so it is only available once the profile itself is fetched."""
    vanity = _text(root, "vanityName", "publicIdentifier")
    direct = _text(root, "publicProfileUrl", "flagshipProfileUrl")
    if not vanity and not direct:
        for node in _walk(payload):
            vanity = vanity or _text(node, "vanityName", "publicIdentifier")
            direct = direct or _text(node, "publicProfileUrl", "flagshipProfileUrl")
            if vanity or direct:
                break
    if direct and "/in/" in direct:
        vanity = vanity or direct.split("/in/")[-1].strip("/").split("?")[0]
    url = direct if direct else (f"https://www.linkedin.com/in/{vanity}" if vanity else None)
    return vanity, url


def parse_profile(payload: Any) -> dict:
    root: dict = {}
    for node in _walk(payload):
        if isinstance(node.get("entityUrn"), str) and "salesProfile" in node["entityUrn"]:
            if len(node) > len(root):
                root = node
    if not root and isinstance(payload, dict):
        root = payload

    positions, seen = [], set()
    for key in ("currentPositions", "pastPositions", "fullPositions", "positions"):
        for raw in (root.get(key) or []):
            if not isinstance(raw, dict):
                continue
            parsed = _position(raw)
            marker = (parsed["title"], parsed["companyName"], parsed["startedOn"])
            if marker in seen:
                continue
            seen.add(marker)
            positions.append(parsed)

    if not positions:
        for node in _walk(payload):
            if _looks_like_position(node):
                parsed = _position(node)
                marker = (parsed["title"], parsed["companyName"], parsed["startedOn"])
                if marker not in seen:
                    seen.add(marker)
                    positions.append(parsed)

    positions.sort(key=lambda p: (p["current"] is True, p["startedOn"] or ""), reverse=True)

    education = []
    for node in _walk(payload):
        school = _text(node, "schoolName")
        if school:
            education.append({
                "school": school,
                "degree": _text(node, "degreeName", "degree"),
                "field": _text(node, "fieldOfStudy"),
                "start": _started(node.get("startedOn")),
                "end": _started(node.get("endedOn")),
            })

    skills = []
    for node in _walk(payload):
        for key in ("skills", "skillsUsed"):
            for entry in (node.get(key) or []):
                name = entry if isinstance(entry, str) else _text(entry or {}, "name")
                if name and name not in skills:
                    skills.append(name)

    vanity, public_url = _public_url(root, payload)
    profile_id = (root.get("entityUrn") or "").split("(")[-1].split(",")[0] or None

    return {
        "profileId": profile_id,
        "vanityName": vanity,
        "linkedinUrl": public_url,
        "memberId": (str(root.get("objectUrn") or "").rsplit(":", 1)[-1]) or None,
        "fullName": _text(root, "fullName") or " ".join(
            filter(None, [_text(root, "firstName"), _text(root, "lastName")])) or None,
        "headline": _text(root, "headline", "summary"),
        "about": _text(root, "about", "summary"),
        "location": _text(root, "geoRegion", "location"),
        "industry": _text(root, "industry"),
        "connections": _num(root.get("numOfConnections")),
        "degree": _num(root.get("degree")),
        "experience": positions,
        "education": education,
        "skills": skills,
    }


def current_company(profile: dict) -> dict | None:
    for position in profile.get("experience", []):
        if position.get("current") and position.get("companyUrn"):
            urn = str(position["companyUrn"])
            return {
                "urn": urn,
                "id": urn.rsplit(":", 1)[-1],
                "name": position.get("companyName"),
            }
    for position in profile.get("experience", []):
        if position.get("companyUrn"):
            urn = str(position["companyUrn"])
            return {"urn": urn, "id": urn.rsplit(":", 1)[-1],
                    "name": position.get("companyName")}
    return None


def parse_company(payload: Any) -> dict:
    best: dict = {}
    for node in _walk(payload):
        if "name" in node and any(k in node for k in
                                  ("employeeCount", "industry", "website", "employeeCountRange")):
            if len(node) > len(best):
                best = node
    if not best and isinstance(payload, dict):
        best = payload

    rng = best.get("employeeCountRange") or {}
    hq = best.get("headquarters") or best.get("headquarter") or {}

    return {
        "name": _text(best, "name"),
        "urn": best.get("entityUrn"),
        "website": _text(best, "website", "companyPageUrl"),
        "industry": _text(best, "industry"),
        "description": _text(best, "description", "tagline"),
        "staffCount": _num(best.get("employeeCount")),
        "staffRange": (f'{rng.get("start")}-{rng.get("end")}'
                       if rng.get("start") is not None else
                       _text(best, "employeeDisplayCount")),
        "revenue": _text(best, "revenue"),
        "founded": (best.get("foundedOn") or {}).get("year"),
        "specialties": best.get("specialties") or best.get("specialities"),
        "location": _text(best, "location"),
        "headquarters": {
            "city": hq.get("city"), "country": hq.get("country"),
            "geographicArea": hq.get("geographicArea"),
        } if hq else None,
    }


def parse_insights(payload: Any, limit: int = 5) -> list[dict]:
    """Recent posts and comments — the personalisation hook for outreach."""
    posts, seen = [], set()
    for node in _walk(payload):
        text = _text(node, "commentary", "text", "summary", "postText")
        if not text or len(text.strip()) < 20:
            continue
        key = text[:120]
        if key in seen:
            continue
        seen.add(key)
        posts.append({
            "text": text.strip()[:2000],
            "type": _text(node, "insightType", "type"),
            "urn": node.get("entityUrn") or node.get("updateUrn"),
        })
        if len(posts) >= limit:
            break
    return posts
