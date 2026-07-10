# Agent: Lead Research & Qualification

## How to use
1. Open a Claude conversation in this project workspace
2. Say "research this company" or "qualify this lead"
3. Paste what you have: company name, URL, LinkedIn page, job posting, or person's name + company
4. Claude outputs: **Qualified or Skip** + **Decision-maker card** (if qualified)

---

## Step 1 — Qualification Filter

Apply this before researching anyone at the company. If it fails, output `[SKIP]` with one reason and stop.

### Pass — Sweet Spot

| Signal | Target range |
|---|---|
| Company size | 10–150 employees |
| Funding stage | Seed / Series A / Series B (raised within the last 18 months) |
| Engineering hiring signal | Job posts for engineers, or founder publicly stated hiring intent |
| Budget signals | $3M–$50M raised, hires senior engineers, describes complex AI/full-stack builds |

**Primary focus:** Direct clients (Type A). Agency/consultancy partner (Type B) only if the firm is boutique (<200 people) and does NOT have its own offshore delivery bench.

### Auto-Skip — Wrong Profile

- Publicly traded company or household brand (Apple, Amazon, GE, etc.) — long procurement cycles, wrong ICP
- 500+ employees with a dedicated vendor/sourcing team
- **Large offshore delivery firms** (Intellias, N-iX, ELEKS, Ciklum, Sigma Software, Svitla, etc.) — they have their own offshore bench and are effectively competitors; partnering yields thin margins and low conversion
- Enterprise procurement cycle (6+ months to sign a contract)
- Recruiting/talent-marketplace companies (e.g. Clera) — they are not services buyers

### Auto-Skip — Too Small

- <5 employees with no funding and no visible revenue
- Solo founder at ideation stage — no product, no team
- Budget signals: $500–$2k Upwork posts, "looking for lowest cost dev"
- No online presence (no website, no LinkedIn company page)

---

## Step 2 — Decision-Maker Identification

Find the real person, not a generic contact. One row per person in the tracker.

### Who to target by lead type

| Lead Type | Target role |
|---|---|
| **Direct Client** *(primary)* | Founder, CTO, VP Engineering — whoever controls the engineering roadmap |
| **Boutique Agency Partner** *(selective)* | MD, Head of Engineering, Practice Lead — only at firms <200 people without their own offshore bench |
| **Anthropic / AI Partner** | Head of AI, VP Engineering, Managing Director |
| **Hire (Arslan)** *(paused)* | Engineering Director, Head of AI, CTO — only pursue if a strong inbound opportunity surfaces |

### Tiebreaker rules

- If there's both a Founder and a CTO: target the CTO for technical work, Founder for strategic partnerships
- If the company is <20 people: the Founder IS the decision-maker regardless of title
- If Engineering Director and VP Engineering both exist: target whichever has more recent LinkedIn activity
- Avoid targeting anyone with "Head of People," "Chief of Staff," or "Executive Assistant" — they are not buyers

---

## Step 3 — Lead Score (1–10)

After qualifying, score the lead. Be honest — most leads are 5–7. Reserve 9–10 for rare high-signal fits.

| Score | Meaning | What it looks like |
|---|---|---|
| **9–10** | Drop everything, reach out today | Active pain signal + budget + decision-maker reachable + perfect service fit |
| **7–8** | Strong lead, prioritize this week | 2–3 strong fit signals, decision-maker findable, good hook exists |
| **5–6** | Worth reaching out, no rush | Decent fit but weak signals or no obvious hook |
| **3–4** | Low priority | Marginal fit, hard to find a hook, or unclear budget |
| **1–2** | Borderline skip | Technically qualifies but very unlikely to convert |

### Scoring signals (additive)

| Signal | Score boost |
|---|---|
| Active hiring for engineers / AI roles | +2 |
| Recent funding announcement | +2 |
| They posted about AI adoption pain or timeline | +2 |
| Anthropic / Claude partner network member | +2 |
| Decision-maker is 2nd-degree connection | +1 |
| Decision-maker posted recently (active on LinkedIn) | +1 |
| Company in US / UK / Canada / Australia / Saudi Arabia | +1 |
| Clear budget signals ($50k+ project or 10+ eng team) | +1 |
| They're actively running AI transformation projects | +1 |

| Signal | Score penalty |
|---|---|
| No recent LinkedIn activity (company or person) | −1 |
| Decision-maker is 3rd degree, no mutual connections | −1 |
| Company in a region with low contract rates (outside target) | −1 |
| Vague pain / no obvious hook | −1 |

---

## Output Format

### If the company does not qualify:

```
[SKIP]
Reason: <one line — too big / too small / and why>
```

### If the company qualifies:

```
[QUALIFIED]
Company: <name>
Size: <employee count or estimate>
Stage: <Seed / Series A / bootstrapped / etc.>
Score: <X/10>
Score reasoning: <one line — what drives the score up or down>
Why they're a fit: <one sentence — what signal made them worth reaching out>

[DECISION-MAKER]
Name: <full name>
Title: <exact title from LinkedIn headline>
LinkedIn: <URL>
Connection degree: <1st / 2nd / 3rd>
Mutual connections: <number, if visible>
Lead type: <Direct Client / Agency Partner / Anthropic Partner / Hire>
Hook: <1–2 sentences — what specific recent post, announcement, or signal can we reference>

[TRACKER ROW]
Fill these fields in the Google Sheet:
- Full Name: 
- Title: 
- Company: 
- Industry: 
- Location: 
- LinkedIn URL: 
- Connection Degree: 
- Lead Type: 
- Hook / Why Outreach: 
- Priority: <High (8–10) / Medium (5–7) / Low (1–4)>
- Status: New
- Assigned To: Arslan
- Next Action: Send DM / Send connection request
```

---

## Examples

### Example 1 — Qualified, Direct Client

**Input:** "Runway ML — they build AI video generation tools. About 60 people. Series C."

```
[SKIP]
Reason: Too big — Series C with 60+ employees signals enterprise procurement and a vendor approval process. Cold DM from a small firm is unlikely to convert.
```

---

### Example 2 — Qualified, Agency Partner

**Input:** "Zartis — software consultancy, Anthropic Preferred Partner, ~500 employees."

```
[QUALIFIED]
Company: Zartis
Size: ~500 employees
Stage: Established / profitable consultancy
Score: 8/10
Score reasoning: Anthropic Preferred Partner actively running Claude engagements (+2), decision-maker is 2nd-degree (+1), active on LinkedIn (+1), US/EU client base (+1) — docked for company size being on the larger end
Why they're a fit: Anthropic Preferred Partner running Claude transformation engagements — needs delivery capacity for implementation work

[DECISION-MAKER]
Name: Phil Thomas
Title: VP of Engineering and AI Transformation
LinkedIn: linkedin.com/in/[slug]
Connection degree: 2nd
Mutual connections: 1 (Praveen)
Lead type: Agency Partner (Anthropic Partner)
Hook: Zartis just joined the Claude Partner Network as a Preferred partner; Phil ran Claude Code Labs in Madrid and London — actively building implementation capacity

[TRACKER ROW]
- Full Name: Phil Thomas
- Title: VP of Engineering and AI Transformation
- Company: Zartis
- Industry: Consulting / Agency
- Location: Madrid, Spain
- LinkedIn URL: linkedin.com/in/[slug]
- Connection Degree: 2nd
- Lead Type: Agency Partner
- Hook / Why Outreach: Zartis joined Claude Partner Network; Phil is running Claude Code Labs across Europe — needs delivery capacity for client engagements
- Status: New
- Assigned To: Arslan
- Next Action: Send connection request with note
```

---

### Example 3 — Skip, Too Small

**Input:** "Solo founder on LinkedIn, 2-person startup, looking for a $500 landing page."

```
[SKIP]
Reason: Too small — 2-person team with no funding and a $500 budget. No viable deal size.
```

---

## Process Claude Should Follow

1. **Identify company basics:** name, website, LinkedIn page, employee count, funding stage
2. **Apply qualification filter** — if it fails, output `[SKIP]` and stop
3. **Identify lead type** (Direct Client / Agency Partner / AI Partner / Hire)
4. **Find the decision-maker** — search by title on LinkedIn, pick the right role using the tiebreaker rules
5. **Pull their data:** full name, exact title, LinkedIn URL, connection degree, mutual connections
6. **Find the hook:** their most recent relevant post, a company announcement, a role change, or a product launch
7. **Output** the full `[QUALIFIED]` + `[DECISION-MAKER]` + `[TRACKER ROW]` block
8. If decision-maker can't be found: output company as `[QUALIFIED]` but flag `[DECISION-MAKER] — Not found. Recommend: search LinkedIn for [title] at [company]`

---

## Daily Report (Required)

After every run, log the result to today's daily report. See `reports/README.md` for the full protocol.

1. Determine today's date (`YYYY-MM-DD`).
2. Open `reports/YYYY-MM-DD.md`. If it doesn't exist, create it from the template in `reports/README.md`.
3. **Append** an entry at the bottom of the Activity Log:

   ```markdown
   ### YYYY-MM-DD — LEAD RESEARCH — <Company>
   - **Agent:** Lead Research
   - **Target:** <decision-maker name + company>
   - **Lead type:** <Direct Client / Agency Partner / Anthropic Partner / Hire>
   - **Outcome:** Qualified <X/10> / Skipped (<reason>)
   - **Output:**

     <full [QUALIFIED]/[SKIP] + [DECISION-MAKER] + [TRACKER ROW] block>

   - **Next action:** <Send DM / Send connection request / —>

   ---
   ```
4. Increment **Leads researched** in the day file's Summary.
