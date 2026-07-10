#!/usr/bin/env python3
"""
Sync ElectroCom daily reports -> Google Sheets (BD Pipeline).

Parses reports/YYYY-MM-DD.md entries and appends new lead-touchpoint rows
to the "Pipeline" tab, and every entry to the "Activity Log" tab.

Idempotent: a state file (scripts/.sheet_sync_state.json) records which
entries have already been pushed, keyed by (date|agent|target). Safe to run
every day via cron — only new entries are appended.

Auth: OAuth (the user's own Google login). First run opens a browser for
consent and caches a refresh token; subsequent runs (incl. cron) are silent.

Config: scripts/sheet_config.json  (auto-created; stores spreadsheet_id).
If no spreadsheet_id is set, a new "ElectroCom BD Pipeline" sheet is created
in the authenticated user's Drive and the id is saved back.

Usage:
    python sync_reports_to_sheet.py            # sync all reports (new entries only)
    python sync_reports_to_sheet.py --date 2026-06-22   # one day
    python sync_reports_to_sheet.py --dry-run  # parse + print rows, no auth, no write
    python sync_reports_to_sheet.py --reauth    # force re-consent
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
REPORTS_DIR = REPO_ROOT / "reports"
CREDENTIALS_FILE = SCRIPT_DIR / "credentials.json"   # OAuth client (you download this)
TOKEN_FILE = SCRIPT_DIR / "token.json"               # cached refresh token (auto)
CONFIG_FILE = SCRIPT_DIR / "sheet_config.json"       # stores spreadsheet_id (auto)
STATE_FILE = SCRIPT_DIR / ".sheet_sync_state.json"   # dedup state (auto)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive.file"]

PIPELINE_TAB = "Pipeline"
ACTIVITY_TAB = "Activity Log"

# Headers for the Pipeline tab, in SCHEMA.md column order (A..AV).
PIPELINE_HEADERS = [
    "Lead ID", "Date Added", "Full Name", "Title", "Company", "Industry", "Location",
    "LinkedIn URL", "Email", "Phone", "Connection Degree", "Mutual Connections",
    "Lead Type", "Service Interest", "Deal Type", "Estimated Budget", "Priority",
    "Lead Score", "Hook / Why Outreach", "Outreach Channel", "From Email",
    "DM / Email Sent Date", "Connection Note Sent", "DM Content", "Email Subject",
    "Email Content", "Outreach by", "Status", "Response Date", "Response Type",
    "Response Summary", "Interested In", "Follow-up 1 Date", "Follow-up 1 Notes",
    "Follow-up 2 Date", "Follow-up 2 Notes", "Follow-up 3 Date", "Follow-up 3 Notes",
    "Meeting / Call Date", "Meeting Notes", "Proposal Sent Date", "Deal Value (USD)",
    "Close Date", "Win/Loss Reason", "Assigned To", "Next Action", "Next Action Date",
    "Lead Source", "Internal Notes",
]

ACTIVITY_HEADERS = [
    "Date", "Agent", "Target", "Lead Type", "Outcome", "Next Action", "Source File",
]

# Which agents represent a lead touchpoint that belongs in the Pipeline tab.
LEAD_AGENTS = ("dm", "email", "follow", "lead research", "lead_research")


# ---------------------------------------------------------------------------
# Report parsing
# ---------------------------------------------------------------------------
ENTRY_RE = re.compile(r"^###\s+(\d{4}-\d{2}-\d{2})\s+[—-]+\s+(.+)$")
FIELD_RE = re.compile(r"^\s*-\s+\*\*(?P<key>[^:*]+):\*\*\s*(?P<val>.*)$")


def parse_report(path: Path) -> list[dict]:
    """Parse one daily report markdown file into a list of entry dicts."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    entries: list[dict] = []
    cur: dict | None = None
    field_key: str | None = None
    collecting_output = False

    for line in lines:
        m = ENTRY_RE.match(line)
        if m:
            if cur is not None:
                entries.append(cur)
            date, header = m.group(1), m.group(2).strip()
            # header is "<AGENT> — <Target>"
            parts = re.split(r"\s+[—-]+\s+", header, maxsplit=1)
            agent = parts[0].strip()
            target = parts[1].strip() if len(parts) > 1 else ""
            cur = {
                "date": date, "agent": agent, "target": target,
                "fields": {}, "output": [], "source_file": path.name,
            }
            field_key = None
            collecting_output = False
            continue
        if cur is None:
            continue
        if line.strip() == "---":
            collecting_output = False
            field_key = None
            continue
        fm = FIELD_RE.match(line)
        if fm:
            key = fm.group("key").strip().lower()
            val = fm.group("val").strip()
            cur["fields"][key] = val
            collecting_output = (key == "output")
            field_key = key
            continue
        if collecting_output:
            cur["output"].append(line)

    if cur is not None:
        entries.append(cur)
    return entries


def split_target(target: str) -> tuple[str, str, str]:
    """Best-effort split of a Target string into (name, title, company)."""
    # strip trailing parenthetical, e.g. "Arslan Noor (LinkedIn personal profile)"
    paren = ""
    pm = re.search(r"\(([^)]*)\)\s*$", target)
    if pm:
        paren = pm.group(1).strip()
        target = target[:pm.start()].strip()
    bits = [b.strip() for b in target.split(",") if b.strip()]
    if not bits:
        return ("", "", paren)
    if len(bits) == 1:
        return (bits[0], "", paren)
    if len(bits) == 2:
        return (bits[0], "", bits[1])
    # 3+: name, title..., company
    return (bits[0], ", ".join(bits[1:-1]), bits[-1])


def is_lead_entry(agent: str) -> bool:
    a = agent.lower()
    return any(k in a for k in LEAD_AGENTS) and "profile setup" not in a \
        and "company page" not in a and "assets" not in a and "infra" not in a


def agent_to_channel_status(agent: str) -> tuple[str, str]:
    a = agent.lower()
    if "follow" in a:
        return ("", "Replied")
    if "email" in a:
        return ("Email", "Email Sent")
    if "dm" in a:
        return ("LinkedIn DM", "DM Sent")
    if "lead" in a:
        return ("", "New")
    return ("", "New")


def entry_key(e: dict) -> str:
    return f"{e['date']}|{e['agent'].lower()}|{e['target'].lower()}"


def entry_to_pipeline_row(e: dict) -> list[str]:
    f = e["fields"]
    name, title, company = split_target(e["target"])
    channel, status = agent_to_channel_status(e["agent"])
    lead_type = f.get("lead type", "")
    outcome = f.get("outcome", "")
    output = "\n".join(e["output"]).strip()
    next_action = f.get("next action", "")
    # Map our 4 BD lead types to the schema dropdown where possible
    lt = lead_type.lower()
    if "agency" in lt:
        lead_type_norm = "Agency Partner"
    elif "anthropic" in lt:
        lead_type_norm = "Anthropic Partner"
    elif "hire" in lt or "personal" in lt:
        lead_type_norm = "Hire (Arslan)"
    elif "client" in lt or "direct" in lt:
        lead_type_norm = "Direct Client"
    else:
        lead_type_norm = lead_type

    row = {h: "" for h in PIPELINE_HEADERS}
    row["Date Added"] = e["date"]
    row["Full Name"] = name
    row["Title"] = title
    row["Company"] = company
    row["Lead Type"] = lead_type_norm
    row["Hook / Why Outreach"] = outcome
    row["Outreach Channel"] = channel
    row["DM / Email Sent Date"] = e["date"]
    row["Status"] = status
    row["Outreach by"] = "Arslan"
    row["Next Action"] = next_action
    row["Internal Notes"] = output[:5000]
    a = e["agent"].lower()
    if "dm" in a:
        row["DM Content"] = output[:5000]
    elif "email" in a:
        row["Email Content"] = output[:5000]
    return [row[h] for h in PIPELINE_HEADERS]


def entry_to_activity_row(e: dict) -> list[str]:
    f = e["fields"]
    return [
        e["date"], e["agent"], e["target"], f.get("lead type", ""),
        f.get("outcome", ""), f.get("next action", ""), e["source_file"],
    ]


# ---------------------------------------------------------------------------
# State (dedup)
# ---------------------------------------------------------------------------
def load_state() -> set[str]:
    if STATE_FILE.exists():
        try:
            return set(json.loads(STATE_FILE.read_text()).get("synced", []))
        except Exception:
            return set()
    return set()


def save_state(keys: set[str]) -> None:
    STATE_FILE.write_text(json.dumps({"synced": sorted(keys)}, indent=2))


def load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(cfg: dict) -> None:
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


# ---------------------------------------------------------------------------
# Collect entries
# ---------------------------------------------------------------------------
def collect_entries(only_date: str | None) -> list[dict]:
    files = sorted(REPORTS_DIR.glob("20*-*-*.md"))
    entries: list[dict] = []
    for fp in files:
        if only_date and fp.stem != only_date:
            continue
        entries.extend(parse_report(fp))
    return entries


# ---------------------------------------------------------------------------
# Google Sheets I/O
# ---------------------------------------------------------------------------
def get_service(force_reauth: bool = False):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if TOKEN_FILE.exists() and not force_reauth:
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token and not force_reauth:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                sys.exit(
                    f"ERROR: {CREDENTIALS_FILE} not found.\n"
                    "Download an OAuth 'Desktop app' client from Google Cloud Console\n"
                    "(APIs & Services > Credentials) and save it there. See scripts/README.md."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            # Try a local browser flow; fall back to console for headless.
            try:
                creds = flow.run_local_server(port=0)
            except Exception:
                creds = flow.run_console()
        TOKEN_FILE.write_text(creds.to_json())
        os.chmod(TOKEN_FILE, 0o600)
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def ensure_spreadsheet(service, cfg: dict) -> str:
    sid = cfg.get("spreadsheet_id")
    if sid:
        return sid
    body = {
        "properties": {"title": "ElectroCom BD Pipeline"},
        "sheets": [
            {"properties": {"title": PIPELINE_TAB,
                            "gridProperties": {"frozenRowCount": 1}}},
            {"properties": {"title": ACTIVITY_TAB,
                            "gridProperties": {"frozenRowCount": 1}}},
        ],
    }
    ss = service.spreadsheets().create(body=body, fields="spreadsheetId,spreadsheetUrl").execute()
    sid = ss["spreadsheetId"]
    cfg["spreadsheet_id"] = sid
    cfg["spreadsheet_url"] = ss.get("spreadsheetUrl", "")
    save_config(cfg)
    print(f"Created spreadsheet: {ss.get('spreadsheetUrl')}")
    return sid


def ensure_tab_and_header(service, sid: str, tab: str, headers: list[str]) -> None:
    meta = service.spreadsheets().get(spreadsheetId=sid).execute()
    titles = [s["properties"]["title"] for s in meta["sheets"]]
    if tab not in titles:
        service.spreadsheets().batchUpdate(
            spreadsheetId=sid,
            body={"requests": [{"addSheet": {"properties": {
                "title": tab, "gridProperties": {"frozenRowCount": 1}}}}]},
        ).execute()
    # write headers if the first row is empty
    resp = service.spreadsheets().values().get(
        spreadsheetId=sid, range=f"'{tab}'!1:1").execute()
    if not resp.get("values"):
        service.spreadsheets().values().update(
            spreadsheetId=sid, range=f"'{tab}'!A1",
            valueInputOption="RAW", body={"values": [headers]}).execute()


def append_rows(service, sid: str, tab: str, rows: list[list[str]]) -> None:
    if not rows:
        return
    service.spreadsheets().values().append(
        spreadsheetId=sid, range=f"'{tab}'!A1",
        valueInputOption="RAW", insertDataOption="INSERT_ROWS",
        body={"values": rows}).execute()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="Sync daily reports to Google Sheets")
    ap.add_argument("--date", help="Only sync this YYYY-MM-DD report")
    ap.add_argument("--dry-run", action="store_true",
                    help="Parse and print rows; no auth, no write")
    ap.add_argument("--reauth", action="store_true", help="Force OAuth re-consent")
    args = ap.parse_args()

    entries = collect_entries(args.date)
    state = load_state()
    new = [e for e in entries if entry_key(e) not in state]

    pipeline_new = [e for e in new if is_lead_entry(e["agent"])]
    print(f"Parsed {len(entries)} entries; {len(new)} new "
          f"({len(pipeline_new)} lead rows for Pipeline).")

    if args.dry_run:
        for e in new:
            tag = "LEAD " if is_lead_entry(e["agent"]) else "activity"
            print(f"  [{tag}] {entry_key(e)}")
            if is_lead_entry(e["agent"]):
                row = entry_to_pipeline_row(e)
                print("        Pipeline:",
                      {h: v for h, v in zip(PIPELINE_HEADERS, row) if v}.__repr__()[:300])
        if not new:
            print("  (nothing new to sync)")
        return 0

    if not new:
        print("Nothing new to sync.")
        return 0

    cfg = load_config()
    service = get_service(force_reauth=args.reauth)
    sid = ensure_spreadsheet(service, cfg)
    ensure_tab_and_header(service, sid, PIPELINE_TAB, PIPELINE_HEADERS)
    ensure_tab_and_header(service, sid, ACTIVITY_TAB, ACTIVITY_HEADERS)

    append_rows(service, sid, PIPELINE_TAB, [entry_to_pipeline_row(e) for e in pipeline_new])
    append_rows(service, sid, ACTIVITY_TAB, [entry_to_activity_row(e) for e in new])

    for e in new:
        state.add(entry_key(e))
    save_state(state)

    url = cfg.get("spreadsheet_url", "")
    print(f"Synced {len(pipeline_new)} lead rows + {len(new)} activity rows.")
    if url:
        print(f"Sheet: {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
