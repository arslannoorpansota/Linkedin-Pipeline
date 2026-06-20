# PLAN.md — ElectroCom Business Development Roadmap

> The portfolio site is already live at electrocomit.com.
> This plan is about the BD operations engine — how we find leads, write outreach, track pipeline, and close.

---

## Phase 1 — BD Infrastructure Setup ✅ / In Progress

**Goal:** Everything we need to operate exists and is configured.

### Tasks

- [x] Company profile finalized (`CLAUDE.md` §1–2)
- [x] Email strategy defined (`CLAUDE.md` §4)
- [ ] Create email alias: `partnerships@electrocomit.com`
- [ ] Google Sheet created (columns from `sheets/SCHEMA.md`)
- [ ] LinkedIn profile optimized (Arslan: headline = "CTO @ ElectroCom IT | Senior AI Engineer | YC Founder")
- [ ] ElectroCom IT LinkedIn company page reviewed and updated
- [ ] Calendly link active (30-min discovery call, link in outreach)
- [ ] Resend / email client configured for outreach sending

---

## Phase 2 — Lead Sourcing

**Goal:** Build a pipeline of 50+ qualified leads across all 4 target types.

### Lead Source Channels

| Channel | Method | Owner |
|---|---|---|
| LinkedIn Sales Navigator (or manual) | Search by title + industry | Faizan |
| Anthropic Partner Network | Manual research — firms listed as Claude partners | Arslan |
| Job boards (LinkedIn, Wellfound, Greenhouse) | Find companies hiring senior AI engineers | Arslan |
| Upwork / Toptal | Companies posting AI/full-stack projects > $10k | Faizan |
| Clutch / G2 / Goodfirms | Competitor client reviews → warm leads | Faizan |
| Referrals | Ask previous clients, YC network | Arslan |

### Target: 50 leads per month minimum
- Type A (Direct Client): 20
- Type B (Agency Partner): 15
- Type C (AI Platform Partner): 10
- Type D (Hiring for Arslan): 5

### Per-lead research checklist (before outreach)
- [ ] Check connection degree
- [ ] Read their 3 most recent posts
- [ ] Note company news / product launches / funding
- [ ] Identify their pain point (hiring? scaling? AI adoption?)
- [ ] Choose DM type: client / partner / hire

---

## Phase 3 — Outreach Generation

**Goal:** Every lead gets a personalized, research-backed outreach. Never spray-and-pray.

### LinkedIn DM Workflow (primary channel)

1. Open `agents/DM_LINKEDIN.md` in a new Claude session (or use this project)
2. Paste the full LinkedIn profile text
3. Claude outputs: connection note (≤300 chars) + full DM (≤150 words)
4. Review, tweak if needed
5. Send from LinkedIn as Arslan
6. Log to Google Sheet immediately

### Cold Email Workflow (secondary channel)

1. Use `agents/EMAIL_OUTREACH.md` (Phase 4 — coming)
2. Send from `arslan@electrocomit.com` or `partnerships@electrocomit.com`
3. Subject lines: short, specific, never "Partnership Opportunity"
4. Log to Google Sheet

### Weekly cadence

| Day | Activity |
|---|---|
| Monday | Research + add 15 new leads to Sheet |
| Tuesday | Generate + send 10 DMs |
| Wednesday | Generate + send 10 DMs |
| Thursday | Follow up on "Replied" leads, book calls |
| Friday | Review pipeline, update Sheet statuses |

---

## Phase 4 — Follow-Up Sequences

**Goal:** Most deals close on follow-up #2 or #3. Never go silent after first contact.

### LinkedIn DM sequence

| Touch | Timing | Action |
|---|---|---|
| Touch 1 | Day 0 | DM sent |
| Touch 2 | Day 5 | Short follow-up ("Just bumping this up...") |
| Touch 3 | Day 14 | Value-add follow-up (share relevant article, case study) |
| Touch 4 | Day 30 | Final check ("Not the right time?") |

### Email sequence (for email leads)

| Touch | Timing | Subject |
|---|---|---|
| Email 1 | Day 0 | Personalized opening |
| Email 2 | Day 4 | Short "did you get a chance to see this?" |
| Email 3 | Day 10 | Different angle (share case study) |
| Email 4 | Day 21 | Break-up email ("closing the loop") |

### Status update rule
Update the Google Sheet status after every single touchpoint. Never leave a row stale > 7 days.

---

## Phase 5 — Conversion & Pipeline Management

**Goal:** Convert interested leads to discovery calls, then proposals.

### Pipeline stages

```
New Lead → DM Sent → Replied → Interested → Call Scheduled → Proposal Sent → Negotiating → Won / Lost
```

### Discovery call checklist
- [ ] Ask: what does success look like in 90 days?
- [ ] Ask: what's the budget range?
- [ ] Ask: do they have internal engineers or need full team?
- [ ] Note: timeline and urgency
- [ ] Send proposal within 48 hours of call

### Proposal template
*(Create `templates/PROPOSAL.md` when first deal enters Proposal Sent stage)*

---

## Phase 6 — Reporting & Iteration

**Goal:** Know what's working so we double down, and cut what isn't.

### Weekly review (every Friday, 30 min)
- [ ] How many leads added this week?
- [ ] How many DMs sent?
- [ ] Response rate % (replies / sent)
- [ ] How many calls booked?
- [ ] Any won/lost this week?
- [ ] Which lead type converts best?

### Monthly review
- Revenue from new clients
- Top performing outreach hook (what message got the most replies?)
- Lead source breakdown (LinkedIn vs email vs referral)

---

## Current Status

**→ Phase 1 in progress — get infrastructure set up first.**

Immediate next actions:
1. Create `partnerships@electrocomit.com` alias in Google Workspace
2. Create the Google Sheet (use `sheets/SCHEMA.md`)
3. Test the DM agent with 3 real LinkedIn profiles
4. Add first 10 leads to Sheet and send DMs
