#!/usr/bin/env python3
"""Cadence reminder — surfaces every lead that needs a touch today.

Reads the BD Pipeline sheet, finds leads whose next touch is DUE or OVERDUE
(using the sheet's own Cadence Stage column + Next Action Date), and writes a
live reminder to a dedicated "Cadence Reminders" tab. Also prints the list so
the cron log (scripts/sync.log) captures it.

A lead "needs a touch" when its Cadence Stage (BE) is past due (starts with
OVERDUE) and it is still on an active cadence status (not On Hold / Closed /
Skip / Won / Lost / Replied). This mirrors the overdue queue in pipeline_health,
so scheduled/future touches and undecided "New" send-queue leads are excluded.

Run:  scripts/.venv/bin/python scripts/cadence_reminder.py [--date YYYY-MM-DD]
"""
import sys, os
from datetime import date, datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SID = '1mhNjCxkgOr-sZ3yRS0MxcpFAJAf0PYNzxSfEck5q51w'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN = os.path.join(HERE, 'token.json')
REMINDER_TAB = 'Cadence Reminders'

# statuses that are OFF the active cadence — never need a touch
INACTIVE = {'on hold', 'skip', 'not relevant', 'won', 'lost', 'nurture'}

def today():
    for i, a in enumerate(sys.argv):
        if a == '--date' and i + 1 < len(sys.argv):
            return datetime.strptime(sys.argv[i + 1], '%Y-%m-%d').date()
    return date.today()

def parse_d(s):
    try:
        return datetime.strptime(s.strip(), '%Y-%m-%d').date()
    except Exception:
        return None

def needs_touch(stage, status, nad, td):
    st = (status or '').strip().lower()
    if any(k in st for k in INACTIVE) or st.startswith('closed'):
        return False
    return (stage or '').strip().upper().startswith('OVERDUE')

def main():
    creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
    svc = build('sheets', 'v4', credentials=creds)
    rows = svc.spreadsheets().values().get(spreadsheetId=SID, range='Pipeline!A1:BE1500').execute().get('values', [])
    hdr = rows[0]
    def idx(n): return hdr.index(n)
    def g(r, i): return (r[i] if len(r) > i else '').strip()
    td = today()

    due = []
    for r in rows[1:]:
        nm = g(r, idx('Full Name'))
        if not nm:
            continue
        # skip non-lead / curation placeholder rows
        low = nm.lower()
        if 'curation' in low or low.startswith('lead list') or not g(r, idx('Company')):
            continue
        stage = g(r, idx('Cadence Stage')) if 'Cadence Stage' in hdr else ''
        if needs_touch(stage, g(r, idx('Status')), g(r, idx('Next Action Date')), td):
            days = g(r, idx('Days Since Last Touch')) if 'Days Since Last Touch' in hdr else ''
            due.append((nm, g(r, idx('Company')), stage or g(r, idx('Status')),
                        days, g(r, idx('Next Action')), g(r, idx('Next Action Date'))))

    def sortkey(x):
        try: return -int(x[3])
        except Exception: return 0
    due.sort(key=sortkey)

    stamp = td.strftime('%Y-%m-%d')
    if due:
        banner = '⏰ %d lead(s) need a touch as of %s' % (len(due), stamp)
    else:
        banner = '✅ Cadence clear as of %s — no touches due' % stamp
    print(banner)
    for d in due:
        print('   %-26s | %-24s | %-14s | %sd due | %s' % (d[0][:26], d[1][:24], d[2][:14], d[3], d[4][:40]))

    # write the reminder tab
    ensure_tab(svc)
    values = [[banner], [], ['Name', 'Company', 'Cadence Stage', 'Days', 'Next Action', 'Next Action Date']]
    for d in due:
        values.append([d[0], d[1], d[2], d[3], d[4], d[5]])
    # clear then write
    svc.spreadsheets().values().clear(spreadsheetId=SID, range="'%s'!A1:F1000" % REMINDER_TAB).execute()
    svc.spreadsheets().values().update(
        spreadsheetId=SID, range="'%s'!A1" % REMINDER_TAB,
        valueInputOption='RAW', body={'values': values}).execute()
    print('Wrote reminder to "%s" tab (%d rows).' % (REMINDER_TAB, len(due)))

def ensure_tab(svc):
    meta = svc.spreadsheets().get(spreadsheetId=SID, fields='sheets/properties').execute()
    titles = [s['properties']['title'] for s in meta['sheets']]
    if REMINDER_TAB not in titles:
        svc.spreadsheets().batchUpdate(spreadsheetId=SID, body={
            'requests': [{'addSheet': {'properties': {'title': REMINDER_TAB, 'index': 1,
                        'gridProperties': {'rowCount': 500, 'columnCount': 6}}}}]}).execute()

if __name__ == '__main__':
    main()
