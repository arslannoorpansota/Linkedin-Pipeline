#!/usr/bin/env python3
"""
Dump the live Pipeline tab to CSV so it can be analysed offline.

Usage:
    python dump_pipeline.py                    # writes pipeline_dump.csv next to script
    python dump_pipeline.py /tmp/out.csv       # custom path
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import sync_reports_to_sheet as sync

SCRIPT_DIR = Path(__file__).resolve().parent

# Read-only work needs just the spreadsheets scope. The cached token was minted
# with that scope alone, so asking for sync.SCOPES (which adds drive.file) makes
# the refresh fail with invalid_scope.
READ_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def read_service():
    creds = Credentials.from_authorized_user_file(str(sync.TOKEN_FILE), READ_SCOPES)
    if not creds.valid:
        creds.refresh(Request())
        sync.TOKEN_FILE.write_text(creds.to_json())
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else SCRIPT_DIR / "pipeline_dump.csv"
    cfg = sync.load_config()
    service = read_service()
    resp = service.spreadsheets().values().get(
        spreadsheetId=cfg["spreadsheet_id"],
        range="Pipeline",
    ).execute()
    rows = resp.get("values", [])
    width = max(len(r) for r in rows)
    with out.open("w", newline="") as fh:
        w = csv.writer(fh)
        for r in rows:
            w.writerow(r + [""] * (width - len(r)))
    print(f"{len(rows)} rows x {width} cols -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
