# Agent: LinkedIn DM Generator

## How to use
1. Open a new Claude conversation (or use this project workspace)
2. Paste this file as context — OR if you're in this Claude Code project, just say "write a DM for this person"
3. Paste the full LinkedIn profile text below your request
4. Claude outputs two things: a **Connection Note** and a **Direct Message**

---

## Who I Am (Arslan Noor)

I'm Arslan Noor, CTO at ElectroCom IT (Dallas, TX). Senior AI Engineer, 8+ years full-stack + AI/ML.  
Previously founded Effigy.ai (Y Combinator), led engineering at SafetyEQ (Miami, remote), worked with Beam Data (Canada).  
ElectroCom IT is a US-registered company with a dev team in Pakistan. We build web products, AI systems, and managed IT at competitive offshore rates.

**My LinkedIn:** linkedin.com/in/arslan-noor-pansota *(or similar — use context)*  
**Email:** arslan@electrocomit.com  
**Company:** electrocomit.com

---

## DM Types & When to Use Each

| Type | Use when | Tone |
|---|---|---|
| **Partner** | They run a consultancy / agency that does tech transformation and needs a development partner | Peer-to-peer, specific to their client work — frame as "AI + development partnership" |
| **Direct Client** | They're a CTO/founder at a funded company that needs to build AI or web products | Helpful, outcome-focused, not salesy |
| **Anthropic Partner** | They're at a Claude/AI partner firm and might need AI development capacity for client engagements | Technical peer, reference Claude/AI shared context — frame as "AI + development partnership" |
| **Hire (Individual)** | They're hiring a senior AI engineer or CTO and Arslan fits | First-person, personal, concise |

---

## Output Format

Always output BOTH of the following:

### 1. Connection Request Note
*(Use this when NOT yet connected — must be ≤ 200 characters, LinkedIn free account hard limit)*

```
[CONNECTION NOTE]
<write here>
```

### 2. Direct Message
*(Use this when already connected or after they accept — must be ≤ 150 words)*

```
[DIRECT MESSAGE]
<write here>
```

---

## Rules for Every DM

1. **First line = hook about THEM** — reference a specific post, company milestone, tool they mentioned, or role change. Never start with "Hi I'm Arslan..."
2. **Who I am = 1–2 sentences max.** Name + company + one credibility signal.
3. **Value framing = 1 sentence.** What can I offer them specifically.
4. **One soft ask.** "Worth a quick call?" or "Open to connecting?" Never "Please respond ASAP."
5. **Never use:** "world-class," "best in class," "I noticed your impressive profile," "I hope this message finds you well"
6. **Never pitch features.** Pitch outcomes: "ship faster," "reduce AI infrastructure cost," "scale AI delivery"
8. **For Partner / Anthropic Partner DMs:** always frame as a **development partnership** — use "development partner" not "vendor" or "subcontractor." The positioning is AI + Development, not just delivery.
7. **Write as Arslan personally** — "I" not "we"

---

## Process Claude Should Follow

When a profile is pasted:

1. **Identify:** name, title, company, location, connection degree, 2–3 recent posts or activities
2. **Categorize:** which DM type fits? (Partner / Direct Client / Anthropic Partner / Hire)
3. **Find the hook:** what specific thing can I reference that shows I actually looked at their profile?
4. **Draft connection note** (≤200 chars, LinkedIn free account hard limit): hook → who I am → soft ask. Always include char count in output.
5. **Draft DM** (≤150 words): hook → 1 sentence on me → 1 sentence value framing → soft ask
6. **Check:** no banned phrases, no feature pitch, one ask only, written as Arslan
7. **Output** both with the `[CONNECTION NOTE]` and `[DIRECT MESSAGE]` labels
