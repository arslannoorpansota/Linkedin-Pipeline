# Google Sheets — ElectroCom BD Pipeline

## Setup instructions
- Sheet name: **ElectroCom BD Pipeline**
- One tab per lead type OR one flat sheet with a "Lead Type" column (recommended: flat sheet, filter by type)
- Freeze row 1 (headers)
- Enable conditional formatting on the **Status** column (color-coded by stage)
- Sort by **Next Action Date** ascending to see what needs attention today

---

## Column Definitions

### Section A — Identity (columns A–G)

| # | Column | Type | Notes |
|---|---|---|---|
| A | Lead ID | Auto-number | Format: `BD-001`, `BD-002`... |
| B | Date Added | Date | When you added them to the sheet |
| C | Full Name | Text | First + Last |
| D | Title | Text | Their exact job title |
| E | Company | Text | Company name |
| F | Industry | Dropdown | `SaaS` / `Consulting / Agency` / `Enterprise` / `Startup` / `Government` / `Healthcare` / `Finance` / `Other` |
| G | Location | Text | City, Country (e.g. "Austin, TX" or "London, UK") |

---

### Section B — Contact Info (columns H–L)

| # | Column | Type | Notes |
|---|---|---|---|
| H | LinkedIn URL | URL | Full profile URL |
| I | Email | Text | If found/given |
| J | Phone | Text | Optional — rarely needed at this stage |
| K | Connection Degree | Dropdown | `1st` / `2nd` / `3rd` / `None` |
| L | Mutual Connections | Number | How many shared connections |

---

### Section C — Lead Qualification (columns M–R)

| # | Column | Type | Notes |
|---|---|---|---|
| M | Lead Type | Dropdown | `Direct Client` / `Agency Partner` / `Anthropic Partner` / `Hire (Arslan)` |
| N | Service Interest | Dropdown (multi) | `Web Dev` / `AI/ML` / `Full-stack` / `Managed IT` / `Staff Aug` / `Partnership` / `Hire Arslan` |
| O | Deal Type | Dropdown | `Project` / `Retainer` / `Staff Augmentation` / `Partnership` / `Remote Role` |
| P | Estimated Budget | Dropdown | `<$5k` / `$5k–$20k` / `$20k–$50k` / `$50k–$100k` / `$100k+` / `Unknown` |
| Q | Priority | Dropdown | `High` / `Medium` / `Low` |
| R | Hook / Why Outreach | Text | What made them worth reaching out to (specific post, event, role change) |

---

### Section D — Outreach (columns S–Z)

| # | Column | Type | Notes |
|---|---|---|---|
| S | Outreach Channel | Dropdown | `LinkedIn DM` / `Email` / `Both` / `Referral` / `Inbound` |
| T | From Email | Dropdown | `arslan@electrocomit.com` / `partnerships@electrocomit.com` / `info@electrocomit.com` / `N/A (LinkedIn)` |
| U | DM / Email Sent Date | Date | Date of first contact |
| V | Connection Note Sent | Checkbox | TRUE if connection request sent with note |
| W | DM Content | Long text | Paste the exact DM sent (for reference and A/B learning) |
| X | Email Subject | Text | If email was sent |
| Y | Email Content | Long text | Paste the email body |
| Z | Outreach by | Dropdown | `Arslan` / `Faizan` |

---

### Section E — Response Tracking (columns AA–AE)

| # | Column | Type | Notes |
|---|---|---|---|
| AA | Status | Dropdown | See status options below |
| AB | Response Date | Date | When they replied |
| AC | Response Type | Dropdown | `Positive` / `Neutral` / `Negative` / `No Response` |
| AD | Response Summary | Text | 1–2 sentence summary of what they said |
| AE | Interested In | Text | What specifically they expressed interest in |

#### Status options (color-code these)
| Status | Color |
|---|---|
| `New` | White |
| `DM Sent` | Light Blue |
| `Email Sent` | Light Blue |
| `Connection Requested` | Light Purple |
| `Connected (No DM yet)` | Light Purple |
| `Replied` | Yellow |
| `Interested` | Orange |
| `Call Scheduled` | Orange |
| `Proposal Sent` | Light Green |
| `Negotiating` | Green |
| `Won` | Dark Green |
| `Lost` | Red |
| `On Hold` | Grey |
| `Not Relevant` | Dark Grey |

---

### Section F — Follow-up Log (columns AF–AK)

| # | Column | Type | Notes |
|---|---|---|---|
| AF | Follow-up 1 Date | Date | When FU1 was sent |
| AG | Follow-up 1 Notes | Text | What you said |
| AH | Follow-up 2 Date | Date | When FU2 was sent |
| AI | Follow-up 2 Notes | Text | What you said |
| AJ | Follow-up 3 Date | Date | When FU3 was sent |
| AK | Follow-up 3 Notes | Text | What you said |

---

### Section G — Pipeline (columns AL–AQ)

| # | Column | Type | Notes |
|---|---|---|---|
| AL | Meeting / Call Date | Date | Discovery call date |
| AM | Meeting Notes | Long text | Key takeaways from the call |
| AN | Proposal Sent Date | Date | |
| AO | Deal Value (USD) | Currency | Estimated deal value |
| AP | Close Date | Date | When Won or Lost |
| AQ | Win/Loss Reason | Text | One sentence on why |

---

### Section H — Admin (columns AR–AV)

| # | Column | Type | Notes |
|---|---|---|---|
| AR | Assigned To | Dropdown | `Arslan` / `Faizan` / `Both` |
| AS | Next Action | Text | What needs to happen next (e.g. "Send FU2" / "Book call" / "Send proposal") |
| AT | Next Action Date | Date | Deadline for next action — sort by this column |
| AU | Lead Source | Dropdown | `LinkedIn Manual` / `LinkedIn Sales Nav` / `Job Board` / `Upwork` / `Referral` / `Inbound` / `Event` |
| AV | Internal Notes | Long text | Anything else (shared context, personal detail to reference later) |

---

## Tab Structure (recommended)

| Tab | Purpose |
|---|---|
| **Pipeline** | Main flat sheet — all leads, all stages |
| **Won** | Auto-filter or copy of Won rows (for reference / testimonials) |
| **Templates** | Paste winning DMs here — A/B comparison |
| **Weekly Stats** | Manual weekly metrics: leads added, DMs sent, response rate, calls booked |

---

## Weekly Stats Tab — Columns

| Column | Track |
|---|---|
| Week | Date of Monday |
| Leads Added | # new rows |
| DMs Sent | # DM Sent status |
| Emails Sent | # Email Sent |
| Replies Received | # Replied |
| Response Rate % | Replies / Sent |
| Calls Booked | # Call Scheduled |
| Won This Week | # Won |
| Revenue This Week | Sum of AO for Won this week |
| Top Hook | What message type got most replies |

---

## Conditional Formatting Rules

Apply to column AA (Status):
- `Won` → dark green background, white text
- `Negotiating` → green
- `Proposal Sent` → light green
- `Call Scheduled` → orange
- `Interested` → light orange
- `Replied` → yellow
- `DM Sent` / `Email Sent` / `Connection Requested` → light blue
- `Lost` → red
- `On Hold` / `Not Relevant` → grey

Apply to column AT (Next Action Date):
- Overdue (< today) → red background
- Due today → orange
- Due in 3 days → yellow
