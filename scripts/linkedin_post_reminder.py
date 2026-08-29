#!/usr/bin/env python3
"""LinkedIn post reminder — surfaces the post that is due this Saturday.

Reads content/linkedin/2026-09-post-schedule.md, finds the row in the schedule
table whose date is today (or the most recent past Saturday still marked ready),
and prints that week's short post body so the cron log (scripts/sync.log)
carries it. Also fires a desktop notification when notify-send is available.

Stdlib only, no Google API and no venv needed.

Run:  python3 scripts/linkedin_post_reminder.py [--date YYYY-MM-DD]
"""
import os
import re
import subprocess
import sys
from datetime import date, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCHEDULE = os.path.join(ROOT, 'content', 'linkedin', '2026-09-post-schedule.md')

# | 1 | 2026-08-29 | AWS Bedrock AgentCore | ready |
ROW = re.compile(r'^\|\s*(\d+)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|')


def today():
    for i, a in enumerate(sys.argv):
        if a == '--date' and i + 1 < len(sys.argv):
            return datetime.strptime(sys.argv[i + 1], '%Y-%m-%d').date()
    return date.today()


def load(path):
    with open(path, encoding='utf-8') as fh:
        return fh.read()


def schedule_rows(text):
    out = []
    for line in text.splitlines():
        m = ROW.match(line)
        if m:
            out.append({
                'week': int(m.group(1)),
                'date': datetime.strptime(m.group(2), '%Y-%m-%d').date(),
                'topic': m.group(3).strip(),
                'status': m.group(4).strip().lower(),
            })
    return out


def short_post(text, week, when):
    """Pull the first fenced block under the Part 1 heading for this week."""
    head = re.compile(r'^## Week %d — %s\b' % (week, when.isoformat()), re.M)
    m = head.search(text)
    if not m:
        return None
    body = text[m.end():]
    fence = re.search(r'```\n(.*?)\n```', body, re.S)
    return fence.group(1).strip() if fence else None


def notify(title, body):
    try:
        subprocess.run(['notify-send', '-u', 'normal', title, body[:400]],
                       check=False, timeout=10)
    except (FileNotFoundError, subprocess.SubprocessError):
        pass  # headless or no libnotify, the log line is the fallback


def main():
    td = today()
    if not os.path.exists(SCHEDULE):
        print('LinkedIn reminder: schedule file missing at %s' % SCHEDULE)
        return 1

    text = load(SCHEDULE)
    rows = schedule_rows(text)
    due = [r for r in rows if r['date'] == td and r['status'] == 'ready']

    stamp = td.strftime('%Y-%m-%d (%A)')
    if not due:
        upcoming = sorted(r for r in
                          [(x['date'], x['week'], x['topic']) for x in rows
                           if x['date'] > td and x['status'] == 'ready'])
        print('LinkedIn reminder %s: nothing scheduled today.' % stamp)
        if upcoming:
            d, w, t = upcoming[0]
            print('   Next: week %d on %s — %s' % (w, d.isoformat(), t))
        else:
            print('   Schedule is exhausted. Time to plan the next month.')
        return 0

    r = due[0]
    banner = '📣 LinkedIn post due today — week %d: %s' % (r['week'], r['topic'])
    print('%s  [%s]' % (banner, stamp))
    post = short_post(text, r['week'], r['date'])
    if post:
        print('-' * 70)
        print(post)
        print('-' * 70)
    print('Full draft + alt hook + first comment: %s' % SCHEDULE)
    print('After posting: mark the row "posted" and log it in reports/%s.md' % td.isoformat())
    notify(banner, post or r['topic'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
