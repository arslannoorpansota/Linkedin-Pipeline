# Agent: Cold Email Generator

## How to use
1. Open a Claude conversation in this project workspace
2. Say "write a cold email for this person" or "write an outreach email"
3. Paste what you have: LinkedIn profile, company page, job posting, or just a name + title + company
4. Claude outputs: **Subject Line** + **Email Body**

---

## Who I Am (Arslan Noor)

I'm Arslan Noor, CTO at ElectroCom IT (Little Elm, TX — Dallas metro). Senior AI Engineer, 8+ years full-stack + AI/ML.  
**Worked with OpenAI in 2025 on training their video generation models** (lead AI credibility signal).  
Co-founded Effigy.ai, led engineering at SafetyEQ (Miami, remote), worked with Beam Data (Canada).  
ElectroCom IT is a US-registered company with a dev team in Pakistan. We build web products, AI systems, full-stack apps, and managed IT at competitive offshore rates.

**Sending email:** `arslan@electrocomit.com` (all outreach) or `partnerships@electrocomit.com` (partner / agency discussions)  
**Company:** electrocomit.com

---

## Email Types & When to Use Each

| Type | Use when | Send from | Tone |
|---|---|---|---|
| **Partner** | Agency / consultancy that needs delivery capacity for client work | `partnerships@electrocomit.com` | Peer-to-peer, delivery-focused |
| **Direct Client** | CTO/founder who needs to build AI or web product | `arslan@electrocomit.com` | Outcome-focused, light on pitch |
| **Staff Aug** | Company hiring engineers — offer embedded talent instead | `arslan@electrocomit.com` | Cost/speed framing |
| **Hire (Arslan)** | Company posted a senior AI engineer / CTO role | `arslan@electrocomit.com` | Personal, first-person, brief |

---

## Output Format

Always output ALL THREE of the following:

### 1. Send From
```
[SEND FROM]
<which email address to use>
```

### 2. Subject Line
```
[SUBJECT]
<subject line — max 8 words, no spam triggers>
```

### 3. Email Body
```
[EMAIL]
<body — max 120 words, 4–5 sentences>
```

---

## Rules for Every Email

1. **Line 1 = specific hook about THEM.** Reference a product launch, job posting, a LinkedIn post, a company milestone, a shared tool, or a recent announcement.
2. **Line 2 = who I am, 1 sentence.** Name + company + one credibility signal. Not a list of services.
3. **Line 3–4 = value framing.** What can I specifically do for them based on what I learned? Pitch outcomes, not features ("ship your AI feature in 6 weeks" not "we offer LLM integration").
4. **Last line = one soft CTA.** "Worth a 20-min call?" or "Happy to share a relevant case study if useful." Never two asks.
5. **Subject line rules:**
   - Short, specific, no buzzwords
   - Good: `Re: your LLM rollout plans`, `AI delivery capacity for [Company]`, `Quick question about [recent post]`
   - Bad: `Partnership Opportunity`, `AI Services from ElectroCom`, `Hello from ElectroCom IT`
6. **Never use:** "I hope this email finds you well," "we're the best," "world-class," "quick question" as the actual subject when it's not a quick question
7. **Sign off:** always `Arslan Noor | CTO, ElectroCom IT | electrocomit.com`

---

## Examples

### Example 1 — Direct Client (Funded Startup CTO)

**Context:** CTO at a Series B health-tech company, they recently posted 3 senior AI engineer roles and their product involves clinical note summarization.

**[SEND FROM]**
arslan@electrocomit.com

**[SUBJECT]**
AI engineering for your clinical NLP work

**[EMAIL]**
Noticed [Company] is scaling your AI team — three senior engineer roles in the last month is a real signal something's moving fast.

I'm Arslan Noor, CTO at ElectroCom IT. I previously built clinical NLP pipelines at SafetyEQ and co-founded Effigy.ai.

We're a US-registered team with engineers in Pakistan — which means you get senior AI delivery at roughly 40–60% of US contractor rates. If you're building document understanding or summarization features, we could accelerate that without the 3-month hiring lag.

Worth a 20-min call to see if there's a fit?

Arslan Noor | CTO, ElectroCom IT | electrocomit.com

*(118 words)*

---

### Example 2 — Partner (Consultancy / Agency)

**Context:** Practice lead at a mid-size digital consultancy in the UK. They recently won a retail AI transformation engagement.

**[SEND FROM]**
partnerships@electrocomit.com

**[SUBJECT]**
Delivery capacity for your retail AI work

**[EMAIL]**
Saw the announcement about [Firm]'s retail transformation engagement — that's exactly the kind of work where implementation speed becomes the variable.

I'm Arslan Noor, CTO at ElectroCom IT (Dallas). We're a US-registered AI and full-stack team. I founded Effigy.ai through YC and we've shipped production RAG pipelines, agentic workflows, and LLM integrations on Claude and OpenAI.

Consulting firms often win engagements ahead of delivery capacity. If you need a reliable offshore engineering partner to absorb scope — competitive rates, NDA-ready, aligned to UK/US timezones — I'd be glad to talk.

Open to a quick call?

Arslan Noor | CTO, ElectroCom IT | electrocomit.com

*(119 words)*

---

### Example 3 — Hire (Arslan personally)

**Context:** Director of AI at a US fintech company posted a Staff AI Engineer role. Arslan is interested individually.

**[SEND FROM]**
arslan@electrocomit.com

**[SUBJECT]**
Staff AI Engineer — Arslan Noor

**[EMAIL]**
Your Staff AI Engineer posting caught my attention — the RAG + agentic workflow requirements are squarely in what I've been shipping in production.

I'm Arslan Noor — Y Combinator founder (Effigy.ai), ex-SafetyEQ (led AI engineering, remote US), Turing-verified. Strong in Python, LLMs, RAG, Next.js, AWS. Full-stack but AI-native.

I'm open to a senior individual role in the right environment — where the work actually ships and the team moves fast.

Resume attached. Happy to do a short technical screen if it's easier than a full interview loop upfront.

Arslan Noor | arslannoorpansota@gmail.com | linkedin.com/in/arslan-noor-pansota

*(102 words)*

---

## Process Claude Should Follow

When context is pasted:

1. **Extract:** name, title, company, what they're working on, any recent news or posts
2. **Choose type:** Partner / Direct Client / Staff Aug / Hire
3. **Choose send-from email:** based on type table above
4. **Find the hook:** the one specific thing that proves you looked — a post, a job posting, a product feature, a company announcement
5. **Draft subject line** (max 8 words, topic-specific, no spam triggers)
6. **Draft email body** (max 120 words): hook → who I am → specific value → one CTA
7. **Check:** no banned phrases, no feature list, one ask only, signed as Arslan
8. **Output** all three blocks: `[SEND FROM]`, `[SUBJECT]`, `[EMAIL]`

---

## Daily Report (Required)

After every run, log the result to today's daily report. See `reports/README.md` for the full protocol.

1. Determine today's date (`YYYY-MM-DD`).
2. Open `reports/YYYY-MM-DD.md`. If it doesn't exist, create it from the template in `reports/README.md`.
3. **Append** an entry at the bottom of the Activity Log:

   ```markdown
   ### YYYY-MM-DD — EMAIL — <Person, Company>
   - **Agent:** Email
   - **Target:** <name + company>
   - **Lead type:** <Partner / Direct Client / Staff Aug / Hire>
   - **Outcome:** Cold email drafted (sending from <email>)
   - **Output:**

     <full [SEND FROM] + [SUBJECT] + [EMAIL] block>

   - **Next action:** Send email

   ---
   ```
4. Increment **Emails written** in the day file's Summary.
