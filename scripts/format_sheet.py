#!/usr/bin/env python3
"""
Beautify the ElectroCom BD Pipeline Google Sheet.

Applies a single visual design system across every tab:

  * Section-tinted header bar   — each block of columns (Identity, Contact,
    Qualification, Outreach, Response, Follow-up, Deal, Admin, Rating,
    Cadence) gets its own dark hue, so you can see where you are while
    scrolling sideways across 57 columns.
  * Frozen header row + first 5 columns, so name/company stay visible.
  * Zebra banding, hairline grid, tuned column widths and row height.
  * Semantic colour: Status chips, Cadence Stage chips, Priority chips,
    red->amber->green gradients on the score columns, and status-aware
    overdue highlighting on Next Action Date.
  * Dead rows (Skip / Not Relevant) are greyed out so live leads pop.
  * Dropdown chips + checkboxes on the categorical columns.
  * A generated "Legend" tab documenting the whole colour system.

Reads the LIVE header row from each tab rather than a hardcoded list, so the
extra columns added over time (Lead Name .. Cadence Stage) are styled too.

Purely presentational — it never writes to a data cell. Idempotent: existing
banding, conditional formats and validation are cleared first, so re-run it
any time.

    python format_sheet.py
    python format_sheet.py --dry-run     # print the plan, change nothing
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_reports_to_sheet import (  # noqa: E402
    get_service, load_config, PIPELINE_TAB, ACTIVITY_TAB,
)

REMINDER_TAB = "Cadence Reminders"
LEGEND_TAB = "Legend"


# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
def rgb(hex_str: str) -> dict:
    h = hex_str.lstrip("#")
    return {"red": int(h[0:2], 16) / 255,
            "green": int(h[2:4], 16) / 255,
            "blue": int(h[4:6], 16) / 255}


WHITE = rgb("#FFFFFF")
INK = rgb("#1F2933")
MUTED_INK = rgb("#9AA0A6")
STRIPE = rgb("#F2F6FC")     # very light brand blue
GRID = rgb("#D7E0EC")
BRAND_NAVY = "#0F2747"

# Column-section header tints. All roughly equal darkness so they read as one
# family rather than a rainbow; hue is what separates them.
SECTIONS = [
    ("Identity",      0,                       "#0F2747"),
    ("Contact",       "LinkedIn URL",          "#10465C"),
    ("Qualification", "Lead Type",             "#0E5245"),
    ("Outreach",      "Outreach Channel",      "#3B4A8C"),
    ("Response",      "Status",                "#6B3F7A"),
    ("Follow-up",     "Follow-up 1 Date",      "#8A4B2F"),
    ("Deal",          "Meeting / Call Date",   "#2C6B3F"),
    ("Admin",         "Assigned To",           "#37475A"),
    ("Rating",        "Lead Name",             "#574A8F"),
    ("Cadence",       "Days Since Last Touch", "#8A5A0B"),
]

# Status chips. Ordered most-specific-first: Sheets applies the first matching
# rule when two rules set the same property. ("prefix", ...) matches by
# TEXT_STARTS_WITH so the T2/T3/T4 cadence families need one rule each.
STATUS_STYLES = [
    ("eq",     "Won",                          "#1E7E34", WHITE),
    ("eq",     "Negotiating",                  "#34C759", None),
    ("eq",     "Proposal Sent",                "#A9DFBF", None),
    ("eq",     "Call Scheduled",               "#FF9F45", None),
    ("eq",     "Interested",                   "#FFD8A8", None),
    ("eq",     "Replied",                      "#FFE699", None),
    ("eq",     "Connected - follow-up sent",   "#C3B4E8", None),
    ("eq",     "Connected (No DM yet)",        "#DDD4F5", None),
    ("eq",     "Connection Requested",         "#E7E0FB", None),
    ("eq",     "DM Sent",                      "#BDD7EE", None),
    ("eq",     "Email Sent",                   "#BDD7EE", None),
    ("prefix", "T2 sent",                      "#CFE2F3", None),
    ("prefix", "T3 sent",                      "#B2D2EC", None),
    ("prefix", "T4 sent",                      "#98C1E3", None),
    ("prefix", "To Review",                    "#FFF2CC", None),
    ("eq",     "New",                          "#EAF1FB", None),
    ("eq",     "On Hold",                      "#E3E3E3", None),
    ("eq",     "Not Relevant",                 "#D8D8D8", MUTED_INK),
    ("eq",     "Skip",                         "#EFEFEF", MUTED_INK),
    ("eq",     "Lost",                         "#F4B7B7", None),
    ("prefix", "Closed",                       "#F7C9C9", None),
]

# Cadence Stage chips. OVERDUE must come before the "due" contains-rule --
# TEXT_CONTAINS is case-insensitive, so "OVERDUE T3" also contains "due".
CADENCE_STYLES = [
    ("prefix",   "OVERDUE", "#E06C6C", WHITE),
    ("eq",       "REPLIED", "#4FA97A", WHITE),
    ("eq",       "PARK",    "#DCDCDC", MUTED_INK),
    ("contains", "due",     "#FFE0A3", None),
]

PRIORITY_STYLES = [
    ("eq", "High",   "#F8CBAD", None),
    ("eq", "Medium", "#FFE699", None),
    ("eq", "Low",    "#EDF2E9", None),
]

# The long free-text outreach columns. You can't read a full DM body in a cell,
# so these are chipped on presence instead: green = copy written, grey = empty.
CONTENT_COLS = ["DM Content", "Email Subject", "Email Content"]
CONTENT_DRAFTED_BG = "#D9EAD3"
CONTENT_EMPTY_BG = "#EDEDED"

# Columns deliberately kept free of data validation. Sheets' "Insert dropdown"
# seeds a STRICT list from whatever is already in the column, which on these
# turns every past DM body into an "option" and then rejects any newly typed
# message. The drafted/empty chips above give the same at-a-glance signal
# without constraining what can be written.
FREE_TEXT_COLS = list(CONTENT_COLS)

# Statuses that mean "this lead is not live" -- used to grey the row out and to
# suppress overdue highlighting on leads nobody is chasing.
DEAD_STATUS_RE = "(?i)skip|not relevant|closed|lost|on hold"

GRADIENTS = {
    "Lead Score":            (1, 5.5, 10, "#F8696B", "#FFEB84", "#63BE7B"),
    "Profile Rating (/10)":  (1, 5.5, 10, "#F8696B", "#FFEB84", "#63BE7B"),
    "Company Rating (/10)":  (1, 5.5, 10, "#F8696B", "#FFEB84", "#63BE7B"),
    # inverted: fresh contact is good, a long silence is bad
    "Days Since Last Touch": (0, 8, 20, "#63BE7B", "#FFEB84", "#F8696B"),
}

DATE_COLS = [
    "Date Added", "DM / Email Sent Date", "Response Date", "Follow-up 1 Date",
    "Follow-up 2 Date", "Follow-up 3 Date", "Meeting / Call Date",
    "Proposal Sent Date", "Close Date", "Next Action Date", "Cadence Due",
]
CURRENCY_COLS = ["Deal Value (USD)"]
INT_COLS = ["Lead Score", "Mutual Connections", "Profile Rating (/10)",
            "Company Rating (/10)", "Days Since Last Touch"]

CHECKBOX_COLS = {"Connection Note Sent"}

# Canonical dropdown values. At runtime these are unioned with the values
# actually present in the column, so historical entries don't get flagged.
DROPDOWNS = {
    "Industry": ["SaaS", "Consulting / Agency", "Enterprise", "Startup",
                 "Government", "Healthcare", "Finance", "Other"],
    "Connection Degree": ["1st", "2nd", "3rd", "None"],
    "Lead Type": ["Direct Client", "Agency Partner", "Anthropic Partner",
                  "Hire (Arslan)"],
    "Deal Type": ["Project", "Retainer", "Staff Augmentation", "Partnership",
                  "Remote Role"],
    "Estimated Budget": ["<$5k", "$5k–$20k", "$20k–$50k", "$50k–$100k",
                         "$100k+", "Unknown"],
    "Priority": ["High", "Medium", "Low"],
    "Outreach Channel": ["Connection Note", "LinkedIn DM", "InMail", "Email",
                         "Both", "Referral", "Inbound", "Skip"],
    "From Email": ["arslan@electrocomit.com", "partnerships@electrocomit.com",
                   "info@electrocomit.com", "N/A (LinkedIn)"],
    "Outreach by": ["Arslan", "Faizan"],
    "Status": [s[1] for s in STATUS_STYLES if s[0] == "eq"] + ["New"],
    "Response Type": ["Positive", "Neutral", "Negative", "No Response"],
    "Assigned To": ["Arslan", "Faizan", "Both"],
}
# Above this many distinct existing values a dropdown stops being useful.
MAX_DROPDOWN_VALUES = 40

WIDTHS = {
    "Full Name": 160, "Title": 190, "Company": 180, "Industry": 150,
    "Location": 150, "LinkedIn URL": 200, "Email": 190,
    "Hook / Why Outreach": 260, "DM Content": 320, "Email Subject": 190,
    "Email Content": 320, "Internal Notes": 320, "Meeting Notes": 240,
    "Next Action": 260, "Response Summary": 240, "Interested In": 200,
    "Rating Reason": 280, "Win/Loss Reason": 200, "Lead Source": 190,
    "Follow-up 1 Notes": 220, "Follow-up 2 Notes": 220,
    "Follow-up 3 Notes": 220, "Cadence Stage": 130,
    # Activity Log
    "Target": 260, "Outcome": 320, "Agent": 150, "Source File": 130,
}
DEFAULT_WIDTH = 125
BODY_ROW_HEIGHT = 22

AGENT_COLORS = {
    "DM": "#BDD7EE", "EMAIL": "#CFE2F3", "FOLLOW-UP": "#FFE699",
    "LEAD RESEARCH": "#D9EAD3", "OPS": "#E3E3E3", "INFRA / OPS": "#E3E3E3",
    "CONTENT": "#FCE5CD", "ASSETS": "#EAD1DC", "PLANNING": "#D9D2E9",
    "COMPANY PAGE": "#D0E0E3", "PROFILE SETUP": "#D0E0E3",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def a1(idx: int) -> str:
    """0-based column index -> A1 letter(s)."""
    s = ""
    idx += 1
    while idx:
        idx, r = divmod(idx - 1, 26)
        s = chr(65 + r) + s
    return s


def txt(bold=False, size=10, color=None, italic=False):
    f = {"bold": bold, "fontSize": size, "italic": italic,
         "fontFamily": "Inter"}
    if color:
        f["foregroundColor"] = color
    return f


def rng(sheet_id, r0=None, r1=None, c0=None, c1=None):
    d = {"sheetId": sheet_id}
    if r0 is not None:
        d["startRowIndex"] = r0
    if r1 is not None:
        d["endRowIndex"] = r1
    if c0 is not None:
        d["startColumnIndex"] = c0
    if c1 is not None:
        d["endColumnIndex"] = c1
    return d


def cf(index, ranges, condition, fmt):
    return {"addConditionalFormatRule": {
        "index": index,
        "rule": {"ranges": ranges,
                 "booleanRule": {"condition": condition, "format": fmt}}}}


def cond(kind, value):
    m = {"eq": "TEXT_EQ", "prefix": "TEXT_STARTS_WITH",
         "contains": "TEXT_CONTAINS"}
    return {"type": m[kind], "values": [{"userEnteredValue": value}]}


def chip(bg, fg=None):
    f = {"backgroundColor": rgb(bg)}
    if fg:
        f["textFormat"] = {"foregroundColor": fg, "bold": True}
    return f


def sheet_meta(service, sid):
    meta = service.spreadsheets().get(spreadsheetId=sid).execute()
    out = {}
    for s in meta["sheets"]:
        p = s["properties"]
        out[p["title"]] = {
            "id": p["sheetId"],
            "rows": p.get("gridProperties", {}).get("rowCount", 1000),
            "cols": p.get("gridProperties", {}).get("columnCount", 26),
            "cf": len(s.get("conditionalFormats", [])),
            "bandings": [b["bandedRangeId"] for b in s.get("bandedRanges", [])],
        }
    return out


def read_values(service, sid, tab, rng_a1):
    return service.spreadsheets().values().get(
        spreadsheetId=sid, range=f"'{tab}'!{rng_a1}").execute().get("values", [])


def managed_cols(headers):
    """Columns whose data validation this script owns.

    Anything else -- e.g. dropdowns added by hand in the UI -- must be left
    alone, so a re-run never silently deletes someone's manual setup.
    """
    return [i for i, h in enumerate(headers)
            if h in DROPDOWNS or h in CHECKBOX_COLS or h in FREE_TEXT_COLS]


# ---------------------------------------------------------------------------
# Shared table styling
# ---------------------------------------------------------------------------
def style_table(sheet_id, headers, n_rows, header_row=0,
                header_colors=None, freeze_cols=0, header_height=42):
    """Header bar, freeze, banding, borders, widths, body typography."""
    n_cols = len(headers)
    reqs = []

    reqs.append({"updateSheetProperties": {
        "properties": {"sheetId": sheet_id, "gridProperties": {
            "frozenRowCount": header_row + 1,
            "frozenColumnCount": freeze_cols}},
        "fields": "gridProperties(frozenRowCount,frozenColumnCount)"}})

    # Header cells, tinted per section.
    colors = header_colors or [BRAND_NAVY] * n_cols
    run_start = 0
    for i in range(1, n_cols + 1):
        if i == n_cols or colors[i] != colors[run_start]:
            reqs.append({"repeatCell": {
                "range": rng(sheet_id, header_row, header_row + 1, run_start, i),
                "cell": {"userEnteredFormat": {
                    "backgroundColor": rgb(colors[run_start]),
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "MIDDLE",
                    "wrapStrategy": "WRAP",
                    "textFormat": txt(bold=True, size=10, color=WHITE)}},
                "fields": ("userEnteredFormat(backgroundColor,horizontalAlignment,"
                           "verticalAlignment,wrapStrategy,textFormat)")}})
            run_start = i

    reqs.append({"updateDimensionProperties": {
        "range": {"sheetId": sheet_id, "dimension": "ROWS",
                  "startIndex": header_row, "endIndex": header_row + 1},
        "properties": {"pixelSize": header_height}, "fields": "pixelSize"}})

    body_start = header_row + 1
    if n_rows > body_start:
        reqs.append({"repeatCell": {
            "range": rng(sheet_id, body_start, n_rows, 0, n_cols),
            "cell": {"userEnteredFormat": {
                "verticalAlignment": "MIDDLE",
                "wrapStrategy": "CLIP",
                "textFormat": txt(size=10, color=INK)}},
            "fields": "userEnteredFormat(verticalAlignment,wrapStrategy,textFormat)"}})
        reqs.append({"updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "ROWS",
                      "startIndex": body_start, "endIndex": n_rows},
            "properties": {"pixelSize": BODY_ROW_HEIGHT}, "fields": "pixelSize"}})

        # Zebra banding over the body only, so the header keeps its tints.
        # Deliberately unbounded (no endRowIndex): the banding then covers every
        # future row, so leads appended by the daily sync are striped on arrival.
        reqs.append({"addBanding": {"bandedRange": {
            "range": rng(sheet_id, body_start, None, 0, n_cols),
            "rowProperties": {"firstBandColor": WHITE,
                              "secondBandColor": STRIPE}}}})

    border = {"style": "SOLID", "color": GRID}
    reqs.append({"updateBorders": {
        "range": rng(sheet_id, header_row, max(n_rows, body_start + 1), 0, n_cols),
        "innerHorizontal": border, "innerVertical": border,
        "top": border, "bottom": border, "left": border, "right": border}})

    for i, h in enumerate(headers):
        w = 40 if not h.strip() else WIDTHS.get(h, DEFAULT_WIDTH)
        reqs.append({"updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "COLUMNS",
                      "startIndex": i, "endIndex": i + 1},
            "properties": {"pixelSize": w}, "fields": "pixelSize"}})

    return reqs


def number_formats(sheet_id, headers, n_rows):
    reqs = []

    def fmt(names, pattern, ftype, halign):
        for name in names:
            if name not in headers:
                continue
            i = headers.index(name)
            reqs.append({"repeatCell": {
                "range": rng(sheet_id, 1, max(n_rows, 2), i, i + 1),
                "cell": {"userEnteredFormat": {
                    "numberFormat": {"type": ftype, "pattern": pattern},
                    "horizontalAlignment": halign}},
                "fields": "userEnteredFormat(numberFormat,horizontalAlignment)"}})

    fmt(DATE_COLS, "yyyy-mm-dd", "DATE", "CENTER")
    fmt(CURRENCY_COLS, '"$"#,##0', "CURRENCY", "RIGHT")
    fmt(INT_COLS, "0", "NUMBER", "CENTER")
    return reqs


def validation(service, sid, tab, sheet_id, headers, n_rows, dry=False):
    """Dropdown chips + checkboxes, unioned with values already in the column."""
    reqs = []
    for i, h in enumerate(headers):
        r = rng(sheet_id, 1, None, i, i + 1)
        if h in FREE_TEXT_COLS:
            # Explicitly strip validation -- a rule with no condition clears it.
            reqs.append({"setDataValidation": {"range": r}})
            continue
        if h in CHECKBOX_COLS:
            reqs.append({"setDataValidation": {
                "range": r, "rule": {"condition": {"type": "BOOLEAN"}}}})
            continue
        if h not in DROPDOWNS:
            continue
        observed = []
        if not dry and n_rows > 1:
            col = read_values(service, sid, tab, f"{a1(i)}2:{a1(i)}{n_rows}")
            observed = sorted({c[0].strip() for c in col if c and c[0].strip()})
        values = list(DROPDOWNS[h])
        for v in observed:
            if v not in values:
                values.append(v)
        if len(values) > MAX_DROPDOWN_VALUES:
            continue  # too many variants for a dropdown to help
        reqs.append({"setDataValidation": {"range": r, "rule": {
            "condition": {"type": "ONE_OF_LIST",
                          "values": [{"userEnteredValue": v} for v in values]},
            "showCustomUi": True, "strict": False}}})
    return reqs


# ---------------------------------------------------------------------------
# Pipeline tab
# ---------------------------------------------------------------------------
def section_colors(headers):
    colors = [BRAND_NAVY] * len(headers)
    starts = []
    for _, key, hexc in SECTIONS:
        if isinstance(key, int):
            starts.append((key, hexc))
        elif key in headers:
            starts.append((headers.index(key), hexc))
    starts.sort()
    for n, (start, hexc) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(headers)
        for i in range(start, end):
            colors[i] = hexc
    return colors


def pipeline_rules(sheet_id, headers, n_rows):
    reqs = []
    idx = 0

    # Conditional-format ranges are unbounded, so every future row is chipped
    # the moment it is added -- no re-run needed after appending leads.
    def col_rng(name):
        i = headers.index(name)
        return [rng(sheet_id, 1, None, i, i + 1)]

    # Status chips
    if "Status" in headers:
        for kind, val, bg, fg in STATUS_STYLES:
            reqs.append(cf(idx, col_rng("Status"), cond(kind, val), chip(bg, fg)))
            idx += 1

    # Cadence Stage chips
    if "Cadence Stage" in headers:
        for kind, val, bg, fg in CADENCE_STYLES:
            reqs.append(cf(idx, col_rng("Cadence Stage"), cond(kind, val), chip(bg, fg)))
            idx += 1

    # Priority chips
    if "Priority" in headers:
        for kind, val, bg, fg in PRIORITY_STYLES:
            reqs.append(cf(idx, col_rng("Priority"), cond(kind, val), chip(bg, fg)))
            idx += 1

    # Outreach copy: drafted vs empty.
    for name in CONTENT_COLS:
        if name not in headers:
            continue
        r = col_rng(name)
        reqs.append(cf(idx, r, {"type": "NOT_BLANK"}, chip(CONTENT_DRAFTED_BG)))
        idx += 1
        reqs.append(cf(idx, r, {"type": "BLANK"}, chip(CONTENT_EMPTY_BG)))
        idx += 1

    # Next Action Date: overdue / today / due-soon, but only for live leads.
    if "Next Action Date" in headers and "Status" in headers:
        nad = a1(headers.index("Next Action Date"))
        st = a1(headers.index("Status"))
        # Handles both real date serials and the older ISO-text rows.
        val = (f'IFERROR(IF(ISNUMBER(${nad}2),${nad}2,DATEVALUE(${nad}2)),9^9)')
        live = f'NOT(REGEXMATCH(${st}2&"","{DEAD_STATUS_RE}"))'
        base = f'${nad}2<>"", {live}'
        for expr, bg, fg in [
            (f'=AND({base}, {val}<TODAY())', "#E06C6C", WHITE),
            (f'=AND({base}, {val}=TODAY())', "#FFB570", None),
            (f'=AND({base}, {val}>TODAY(), {val}<=TODAY()+3)', "#FFE9B8", None),
        ]:
            reqs.append(cf(idx, col_rng("Next Action Date"),
                           {"type": "CUSTOM_FORMULA",
                            "values": [{"userEnteredValue": expr}]},
                           chip(bg, fg)))
            idx += 1

    # Score gradients
    for name, (lo, mid, hi, c_lo, c_mid, c_hi) in GRADIENTS.items():
        if name not in headers:
            continue
        reqs.append({"addConditionalFormatRule": {"index": idx, "rule": {
            "ranges": col_rng(name),
            "gradientRule": {
                "minpoint": {"color": rgb(c_lo), "type": "NUMBER", "value": str(lo)},
                "midpoint": {"color": rgb(c_mid), "type": "NUMBER", "value": str(mid)},
                "maxpoint": {"color": rgb(c_hi), "type": "NUMBER", "value": str(hi)}}}}})
        idx += 1

    # Whole-row mute for dead leads. Text colour only, so banding still shows
    # and the Status chip above keeps its own styling.
    if "Status" in headers:
        st = a1(headers.index("Status"))
        reqs.append(cf(idx, [rng(sheet_id, 1, None, 0, len(headers))],
                       {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue":
                        f'=REGEXMATCH(${st}2&"","{DEAD_STATUS_RE}")'}]},
                       {"textFormat": {"foregroundColor": MUTED_INK}}))
        idx += 1

    return reqs


# ---------------------------------------------------------------------------
# Cadence Reminders tab (banner row 1, blank row 2, header row 3, data row 4+)
# ---------------------------------------------------------------------------
def reminder_requests(sheet_id, headers, n_rows):
    reqs = []
    n_cols = max(len(headers), 6)

    # No-op if nothing is merged; guards against a leftover banner merge, which
    # would make the frozen-column request below fail.
    reqs.append({"unmergeCells": {"range": rng(sheet_id, 0, 1, 0, n_cols)}})
    reqs.append({"repeatCell": {
        "range": rng(sheet_id, 0, 1, 0, n_cols),
        "cell": {"userEnteredFormat": {
            "backgroundColor": rgb("#8A5A0B"),
            "horizontalAlignment": "LEFT",
            "verticalAlignment": "MIDDLE",
            "padding": {"left": 12},
            "textFormat": txt(bold=True, size=13, color=WHITE)}},
        "fields": ("userEnteredFormat(backgroundColor,horizontalAlignment,"
                   "verticalAlignment,padding,textFormat)")}})
    # Deliberately NOT merged: the banner text overflows the empty cells to its
    # right on its own, and a merged cell spanning A:F would block the frozen
    # name/company columns below it.
    for r, h in ((0, 34), (1, 8)):
        reqs.append({"updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "ROWS",
                      "startIndex": r, "endIndex": r + 1},
            "properties": {"pixelSize": h}, "fields": "pixelSize"}})

    reqs += style_table(sheet_id, headers, n_rows, header_row=2,
                        header_colors=[BRAND_NAVY] * n_cols,
                        freeze_cols=2, header_height=32)

    if "Cadence Stage" in headers and n_rows > 3:
        i = headers.index("Cadence Stage")
        r = [rng(sheet_id, 3, None, i, i + 1)]
        for n, (kind, val, bg, fg) in enumerate(CADENCE_STYLES):
            reqs.append(cf(n, r, cond(kind, val), chip(bg, fg)))
    return reqs


# ---------------------------------------------------------------------------
# Legend tab
# ---------------------------------------------------------------------------
def legend_rows():
    rows = [["ElectroCom BD Pipeline — colour legend", "", ""],
            ["", "", ""],
            ["COLUMN SECTIONS", "", "Header bar colour by block of columns"]]
    for label, _, hexc in SECTIONS:
        rows.append([label, "", hexc])
    rows += [["", "", ""], ["STATUS", "", "Chip colour in the Status column"]]
    for kind, val, hexc, _ in STATUS_STYLES:
        rows.append([val + ("…" if kind == "prefix" else ""), "", hexc])
    rows += [["", "", ""], ["CADENCE STAGE", "", ""]]
    for kind, val, hexc, _ in CADENCE_STYLES:
        rows.append([val + ("…" if kind != "eq" else ""), "", hexc])
    rows += [["", "", ""], ["PRIORITY", "", ""]]
    for _, val, hexc, _ in PRIORITY_STYLES:
        rows.append([val, "", hexc])
    rows += [["", "", ""],
             ["OUTREACH COPY", "", " / ".join(CONTENT_COLS)],
             ["Drafted", "", CONTENT_DRAFTED_BG],
             ["Empty", "", CONTENT_EMPTY_BG]]
    rows += [
        ["", "", ""],
        ["NEXT ACTION DATE", "", "Live leads only — dead statuses are exempt"],
        ["Overdue", "", "#E06C6C"],
        ["Due today", "", "#FFB570"],
        ["Due within 3 days", "", "#FFE9B8"],
        ["", "", ""],
        ["SCORES", "", "Lead Score / Profile / Company ratings, 1→10"],
        ["Low", "", "#F8696B"],
        ["Mid", "", "#FFEB84"],
        ["High", "", "#63BE7B"],
        ["", "", ""],
        ["Days Since Last Touch", "", "Green when fresh → red past ~20 days"],
        ["", "", ""],
        ["Greyed-out rows", "", "Status = Skip / Not Relevant / Closed / Lost / On Hold"],
    ]
    return rows


def legend_requests(sheet_id, rows):
    reqs = [
        {"updateSheetProperties": {
            "properties": {"sheetId": sheet_id,
                           "gridProperties": {"frozenRowCount": 1}},
            "fields": "gridProperties.frozenRowCount"}},
        {"repeatCell": {
            "range": rng(sheet_id, 0, 1, 0, 3),
            "cell": {"userEnteredFormat": {
                "backgroundColor": rgb(BRAND_NAVY),
                "verticalAlignment": "MIDDLE",
                "padding": {"left": 12},
                "textFormat": txt(bold=True, size=13, color=WHITE)}},
            "fields": ("userEnteredFormat(backgroundColor,verticalAlignment,"
                       "padding,textFormat)")}},
        {"mergeCells": {"range": rng(sheet_id, 0, 1, 0, 3),
                        "mergeType": "MERGE_ALL"}},
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "ROWS",
                      "startIndex": 0, "endIndex": 1},
            "properties": {"pixelSize": 36}, "fields": "pixelSize"}},
    ]
    for i, w in ((0, 280), (1, 90), (2, 420)):
        reqs.append({"updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "COLUMNS",
                      "startIndex": i, "endIndex": i + 1},
            "properties": {"pixelSize": w}, "fields": "pixelSize"}})

    # Col B is the swatch, painted with the hex that col C spells out; section
    # rows (ALL CAPS label, no hex) become sub-headings instead.
    for r, row in enumerate(rows):
        if r == 0:
            continue
        label, _, third = row[0], row[1], row[2]
        is_heading = label.isupper() and label and not third.startswith("#")
        if is_heading:
            reqs.append({"repeatCell": {
                "range": rng(sheet_id, r, r + 1, 0, 3),
                "cell": {"userEnteredFormat": {
                    "backgroundColor": rgb("#E8EEF7"),
                    "textFormat": txt(bold=True, size=10, color=rgb(BRAND_NAVY))}},
                "fields": "userEnteredFormat(backgroundColor,textFormat)"}})
        elif third.startswith("#"):
            reqs.append({"repeatCell": {
                "range": rng(sheet_id, r, r + 1, 1, 2),
                "cell": {"userEnteredFormat": {"backgroundColor": rgb(third)}},
                "fields": "userEnteredFormat.backgroundColor"}})
    return reqs


def ensure_legend_tab(service, sid, meta):
    if LEGEND_TAB in meta:
        return meta[LEGEND_TAB]["id"]
    res = service.spreadsheets().batchUpdate(spreadsheetId=sid, body={"requests": [
        {"addSheet": {"properties": {
            "title": LEGEND_TAB,
            "gridProperties": {"rowCount": 120, "columnCount": 3}}}}]}).execute()
    return res["replies"][0]["addSheet"]["properties"]["sheetId"]


# ---------------------------------------------------------------------------
def clear_existing(service, sid, meta, headers_by_tab):
    """Drop what this script owns so a re-run stays idempotent.

    Validation is cleared PER MANAGED COLUMN, never across the full width:
    dropdowns added by hand in the UI (e.g. on the outreach-copy columns) live
    on columns this script does not manage, and wiping them on every re-run
    would silently destroy someone's setup.
    """
    reqs = []
    for tab, headers in headers_by_tab.items():
        if tab not in meta:
            continue
        info = meta[tab]
        for bid in info["bandings"]:
            reqs.append({"deleteBanding": {"bandedRangeId": bid}})
        for i in range(info["cf"] - 1, -1, -1):
            reqs.append({"deleteConditionalFormatRule":
                         {"sheetId": info["id"], "index": i}})
        for c in managed_cols(headers):
            reqs.append({"setDataValidation": {
                "range": rng(info["id"], 1, None, c, c + 1)}})
    if reqs:
        service.spreadsheets().batchUpdate(
            spreadsheetId=sid, body={"requests": reqs}).execute()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    sid = cfg.get("spreadsheet_id")
    if not sid:
        sys.exit("No spreadsheet_id in sheet_config.json — run the sync first.")
    service = get_service()
    meta = sheet_meta(service, sid)

    tabs = [t for t in (PIPELINE_TAB, ACTIVITY_TAB, REMINDER_TAB) if t in meta]

    # Headers are needed before clearing, so validation is only dropped from the
    # columns this script actually manages.
    headers_by_tab = {}
    if PIPELINE_TAB in meta:
        headers_by_tab[PIPELINE_TAB] = read_values(
            service, sid, PIPELINE_TAB, "A1:BZ1")[0]
    if ACTIVITY_TAB in meta:
        headers_by_tab[ACTIVITY_TAB] = read_values(
            service, sid, ACTIVITY_TAB, "A1:Z1")[0]
    reminder_vals = (read_values(service, sid, REMINDER_TAB, "A1:F1000")
                     if REMINDER_TAB in meta else [])
    if REMINDER_TAB in meta:
        # Header row is the 3rd (banner, blank, headers).
        headers_by_tab[REMINDER_TAB] = reminder_vals[2] if len(
            reminder_vals) > 2 else ["Name", "Company", "Cadence Stage", "Days",
                                     "Next Action", "Next Action Date"]
    if LEGEND_TAB in meta:
        headers_by_tab[LEGEND_TAB] = []   # no managed columns; clears CF/banding

    if not args.dry_run:
        clear_existing(service, sid, meta, headers_by_tab)
        meta = sheet_meta(service, sid)

    reqs = []
    summary = []

    # ---- Pipeline ----
    if PIPELINE_TAB in meta:
        info = meta[PIPELINE_TAB]
        headers = headers_by_tab[PIPELINE_TAB]
        n_rows = max(len(read_values(service, sid, PIPELINE_TAB, "C1:C")), 2)
        srows = info["rows"]
        colors = section_colors(headers)
        reqs += style_table(info["id"], headers, srows,
                            header_colors=colors, freeze_cols=5)
        reqs += number_formats(info["id"], headers, srows)
        reqs += pipeline_rules(info["id"], headers, srows)
        reqs += validation(service, sid, PIPELINE_TAB, info["id"], headers,
                           n_rows, dry=args.dry_run)
        summary.append(f"{PIPELINE_TAB}: {len(headers)} cols, {n_rows - 1} rows")

    # ---- Activity Log ----
    if ACTIVITY_TAB in meta:
        info = meta[ACTIVITY_TAB]
        headers = headers_by_tab[ACTIVITY_TAB]
        n_rows = max(len(read_values(service, sid, ACTIVITY_TAB, "A1:A")), 2)
        srows = info["rows"]
        reqs += style_table(info["id"], headers, srows,
                            header_colors=[BRAND_NAVY] * len(headers),
                            freeze_cols=3)
        reqs += number_formats(info["id"], headers, srows)
        if "Agent" in headers:
            i = headers.index("Agent")
            r = [rng(info["id"], 1, None, i, i + 1)]
            for n, (name, hexc) in enumerate(AGENT_COLORS.items()):
                reqs.append(cf(n, r, cond("eq", name), chip(hexc)))
        summary.append(f"{ACTIVITY_TAB}: {len(headers)} cols, {n_rows - 1} rows")

    # ---- Cadence Reminders ----
    if REMINDER_TAB in meta:
        info = meta[REMINDER_TAB]
        headers = headers_by_tab[REMINDER_TAB]
        n_rows = max(len(reminder_vals), 4)
        reqs += reminder_requests(
            info["id"], headers, info["rows"])
        summary.append(f"{REMINDER_TAB}: {n_rows - 3} due rows")

    # ---- Legend ----
    rows = legend_rows()
    if not args.dry_run:
        lid = ensure_legend_tab(service, sid, meta)
        service.spreadsheets().values().update(
            spreadsheetId=sid, range=f"'{LEGEND_TAB}'!A1",
            valueInputOption="RAW", body={"values": rows}).execute()
        reqs += legend_requests(lid, rows)
        summary.append(f"{LEGEND_TAB}: {len(rows)} rows")

    if args.dry_run:
        print(f"[dry-run] {len(reqs)} formatting requests across {len(tabs)} tabs")
        for line in summary:
            print("  -", line)
        return 0

    # Send in chunks; a single batch of a few thousand requests can time out.
    CHUNK = 250
    for i in range(0, len(reqs), CHUNK):
        service.spreadsheets().batchUpdate(
            spreadsheetId=sid, body={"requests": reqs[i:i + CHUNK]}).execute()

    print(f"Applied {len(reqs)} formatting requests.")
    for line in summary:
        print("  -", line)
    print(cfg.get("spreadsheet_url", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
