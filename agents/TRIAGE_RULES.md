# TRIAGE_RULES.md — The complete profile triage checklist

> **One-page operational reference. Written 2026-09-17 so a second chat can run the paste → rate →
> draft → log loop without reading five other files.**
>
> Source files this consolidates: `WEBSITE_GAP_TRIAGE.md` (keep/skip test + disqualifiers),
> `LIST_LOGGING.md` (logging protocol + channel table), `OUTREACH_LENGTHS.md` (message lengths),
> `CADENCE.md` (geo + follow-up), `CLAUDE.md` §9 (tone).
> Where this file and another disagree, **check the source file** — this is a summary, not an override.

---

## The loop, in order

For every pair of profiles pasted:

1. **Dedupe first** — always, before any analysis.
2. **Apply the free disqualifiers** — most skips die here, before a full read.
3. **Apply the founder gate** — does this person or company already own the engineering?
4. **Rate the profile** (col AZ) and the company (col BA).
5. **Draft messages** if the profile rates 6+, humanize them, assert the lengths.
6. **Write the row immediately** — never batch, never wait for the next pair.
7. **Reply in chat** — skips get the verdict only, keeps get rating + reason + message copy.

---

## 1. Dedupe (Pass 0 — never skip this)

Normalize with `re.sub(r'[^a-z0-9]', '', s.lower())` and check **name (col C)** and
**company (col E)** against `Pipeline!C1:E5000`. Also run loose substring scans on the
surname and a distinctive company fragment, because "Dr." prefixes, accents and legal
suffixes (Sàrl, GmbH, SL, Inc.) defeat exact matching.

Check the **other decision-makers too** (co-founders, the CEO, the CTO named on the
account page). A company already in the sheet under a different person is still a collision.

**Expect false positives.** Fragments like `mana` match every "Management" in the sheet.
Read the hits before calling a dupe. Say "NO DUPES" explicitly when there are none.

If a genuine dupe surfaces, **update the existing row** rather than creating a second one.

---

## 2. Free disqualifiers — apply BEFORE spending a full read

Each of these cost a wasted read to learn. Full list and worked examples in
`WEBSITE_GAP_TRIAGE.md`; this is the working set.

| # | Disqualifier | Why |
|---|---|---|
| 1 | **AI in the product or the company name** | They built their own stack |
| 2 | **Hardware / devices / physical product** | No entry point; capital goes to machines |
| 3 | **Device distributor or reseller** | Same |
| 4 | **Clinic / hospital / med-spa / aesthetics / therapy practice** | Read the About line, not the name |
| 5 | **Teaches, coaches, trains, or sells courses** | A training business, and a coding school has developers |
| 6 | **Nonprofit / association / foundation / federation** | Donor or grant funded, no discretionary budget |
| 7 | **Government / crown corporation / public body** | Buys through procurement; a DM cannot start that |
| 8 | **Subsidiary of a larger parent** | Does not own its stack |
| 9 | **Consulting or services business** | Nothing to build |
| 10 | **One-person advisory or personal consulting brand** | No organisation under the title |
| 11 | **Competitor or competitor-adjacent** | Sells our offer to our buyer |
| 12 | **Investor / VC / fund** | Wrong side of the table |
| 13 | **Solo practice** | Too small to have the problem |
| 14 | **WhatsApp-only intake** | Has deliberately chosen no platform |
| 15 | **Geo: India, Pakistan, China, Thailand** | Only these four. Everywhere else is eligible |

**Geo note:** UK came back in on 2026-09-04. US, Canada, Australia, Singapore, Gulf, all of
Europe, Ireland, LATAM, Mexico, Türkiye are all eligible. Geo is a filter, not a judgement call.
See `CADENCE.md` §5.

---

## 3. The founder gate — the decisive keep/skip test

> **Technical founder = skip. Non-technical founder with a real build need = keep.**
>
> ### Set by Faizan 2026-09-19 — FINAL, and it comes FIRST
> *"Keep all the non-technical who do not have a CTO and any engineering team."*
>
> A KEEP needs **all three**: the **founder is non-technical**, the company has **no CTO**,
> and the company has **no engineers at all**. **Any engineer on staff is a SKIP** —
> confirmed explicitly, a single hired developer with no CTO still counts as covered.
>
> This **supersedes the 2026-09-09 override** that treated a CTO or dev arrangement as a
> caveat to verify on accept. A company with engineers can handle dev in-house, so there is
> nothing to sell. The line below under "Fails the gate" (*the company employs a CTO or
> CPO*) is therefore **correct and back in force**.
>
> **Scan All Employees, not just the CXO panel.** Senior Engineer, Infrastructure Engineer,
> Cybersecurity Analyst, UI/UX QA and Product Designer all count as engineering.
>
> The website gap (`WEBSITE_GAP_TRIAGE.md`) decides **what to build and what to say**, and
> makes the hook verifiable. It does not decide the verdict on its own.
>
> Worked example: **Blake Stevenson / Clear Health (row 2460)** flipped twice on 2026-09-19
> and settled on **SKIP**. Non-technical founder (BBA Marketing, sales career, zero
> technical endorsements), live ML product, 17% six-month growth, but the company employs a
> CTO, a Senior Engineer, a Cybersecurity Analyst and a UI/UX QA. The two keeps from the
> same day both have **zero engineers**: Kayla Sol / RY Services and Larisa Krichevsky /
> Launch To Wellness.

Extended in practice to: **does the COMPANY already own its engineering?** — yes, and per the box above that now includes *any* engineer on staff, not only a CTO.

### Fails the gate (skip)

- Title is **CTO**, Co-Founder & CTO, Chief AI Officer, Head of Engineering.
- **Career engineer** — prior roles as developer, software engineer, quant, architect.
  Check the full experience list, not just the current role.
- **Endorsements give it away** — Java, Python, Git, Spring, Software Development,
  Software Architecture, programming languages of any kind.
- **Conference talks on technical topics** — TDD, frameworks, architecture.
- **The company employs a CTO or CPO**, even if this person does not.
- **The company is tagged Software Development** or describes itself as a platform it built.
- **A corporate parent or acquirer now owns the roadmap** — a majority shareholder with
  board seats funds and specifies the build.
- **They already ship integrations** — an EHR integration, a marketplace app, an API.

### Passes the gate (keep candidate)

- Domain founder: clinician, therapist, forester, salesperson, economist, lawyer.
- Endorsements are **operational** — Leadership, Operations Management, Strategy,
  Team Management, Business Development.
- Degree is outside engineering, and a PhD or MD does **not** make someone technical.
  **But check the degree field** — an MD whose skills are Python and Machine Learning is technical.

### Credential trap

`Dr.`, `PhD`, `MD`, `CEng` in the name line mean nothing on their own. Always check the
**degree field** and the **skills list**. Several misses came from reading the title only.

---

## 4. What makes a KEEP (the positive signal)

A skip is the default. A keep needs an affirmative reason, usually one of:

| Signal | What it looks like |
|---|---|
| **Multi-site or mobile workforce** | Staff dispatched across locations, sites, or client premises |
| **Things that expire** | Certifications, licences, DBS checks, PPE inspections, re-indications |
| **Derived values tracked over time** | Lab indices, per-patient trends, anything computed from several inputs |
| **Deadlines and states per case** | Start dates, extensions, renewals, compliance windows |
| **Hiring for coordination** | A vacancy whose task list is "watch dates and chase missing data" |
| **Fast headcount growth** | +25% or more, especially with a low median tenure (new team) |
| **A promise that is hard to keep** | "Results in one hour", "same carer every time", a performance guarantee |
| **Thin exec bench against real scale** | Few or no CXOs, one founder carrying the coordination |

**Growth is a strong secondary filter.** Flat or negative headcount across all windows usually
means a stable mature business that is not straining — dock the rating even when the shape fits.

**Verifiable hook required.** Only reference a post, talk, article or job ad you can actually
point to. If someone replies "which post?" and it does not exist, credibility is gone.

---

## 5. Rating and channel

Two separate ratings:

- **AZ = profile rating** — the person, and whether they are the right buyer. **Drives the channel.**
- **BA = company rating** — the business quality and the size of the opportunity.

### Channel by PROFILE rating (col AZ)

| AZ | Channel |
|---|---|
| **7+** | **BOTH** a connection note **AND** an InMail, drafted in the same pass, never ask first |
| **6** | Connection note only |
| **Below 6** | Skip, but log the row fully |

A lead can have a low company rating and still be a Profile 7 that earns note + InMail.
Rate the profile, then apply the table.

> This **overrides** `CADENCE.md` §2a, which frames InMail as fallback-only on reply-rate data.
> Faizan overruled that for P7+. Never withhold an InMail from a P7 by citing those stats.

### Rating guidance observed in practice

- **P7** — non-technical founder, real coordination problem, verifiable hook, eligible geo.
- **P6** — the shape fits but something is soft: flat growth, a partial disqualifier, smaller scale.
- **P4** — a genuine near-miss worth recording as a revisit candidate (explosive growth,
  enterprise logo) but blocked today by a disqualifier.
- **P1–P3** — clean skip.

---

## 6. Message rules

| Asset | Length | Hard rule |
|---|---|---|
| **Note** | **under 300 characters** | The default when Faizan says "note" |
| **Connection request note** | **under 200 characters** | Only when it rides on a connection request (LinkedIn hard cap) |
| **InMail** | **under 150 words** | Body after the subject line |

**Assert before showing, every time:**

```python
assert len(note) < 300
assert wc < 150
assert chr(8212) not in x and chr(8211) not in x   # no em dash, no en dash
```

The 300-character assertion is the single most common failure in this loop — roughly a
dozen leads needed a trim. **Trim by cutting words, not by rephrasing**, and re-check the
length after every edit. Two edits made notes *longer* while trying to shorten them.

### Content rules

- Run every message through the **humanizer** skill first. No em dashes, no rule-of-three,
  no promotional adjectives, no negative parallelism, no filler.
- **Lead with the observation about them**, never the pitch.
- **One ask only**, at the end. Soft: "Worth a 20-min call?" not "Please respond ASAP."
- Write as **Arslan (CTO)**, first person singular. "I", not "we".
- Include the **OpenAI video-model credential** — worked with OpenAI in 2025 on training
  their video generation models.
- **Never** lead with "US-registered" or "offshore team". It reads cheap.
- **Write in their language** where the profile is not in English. French, Spanish, Polish,
  Dutch, German, Italian have all been used. Use their own internal vocabulary where visible.
- **Vary the structure**, not just the first line. Same body with a swapped hook is a template.

---

## 7. Writing the row

**Log every lead immediately after its verdict. Never batch.**

Column map (full version in `sheet-write-schema` memory):

| Col | Field | Col | Field |
|---|---|---|---|
| B | date | T | channel |
| C | name | V | sent date |
| D | title | W | sent flag |
| E | company | X | note body |
| F | description | Y | T2 / DM body |
| G | geo | Z | InMail body |
| K | degree | AB | status |
| L | mutuals | AT | next action |
| M | type | AU | next action date |
| N | service | AV | lead source |
| O | project type | AW | caveat / internal note |
| P | budget | AX | name (dup) |
| Q | priority | AY | company (dup) |
| R | score | AZ | **profile rating** |
| S | hook | BA | company rating |
| | | BB | **reason** |
| | | BC | days since touch |
| | | BD | cadence due |
| | | BE | cadence stage |

**Both `AW` and `BB` are always filled, on keeps and skips alike.** `BB` is the verdict and
reason; `AW` is the long internal note with the evidence. A skip with an empty reason is a
row someone will have to re-research later.

Write with `values().batchUpdate(valueInputOption='USER_ENTERED')` anchored to explicit
cells. **Do not use `values().append`** — column A is blank and append shifts rows by one.

Wrap every call in a 6-attempt retry: `time.sleep(2 * (attempt + 1))` on exception.

### A drafted message is logged as SENT in the same write

Set `V` = date, `W` = TRUE, `T` = the channel, `AB` = contacted, `BE` = T1 sent,
`AU`/`BD` = the nudge date. Do not leave a drafted message in a pending state.

---

## 8. Cadence and post-accept

**Four touches: day 0 / +3 / +8 / +15, park at +45.** `AU` is never blank while a lead is live.

### Post-accept rule — the one that gets broken

| They were sent | They accept | Action |
|---|---|---|
| **Note + InMail (P7)** | | **SEND NOTHING.** The InMail is already in their inbox with the closing question. Messaging on top is a second touch in one day. Wait for a reply, then T2 on schedule. |
| **Note only (P6)** | | **Free T2 immediately.** No InMail is pending, so the accept earns the next message. |

**Never send a second InMail** to a lead whose first InMail is unanswered. Wait for a free
accept, then park.

### On a decline

Log it, close the row (`BE` = Closed - declined), clear `AU` and `BD`, and record in `AW`
what was tried and what the refusal actually said. **Do not nudge a courteous no.** One soft
close is acceptable; a third message is not.

---

## 9. Chat reply format

> ### THE VERDICT IS THE WHOLE REPLY
>
> **Set by Faizan 2026-09-17, tightened the same day.** Chat gets **KEEP** or **SKIP**
> plus the rating, and nothing else. No reasoning, no evidence, no justification, on
> keeps or on skips. All of it goes to the sheet.

**Correct:**

```
Mario Farag — KEEP, P6.
[message copy follows]

Nima Ahmadi — SKIP (P3).
```

**Wrong:** anything that explains the verdict. Leading with what the company does, what
was noticed on the profile, how the analysis went, or a one-line reason appended to the
rating. The earlier version of this rule allowed a single clause on each lead; **it no
longer does.**

- **Skips** — name and rating. That is the entire line.
- **Keeps** — name, rating, then the message copy. The copy is what Faizan acts on; the
  reason is not.
- **Running tally** at the end: `N read, N keeps, N skips, N dupes`.
- **No unsolicited commentary.** Do not volunteer pattern observations, triage-rule
  suggestions or "worth flagging" notes during the loop. If something genuinely warrants
  a rules change, put it in the daily report.

**The sheet does not get shorter.** `BB` and `AW` are written at full depth exactly as
before. Chat brevity is a reading-speed decision, not a research-depth one: a skip with a
thin `AW` is a row someone re-researches from scratch later.

Do not paste skip reasoning into chat. It is in `BB` and `AW` where it belongs.

---

## 10. Known filter defects to watch for

The Sales Nav Founder/Co-Founder title filter matches people whose **founded entity is not an
operating company**. Logged repeatedly:

- A **VC fund** founder (Lynne Chou O'Keefe, row 2245)
- A **nonprofit** founder whose day job is elsewhere (Freddy Morello 2252, Genevieve Ngambia 2254)
- A **personal consulting brand** (The Capacity Leader, row 2252)
- **Side ventures** — a beverage cart, a cycling association, two charities, a student microfund,
  a student society presidency, a citizen movement

Check what the person's **actual job** is before rating. The founder title may belong to
something they do on weekends.

Also watch: **geo leaks** (India profiles surfacing despite the filter) and **competitors**
appearing in results — three so far selling to our exact buyer.

---

Relates to `agents/WEBSITE_GAP_TRIAGE.md`, `agents/LIST_LOGGING.md`,
`agents/OUTREACH_LENGTHS.md`, `agents/CADENCE.md`, `CLAUDE.md` §9, and the memory notes
`icp-triage-engineering-gate`, `outreach-channel-by-rating`, `p7-always-note-and-inmail`,
`sheet-write-schema`, `log-every-lead-immediately`, `no-skip-reasons-in-chat`,
`target-geographies`, `humanize-outreach-messages`.
