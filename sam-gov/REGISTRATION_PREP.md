# SAM.gov Entity Registration — Prep Packet

> **Entity:** ElectroCom Innovations LLC · **Goal:** Complete full registration (eligible to bid on US federal awards)
> **Owner:** Faizan (BD) · **Reviewer:** Arslan / Zulfiqar
> Last updated: 2026-07-01

This packet records the confirmed entity status, flags the data we still need,
recommends NAICS codes, and gives the exact step-by-step for the live SAM.gov flow.
SAM.gov requires a personal **Login.gov** sign-in and on-site entry of sensitive fields
(EIN, bank/EFT) — those can't be filled in advance, only prepared.

---

## ⭐ STATUS — CONFIRMED 2026-07-01 (entity search)

We are **NOT registering from scratch.** A SAM.gov record already exists and is **ours**
(confirmed by team). It is stuck at the **UEI-only** stage — full registration was never
completed, so **we cannot yet bid on federal awards.** The task is to **COMPLETE** it.

| Field | Confirmed value |
|---|---|
| **Legal name** | **ElectroCom Innovations LLC** (NOT "ElectroCom IT" — that's the brand) |
| **UEI** | **P5Y6JWM2JA53** |
| **SAM status** | **"ID Assigned"** = UEI only, registration INCOMPLETE → can't bid |
| **Structure** | LLC |
| **State** | TX |
| **Address on SAM** | 1212 Horsemint Dr, Little Elm, TX 75068 ⚠️ (differs from Celina HQ — reconcile, see below) |
| **UEI assigned** | Jul 4, 2025 |

> 🚨 **Internal-notes correction:** CLAUDE.md says "SAM.gov registered." That's misleading —
> we only have a UEI, not an active registration. Update once registration goes Active.

---

## STEP 0 — Find the account holder (DO THIS FIRST)

Completing the registration requires logging into the **existing** record. Whoever created
the UEI on **Jul 4, 2025** holds the **Login.gov account + Entity Administrator role.**

- **Ask the team:** *"Who created the SAM.gov UEI last July — whose Login.gov email is it under?"*
- **If found** → that person signs in: **sam.gov → Workspace → Entity → continue/complete registration.**
- **If nobody has it / they left** → request the **Entity Administrator role** via SAM.gov
  (identity-verification process; slower but doable). Federal Service Desk can guide this.

**Reconcile the address:** the SAM record shows Little Elm, but our HQ is Celina. The address
on SAM must match the LLC's **legal formation / IRS records.** Confirm which address the LLC
was actually formed under and use that; update it during completion if needed.

---

## STEP 1 — Data we ALREADY have ✅

| Field | Value |
|---|---|
| Legal name | ElectroCom Innovations LLC |
| UEI | P5Y6JWM2JA53 |
| Entity structure | LLC |
| State | TX |
| Brand / website | ElectroCom IT · electrocomit.com |
| Employee count | 11+ |
| Founded (operating history) | 1998 (telecom roots → full IT services) |
| Primary business | IT solutions / software / AI-ML engineering |

---

## STEP 2 — Data we still NEED to COMPLETE registration ⚠️ (fill these in)

Legal name, UEI, structure and state are now confirmed (see Status box). The fields below
come from the LLC's formation docs + IRS records. **The legal name "ElectroCom Innovations LLC"
must match the IRS EIN letter EXACTLY** or the TIN match fails.

| Field | Why it's needed | Value (FILL IN) |
|---|---|---|
| **Login.gov account holder** | Whoever created the UEI Jul 4 2025 — needed to access the record | __________ |
| **Correct legal address** | Reconcile Little Elm (on SAM) vs Celina HQ — use the LLC's formation/IRS address | __________ |
| **LLC formation date** | Date ElectroCom Innovations LLC was formed (NOT 1998) | __________ |
| **EIN / TIN** (9-digit) | IRS taxpayer ID — must match "ElectroCom Innovations LLC". *Sensitive — on-site only.* | __________ |
| **Name exactly as on IRS records** | For the IRS TIN match step | __________ |
| **Bank routing + account #** | For EFT (how the govt pays you). *Sensitive — on-site only.* | __________ |
| **Prior-year annual revenue** | For small-business size determination | __________ |
| **DBA (if any)** | e.g. "ElectroCom IT" as a doing-business-as name | __________ |

---

## STEP 3 — Points of Contact (POCs)

SAM.gov requires named POCs. Recommended mapping (confirm with team):

| Role | Suggested person | Email |
|---|---|---|
| Entity Administrator | Faizan or Arslan (whoever owns the Login.gov account) | __________ |
| Electronic Business POC | Arslan Noor (CTO) | arslan@electrocomit.com |
| Government Business POC | Zulfiqar Saeed (CEO) | __________ |
| Past Performance POC | Arslan Noor | arslan@electrocomit.com |

> Consider routing the govt-business POC to **partnerships@electrocomit.com** once that alias
> is live, so federal correspondence is tracked separately from commercial BD.

---

## STEP 4 — Recommended NAICS codes

NAICS = the industry classifications that determine which solicitations match us and whether
we qualify as a small business. **Pick ONE primary + several secondary.** For a software/AI/IT
shop with 11 staff, we comfortably qualify as a **small business** under all of these (their
size standards run $19M–$34M in revenue — well above us), which unlocks small-business set-asides.

**Primary (recommended):**
- **541511 — Custom Computer Programming Services** → web/full-stack/SaaS dev. Best fit for our core. *(Size std: $34M)*

**Secondary:**
- **541512 — Computer Systems Design Services** → architecture, systems integration, AI systems
- **541519 — Other Computer Related Services** → catch-all incl. staff augmentation/IT services
- **518210 — Computing Infrastructure Providers, Data Processing, Web Hosting** → managed IT, cloud, DevOps
- **541611 — Administrative & General Management Consulting** → strategic IT consulting / digital transformation
- **541715 — R&D in Physical, Engineering & Life Sciences** → optional, for AI/ML research framing
- **561320 — Temporary Help Services** → optional, if pitching staff augmentation to govt teams

> Map to our 5 service pillars: Web Dev → 541511 · AI/ML → 541512/541715 · Managed IT → 518210 ·
> Consulting → 541611 · Staff Aug → 541519/561320.

---

## STEP 5 — Reps & Certifications (heads-up)

Full registration ends with the FAR/DFARS reps & certs — a long yes/no questionnaire
(business types, small-business status, ownership, no debarments, etc.). Nothing to prepare in
advance, but budget ~30–45 min. Answer honestly; small-business and any
minority/disadvantaged-owned status here drive set-aside eligibility.

---

## STEP 6 — The live flow (order of operations)

1. **Create/sign in to Login.gov** (personal account for the person registering).
2. sam.gov → **Get Started → Register Entity** → choose **"Bid on contracts / apply for awards."**
3. Enter **entity details** (legal name, address, start date, structure) → SAM validates against public records → assigns a **Unique Entity ID (UEI)**.
4. **IRS TIN match** (EIN + IRS name) — can take 1–2 business days.
5. **CAGE code** assigned automatically for US entities.
6. Enter **banking/EFT** details.
7. Add **POCs** (Step 3).
8. Complete **Reps & Certs** (Step 5).
9. Submit → **up to 10 business days to go Active.**

---

## STEP 7 — Free help available

- **APEX Accelerators** (formerly PTACs) — free, government-funded help completing SAM.gov registration. Find the local TX office; worth using for the first registration.
- **Federal Service Desk** — fsd.gov, live chat/phone Mon–Fri 8am–8pm ET, for technical issues.

---

## Outstanding actions
- [x] Run entity-status check → FOUND: ElectroCom Innovations LLC, UEI P5Y6JWM2JA53, status "ID Assigned"
- [x] Confirm it's our company → YES (team confirmed)
- [ ] **Identify the Login.gov account holder who created the UEI Jul 4 2025** ← critical blocker
- [ ] Reconcile address (Little Elm on SAM vs Celina HQ — use legal formation address)
- [ ] Fill remaining ⚠️ fields in Step 2 (formation date, EIN, EFT bank, revenue)
- [ ] Confirm POC mapping (Step 3)
- [ ] Confirm primary + secondary NAICS (Step 4)
- [ ] Log into Workspace → Entity → complete full registration (ID Assigned → Active)
- [ ] Once Active: correct the "SAM.gov registered" line in CLAUDE.md
