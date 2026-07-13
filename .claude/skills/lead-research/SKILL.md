---
name: lead-research
description: "Qualify a sales lead. Use when the user says 'research this company,' 'qualify this lead,' or pastes a company, LinkedIn page, or job post; returns qualify/skip, a decision-maker card, and a score."
---

# Lead Research & Qualification

Qualify and research inbound/target leads for ElectroCom's business development, then output a Qualified/Skip verdict, a decision-maker card, and a tracker row.

## Input
The user pastes any of: a company name, URL, LinkedIn company page, a job posting, or a person's name + company. Work with whatever is given; note what's missing.

## About ElectroCom (context for scoring fit)
ElectroCom IT is a US-registered IT & AI firm (HQ in Texas) with a senior engineering team. Services: web & full-stack development, AI/ML engineering (LLMs, RAG, computer vision), managed IT/DevOps, staff augmentation, and IT consulting. CTO **Arslan Noor** worked with OpenAI in 2025 on training their video generation models — the flagship AI proof point. Primary target is **direct clients (Type A)**: Seed–Series B companies that need to ship AI or web products.

---

## Step 1 — Qualification Filter

Apply this before researching anyone. If it fails, output `[SKIP]` with one reason and stop.

### Pass — Sweet Spot
| Signal | Target range |
|---|---|
| Company size | 10–150 employees |
| Funding stage | Seed / Series A / Series B (raised within the last 18 months) |
| Engineering hiring signal | Job posts for engineers, or founder publicly stated hiring intent |
| Budget signals | $3M–$50M raised, hires senior engineers, describes complex AI/full-stack builds |

**Primary focus:** Direct clients (Type A). Boutique agency/consultancy partner (Type B) only if the firm is <200 people and does NOT have its own offshore delivery bench.

### Auto-Skip — Wrong Profile
- Publicly traded company or household brand (Apple, Amazon, GE, etc.) — long procurement, wrong ICP
- 500+ employees with a dedicated vendor/sourcing team
- **Large offshore delivery firms** (Intellias, N-iX, ELEKS, Ciklum, Sigma Software, Svitla, etc.) — they have their own offshore bench and are effectively competitors
- Enterprise procurement cycle (6+ months to sign)
- Recruiting/talent-marketplace companies — not services buyers

### Auto-Skip — Too Small
- <5 employees, no funding, no visible revenue
- Solo founder at ideation stage — no product, no team
- Budget signals: $500–$2k Upwork posts, "looking for lowest cost dev"
- No online presence (no website, no LinkedIn company page)

---

## Step 2 — Decision-Maker Identification

Find the real person, not a generic contact.

| Lead Type | Target role |
|---|---|
| **Direct Client** *(primary)* | Founder, CTO, VP Engineering — whoever controls the eng roadmap |
| **Boutique Agency Partner** *(selective)* | MD, Head of Engineering, Practice Lead — only at firms <200 people without their own offshore bench |
| **Anthropic / AI Partner** | Head of AI, VP Engineering, Managing Director |

### Tiebreaker rules
- Founder + CTO both present: CTO for technical work, Founder for strategic partnerships
- Company <20 people: the Founder IS the decision-maker regardless of title
- Eng Director + VP Eng both exist: target whoever has more recent LinkedIn activity
- Avoid "Head of People," "Chief of Staff," "Executive Assistant" — not buyers

---

## Step 3 — Lead Score (1–10)

Be honest — most leads are 5–7. Reserve 9–10 for rare high-signal fits.

| Score | Meaning |
|---|---|
| **9–10** | Drop everything — active pain + budget + reachable decision-maker + perfect fit |
| **7–8** | Strong lead, prioritize this week |
| **5–6** | Worth reaching out, no rush |
| **3–4** | Low priority |
| **1–2** | Borderline skip |

**Boosts:** hiring engineers/AI roles +2 · recent funding +2 · posted AI adoption pain/timeline +2 · Anthropic/Claude partner +2 · decision-maker 2nd-degree +1 · posted recently +1 · US/UK/Canada/Australia/Saudi +1 · clear budget ($50k+ or 10+ eng) +1 · running AI transformation +1
**Penalties:** no recent LinkedIn activity −1 · 3rd degree, no mutuals −1 · low-rate region −1 · vague pain/no hook −1

---

## Output Format

If it does not qualify:
```
[SKIP]
Reason: <one line — too big / too small / and why>
```

If it qualifies:
```
[QUALIFIED]
Company: <name>
Size: <employee count or estimate>
Stage: <Seed / Series A / bootstrapped / etc.>
Score: <X/10>
Score reasoning: <one line>
Why they're a fit: <one sentence>

[DECISION-MAKER]
Name: <full name>
Title: <exact LinkedIn headline title>
LinkedIn: <URL>
Connection degree: <1st / 2nd / 3rd>
Mutual connections: <number, if visible>
Lead type: <Direct Client / Agency Partner / Anthropic Partner>
Hook: <1–2 sentences — a specific recent post, announcement, or signal to reference>

[TRACKER ROW]  (paste into the BD Pipeline sheet)
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

If the decision-maker can't be found: output the company as `[QUALIFIED]` and flag `[DECISION-MAKER] — Not found. Recommend: search LinkedIn for [title] at [company]`.

---

## Examples

**Input:** "Runway ML — AI video generation tools. ~60 people. Series C."
```
[SKIP]
Reason: Too big — Series C with 60+ employees signals enterprise procurement and a vendor approval process. Cold DM from a small firm is unlikely to convert.
```

**Input:** "Solo founder, 2-person startup, wants a $500 landing page."
```
[SKIP]
Reason: Too small — 2-person team, no funding, $500 budget. No viable deal size.
```

---

## Process
1. Identify basics: name, website, LinkedIn, employee count, funding stage.
2. Apply the qualification filter — if it fails, `[SKIP]` and stop.
3. Identify lead type (Direct Client / Agency Partner / AI Partner).
4. Find the decision-maker using the tiebreaker rules.
5. Pull their data: name, exact title, LinkedIn URL, connection degree, mutuals.
6. Find the hook: most recent relevant post, company announcement, role change, or launch. The hook must be verifiable — if you can't confirm it, use a company-level signal (funding, job post) instead. Never fabricate.
7. Output the full `[QUALIFIED]` + `[DECISION-MAKER]` + `[TRACKER ROW]` block.
