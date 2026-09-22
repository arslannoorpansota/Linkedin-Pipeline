# Shortlist + note drafting prompt (filter pass 2)

Run this after `enrich.py`. Paste into Claude Code from the project root.

---

I have enriched LinkedIn leads at `data/out/leads_flat.json`. Each record has
the lead's profile (About, full role history, skills), their company (size,
industry, description), and often their recent posts under `activity`.

Shortlist the ones genuinely worth contacting, and draft a connection note for
each.

**Who to keep:**
- <!-- e.g. Actually owns the buying decision for developer tooling -->
- <!-- e.g. Company is 50-1000 and not an agency or consultancy -->
- <!-- e.g. Been in the role 12+ months -->
- <!-- e.g. Drop anyone whose company already uses a direct competitor -->

**What I'm reaching out about:**
<!-- One or two sentences. This is what the notes have to land. -->

**Output `data/shortlist.json`** — an array of:

```json
{
  "key": "<salesUrn, memberId or publicIdentifier from the record>",
  "keep": true,
  "reason": "<one line: why this person, now>",
  "note": "<the connection note>"
}
```

Include entries with `"keep": false` for anyone you rejected, with a `reason`
and no note — I want to see what you dropped and why.

**Note rules:**
- **Under 300 characters.** LinkedIn's connection-note limit. Count them.
- Open with something specific to *them* — a post they wrote, a detail from
  their role history, something about their company. If you have nothing
  specific, say so in the reason and set `keep: false` rather than writing
  filler.
- No "I came across your profile", no "I hope this finds you well", no
  flattery about their "impressive background".
- Plain sentences. Write it the way one person messages another.
- Do not invent facts. Everything in the note must be traceable to the record.

Then build the worksheet:

```bash
cd enrich && python3 outreach.py ../data/shortlist.json \
  -e ../data/out/leads_flat.json -o ../data/outreach.html
```

Tell me the counts: shortlisted, rejected, and how many you couldn't find a
specific hook for.
