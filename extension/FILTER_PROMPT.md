# Filtering prompt for Claude Code

Paste this into Claude Code with the exported CSV in the working directory.

---

I have a LinkedIn Sales Navigator lead export at `leads.csv`. Filter it to my ICP.

**ICP:**
- <!-- e.g. Seniority: Director level or above -->
- <!-- e.g. Function: Engineering or Product -->
- <!-- e.g. Company size: 50-1000 employees -->
- <!-- e.g. Industry: B2B SaaS, fintech. Exclude agencies and consultancies. -->
- <!-- e.g. Exclude anyone under 12 months in role -->

**How to do it — this part matters:**

1. Read `leads.csv`. Each row has a `row` integer and qualifying signals
   (`headline`, `currentTitle`, `companyName`, `companyStaffRange`, `industry`,
   `location`, `seniority`, `yearsInRole`, `yearsAtCompany`).
2. Judge each lead against the ICP and write your decisions to `decisions.json`
   as `[{"row": 1, "keep": true, "reason": "..."}, ...]`. One entry per row,
   every row accounted for.
3. Then write a short Python script that reads `leads.csv` and `decisions.json`
   and emits `leads_filtered.csv` containing only the kept rows, with all
   original columns unchanged.
4. Run it, then verify nothing went missing:

   ```bash
   python3 enrich/check_filter.py leads.csv leads_filtered.csv -d decisions.json
   ```

   It must exit 0. If it reports rows with no decision, judge those and re-run.
5. Report the counts: total in, kept, dropped, and the most common drop reasons.

**Do not retype or regenerate the lead rows yourself.** Your judgement goes in
`decisions.json`; the row copying is done by the script. That keeps names,
URNs and encodings byte-identical, and makes the filter auditable — I can read
`decisions.json` to see why any lead was dropped and re-run step 3 after
adjusting the ICP without re-judging everything.
