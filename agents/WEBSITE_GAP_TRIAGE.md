# WEBSITE_GAP_TRIAGE.md — The website-gap method

> **Standing method, set by Faizan 2026-09-11 and validated across 40 account reads on 2026-09-11 and 2026-09-15.**
> Replaces the old "does the company already own its engineering?" gate as the primary keep/skip test.

---

## The rule

**The only question is whether there is work on their site we could do.**

If there is a visible gap, it is a KEEP — **regardless of whether they have a CTO, a dev team, or an agency.**
A company with engineers still buys outside capacity when the roadmap outruns the team.

This replaced the engineering gate on 2026-09-11 at Faizan's instruction, after the old rule failed four
times in one day (Sohar Health, Oler Health, Zina Ortiz, Sharleen McDowall all had hidden engineering).

---

## Order of operations (saves the most time)

1. **Read the full Sales Nav About line at list view** — not just the company name.
2. **Read the website.**
3. **Only pull the profile if the site shows visible work.**

Tier 3 of the first account list went 0 for 7 because five of seven died on the PRODUCT check before
the buyer question ever mattered. Reading the site first would have saved five full profile reads.

---

## What counts as a real gap (every keep came from this list)

| Gap | Example |
|---|---|
| **Placeholder content live on the page** | Remission Medical: Partners section rendering `Item 1` ×35 + `Default Title` |
| **Alt text rendering as body copy** | Omatochi: 16 partner logos showing as `Partners 05`, `Partners 27`… |
| **Image filenames / CSS classes as visible text** | 4YouandMe: `Home Hero`, `TransparentFern 1`, `Dark 4` |
| **Content that stops mid-sentence** | 4YouandMe: "Using artificial intelligence and machine learning…" then nothing |
| **Site outsourced to an agency while internal eng builds the product** | Remission Medical: "Website designed and maintained by Fireside Digital" |
| **Rented core capability** | Plutonic: "Some virtual spaces are hosted on 3rd party platforms", avatars from ReadyPlayerMe |
| **Stale footer vs live activity** | Bilingual Generation: footer says © 2023 while they ship an app and win grants |
| **Domain mismatch on their own profile** | Origin Therapy: LinkedIn points to joinoriginspeech.com, live site is origintherapy.com |
| **A named product with no page behind it** | Plutonic: footer link "AI Mental Health" goes nowhere |
| **Disconnected web properties** | Bilingual Generation: org site, app site and book site never link to each other |
| **One engineer (or none) against real scale** | Hey Nouri: ONE Founding Engineer, 37 staff, 270% 6-month growth, zero eng roles open |
| **"Primary onshore production engineer" in a job post** | IMPaCT Care: the word *onshore* only appears when the rest is offshore |

### What is NOT a gap

**Marketing copy describing finished features.** Sonar's homepage listed five things we could "help with"
and all five were already shipped. A polished marketing site is written to look complete — it will not
reveal gaps. Prefer companies whose product or app is publicly reachable.

---

## Free disqualifiers — apply BEFORE spending a read

All proven on real accounts, each one cost a wasted read to learn:

1. **"AI" in the company name** → they built their own stack. (Burna AI, Imagene AI, Basil Health AI, CIPRA.ai, Shyld AI)
2. **A company whose PRODUCT IS AI GENERATION** → sharper version of the above. Medudy generates lifelike AI avatar video for ~240,000 doctors. The closest company to what we do is exactly the one with nothing to buy.
3. **Hardware / device / physical product** → no entry point. (Toi Labs' TrueLoo toilet seat, Medirion's thermography device, Carpod, Exelint)
4. **Device distributor / reseller** → The Air Station (ResMed CPAP).
5. **A company that TEACHES CODING has developers.** (Code Mantra, codeCampus, App Akademie, Syntax Technologies)
6. **Crown corporation / government agency / public body** → buys through PROCUREMENT (RFPs, tenders, vendor registration). A cold LinkedIn message cannot start that process. (CoRE = Alberta Crown corporation)
7. **Nonprofit** → already in the list-view criteria. Check for a "Needs Funding" section: 4YouandMe publicly lists unfunded studies.
8. **Subsidiary of a larger parent** → does not own its stack. (Doktor.De under Doktor.se 357 emp; The Air Station under Easmed 107 emp; EGS under Eagle Group)
9. **Clinic / hospital / surgical centre / med-spa / aesthetics** → already in the criteria, but **READ THE ABOUT LINE**: "Nadora Healthcare" and "Kalia Lab" both read like product companies and both run clinics. Two misses in one day from reading the company name only.
10. **Consulting / services business** → nothing to build. (Model Oncology, Shield Health, ETHOS, EGS, Esperta)
11. **WhatsApp-only intake** → a small coordination desk has deliberately chosen no platform. (EGS)
12. **Credentials in the name line need a DEGREE-FIELD CHECK.** PhD/CEng/MD does not mean non-technical:
    - Ravi Hariprasad (Zenara) — "psychiatrist, **engineer**", Cornell operations research
    - Reza Amin (Bastion) — PhD **Mechanical Engineering**, MEng Mechatronics, skills are Matlab/C++/Robotics
    - Stuart Harrison (ETHOS) — **CEng FIET MIEEE**, authored the NHS DCB 0129/0160 standards
    - Jack Luo (Modern Menopause) — **MD** whose skills are **Python and Machine Learning**, built drone-delivery infra
13. **Check the CAREERS page — it often states the build arrangement outright.** Medirion: *"We are building all our prototypes and **code all our software inhouse**."* Fastest disqualifier available and free to read.
14. **LinkedIn HQ can be a REGISTRATION address, not the real operation.** Sahara mind lists Chicago and runs in Nepal; Mind Friend listed Delaware and ran in the UK. Tells: site language, named staff, crisis/helpline numbers.
15. **Scan All Employees, not just the CXO panel.** Sohar Health's CTO was the second name under All Employees while the CXO panel showed only the CEO.
16. **Relationship conflict check** — does this person share a connection with anyone already LIVE in the pipeline? Hemi Health's Amy Aanen shares a connection with Jelle Heisen (live T2, Pipeline row 1910). Do not approach cold and cross a warm thread.
17. **Two competitors in the same pull** → the one with the engineering team wins; the smaller one is usually a services business dressed as a platform. (Reesi 13 emp w/ ex-CTO vs iuvando Health 8 emp "physician-led")

---

## Non-founder CXO accounts (Tier 3) are not worth reading

Seven accounts where Sales Nav returned a COO/CMO/CGO instead of a founder: **0 keeps from 7.**
But **not for the reason expected** — five of seven died on the PRODUCT check before the buyer question
mattered (Arima built computer-vision screening, HealthMe shipped agentic AI, Precise acquired Rose Health,
Esperta has a CIO plus proprietary systems, Malama has NIH-funded AI). One had no product at all (Shield),
one was a clinic (The Anxiety Center).

---

Relates to `agents/LIST_LOGGING.md`, `agents/OUTREACH_LENGTHS.md`, `CLAUDE.md` §9,
and the memory notes `website-gap-triage`, `icp-triage-engineering-gate`, `sales-nav-winning-recipe`.
