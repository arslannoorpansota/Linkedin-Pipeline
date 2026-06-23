#!/usr/bin/env python3
"""
One-off: push the 40-company prospecting database (assets/prospect-database-40.md)
into the BD Pipeline sheet as 40 individual rows on the "Pipeline" tab.

Reuses the OAuth token, spreadsheet id, and Sheets helpers from
sync_reports_to_sheet.py. Idempotent via its own state file
(.prospect_push_state.json), keyed by company name — re-runs only append
companies not already pushed.

Usage:
    python push_prospects_to_sheet.py            # push new prospects
    python push_prospects_to_sheet.py --dry-run  # print rows, no write
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import sync_reports_to_sheet as sync

SCRIPT_DIR = Path(__file__).resolve().parent
STATE_FILE = SCRIPT_DIR / ".prospect_push_state.json"

# (Company, Website, Contact, Role, LinkedIn, Industry, Location, LeadType,
#  Service Interest, Hook, Priority)
PROSPECTS = [
    ("Runware", "runware.ai", "Flaviu Radulescu", "Co-Founder & CEO", "linkedin.com/in/flaviur", "AI inference infrastructure (image/video API)", "San Francisco, CA", "Direct Client", "AI/ML + DevOps", "Raised $50M Series A led by Dawn Capital (Comcast Ventures, a16z speedrun), Dec 11 2025", "Medium"),
    ("Kernel", "kernel.sh", "Catherine Jue", "Co-Founder & CEO", "linkedin.com/in/juecd", "Browser infrastructure for AI agents", "San Francisco, CA", "Direct Client", "Infra/DevOps + SDK", "Raised $22M Seed+Series A led by Accel (YC S25; angels incl. Paul Graham), Oct 9 2025", "High"),
    ("Leo AI", "getleo.ai", "Maor Farid", "Co-Founder & CEO", "linkedin.com/in/maorfaridphd", "Generative AI for mechanical engineering / CAD", "Cambridge, MA", "Direct Client", "Full-stack + RAG", "Closed oversubscribed $9.7M seed led by Flint Capital (Google VP Yossi Matias), Sep 2 2025", "Medium"),
    ("Structured AI", "getstructured.ai", "Raymond Zhao", "Co-Founder & CEO", "linkedin.com/in/raymondz1", "Construction QA/QC AI agents (computer vision)", "New York, NY", "Direct Client", "Computer vision + full-stack", "Raised $4.2M seed led by FCVC (YC F25, 20VC, Cherry), Jun 10 2026", "High"),
    ("Coactive AI", "coactive.ai", "Cody Coleman", "Co-Founder & CEO", "linkedin.com/in/codyaustun", "Multimodal AI over image/video data", "San Jose, CA", "Direct Client", "Data engineering + staff-aug", "Scaled to ~64 staff across 3 continents (Apr 2026); MIT News profile Jun 2025; $44M total raised", "Medium"),
    ("Newo.ai", "newo.ai", "Jason Luo", "CEO (appointed Apr 21 2026)", "VERIFY - not confirmed", "Voice AI agents for SMB front-desk ops", "San Francisco, CA", "Direct Client", "Voice/telephony + backend", "Raised $25M Series A led by Ratmir Timashev (Veeam), Feb 10 2026; new CEO for partner-led expansion", "Medium"),
    ("Parasail", "parasail.io", "Mike Henry", "Founder & CEO", "linkedin.com/in/mike-henry-72204123", "AI inference supercloud (GPU/pay-per-token)", "San Mateo, CA", "Direct Client", "Backend orchestration + DevOps", "Raised $32M Series A co-led by Touring Capital & Kindred Ventures, Apr 15 2026", "Medium"),
    ("Worth AI", "worthai.com", "Sal Rehmetullah", "CEO & Co-Founder", "linkedin.com/in/sal-rehmetullah-59704741", "FinTech - AI SMB onboarding / KYB / underwriting", "Orlando, FL", "Direct Client", "ML + data pipelines", "Raised $30M Series A led by Fulcrum Equity (Amex Ventures, TTV), Mar 24 2026", "High"),
    ("Sequence", "sequencehq.com", "Riya Grover", "Co-Founder & CEO", "uk.linkedin.com/in/riya-grover-a22a4822", "FinTech - AI revenue ops / order-to-cash", "New York, NY", "Direct Client", "Agentic AI + integrations", "Raised $20M Series A led by 645 Ventures (a16z), Dec 2025; 10x ARR, expanding engineering", "High"),
    ("Pillar", "pillarhq.com", "Harsha Ramesh", "Co-Founder & CEO", "linkedin.com/in/harshavramesh", "FinTech - AI financial risk / automated hedging", "New York, NY", "Direct Client", "Real-time pipelines + ML", "Raised $20M seed led by a16z (Dara Khosrowshahi angel), ~Apr 14 2026", "High"),
    ("Ironlight Group", "ironlight.io", "Rob McGrath", "Co-Founder & CEO", "VERIFY - Crunchbase only", "FinTech - tokenized securities infra (ATS)", "Austin, TX", "Direct Client", "Blockchain/settlement + compliance", "Closed $21M Series A backed by ex-TD Bank CEO Greg Braca, Mar 16 2026", "Medium"),
    ("Yuzu Health", "yuzu.health", "Max Kauderer", "Co-Founder & CEO", "linkedin.com/in/max-kauderer", "HealthTech - next-gen TPA / health-plan infra", "New York, NY", "Anthropic Partner", "Claims backend + HIPAA infra", "Raised $35M Series A led by General Catalyst & Chemistry (Anthropic Anthology Fund), Apr 6 2026", "High"),
    ("Amperos Health", "amperos.com", "Michal Miernowski", "Co-Founder & CEO", "linkedin.com/in/michalmiernowski", "HealthTech - agentic AI for revenue cycle mgmt", "New York, NY", "Direct Client", "Agentic AI/LLM + EHR integration", "Raised $16M Series A led by Bessemer, ~Apr 22 2026; launched AI denial-management platform", "High"),
    ("Coral", "VERIFY DOMAIN", "Ajay Shrihari", "Founder & CEO", "linkedin.com/in/ajay-shrihari", "HealthTech - AI healthcare back-office automation", "New York, NY", "Direct Client", "AI/LLM doc automation + integrations", "Raised $12.5M led by Lightspeed & Z47, Apr 20 2026; targeting 4x growth, adding engineers", "High"),
    ("FamilyWell Health", "familywellhealth.com", "Dr. Jessica Gaulton", "Founder & CEO", "linkedin.com/in/jessicagaulton", "Digital Health - women's / maternal mental health", "Massachusetts", "Direct Client", "AI triage + telehealth platform", "Raised $8M Series A led by New Markets Venture Partners, Nov 18 2025; advancing AI capabilities", "Medium"),
    ("Conduit", "helloconduit.com", "Conrad Lilleness", "Co-Founder & CEO", "linkedin.com/in/conradlilleness", "Logistics - AI OS for dock & yard operations", "Seattle, WA", "Direct Client", "Full-stack + LLM automation + DevOps", "Raised $6M seed led by Innovation Endeavors (YC), Mar 24 2026; 172% net dollar retention", "Medium"),
    ("FleetWorks", "fleetworks.app", "Paul Singer", "Co-Founder & CEO", "linkedin.com/in/paul-singer", "Logistics - AI freight marketplace / dispatch", "San Francisco, CA", "Direct Client", "AI voice/agent + data pipelines", "Raised $17M (incl. $15M Series A) led by First Round, Oct 14 2025; 10,000+ carriers in 6 months", "High"),
    ("Vori", "vori.com", "Brandon Hill", "Co-Founder & CEO", "linkedin.com/in/bhill93", "Retail/Logistics - AI OS for grocery stores", "San Francisco, CA", "Direct Client", "Full-stack + AI forecasting + staff-aug", "Raised $22M Series B led by Cherryrock Capital (Greylock), May 6 2026; ~$50M total", "Medium"),
    ("Mentium", "mentium.io", "Aziz Satarov", "Co-Founder & CEO", "linkedin.com/in/aziz-satarov-06b80357", "Logistics - AI digital workers for freight brokers", "Austin, TX", "Direct Client", "AI agents/LLM + staff-aug", "Raised $3.2M seed led by Lerer Hippeau, Oct 9 2025 - explicitly to grow the engineering team", "High"),
    ("ReFiBuy", "refibuy.ai", "Scot Wingo", "CEO & Co-Founder", "linkedin.com/in/thescotwingo", "E-commerce - agentic commerce / product-data infra", "Raleigh, NC", "Direct Client", "RAG + data/ETL + LLM", "Raised $13.6M oversubscribed seed led by NewRoad Capital, May 5 2026; planning ~10 eng hires", "High"),
    ("Onton", "onton.com", "Zach Hudson", "Co-Founder & CEO", "linkedin.com/in/hudsonzp", "E-commerce - AI product search & discovery", "San Francisco, CA", "Direct Client", "AI/ML + vector search + RAG", "Raised $7.5M seed led by Footwork, Nov 26 2025; scaled 50K->1M+ MAUs with a tiny team", "Medium"),
    ("Flock AI", "flockai.com", "Manvitha Mallela", "Co-Founder & CEO", "linkedin.com/in/manvitha-mallela-9a699884", "E-commerce - generative-AI visual commerce", "New York, NY", "Direct Client", "CV/diffusion model + GPU DevOps", "Closed $6M seed led by Work-Bench, Feb 2026 ($7.5M total)", "Medium"),
    ("Sequen", "sequen.ai", "Zoe Weil", "Co-Founder & CEO", "linkedin.com/in/zoefrancesweil", "Retail - real-time personalization / AI ranking", "New York, NY", "Direct Client", "Integration engineering + data eng", "Raised $16M Series A co-led by White Star & Threshold, Mar 18 2026; CEO ex-Etsy AI ranking", "Medium"),
    ("AdsGency AI", "adsgency.ai", "Bolbi Liu", "Founder & CEO", "linkedin.com/in/bolbi-liu", "MarTech - agentic AI ad automation", "San Francisco, CA", "Direct Client", "AI/ML + RAG + full-stack staff-aug", "Raised $12M seed led by XYZ Venture Capital, Oct 19 2025 - explicitly to hire a top eng team", "High"),
    ("Scrunch AI", "scrunch.com", "Chris Andrew", "CEO & Co-Founder", "linkedin.com/in/chriswandrew", "MarTech - AI-search visibility (AEO)", "Salt Lake City, UT", "Direct Client", "DevOps/cloud + RAG + dashboards", "Raised $15M Series A led by Decibel (Mayfield, Homebrew), Jul 22 2025; 50% MoM customer growth", "Medium"),
    ("Firsthand", "firsthand.ai", "Jon Heller", "Co-Founder & Co-CEO", "linkedin.com/in/jonheller", "AdTech - AI Brand Agent platform", "New York, NY", "Direct Client", "Senior ML/LLM staff-aug + data eng", "Raised $26M Series A led by Radical Ventures (FirstMark, Crossbeam), Mar 4 2025; doubling team", "Medium"),
    ("Cambio", "cambio.ai", "Stephanie Grayson", "Co-Founder & Co-CEO", "linkedin.com/in/stephaniegrayson", "PropTech - AI-native CRE operations", "New York, NY", "Direct Client", "RAG + doc-extraction + agents", "Raised $18M Series A at ~$100M val led by Maverick (OpenAI/Anthropic angels), Jan 22 2026", "High"),
    ("Lula", "lula.life", "Bo Lais", "Founder & CEO", "linkedin.com/in/bolais", "PropTech - AI property-maintenance / work orders", "Overland Park, KS", "Direct Client", "AI/ML/LLM + cloud DevOps", "Raised $28M Series A led by PeakSpan (RET Ventures), Feb 3 2025 - to build 'Foresight' AI SaaS", "High"),
    ("Roam", "roam.com", "Raunaq Singh", "Founder & CEO", "linkedin.com/in/raunaqsingh87", "PropTech/FinTech - assumable-mortgage marketplace", "New York, NY", "Direct Client", "Workflow automation + integrations + AI", "Raised $11.5M Series A led by Khosla/Keith Rabois, Apr 2 2025; Opendoor mortgage partnership Nov 2025", "Medium"),
    ("CasaPerks", "casaperks.com", "Kevin J. Bradt", "Founder & CEO", "linkedin.com/in/kevin-bradt-7223572", "PropTech - AI rent/resident loyalty & rewards", "Austin, TX", "Anthropic Partner", "AI/ML + data integration + full-stack", "Closed $15.8M seed (Longevity Equity), May 26 2026; 10x revenue; built on Anthropic's Claude", "High"),
    ("Trayd", "trayd.io", "Anna Berger", "Co-Founder & CEO", "linkedin.com/in/annajberger", "Construction SaaS - payroll/HR/compliance", "New York, NY", "Direct Client", "Backend + AI classification + DevOps", "Raised $10M Series A led by White Star Capital (YC, Suffolk Tech), Mar 25 2026; 600%+ YoY revenue", "Medium"),
    ("Empromptu", "empromptu.ai", "Shanea Leven", "Founder & CEO", "linkedin.com/in/shaneak", "SaaS - AI-native app eval/observability", "San Francisco, CA", "Direct Client", "RAG/LLM eval + dashboards", "Raised $2M pre-seed led by Precursor Ventures, Dec 9 2025; 2,000+ businesses integrating", "Medium"),
    ("Squint", "squint.ai", "Devin Bhushan", "Founder & CEO", "linkedin.com/in/devinbhushan", "Manufacturing - AI+AR factory operations", "San Francisco, CA", "Direct Client", "LLM agents + CV + mobile staff-aug", "Raised $40M Series B at $265M val (TCV, Sequoia, Menlo), Aug 12 2025; PepsiCo/Ford/Siemens customers", "Medium"),
    ("Emerald AI", "emeraldai.co", "Dr. Varun Sivaram", "Founder & CEO", "linkedin.com/in/varunsivaram", "Climate Tech - grid-flexibility for AI data centers", "Washington, DC", "Direct Client", "ML forecasting + DevOps + dashboards", "Launched from stealth with $24.5M seed (Jul 2025) + $18M (Oct 2025); NVIDIA/Radical; TIME100 Climate", "Medium"),
    ("Claros", "claros.tech", "Daniel Kultran", "Co-Founder & CEO", "linkedin.com/in/danielkultran", "Climate/Industrial - chip-to-grid power mgmt", "McLean, VA", "Direct Client", "Telemetry dashboards + ML + DevOps", "Raised $30M oversubscribed seed co-led by General Catalyst & Red Cell, Mar 19 2026; Samsung Foundry deal Jun 2026", "Medium"),
    ("Rondo Energy", "rondo.com", "John O'Donnell", "Co-Founder & CEO", "VERIFY - company page only", "Climate Tech - industrial heat batteries", "Alameda, CA", "Direct Client", "SCADA/IoT pipelines + predictive ML", "Brought world's largest 100 MWh industrial heat battery online, Oct 2025; backed by Microsoft, Aramco", "Medium"),
    ("Juno", "junotax.com", "Dave Haase", "Founder & CEO", "linkedin.com/in/dshaase", "FinTech - AI tax-prep for accounting firms", "San Diego, CA", "Direct Client", "AI/ML doc-extraction + staff-aug", "Raised $12M seed led by Bonfire Ventures, ~Apr 9 2026 - stated will 'double the engineering team'", "High"),
    ("Courier Health", "courierhealth.com", "Danny Sigurdson", "Founder & CEO", "linkedin.com/in/dannysigurdson", "HealthTech - AI patient-CRM for biopharma", "New York, NY", "Direct Client", "Data eng/RAG + AI features + embedded eng", "Raised $50M Series B led by Oak HC/FT (Norwest, Work-Bench), ~Apr 22 2026; 400%+ customer growth in 2025", "High"),
    ("Paxton AI", "paxton.ai", "Dr. Tanguy Chau", "Co-Founder & CEO", "linkedin.com/in/tanguychau", "LegalTech - generative-AI legal research", "Portland, OR", "Hire (Arslan)", "AI eng (RAG) + CTO-advisory", "Raised $22M Series A led by Unusual Ventures, Jan 2025; 14x MRR in 9 months; CTO co-founder departed Jun 2025", "High"),
    ("Ressio Software", "ressiosoftware.com", "Mitchell Kasselman", "Co-Founder & CEO", "linkedin.com/in/mitchellkasselman", "Construction SaaS - AI construction management", "Washington, DC", "Direct Client", "Full-stack + AI doc handling", "Raised $8.75M Series A led by Blueprint Equity, ~Jan 9 2026 - to accelerate product development", "Medium"),
]


def load_state() -> set[str]:
    if STATE_FILE.exists():
        try:
            return set(json.loads(STATE_FILE.read_text()).get("pushed", []))
        except Exception:
            return set()
    return set()


def save_state(keys: set[str]) -> None:
    STATE_FILE.write_text(json.dumps({"pushed": sorted(keys)}, indent=2))


def prospect_to_row(p) -> list[str]:
    (company, website, contact, role, linkedin, industry, location,
     lead_type, service, hook, priority) = p
    row = {h: "" for h in sync.PIPELINE_HEADERS}
    row["Full Name"] = contact
    row["Title"] = role
    row["Company"] = company
    row["Industry"] = industry
    row["Location"] = location
    row["LinkedIn URL"] = linkedin
    row["Lead Type"] = lead_type
    row["Service Interest"] = service
    row["Priority"] = priority
    row["Hook / Why Outreach"] = hook
    row["Status"] = "New"
    row["Assigned To"] = "Arslan"
    row["Lead Source"] = "Prospect DB 2026-06-23 (assets/prospect-database-40.md)"
    row["Next Action"] = "Verify LinkedIn/domain, then run DM agent"
    return [row[h] for h in sync.PIPELINE_HEADERS]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    state = load_state()
    new = [p for p in PROSPECTS if p[0].lower() not in state]
    print(f"{len(PROSPECTS)} prospects total; {len(new)} new to push.")

    if args.dry_run:
        for p in new:
            print(f"  [{p[0]}] {p[2]} - {p[3]}")
        return 0

    if not new:
        print("Nothing new to push.")
        return 0

    cfg = sync.load_config()
    service = sync.get_service()
    sid = sync.ensure_spreadsheet(service, cfg)
    sync.ensure_tab_and_header(service, sid, sync.PIPELINE_TAB, sync.PIPELINE_HEADERS)

    sync.append_rows(service, sid, sync.PIPELINE_TAB, [prospect_to_row(p) for p in new])

    for p in new:
        state.add(p[0].lower())
    save_state(state)

    print(f"Pushed {len(new)} prospect rows to Pipeline tab.")
    print(f"Sheet: {cfg.get('spreadsheet_url', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
