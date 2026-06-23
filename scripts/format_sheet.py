#!/usr/bin/env python3
"""
Beautify the ElectroCom BD Pipeline Google Sheet.

Applies brand styling: navy header bar, frozen header, alternating row stripes,
color-coded Status column (per sheets/SCHEMA.md), overdue/due-today highlighting
on Next Action Date, and readable column widths.

Idempotent — clears existing banding + conditional-format rules first, so it can
be re-run any time. Reuses the OAuth token from sync_reports_to_sheet.py.

    python format_sheet.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Reuse auth/config/helpers from the sync module.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_reports_to_sheet import (  # noqa: E402
    get_service, load_config, PIPELINE_TAB, ACTIVITY_TAB,
    PIPELINE_HEADERS, ACTIVITY_HEADERS,
)


# ---- palette (0..1 RGB) ----------------------------------------------------
def rgb(hex_str: str) -> dict:
    h = hex_str.lstrip("#")
    return {"red": int(h[0:2], 16) / 255,
            "green": int(h[2:4], 16) / 255,
            "blue": int(h[4:6], 16) / 255}


NAVY = rgb("#0F2747")        # header bar
NAVY_TEXT = rgb("#FFFFFF")
STRIPE = rgb("#EAF1FB")      # light electric-blue stripe
WHITE = rgb("#FFFFFF")
GRID = rgb("#C9D6E5")

STATUS_COLORS = {
    "Won": ("#1E7E34", True), "Negotiating": ("#34C759", False),
    "Proposal Sent": ("#C6EFCE", False), "Call Scheduled": ("#FFB570", False),
    "Interested": ("#FFD8A8", False), "Replied": ("#FFE699", False),
    "DM Sent": ("#BDD7EE", False), "Email Sent": ("#BDD7EE", False),
    "Connection Requested": ("#D6C9F0", False),
    "Connected (No DM yet)": ("#D6C9F0", False),
    "Lost": ("#F4B7B7", False), "On Hold": ("#D9D9D9", False),
    "Not Relevant": ("#CFCFCF", False),
}

# Wider columns (by header name) -> pixel width. Default is 130.
WIDE = {
    "Company": 170, "Title": 170, "Hook / Why Outreach": 230,
    "DM Content": 340, "Email Content": 340, "Internal Notes": 340,
    "Meeting Notes": 260, "Next Action": 200, "Response Summary": 220,
    "Interested In": 200, "Full Name": 150, "LinkedIn URL": 190,
    # activity log
    "Target": 240, "Outcome": 300, "Next Action": 260,
}


def sheet_ids(service, sid: str) -> dict:
    meta = service.spreadsheets().get(spreadsheetId=sid).execute()
    out = {}
    for s in meta["sheets"]:
        p = s["properties"]
        out[p["title"]] = {
            "id": p["sheetId"],
            "cf": [cf for cf in s.get("conditionalFormats", [])],
            "bandings": [b["bandedRangeId"] for b in s.get("bandedRanges", [])],
        }
    return out


def header_text_format(size=10, bold=True, color=None):
    return {"bold": bold, "fontSize": size,
            "foregroundColor": color or {"red": 0, "green": 0, "blue": 0}}


def style_tab(sheet_id, n_cols, n_rows, headers):
    """Return a list of batchUpdate requests to style one tab."""
    reqs = []

    # 1. Freeze header row.
    reqs.append({"updateSheetProperties": {
        "properties": {"sheetId": sheet_id,
                       "gridProperties": {"frozenRowCount": 1}},
        "fields": "gridProperties.frozenRowCount"}})

    # 2. Header bar: navy fill, white bold, centered, wrapped.
    reqs.append({"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1,
                  "startColumnIndex": 0, "endColumnIndex": n_cols},
        "cell": {"userEnteredFormat": {
            "backgroundColor": NAVY,
            "horizontalAlignment": "CENTER",
            "verticalAlignment": "MIDDLE",
            "wrapStrategy": "WRAP",
            "textFormat": header_text_format(10, True, NAVY_TEXT)}},
        "fields": ("userEnteredFormat(backgroundColor,horizontalAlignment,"
                   "verticalAlignment,wrapStrategy,textFormat)")}})

    # 3. Taller header row.
    reqs.append({"updateDimensionProperties": {
        "range": {"sheetId": sheet_id, "dimension": "ROWS",
                  "startIndex": 0, "endIndex": 1},
        "properties": {"pixelSize": 40}, "fields": "pixelSize"}})

    # 4. Body cells: top-aligned, clip wrap, readable font.
    if n_rows > 1:
        reqs.append({"repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": n_rows,
                      "startColumnIndex": 0, "endColumnIndex": n_cols},
            "cell": {"userEnteredFormat": {
                "verticalAlignment": "TOP",
                "wrapStrategy": "CLIP",
                "textFormat": {"fontSize": 10}}},
            "fields": "userEnteredFormat(verticalAlignment,wrapStrategy,textFormat)"}})

    # 5. Alternating row stripes (banding) over the whole table.
    reqs.append({"addBanding": {"bandedRange": {
        "range": {"sheetId": sheet_id, "startRowIndex": 0,
                  "startColumnIndex": 0, "endColumnIndex": n_cols},
        "rowProperties": {
            "headerColor": NAVY,
            "firstBandColor": WHITE,
            "secondBandColor": STRIPE}}}})

    # 6. Thin borders around the data block.
    border = {"style": "SOLID", "color": GRID}
    reqs.append({"updateBorders": {
        "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": max(n_rows, 2),
                  "startColumnIndex": 0, "endColumnIndex": n_cols},
        "innerHorizontal": border, "innerVertical": border,
        "top": border, "bottom": border, "left": border, "right": border}})

    # 7. Column widths.
    for i, h in enumerate(headers):
        w = WIDE.get(h, 130)
        reqs.append({"updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "COLUMNS",
                      "startIndex": i, "endIndex": i + 1},
            "properties": {"pixelSize": w}, "fields": "pixelSize"}})

    return reqs


def status_rules(sheet_id, status_col):
    """Conditional-format rules coloring the Status column by value."""
    reqs = []
    rng = {"sheetId": sheet_id, "startRowIndex": 1,
           "startColumnIndex": status_col, "endColumnIndex": status_col + 1}
    for i, (text, (hexc, white)) in enumerate(STATUS_COLORS.items()):
        fmt = {"backgroundColor": rgb(hexc)}
        if white:
            fmt["textFormat"] = {"foregroundColor": WHITE, "bold": True}
        reqs.append({"addConditionalFormatRule": {"index": i, "rule": {
            "ranges": [rng],
            "booleanRule": {
                "condition": {"type": "TEXT_EQ",
                              "values": [{"userEnteredValue": text}]},
                "format": fmt}}}})
    return reqs


def date_rules(sheet_id, date_col, base_index):
    """Overdue (red) / due-today (orange) highlighting on a date column."""
    rng = {"sheetId": sheet_id, "startRowIndex": 1,
           "startColumnIndex": date_col, "endColumnIndex": date_col + 1}
    return [
        {"addConditionalFormatRule": {"index": base_index, "rule": {
            "ranges": [rng],
            "booleanRule": {
                "condition": {"type": "DATE_BEFORE",
                              "values": [{"relativeDate": "TODAY"}]},
                "format": {"backgroundColor": rgb("#F4B7B7")}}}}},
        {"addConditionalFormatRule": {"index": base_index + 1, "rule": {
            "ranges": [rng],
            "booleanRule": {
                "condition": {"type": "DATE_EQ",
                              "values": [{"relativeDate": "TODAY"}]},
                "format": {"backgroundColor": rgb("#FFB570")}}}}},
    ]


def clear_existing(service, sid, info):
    """Delete existing bandings + conditional formats so re-runs stay clean."""
    reqs = []
    for tab in (PIPELINE_TAB, ACTIVITY_TAB):
        if tab not in info:
            continue
        sd = info[tab]
        for bid in sd["bandings"]:
            reqs.append({"deleteBanding": {"bandedRangeId": bid}})
        # delete conditional formats from the end backwards (indices shift)
        for idx in range(len(sd["cf"]) - 1, -1, -1):
            reqs.append({"deleteConditionalFormatRule":
                         {"sheetId": sd["id"], "index": idx}})
    if reqs:
        service.spreadsheets().batchUpdate(
            spreadsheetId=sid, body={"requests": reqs}).execute()


def row_count(service, sid, tab):
    resp = service.spreadsheets().values().get(
        spreadsheetId=sid, range=f"'{tab}'!A:A").execute()
    return max(len(resp.get("values", [])), 2)


def main() -> int:
    cfg = load_config()
    sid = cfg.get("spreadsheet_id")
    if not sid:
        sys.exit("No spreadsheet_id in sheet_config.json — run the sync first.")
    service = get_service()

    info = sheet_ids(service, sid)
    clear_existing(service, sid, info)
    info = sheet_ids(service, sid)  # refresh after clearing

    reqs = []

    # Pipeline tab
    p = info[PIPELINE_TAB]
    p_rows = row_count(service, sid, PIPELINE_TAB)
    reqs += style_tab(p["id"], len(PIPELINE_HEADERS), p_rows, PIPELINE_HEADERS)
    status_col = PIPELINE_HEADERS.index("Status")
    reqs += status_rules(p["id"], status_col)
    nad_col = PIPELINE_HEADERS.index("Next Action Date")
    reqs += date_rules(p["id"], nad_col, base_index=len(STATUS_COLORS))

    # Activity Log tab
    a = info[ACTIVITY_TAB]
    a_rows = row_count(service, sid, ACTIVITY_TAB)
    reqs += style_tab(a["id"], len(ACTIVITY_HEADERS), a_rows, ACTIVITY_HEADERS)

    service.spreadsheets().batchUpdate(
        spreadsheetId=sid, body={"requests": reqs}).execute()

    print(f"Styled {PIPELINE_TAB} ({p_rows} rows) and {ACTIVITY_TAB} ({a_rows} rows).")
    print(f"Sheet: {cfg.get('spreadsheet_url', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
