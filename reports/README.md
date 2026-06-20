# Daily Reports — Reporting Protocol

> Every agent in this workspace logs its output here. One file per day.
> This is mandatory: after **any** agent run, the result is appended to that day's report.

---

## 1. File Convention

- One report file per calendar day: `reports/YYYY-MM-DD.md`
- File name uses today's date (e.g. `2026-06-20.md`)
- If the day's file does not exist yet, **create it** from the template below before appending
- Never overwrite a day's file — always **append** a new entry to the bottom

---

## 2. Which Agents Report

| Agent | Logs when |
|---|---|
| `LEAD_RESEARCH` | After every qualify/skip verdict |
| `DM_LINKEDIN` | After every connection note + DM generated |
| `EMAIL_OUTREACH` | After every cold email generated |
| `FOLLOW_UP` | After every follow-up message generated |

---

## 3. Daily File Template

When creating a new day's file, start it with this header:

```markdown
# Daily Report — YYYY-MM-DD

> Day: <Weekday>
> All agent activity for this date is logged below, newest at the bottom.

## Summary
- Leads researched: 0
- DMs written: 0
- Emails written: 0
- Follow-ups written: 0

---

## Activity Log
```

Update the **Summary** counters each time you append an entry.

---

## 4. Entry Format (append one per agent run)

Each entry MUST start with the date and the agent name:

```markdown
### YYYY-MM-DD — <AGENT NAME> — <Lead/Person/Company>

- **Time:** <HH:MM, if known, else "—">
- **Agent:** Lead Research / DM / Email / Follow-Up
- **Target:** <name + company>
- **Lead type:** <Direct Client / Agency Partner / Anthropic Partner / Hire>
- **Outcome:** <one line — e.g. "Qualified 8/10", "DM drafted", "FU2 sent">
- **Output:**

  <the full agent output block, indented or fenced>

- **Next action:** <what happens next, if any>

---
```

---

## 5. Rules

1. **Always date-stamp.** Every entry begins with `### YYYY-MM-DD`. The day file is also dated in its title.
2. **Append, never replace.** New runs go at the bottom of the current day's file.
3. **One entry per agent run.** If you generate 3 DMs in one session, that's 3 entries.
4. **Update the Summary counters** at the top of the day file after each append.
5. **Carry the full output.** Paste the agent's actual output block so the report is self-contained.
