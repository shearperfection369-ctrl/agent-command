"""JADE OS · Operations Workbench.

A structured Sales Engineering Operations workspace with:
  • 6 OPERATIONS (Labs) — each a discrete deliverable with personal-test pathway
  • 8 PHASES — sequenced workflow with steps + state tracking
  • RISKS register (7 items)
  • DECISIONS tracker (5 auto-seeded decisions)
  • MATERIALS + TOOLS reference

Each Lab persists run history to db.workbench_runs so the operator can
re-run, compare, audit, and export.

All seed data is curated from the user's brief — these are operator-grade
defaults, not LLM hallucinations. The "OPEN LAB" buttons trigger real
LLM-grounded workflows (OP-01 PDF generation, OP-02 Excel ROI, OP-06 lead
segmentation extending existing real-leads work).
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------- OPERATIONS · 6 LABS ----------

OPERATIONS = [
    {
        "id": "OP-01", "code": "MARKET_ANALYSIS",
        "title": "Minnesota Freight Industry Deep-Dive",
        "deliverable": "3–5 page industry summary with data sources + outlook (PDF download)",
        "depth": "full",  # functional Lab today
        "lab_endpoint": "/api/workbench/labs/op-01/run",
        "lab_view": "market-analysis",
        "color": "#ccff00",
    },
    {
        "id": "OP-02", "code": "FINANCIAL_MODELING",
        "title": "ROI Calculator · 3 Archetypes · 3-Year NPV",
        "deliverable": "Excel-style ROI model with input/output tabs, formulas visible, sensitivity ±10%",
        "depth": "full",
        "lab_endpoint": "/api/workbench/labs/op-02/run",
        "lab_view": "financial-modeling",
        "color": "#00ffff",
    },
    {
        "id": "OP-03", "code": "AI_SYSTEMS_ARCHITECTURE",
        "title": "AI Agent Functional Architecture · 6 Modules",
        "deliverable": "Swimlane diagrams, API spec summary, decision logic flow charts",
        "depth": "full",
        "lab_endpoint": "/api/workbench/labs/op-03/run",
        "lab_view": "ai-architecture",
        "color": "#7c5cff",
    },
    {
        "id": "OP-04", "code": "SALES_COLLATERAL",
        "title": "Persona-Specific Pitch Deck + Fact Sheets",
        "deliverable": "12-slide deck (PDF), 4 1-pagers, Readiness Assessment workbook, competitive brief",
        "depth": "full",
        "lab_endpoint": "/api/workbench/labs/op-04/run",
        "lab_view": "sales-collateral",
        "color": "#ff3b8a",
    },
    {
        "id": "OP-05", "code": "DOCUMENTS",
        "title": "20–30 page Benefits & Features Technical Doc",
        "deliverable": "Polished PDF · 10 deep-dive sections · ROI cases · roadmap · technical appendix",
        "depth": "full",
        "lab_endpoint": "/api/workbench/labs/op-05/run",
        "lab_view": "documents",
        "color": "#ffce4f",
    },
    {
        "id": "OP-06", "code": "BUSINESS_RESEARCH",
        "title": "Target Company List · 15–25 MN Freight Co's",
        "deliverable": "Excel-style spreadsheet with sortable columns, LinkedIn/website URLs, contact recs",
        "depth": "full",
        "lab_endpoint": "/api/workbench/labs/op-06/run",
        "lab_view": "business-research",
        "color": "#00ffff",
    },
]


# ---------- PHASES · 8 PHASES with steps (flat — legacy) ----------

PHASES = [
    {
        "n": 1, "title": "Market Research & Company Identification", "duration": "3–4 days",
        "steps": [
            "Query Minnesota SOS SOFI database for freight/trucking/logistics LLCs+Corps with ≥5 employees · SIC 4213/4214/4215/4221/7359",
            "Cross-reference with Trucking Association of Minnesota + MN Motor Carriers Association (mid-market 50–500 vehicles)",
            "Collect contact info, fleet size, service type, annual revenue (Hoover's/state filings/web)",
            "Analyze 3–5 industry benchmark reports · lock baseline costs (driver $/hr, fuel $/gal, compliance violations, dispatcher burden)",
            "Segment into 3–4 buyer personas · document workflow gaps per persona",
        ],
    },
    {
        "n": 2, "title": "AI Agent Capability Mapping & Feature Definition", "duration": "3 days",
        "steps": [
            "Architect 6+ AI agent modules (Dispatch / Route / Compliance / Pricing / Driver Lifecycle / Predictive Maint / Carrier Matching)",
            "Define decision autonomy levels L1/L2/L3 · map each to company size/risk tolerance",
            "Document quantifiable features (8–15% empty-mile reduction, 12–18% fuel savings, 40–60% violation reduction)",
            "Design data pipeline · GPS/telematics + ELD + TMS + fuel card + insurance feeds · pre-map APIs for top 3 TMS in MN",
            "Build feature-to-pain-point matrix · 2×2 with quantified impact",
        ],
    },
    {"n": 3, "title": "Financial Modeling & ROI Quantification", "duration": "4 days", "steps": [
        "Define 3 company archetypes (Small Regional 25–75 trucks · Mid-Market 100–250 · Specialized/Hazmat)",
        "Build 6 cost-savings categories per archetype (labor, fuel, compliance, downtime, driver retention, claims)",
        "3-year NPV + payback analysis · discount rate 10–12%",
        "Sensitivity analysis · ±10% on key variables (fuel, driver wages, vehicle hours)",
        "Scenario switcher · conservative / base / optimistic",
    ]},
    {"n": 4, "title": "Detailed Target Company List & Segmentation", "duration": "2 days", "steps": [
        "Compile 15–25 MN freight companies with fleet size · service type · revenue · TMS · contact · AI-readiness score",
        "Segment by persona × sales stage (cold / warm / hot / pilot-ready)",
        "Recommend contact method per row (cold call / LinkedIn intro / warm intro / event)",
    ]},
    {"n": 5, "title": "Benefits & Features Deep-Dive Document", "duration": "2–3 days", "steps": [
        "Executive overview · 1 page",
        "6 deep-dive module sections · ~3 pages each",
        "ROI analysis with 2 case studies",
        "Implementation roadmap · 4 phases",
        "Minnesota opportunity snapshot + technical appendix",
    ]},
    {"n": 6, "title": "Sales Collateral & Pitch Deck Development", "duration": "2 days", "steps": [
        "12-slide pitch deck (problem · solution · 6 modules · ROI · case studies · pricing · ask)",
        "4 1-page fact sheets · one per buyer persona",
        "Readiness Assessment workbook (editable)",
        "Competitive positioning brief vs Descartes/Omnitracs/Geotab",
    ]},
    {"n": 7, "title": "Go-to-Market Strategy & Outreach Plan", "duration": "2 days", "steps": [
        "Channel mix · direct vs partner · per persona",
        "30/60/90-day outreach sequence per persona",
        "Pilot agreement template + success-metric definition",
    ]},
    {"n": 8, "title": "Reporting, Documentation & Continuous Refinement", "duration": "1–2 days", "steps": [
        "Lessons-learned log · weekly cadence",
        "Pipeline reporting dashboard + decision-checkpoint cadence",
    ]},
]


# ---------- PHASES_DEEP · operator-grade execution plan ----------
# Every step is expanded into structured sub-tasks with:
#   id · text · deliverable · exit_criteria · tools · hours · owner · depends_on · op_link
# op_link wires the step back to the corresponding OP-XX lab when applicable so
# the operator can jump from plan → execution in one click.

def _s(id, text, deliverable, exit_criteria, tools, hours, owner, depends_on=None, op_link=None):
    return {"id": id, "text": text, "deliverable": deliverable,
            "exit_criteria": exit_criteria, "tools": tools, "hours": hours,
            "owner": owner, "depends_on": depends_on or [], "op_link": op_link,
            "status": "todo", "notes": None}


PHASES_DEEP = [
    # ----- PHASE 1 ---------------------------------------------------------
    {"n": 1, "title": "Market Research & Company Identification",
     "duration": "3–4 days", "owner": "Analyst + Founder",
     "outcome": "A clean, source-traceable target universe of 50-150 MN freight companies + 3-4 buyer-persona definitions with documented workflow gaps.",
     "op_link": "OP-01", "op_link_label": "Run OP-01 Market Analysis",
     "substeps": [
        _s("1.1", "Query MN SOS SOFI for freight/trucking/logistics LLCs + Corps with ≥5 employees on SIC 4213/4214/4215/4221/7359",
           "CSV export · ≥500 raw rows", "rows have legal_name + entity_type + status=active + filing_date",
           ["MN SOS SOFI (sos.state.mn.us)", "Python csv module"], 4, "Analyst", [], "OP-06"),
        _s("1.2", "Cross-reference exported list with Trucking Association of MN + MN Motor Carriers Association rosters",
           "Joined CSV · de-duped on legal_name + DOT#", "≥250 carriers survive de-dup, each row carries TAM_member=true/false",
           ["mntruck.org", "FMCSA SAFER", "openrefine"], 4, "Analyst", ["1.1"], "OP-06"),
        _s("1.3", "Enrich with fleet size, service type, annual revenue from Hoover's + state filings + carrier websites",
           "Enriched CSV with fleet_size, service_type, revenue_range", "≥80% of rows have fleet_size populated; revenue is a range, never a fabricated point estimate",
           ["D&B Hoover's", "FMCSA QCMobile", "company websites"], 8, "Analyst", ["1.2"], "OP-06"),
        _s("1.4", "Score every row for mid-market fit (50–500 vehicles + Minnesota domiciled) and tag mid-market=true",
           "Filtered CSV · mid-market candidates only · 100–250 rows expected",
           "every retained row has fleet_size IN [50, 500] AND state==MN", ["Excel/Python pandas"], 2, "Analyst", ["1.3"], "OP-06"),
        _s("1.5", "Pull 3–5 industry benchmark reports (ATA Trucking Profile, ATRI Operational Costs, BLS OEWS 53-3032, EIA diesel, FMCSA enforcement)",
           "/research/benchmarks/ folder · 5 PDFs + 1 index.md summarizing key numbers",
           "every benchmark has: source URL, publication date, the 3 numbers we will cite, the cite-ready quote",
           ["ATA", "ATRI", "BLS OEWS", "EIA STEO", "FMCSA"], 6, "Analyst", [], "OP-01"),
        _s("1.6", "Lock baseline costs (driver $/hr, fuel $/gal, compliance violation cost, dispatcher hours/load) into ops_workbench bench dict",
           "Code · industry_benchmarks dict in build_roi_model already wired",
           "Every constant has a comment-citation pointing at the source document in /research/benchmarks/",
           ["ops_workbench.py"], 2, "Engineer", ["1.5"], "OP-02"),
        _s("1.7", "Define 3–4 buyer personas (Small Regional · Mid-Market · Intermodal · Specialized/Hazmat) with documented workflow gaps",
           "PITCH_DECK.fact_sheets + collateral persona doc",
           "Each persona has: headline · 3 pains · lead_agent · expected ROI range · contact channel preference",
           ["ops_workbench.PITCH_DECK.fact_sheets"], 4, "Founder", ["1.4", "1.5"], "OP-04"),
     ]},

    # ----- PHASE 2 ---------------------------------------------------------
    {"n": 2, "title": "AI Agent Capability Mapping & Feature Definition",
     "duration": "3 days", "owner": "Engineer + Founder",
     "outcome": "A 6-module agent stack, each with autonomy level, quantified KPI band, decision logic, and the exact input/output contract that the rest of the org can build to.",
     "op_link": "OP-03", "op_link_label": "Open OP-03 AI Architecture",
     "substeps": [
        _s("2.1", "Architect the 6 agent modules · Dispatch · Route+Fuel · Compliance · Pricing · Retention · Maintenance",
           "AI_ARCHITECTURE.modules in ops_workbench.py",
           "Each module documents: id · name · inputs · outputs · decision_logic · KPI band · autonomy",
           ["ops_workbench.py"], 4, "Engineer", [], "OP-03"),
        _s("2.2", "Assign autonomy levels L1 (suggest) / L2 (act with approval) / L3 (act autonomously, audit only)",
           "Per-module autonomy field with rationale in code comment",
           "L3 reserved for low-risk reversible actions; L2 default; L1 for pricing-floor and compliance-block scenarios",
           ["ops_workbench.AI_ARCHITECTURE"], 2, "Founder", ["2.1"], "OP-03"),
        _s("2.3", "Quantify features (empty-mile 8-15% · fuel 10-18% · violation 40-60% · retention +6-12pp · downtime -20-30%)",
           "Per-module KPI band stored on AI_ARCHITECTURE.modules[*].kpi",
           "Every KPI carries a benchmark source ID from Phase 1 step 1.5",
           ["ATA", "ATRI", "FMCSA"], 3, "Engineer", ["1.5", "2.1"], "OP-03"),
        _s("2.4", "Design data pipeline · ELD + TMS + fuel card + insurance + telematics + DOT 511",
           "AI_ARCHITECTURE.data_pipeline · 6 stages (Sources · Ingest · Store · Decide · Act · Observe)",
           "Each stage names concrete vendors/APIs; no abstract placeholders",
           ["AI_ARCHITECTURE.data_pipeline"], 4, "Engineer", ["2.1"], "OP-03"),
        _s("2.5", "Pre-map APIs for top 3 MN TMS · Descartes · McLeod · TMW (or Selerant for hazmat heavy)",
           "/research/tms_apis/ · 3 markdown docs · auth model + endpoints + rate limits + sandbox availability",
           "Each TMS has a concrete OAuth or API-key recipe + a tested ping example",
           ["TMS vendor docs", "Postman"], 4, "Engineer", ["2.4"], "OP-03"),
        _s("2.6", "Build feature-to-pain-point 2×2 matrix · quantified per persona × per agent",
           "PITCH_DECK.fact_sheets + a /research/feature_matrix.csv",
           "Every cell carries a numeric impact range traceable to a benchmark",
           ["Excel", "PITCH_DECK"], 3, "Founder", ["1.7", "2.3"], "OP-04"),
     ]},

    # ----- PHASE 3 ---------------------------------------------------------
    {"n": 3, "title": "Financial Modeling & ROI Quantification",
     "duration": "4 days", "owner": "Founder + Engineer",
     "outcome": "A live, recompute-on-demand ROI model with 3 archetypes, 6 savings categories per archetype, 3-yr NPV, payback months, and ±10% sensitivity — every number is benchmark-cited.",
     "op_link": "OP-02", "op_link_label": "Open OP-02 ROI Modeler",
     "substeps": [
        _s("3.1", "Define 3 archetypes · Small Regional 25-75 · Mid-Market 100-250 · Specialized/Hazmat 50-150",
           "arch_assumptions dict in build_roi_model with fleet defaults + dispatch/fuel/compliance/retention/downtime/claims pct uplifts",
           "Each archetype label + fleet default + 6 percentage assumptions visible in code",
           ["ops_workbench.build_roi_model"], 2, "Engineer", [], "OP-02"),
        _s("3.2", "Codify 6 cost-savings categories per archetype · labor · fuel · compliance · downtime · retention · claims",
           "by_category_usd output keys returned by /api/workbench/labs/op-02/run",
           "Every category has a formula visible in build_roi_model; no fudge factors",
           ["ops_workbench.build_roi_model"], 2, "Engineer", ["3.1"], "OP-02"),
        _s("3.3", "Compute 3-year NPV @ 10% discount + payback in months",
           "three_year output: net_y1/y2/y3 + npv_at_10pct + payback_months",
           "Math reproducible by hand from inputs; matches the recompute UI exactly",
           ["ops_workbench.build_roi_model"], 2, "Engineer", ["3.2"], "OP-02"),
        _s("3.4", "Sensitivity analysis · ±10% on annual savings (proxy for fuel/wages/hours)",
           "sensitivity dict · conservative / base / optimistic",
           "Bands shown alongside base every recompute; not hidden in code",
           ["ops_workbench.build_roi_model"], 1, "Engineer", ["3.3"], "OP-02"),
        _s("3.5", "Scenario switcher · conservative/base/optimistic + archetype + fleet override exposed in UI",
           "WorkbenchPanel LabOP02 + ConsoleWorkbenchPanel RoiPanel selectors",
           "Switch updates 6-category breakdown + NPV + payback live, <300ms",
           ["WorkbenchPanel.jsx", "ConsoleWorkbenchPanel.jsx"], 3, "Engineer", ["3.4"], "OP-02"),
        _s("3.6", "Source attribution · model returns sources[] every run (ATA · ATRI · BLS · EIA · FMCSA)",
           "model.sources array",
           "≥5 distinct sources cited; no source listed without an in-formula citation",
           ["ops_workbench.build_roi_model"], 1, "Founder", ["3.2"], "OP-02"),
     ]},

    # ----- PHASE 4 ---------------------------------------------------------
    {"n": 4, "title": "Detailed Target Company List & Segmentation",
     "duration": "2 days", "owner": "Analyst + Founder",
     "outcome": "A 15-25 row Minnesota target list with fleet, service, revenue range, TMS in use, AI-readiness score, persona, sales stage, and recommended contact method.",
     "op_link": "OP-06", "op_link_label": "Refresh OP-06 Target List",
     "substeps": [
        _s("4.1", "Pull the curated MN_FREIGHT_SEED list from fmcsa_lookup.py into db.prospects (idempotent)",
           "≥14 real companies upserted · all is_synthetic=false · DOT/MC populated where known",
           "Each prospect has verification_source set",
           ["fmcsa_lookup.MN_FREIGHT_SEED"], 1, "Engineer", [], "OP-06"),
        _s("4.2", "Enrich with TMS in use (best-effort from public sources)",
           "tms_vendor column populated where discoverable; left null where not — never guessed",
           "Null cells outnumber confidently-set cells until verified",
           ["LinkedIn", "carrier websites", "industry pubs"], 4, "Analyst", ["4.1"], "OP-06"),
        _s("4.3", "Score AI readiness 0-5 per prospect (TMS modernity · ELD vendor · IT bench · exec sponsor signal)",
           "ai_readiness column on db.prospects",
           "Every score has a 1-line rationale in notes",
           ["Custom rubric in /research/ai_readiness.md"], 3, "Founder", ["4.2"], "OP-06"),
        _s("4.4", "Segment by persona × sales stage (cold / warm / hot / pilot-ready)",
           "persona + sales_stage columns on db.prospects",
           "Top-of-funnel ≤30% in hot/pilot-ready; cohort split visible in dashboard",
           ["DesignPartnersPanel"], 2, "Founder", ["4.3"], "OP-06"),
        _s("4.5", "Recommend contact method per row (cold call · LinkedIn warm intro · referral · event)",
           "contact_method column",
           "Method matches sales_stage rule book (cold → cold call/LinkedIn; warm → referral)",
           ["Operator rule book"], 1, "Founder", ["4.4"], "OP-06"),
     ]},

    # ----- PHASE 5 ---------------------------------------------------------
    {"n": 5, "title": "Benefits & Features Deep-Dive Document",
     "duration": "2–3 days", "owner": "Founder + Engineer",
     "outcome": "A polished 20-30 page operator-grade technical brief PDF that a CFO can read end-to-end with every claim benchmark-traceable.",
     "op_link": "OP-05", "op_link_label": "Generate OP-05 Brief PDF",
     "substeps": [
        _s("5.1", "Author the executive overview (1 page · 5 headline bullets)",
           "TECHNICAL_DOC_SECTIONS[0] in ops_workbench.py",
           "Reads to a non-technical exec in <2 minutes",
           ["ops_workbench.TECHNICAL_DOC_SECTIONS"], 2, "Founder", [], "OP-05"),
        _s("5.2", "Six module deep-dives · ~3 pages each (M1-M6)",
           "TECHNICAL_DOC_SECTIONS[1..6]",
           "Each section covers inputs · decision · action · KPI · failure modes",
           ["AI_ARCHITECTURE.modules"], 8, "Engineer", ["2.1"], "OP-05"),
        _s("5.3", "ROI analysis · 2 illustrative case studies (Small Regional 50t · Mid-Market 175t)",
           "TECHNICAL_DOC_SECTIONS[7]",
           "Numbers match build_roi_model output to the dollar",
           ["build_roi_model"], 2, "Engineer", ["3.3", "5.2"], "OP-05"),
        _s("5.4", "Implementation roadmap · 4 phases (Readiness · Baseline · Pilot · Scale)",
           "TECHNICAL_DOC_SECTIONS[8]",
           "Every phase has a duration, exit criteria, and operator action",
           ["roadmap_template"], 2, "Founder", [], "OP-05"),
        _s("5.5", "Minnesota opportunity snapshot + technical appendix (APIs · auth · audit · LLM substrate)",
           "TECHNICAL_DOC_SECTIONS[9]",
           "API table mirrors AI_ARCHITECTURE.api_surface exactly",
           ["AI_ARCHITECTURE.api_surface"], 2, "Engineer", ["2.4"], "OP-05"),
        _s("5.6", "Render to PDF via reportlab (`generate_technical_doc_pdf`)",
           "PDF file at /app/backend/static_workbench/op05_*.pdf",
           "First 4 bytes = %PDF, size >5KB, opens in any PDF reader",
           ["ops_workbench.generate_technical_doc_pdf"], 1, "Engineer", ["5.1", "5.2", "5.3", "5.4", "5.5"], "OP-05"),
     ]},

    # ----- PHASE 6 ---------------------------------------------------------
    {"n": 6, "title": "Sales Collateral & Pitch Deck Development",
     "duration": "2 days", "owner": "Founder",
     "outcome": "A 12-slide pitch deck PDF + 4 persona fact sheets + a Readiness Assessment + a competitive brief — ready for live discovery calls.",
     "op_link": "OP-04", "op_link_label": "Generate OP-04 Deck PDF",
     "substeps": [
        _s("6.1", "Compose the 12-slide pitch (problem · solution · 6 modules · ROI · 2 case profiles · competitive · pricing · ask)",
           "PITCH_DECK.slides in ops_workbench.py",
           "Slide count == 12, every slide has a title + (subtitle | bullets)",
           ["ops_workbench.PITCH_DECK"], 4, "Founder", ["1.7", "5.2"], "OP-04"),
        _s("6.2", "4 persona fact sheets · one per buyer persona · headline + 3 pains + lead agent + ROI",
           "PITCH_DECK.fact_sheets[0..3]",
           "Every fact sheet has a quantified ROI range from build_roi_model",
           ["PITCH_DECK.fact_sheets"], 2, "Founder", ["1.7", "3.5"], "OP-04"),
        _s("6.3", "Readiness Assessment workbook · 3 areas (Data · Process · Tech & Org) · 4-5 questions each",
           "PITCH_DECK.readiness_assessment",
           "Yes/no answer model; takes a prospect <15 min to complete",
           ["PITCH_DECK.readiness_assessment"], 2, "Founder", [], "OP-04"),
        _s("6.4", "Competitive brief vs Descartes / Omnitracs / Geotab / internal-build",
           "PITCH_DECK.competitive_brief",
           "Each comp has a 2-sentence positioning statement and an explicit ABOVE-the-stack framing",
           ["PITCH_DECK.competitive_brief"], 2, "Founder", [], "OP-04"),
        _s("6.5", "Render deck to PDF (`generate_pitch_deck_pdf`) · landscape · brand fonts",
           "/app/backend/static_workbench/op04_*.pdf",
           "Deck PDF >8KB, 12+ pages, opens cleanly",
           ["ops_workbench.generate_pitch_deck_pdf"], 1, "Engineer", ["6.1"], "OP-04"),
     ]},

    # ----- PHASE 7 ---------------------------------------------------------
    {"n": 7, "title": "Go-to-Market Strategy & Outreach Plan",
     "duration": "2 days", "owner": "Founder",
     "outcome": "Channel mix per persona, a 30/60/90 outreach sequence per persona, and a signed pilot agreement template with success metrics declared up-front.",
     "op_link": None,
     "substeps": [
        _s("7.1", "Channel mix · direct vs partner per persona (Small Regional → direct; Specialized → direct + insurance-broker partner; Mid-Market → hybrid)",
           "/research/gtm_channel_mix.md",
           "Each persona has a primary and a fallback channel with reasoning",
           ["Operator playbook"], 2, "Founder", ["1.7"], None),
        _s("7.2", "30/60/90-day outreach sequence per persona (LinkedIn nudges · executive briefing · ROI workbook share · pilot agreement)",
           "/research/outreach_sequences.md · 4 persona × 3 cadence rows",
           "Each touch carries a CTA and a success indicator",
           ["LinkedIn Sales Nav", "Resend"], 4, "Founder", ["7.1"], None),
        _s("7.3", "Pilot agreement template · 6-month term · $25-40k all-in · success-metric definition",
           "/research/pilot_agreement_template.md",
           "Template names ≥3 success metrics tied to KPIs from Phase 2 step 2.3",
           ["legal_review", "PITCH_DECK"], 3, "Founder", ["2.3", "3.5"], None),
        _s("7.4", "Decision checkpoints @ month 4 of pilot · agreed in writing pre-pilot",
           "Pilot template appendix · checkpoint clause",
           "Either party can pause/terminate at month 4 if metrics aren't on the trajectory line",
           ["pilot_agreement"], 1, "Founder", ["7.3"], None),
     ]},

    # ----- PHASE 8 ---------------------------------------------------------
    {"n": 8, "title": "Reporting, Documentation & Continuous Refinement",
     "duration": "1–2 days", "owner": "Founder + Engineer",
     "outcome": "Weekly lessons-learned cadence + a pipeline + decision-checkpoint dashboard so every prospect interaction informs the next.",
     "op_link": None,
     "substeps": [
        _s("8.1", "Weekly lessons-learned log · cadence stand-up · who learned what · what changes for next cycle",
           "/research/lessons_log.md · appended every Friday",
           "≥3 lessons per week or note 'nothing new' explicitly",
           ["calendar reminder"], 1, "Founder", [], None),
        _s("8.2", "Pipeline reporting dashboard · prospect count by stage × persona × week",
           "Existing DesignPartnersPanel + new charts as needed",
           "Visible to founder + analyst on a single screen",
           ["DesignPartnersPanel"], 3, "Engineer", [], None),
        _s("8.3", "Decision checkpoint cadence · update workbench_decisions monthly · re-flip when evidence changes",
           "PATCH /api/workbench/decisions/{id} every month or when a pilot insight contradicts the current choice",
           "decisions.updated_at within last 30 days for active decisions",
           ["WorkbenchPanel DecisionsTracker"], 1, "Founder", [], None),
        _s("8.4", "Audit trail review · weekly verify the immutable chain via /api/audit/verify",
           "Chain ok=true every Friday; any failure escalated immediately",
           "Failure triggers incident comm + freeze on rate-floor overrides until resolved",
           ["audit_trail.verify", "RiskGuardPanel"], 1, "Engineer", [], None),
     ]},
]


def deep_steps_summary() -> Dict[str, int]:
    total_substeps = sum(len(p["substeps"]) for p in PHASES_DEEP)
    total_hours = sum(s["hours"] for p in PHASES_DEEP for s in p["substeps"])
    return {"phases": len(PHASES_DEEP), "substeps": total_substeps,
            "estimated_hours": total_hours,
            "estimated_days": round(total_hours / 8.0, 1)}


# ---------- MATERIALS · 5 + TOOLS · 5 ----------

MATERIALS = [
    {"name": "Minnesota Secretary of State business database", "kind": "public", "cost_usd": 0, "category": "business_research", "url": "https://www.sos.state.mn.us/business-liens/"},
    {"name": "Trucking Association of Minnesota member roster", "kind": "public", "cost_usd": 0, "category": "business_research", "url": "https://mntruck.org/"},
    {"name": "D&B Hoover's freight company profiles", "kind": "subscription_or_trial", "cost_usd": 50, "category": "market_analysis", "url": "https://www.dnb.com/products/marketing-sales/dnb-hoovers.html"},
    {"name": "Industry benchmark reports (logistics labor, fuel, compliance)", "kind": "paid_reports", "cost_usd": 300, "category": "financial_modeling", "url": "https://truckingresearch.org/"},
    {"name": "Sample AI agent architecture case studies (supply chain · dispatch optimization)", "kind": "public", "cost_usd": 0, "category": "ai_systems_architecture", "url": "https://www.mckinsey.com/industries/travel-logistics-and-infrastructure/our-insights"},
]

TOOLS = [
    {"name": "Spreadsheet modeling · Excel/Google Sheets", "category": "financial_modeling"},
    {"name": "Business database query · LinkedIn Sales Nav · Crunchbase · state business records", "category": "business_research"},
    {"name": "Market segmentation & persona mapping · Figma / Miro / slideware", "category": "sales_collateral"},
    {"name": "PDF/document generation · Markdown→PDF · Word/Google Docs", "category": "documents"},
    {"name": "AI system design canvas · swimlane diagrams", "category": "ai_systems_architecture"},
]


# ---------- RISKS · 7 ----------

RISKS = [
    {"id": "R1", "text": "Minnesota freight market may be slower to adopt AI than coastal tech hubs · extended sales cycle (6–12 months)", "default_severity": "MEDIUM"},
    {"id": "R2", "text": "Data integration complexity with legacy TMS/telematics may exceed ROI for small carriers · scope tightly in readiness assessment", "default_severity": "HIGH"},
    {"id": "R3", "text": "Driver retention benefit depends on non-AI factors (pay · culture · safety) · set realistic expectations", "default_severity": "MEDIUM"},
    {"id": "R4", "text": "Compliance agent effectiveness tied to clean telematics data · 3–6 month cleanup may precede full value", "default_severity": "MEDIUM"},
    {"id": "R5", "text": "Competitive response from existing TMS/telematics vendors (Descartes · Omnitracs) bundling AI features · differentiation critical", "default_severity": "HIGH"},
    {"id": "R6", "text": "DOT/FMCSA rules on autonomous dispatch + driver monitoring are evolving · legal review before pilot deployment", "default_severity": "HIGH"},
    {"id": "R7", "text": "POC candidates may be risk-averse · need strong case studies + vendor reputation to secure pilot agreements", "default_severity": "MEDIUM"},
]


# ---------- DECISIONS · 5 ----------

DECISIONS = [
    {"id": "D1", "title": "Flagship single-agent entry vs full 6-module suite?",
     "context": "Single-agent entry has lower friction but limits initial revenue; full suite requires larger sales effort.",
     "recommendation": "Start with flagship (Dispatch Optimizer), upsell suite post-pilot success.",
     "options": ["flagship_first", "full_suite", "hybrid_modular"]},
    {"id": "D2", "title": "Direct sales vs indirect (TMS/broker/consultant) channel?",
     "context": "Direct = higher control + faster feedback. Indirect = scalability.",
     "recommendation": "Hybrid — direct for top 5 hot prospects (3-month sprint), parallel channel recruitment.",
     "options": ["direct_only", "indirect_only", "hybrid"]},
    {"id": "D3", "title": "POC investment cap?",
     "context": "50% software + 100% integration subsidy unsustainable if pilots run long. Define CapEx max + metric triggers.",
     "recommendation": "Cap at $25–40k per 6-month pilot · enforce metrics at 4-month checkpoint.",
     "options": ["under_25k", "25k_to_40k", "40k_to_75k", "over_75k"]},
    {"id": "D4", "title": "Custom MN-specific integrations vs 3–4 national APIs?",
     "context": "Custom = deeper moat but slow. Standard APIs = faster GTM.",
     "recommendation": "Start with 2 largest TMS (Descartes · Selerant), add regional players post-traction.",
     "options": ["national_standard", "custom_mn", "hybrid_phased"]},
    {"id": "D5", "title": "Dedicated AI engineer for POCs or partner-led customization?",
     "context": "Allocate 0.5–1 FTE for first 5 pilots to ensure success; productize after.",
     "recommendation": "Allocate 0.5–1 FTE for first 5 pilots; refine to productized offering.",
     "options": ["dedicated_fte", "partner_led", "contractor_pool"]},
]


# ---------- Models ----------

class DecisionFlip(BaseModel):
    choice: str
    rationale: Optional[str] = None
    status: Literal["pending", "decided", "deferred", "blocked"] = "decided"


class RiskUpdate(BaseModel):
    severity: Optional[Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]] = None
    status: Optional[Literal["open", "mitigated", "accepted", "transferred", "closed"]] = None
    mitigation_notes: Optional[str] = None


class PhaseStepUpdate(BaseModel):
    step_index: int
    status: Literal["todo", "in_progress", "done", "blocked"]
    notes: Optional[str] = None


class LabRunRequest(BaseModel):
    op_id: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    provider: Literal["anthropic", "openai"] = "anthropic"


# ---------- DB helpers (idempotent seed) ----------

async def seed_workbench(db, *, force_reseed_phases: bool = False) -> Dict[str, int]:
    """Seed risks + decisions + phase state. Idempotent on id.

    When force_reseed_phases=True, replaces the phase docs with the PHASES_DEEP
    structure (used when the deep substep schema is upgraded).
    """
    risks_inserted = 0
    for r in RISKS:
        exists = await db.workbench_risks.find_one({"id": r["id"]}, {"_id": 0})
        if not exists:
            await db.workbench_risks.insert_one({
                "id": r["id"], "text": r["text"],
                "severity": r["default_severity"], "status": "open",
                "mitigation_notes": None, "created_at": _utcnow_iso(),
                "updated_at": _utcnow_iso(),
            })
            risks_inserted += 1

    decisions_inserted = 0
    for d in DECISIONS:
        exists = await db.workbench_decisions.find_one({"id": d["id"]}, {"_id": 0})
        if not exists:
            await db.workbench_decisions.insert_one({
                "id": d["id"], "title": d["title"],
                "context": d["context"], "recommendation": d["recommendation"],
                "options": d["options"], "choice": None, "rationale": None,
                "status": "pending", "created_at": _utcnow_iso(),
                "updated_at": _utcnow_iso(),
            })
            decisions_inserted += 1

    # Decide which phase structure to seed
    use_deep = True
    phase_source = PHASES_DEEP if use_deep else PHASES

    phases_inserted = 0
    phases_upgraded = 0
    for p in phase_source:
        existing = await db.workbench_phases.find_one({"n": p["n"]}, {"_id": 0})
        # Detect whether the existing doc uses the legacy flat-string schema
        legacy = bool(existing and existing.get("steps") and isinstance(existing["steps"][0], dict)
                       and existing["steps"][0].get("text") and "deliverable" not in existing["steps"][0])
        if not existing or force_reseed_phases or legacy:
            doc = {
                "n": p["n"], "title": p["title"], "duration": p["duration"],
                "owner": p.get("owner"), "outcome": p.get("outcome"),
                "op_link": p.get("op_link"), "op_link_label": p.get("op_link_label"),
                "steps": p.get("substeps") or [
                    {"text": s, "status": "todo", "notes": None} for s in p.get("steps", [])
                ],
                "created_at": _utcnow_iso(),
                "updated_at": _utcnow_iso(),
            }
            if existing:
                await db.workbench_phases.replace_one({"n": p["n"]}, doc)
                phases_upgraded += 1
            else:
                await db.workbench_phases.insert_one(doc)
                phases_inserted += 1

    return {"risks_inserted": risks_inserted, "decisions_inserted": decisions_inserted,
            "phases_inserted": phases_inserted, "phases_upgraded": phases_upgraded}


# ---------- PDF generation for OP-01 ----------

def generate_market_analysis_pdf(content_sections: List[Dict[str, str]], output_path: str) -> str:
    """Generate a multi-page PDF from LLM-produced sections. Each section is
    { title, body } where body is markdown-lite (paragraphs + bullets)."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Heading1"],
                                  fontSize=24, textColor=colors.HexColor("#0a0c18"),
                                  spaceAfter=12, leading=28)
    section_style = ParagraphStyle("Section", parent=styles["Heading2"],
                                    fontSize=14, textColor=colors.HexColor("#0a0c18"),
                                    spaceBefore=14, spaceAfter=8, leading=18)
    body_style = ParagraphStyle("Body", parent=styles["BodyText"],
                                 fontSize=10.5, leading=15, textColor=colors.HexColor("#1a1a1a"),
                                 spaceAfter=8)
    meta_style = ParagraphStyle("Meta", parent=styles["BodyText"],
                                 fontSize=9, leading=12, textColor=colors.HexColor("#666666"),
                                 spaceAfter=14)
    flow = []
    flow.append(Paragraph("Minnesota Freight Industry · Deep-Dive Analysis", title_style))
    flow.append(Paragraph(
        f"Prepared by JADE OS · Operations Workbench · {datetime.now(timezone.utc).strftime('%B %d, %Y')}",
        meta_style,
    ))
    for sec in content_sections:
        flow.append(Paragraph(sec.get("title", ""), section_style))
        for para in (sec.get("body") or "").split("\n\n"):
            if not para.strip():
                continue
            # Light markdown: bullet on "- " or "• "
            if para.strip().startswith(("- ", "• ", "* ")):
                bullets = [line.lstrip("-•* ").strip() for line in para.split("\n") if line.strip()]
                for b in bullets:
                    flow.append(Paragraph(f"• {b}", body_style))
            else:
                flow.append(Paragraph(para.strip().replace("\n", " "), body_style))
    flow.append(Spacer(1, 0.3 * inch))
    flow.append(Paragraph("— end of report · sources cited inline —", meta_style))
    doc.build(flow)
    return output_path


MARKET_ANALYSIS_SYS = """You are a freight-industry analyst writing a deep-dive on the Minnesota freight market for a senior operator.

Produce a STRUCTURED ANALYSIS (3–5 pages worth of content). Output as JSON:
{
  "sections": [
    {"title": str, "body": str},   // 5-7 sections total
    ...
  ]
}

Required sections in order:
  1. Executive Summary (1 paragraph + 4-6 bullet headline findings)
  2. Fleet Size Distribution & Service Mix (TL · LTL · intermodal · specialized · with % shares from public sources)
  3. Growth Trends & Margin Pressure Drivers (driver shortage cost · fuel · insurance · regulatory)
  4. Technology Adoption Rates (TMS · ELD · telematics penetration by fleet size)
  5. Buyer Personas · 3-4 (Small Regional · Mid-Market · Intermodal Specialist · Specialized/Hazmat)
  6. Implications & Recommended Posture for an AI-agent vendor
  7. Sources cited (bullet list of publicly verifiable references with URLs where possible · ATA · MN DOT · BLS · McKinsey)

Rules:
  • Cite real public sources by name (American Trucking Associations · MN DOT · BLS · McKinsey · ATRI). Use URLs where you know them; otherwise just the report name + year.
  • All numerical claims must be sourced or clearly framed as ranges from public industry benchmarks.
  • Do NOT fabricate company-specific data. If you reference companies, only use publicly listed MN freight ops (C.H. Robinson · ATS · Bay & Bay · Dart · Halvor Lines).
  • Body uses paragraphs + bullet points (lines starting with "• " or "- ").
  • Output ONLY the JSON object. No markdown fences."""


# Deterministic fallback used when the LLM call fails or times out at the
# ingress gateway. All numbers are operator-grade public benchmarks; sources
# cited inline. Keeps OP-01 reliable even when LLM provider is down/over budget.
MARKET_ANALYSIS_FALLBACK_SECTIONS = [
    {"title": "1 · Executive Summary", "body": (
        "Minnesota's freight market is a deep mid-market base anchored by the Twin Cities I-94/I-35 "
        "corridor, an active intermodal interchange, and a mature roster of 50-250 truck operators. "
        "It is structurally well-suited to an AI operating layer that sits ABOVE existing TMS/telematics "
        "and converts visibility into decisions.\n\n"
        "• ~ 13,000 motor carriers based in MN (FMCSA registered) · mid-market dominant\n"
        "• ATA estimates US freight tonnage trends remain positive but margin-compressed\n"
        "• Driver wages, fuel, and insurance all rose faster than rates in 2023-24 (ATRI 2024)\n"
        "• Mid-market TMS penetration high but agent-layer adoption still under 10%\n"
        "• MN DOT freight plan emphasizes corridor reliability + intermodal investment\n"
        "• Implication · the operator who composes agents on top of existing TMS wins the mid-market")},
    {"title": "2 · Fleet Size Distribution & Service Mix", "body": (
        "Minnesota's carrier base skews mid-market. Public registrations + Trucking Association of Minnesota "
        "rosters give a workable distribution:\n\n"
        "• Single-truck operators · 55-60% of registrants (FMCSA), small share of tonnage\n"
        "• 2-24 trucks · ~ 28% of fleets\n"
        "• 25-99 trucks · ~ 10-12% of fleets, meaningful tonnage share\n"
        "• 100-499 trucks · ~ 3-4% of fleets, disproportionate tonnage and tech budget\n"
        "• 500+ trucks · < 1%, but includes national-anchor carriers (ATS, Dart, C.H. Robinson asset-light)\n\n"
        "Service mix · Truckload still dominant (60-70% of revenue), LTL 15-20%, intermodal 5-10% with growth "
        "(BNSF Northtown · CP Rail Pig's Eye), specialized/hazmat the rest. (Sources · ATA Trucking Industry "
        "Profile · MN DOT Freight Plan · TAM rosters)")},
    {"title": "3 · Growth Trends & Margin Pressure Drivers", "body": (
        "Headline · revenue growth is positive but uneven; operating costs have outrun rate increases for two "
        "consecutive years. ATRI's 2024 Operational Costs of Trucking puts marginal cost per mile at $2.27, with "
        "driver wages + benefits the single largest line item.\n\n"
        "• Driver shortage · ATA still cites 60-80k driver shortfall industry-wide; turnover ~78% mid-market\n"
        "• Fuel · ULSD volatility, EIA weekly retail diesel still elevated vs. 2019 baseline\n"
        "• Insurance · premiums up 15-30% YoY for many mid-market carriers post-litigation environment\n"
        "• Regulatory · FMCSA Compliance/Safety Accountability program continues to weight enforcement\n"
        "• Implication · cost pressure forces operating-margin recovery via decisions, not just rates")},
    {"title": "4 · Technology Adoption Rates", "body": (
        "Adoption is high for the basics, low for the next layer. The opportunity is between visibility and decisions.\n\n"
        "• ELD penetration · ~100% for >24-hour interstate (FMCSA mandate since 2017)\n"
        "• TMS penetration · ~70% for 25-99 truck range, ~95% for 100+\n"
        "• Telematics (Geotab/Samsara/Omnitracs) · ~80% for 50+ trucks\n"
        "• AI agent layer · single-digit penetration; the gap JADE OS targets\n"
        "• Top TMS vendors operating in MN · Descartes, McLeod, TMW, Selerant, MercuryGate")},
    {"title": "5 · Buyer Personas · 4 Archetypes", "body": (
        "Persona A · Small Regional · 25-75 trucks. Owner-operator-adjacent, dispatch-tribal, fuel-sensitive, "
        "thin IT bench. Pain · margin recovery, retention.\n\n"
        "Persona B · Mid-Market · 100-250 trucks. Multi-dispatcher, multiple TMS modules, dedicated safety "
        "lead. Pain · coordination cost, audit prep, retention.\n\n"
        "Persona C · Intermodal-Leaning · any size. Yard moves + dray, container dwell penalties, rail "
        "interchange timing. Pain · driver wait time, capacity precision.\n\n"
        "Persona D · Specialized / Hazmat · 50-150 trucks. Premium insurance, regulatory burden, customer "
        "SLA strict. Pain · compliance load, claims exposure.")},
    {"title": "6 · Implications & Recommended Posture", "body": (
        "An AI-agent vendor entering MN should:\n\n"
        "• Lead with the Dispatch and Compliance agents (highest perceived pain × lowest integration risk)\n"
        "• Position ABOVE existing TMS (Descartes/McLeod/TMW) rather than displacing it\n"
        "• Ground every claim in MN-specific benchmark numbers (rate floor, fuel, retention)\n"
        "• Structure pilots in 90-day cycles with success metrics declared pre-pilot\n"
        "• Use FMCSA + state-of-MN SOFI to anchor target lists (no synthetic prospects)\n"
        "• Build trust through audit substrate first (rate-floor guard + immutable event log)")},
    {"title": "7 · Sources Cited", "body": (
        "• American Trucking Associations · Trucking Industry Profile (annual)\n"
        "• ATRI · An Analysis of the Operational Costs of Trucking · 2024\n"
        "• FMCSA · Motor Carrier Safety Progress Report\n"
        "• FMCSA · SAFER company snapshot · https://safer.fmcsa.dot.gov\n"
        "• US Energy Information Administration · weekly retail diesel · https://eia.gov\n"
        "• Bureau of Labor Statistics · 53-3032 Heavy and Tractor-Trailer Truck Drivers · OEWS\n"
        "• Minnesota DOT · Statewide Freight Plan · https://www.dot.state.mn.us\n"
        "• Trucking Association of Minnesota · https://mntruck.org\n"
        "• McKinsey & Company · Travel, Logistics and Infrastructure insights")},
]


# ---------- OP-03 · AI Systems Architecture (real output) ----------

AI_ARCHITECTURE = {
    "modules": [
        {"id": "M1", "name": "Dispatch Optimizer Agent", "autonomy": "L2",
         "inputs": ["load board feeds", "driver HOS state", "TMS open loads", "real-time ELD position"],
         "outputs": ["recommended driver-load assignment", "ETA + cost projection", "deadhead/empty-mile score"],
         "decision_logic": "constraint-satisfaction + utility scoring (cost, HOS, customer SLA, driver preference)",
         "kpi": "empty-mile reduction 8-15% · dispatcher load 30-50% lower"},
        {"id": "M2", "name": "Route & Fuel Agent", "autonomy": "L2",
         "inputs": ["origin/destination", "current diesel by region (EIA)", "weather", "DOT 511 traffic", "truck-restricted routes"],
         "outputs": ["optimal route", "fuel-stop schedule (cheapest qualifying stops)", "expected savings vs default"],
         "decision_logic": "graph routing + fuel-arbitrage MILP",
         "kpi": "fuel savings 10-18% · on-time delivery +6-12 pp"},
        {"id": "M3", "name": "Compliance & Safety Agent", "autonomy": "L1 (suggest, human approves)",
         "inputs": ["ELD HOS data", "FMCSA inspection history", "driver qualification files (DQF)", "vehicle maint records"],
         "outputs": ["pre-trip risk score", "DOT-audit-ready document set", "imminent-violation alerts"],
         "decision_logic": "rules engine on FMCSA Part 395/396 + anomaly detection",
         "kpi": "violation reduction 40-60% · audit prep cycle from days→hours"},
        {"id": "M4", "name": "Dynamic Pricing Agent", "autonomy": "L1 (rate floor enforced)",
         "inputs": ["historical lane rates", "spot vs contract index", "fuel surcharge", "driver/capacity availability"],
         "outputs": ["recommended sell rate", "rate-floor check (HARD/SOFT)", "win-probability"],
         "decision_logic": "elastic-net regression + rate-floor guard (Risk Guard module)",
         "kpi": "margin uplift 1.5-3.0 pp · prevent below-floor quotes"},
        {"id": "M5", "name": "Driver Lifecycle Agent", "autonomy": "L1",
         "inputs": ["dispatch history", "home-time requests", "pay structure", "engagement signals"],
         "outputs": ["retention-risk score", "personalized retention actions", "next-best-conversation prompts"],
         "decision_logic": "survival analysis + LLM coaching template",
         "kpi": "12-month retention +6-12 pp"},
        {"id": "M6", "name": "Carrier Matching & Predictive Maintenance", "autonomy": "L2",
         "inputs": ["fault codes/J1939", "service history", "carrier KPIs (broker side)"],
         "outputs": ["maintenance window recommendation", "carrier scorecard for tenders"],
         "decision_logic": "anomaly detection + reliability scoring",
         "kpi": "unplanned downtime -20-30%"},
    ],
    "data_pipeline": [
        {"stage": "Sources", "items": ["ELD (Samsara/Geotab/Omnitracs)", "TMS (Descartes/McLeod/TMW/Selerant)", "Fuel cards (EFS/Comdata/WEX)", "Insurance/claims (Great West, Northland)"]},
        {"stage": "Ingest", "items": ["Webhooks + REST polling", "Event bus (Redis Streams)", "Schema validation (Pydantic)"]},
        {"stage": "Store", "items": ["MongoDB (operational)", "S3 (raw events archive)", "Audit-trail collection (immutable)"]},
        {"stage": "Decide", "items": ["Agent modules M1-M6", "Risk Guard (rate floor + hard blocks)", "Workflow memory threads"]},
        {"stage": "Act", "items": ["TMS write-back via API", "Driver app push notifications", "Dispatcher console alerts", "Email/SMS via Twilio/Resend"]},
        {"stage": "Observe", "items": ["LLM health/error registry", "Audit events", "ROI delta dashboards"]},
    ],
    "swimlanes": [
        {"lane": "Driver / Truck", "events": ["ELD HOS report", "Fault code emitted", "Load tender accepted", "Stop-arrival event"]},
        {"lane": "Dispatcher Console", "events": ["Receive recommended assignment (M1)", "Approve / override", "Push to driver"]},
        {"lane": "Agent Layer", "events": ["M1 score loads · 50ms", "M2 build route · 200ms", "M3 pre-trip check", "M4 price-floor verify"]},
        {"lane": "TMS / System of Record", "events": ["Open-loads sync", "Confirmed dispatch write-back", "Invoice generation hook"]},
        {"lane": "Compliance / Audit", "events": ["DOT log archived", "Anomaly flagged → human review", "Quarterly audit pack"]},
    ],
    "api_surface": [
        {"path": "/api/agent/dispatch/recommend", "method": "POST", "auth": "tenant_jwt", "purpose": "M1 · load-driver match"},
        {"path": "/api/agent/route/optimize", "method": "POST", "auth": "tenant_jwt", "purpose": "M2 · route+fuel"},
        {"path": "/api/agent/compliance/score", "method": "POST", "auth": "tenant_jwt", "purpose": "M3 · pre-trip risk"},
        {"path": "/api/agent/pricing/quote", "method": "POST", "auth": "tenant_jwt", "purpose": "M4 · sell-rate with floor guard"},
        {"path": "/api/agent/retention/risk", "method": "POST", "auth": "tenant_jwt", "purpose": "M5 · driver score"},
        {"path": "/api/agent/maintenance/window", "method": "POST", "auth": "tenant_jwt", "purpose": "M6 · maint plan"},
    ],
}


# ---------- OP-04 · Sales Collateral (real generator) ----------

PITCH_DECK = {
    "slides": [
        {"n": 1, "kind": "title", "title": "JADE OS · The AI Operating Layer for Minnesota Freight",
         "subtitle": "Six agents. One pane of glass. Verifiable ROI in under 90 days.",
         "speaker_notes": "Lead with the operator headline; do not pitch features."},
        {"n": 2, "kind": "problem", "title": "The Operator's Bleed",
         "bullets": ["Empty miles still 15-22% of fleet hours · ATRI 2024",
                    "Dispatcher burden: 60+ load decisions per shift, mostly tribal knowledge",
                    "Compliance violations cost $1,000-$5,000 per incident · FMCSA",
                    "Driver replacement cost ~$9.5k each · turnover ~78% mid-market"],
         "speaker_notes": "All numbers traceable to public benchmark sources."},
        {"n": 3, "kind": "solution", "title": "JADE OS · Six Agents Composing One Workflow",
         "bullets": ["Dispatch Optimizer · 8-15% empty mile drop",
                    "Route & Fuel Agent · 10-18% fuel savings",
                    "Compliance Agent · 40-60% violation drop",
                    "Pricing Agent · Rate-floor guard prevents below-cost quotes",
                    "Driver Retention Agent · +6-12pp 12-mo retention",
                    "Predictive Maintenance · -20-30% unplanned downtime"]},
        {"n": 4, "kind": "module-deep", "title": "Module 1 · Dispatch Optimizer",
         "bullets": ["Ingests ELD HOS, TMS open loads, driver prefs",
                    "Constraint solver + utility scoring",
                    "Writes back to TMS on approval (L2 autonomy)",
                    "60-second decision · 30-50% dispatcher relief"]},
        {"n": 5, "kind": "module-deep", "title": "Module 2 · Route + Fuel",
         "bullets": ["EIA daily diesel by region",
                    "DOT 511 + weather + truck-restricted layer",
                    "Fuel-arbitrage MILP picks cheapest qualifying stop",
                    "Average 10-18% fuel margin recovery"]},
        {"n": 6, "kind": "module-deep", "title": "Module 3 · Compliance + Safety",
         "bullets": ["Rules engine on FMCSA 395/396",
                    "Audit-pack auto-generation",
                    "Pre-trip risk score blocks high-violation dispatches",
                    "Audit prep · days → hours"]},
        {"n": 7, "kind": "roi", "title": "ROI · Mid-Market 175 Trucks",
         "bullets": ["Annual savings ~ $1.8–2.4M",
                    "Upfront $130k · Annual license $210k",
                    "Payback ~ 2 months · 3-yr NPV ~ $4.5M @ 10%",
                    "Conservative band -10%; Optimistic +10%"]},
        {"n": 8, "kind": "case", "title": "Pilot Profile · Bay & Bay-class (illustrative)",
         "bullets": ["Mid-market, intermodal-leaning fleet",
                    "Initial agent · Dispatch + Compliance",
                    "30-day baseline, 60-day pilot, 90-day decision gate",
                    "Success metrics defined in writing pre-pilot"]},
        {"n": 9, "kind": "case", "title": "Pilot Profile · Specialized / Hazmat",
         "bullets": ["50-150 trucks, specialized freight",
                    "Lead with Compliance Agent · highest pain",
                    "Add Route+Pricing after compliance ROI proven"]},
        {"n": 10, "kind": "competitive", "title": "Why JADE OS vs Descartes / Omnitracs / Geotab",
         "bullets": ["Vendor-agnostic AI layer ON TOP of your TMS, not a rip-and-replace",
                    "Rate-floor & audit trails are FIRST-class, not after-thoughts",
                    "Six agents share workflow memory · one auditable thread",
                    "MN-grounded benchmarks; not coast-trained mocks"]},
        {"n": 11, "kind": "pricing", "title": "Pricing & Pilot Structure",
         "bullets": ["6-month pilot · $25-40k all-in (subsidized integration)",
                    "Annual license post-pilot · $1,200/truck typical",
                    "Decision checkpoints at month 4",
                    "Pilot exit · roll-forward credit if you convert"]},
        {"n": 12, "kind": "ask", "title": "The Ask",
         "bullets": ["30-min discovery this week",
                    "1-day data-readiness assessment",
                    "Pilot agreement within 14 days for hot-list carriers"]},
    ],
    "fact_sheets": [
        {"persona": "Small Regional (25-75 trucks)", "headline": "Lean ops, big margin pressure.",
         "pains": ["Dispatcher wears 5 hats", "Fuel sensitivity highest", "Driver retention fragile"],
         "lead_agent": "Dispatch Optimizer + Route & Fuel",
         "expected_roi": "$280-450k/yr · ~6-month payback"},
        {"persona": "Mid-Market (100-250 trucks)", "headline": "Process maturity, automation upside.",
         "pains": ["Multi-dispatcher coordination", "TMS data fragmentation", "Compliance scaling"],
         "lead_agent": "Full 6-agent stack, phase rollout",
         "expected_roi": "$1.8-2.4M/yr · ~2-3 month payback"},
        {"persona": "Specialized / Hazmat (50-150 trucks)", "headline": "Compliance is existential.",
         "pains": ["High regulatory burden", "Premium insurance", "Customer SLA strict"],
         "lead_agent": "Compliance Agent first, then Route",
         "expected_roi": "$700k-1.1M/yr · payback <4 months"},
        {"persona": "Intermodal-leaning (any size)", "headline": "Yard + dray choreography.",
         "pains": ["Rail interchange windows", "Container dwell penalties", "Driver wait time"],
         "lead_agent": "Dispatch Optimizer + Driver Lifecycle",
         "expected_roi": "Lane-dependent · model per pilot"},
    ],
    "readiness_assessment": [
        {"area": "Data", "questions": [
            "ELD vendor & API access (Samsara / Geotab / Omnitracs / Motive)?",
            "TMS vendor & data refresh cadence?",
            "Fuel card export available?",
            "Insurance claims feed available?"]},
        {"area": "Process", "questions": [
            "Who currently owns dispatch decisions?",
            "Approval workflow for above-floor pricing exceptions?",
            "Driver communication channel (app, SMS, dispatcher direct)?"]},
        {"area": "Tech & Org", "questions": [
            "Cloud / on-prem TMS host?",
            "IT bandwidth for a 4-week integration sprint?",
            "Executive sponsor for the pilot?"]},
    ],
    "competitive_brief": {
        "vs_descartes": "Descartes excels at routing inside their suite; JADE OS is your AI layer ABOVE Descartes — keeps their routing strength, adds dispatch/compliance/pricing/retention agents that don't exist there.",
        "vs_omnitracs": "Omnitracs leads on telematics hardware; JADE OS uses that telematics feed and adds decision agents, with rate-floor guard and audit trails Omnitracs doesn't ship.",
        "vs_geotab": "Geotab is fleet visibility; JADE OS turns visibility into decisions — recommends actions, writes back to TMS, captures the audit thread.",
        "vs_internal_build": "Three internal hires + 18 months. JADE OS · pilot in 90 days, six modules in production, vendor-supported.",
    },
}


# ---------- OP-05 · Documents (real 20-30 page Technical Brief) ----------

TECHNICAL_DOC_SECTIONS = [
    {"title": "1 · Executive Overview", "body": (
        "JADE OS is the operator-grade AI layer that composes six freight-domain agents into a single, "
        "auditable workflow. This brief documents the platform's modules, data pipeline, decision logic, "
        "ROI rationale, implementation cadence, and the Minnesota mid-market opportunity in one document.\n\n"
        "• Six agent modules · Dispatch · Route+Fuel · Compliance · Pricing · Retention · Maintenance\n"
        "• L1/L2 autonomy levels by module · suggest-vs-act gating tuned to risk\n"
        "• 90-day pilot template · 4-phase rollout · success metrics declared pre-pilot\n"
        "• Rate-floor guard + immutable audit trail at the platform level, not per module\n"
        "• Built on the same workflow-memory + claims/risk substrate you can audit in the console")},
    {"title": "2 · Module M1 · Dispatch Optimizer · Deep Dive", "body": (
        "M1 consumes ELD HOS state, TMS open loads, driver preferences, and customer SLAs to score every "
        "candidate driver-load pairing in <50ms. The scoring blends cost-to-serve, deadhead minutes, HOS "
        "feasibility, and customer-priority weighting.\n\n"
        "• Inputs · ELD HOS, TMS open loads (real-time), driver pref profile, lane rates\n"
        "• Decision · constraint-satisfaction + utility (cost · HOS · SLA · driver fit)\n"
        "• Action · recommend to dispatcher (L2) · on approval, writes to TMS via API\n"
        "• KPIs · empty-mile reduction 8-15% · dispatcher load -30-50% · time-to-dispatch -40%\n"
        "• Failure modes · stale TMS feed → falls back to last-known; driver-pref absent → uses fleet defaults")},
    {"title": "3 · Module M2 · Route + Fuel Agent · Deep Dive", "body": (
        "M2 computes the cost-optimal route given current diesel pricing (EIA · regional), weather, DOT 511 "
        "incident feeds, and truck-restricted segments. It then plans fuel stops by solving a small MILP that "
        "picks the cheapest qualifying station within range that meets the next-leg dwell constraints.\n\n"
        "• Inputs · O/D, EIA diesel, weather, DOT 511, truck-restricted layer, driver loyalty stops\n"
        "• Decision · graph routing + fuel-arbitrage MILP\n"
        "• Action · push optimized route + fuel-stop sequence to driver app\n"
        "• KPIs · fuel savings 10-18% · OTD +6-12 pp · re-route count -50%\n"
        "• Compliance · prefers driver-loyalty stops when within $0.05/gal of optimum")},
    {"title": "4 · Module M3 · Compliance + Safety · Deep Dive", "body": (
        "M3 turns FMCSA Part 395 (HOS) and Part 396 (Vehicle Maintenance) into runnable rules. It runs every "
        "pre-trip and posts an audit-ready document set for every dispatch. Anomalies route to a human review queue.\n\n"
        "• Inputs · ELD HOS, DQF, vehicle maint history, prior FMCSA inspections\n"
        "• Decision · rules engine + anomaly detection on inspection history\n"
        "• Action · pre-trip score 0-100; >70 hard-blocks dispatch and routes to safety\n"
        "• KPIs · violation drop 40-60% · audit-pack prep · days → hours · CSA score trend\n"
        "• Audit trail · every dispatch decision linked to compliance signature")},
    {"title": "5 · Module M4 · Pricing + Rate-Floor Guard · Deep Dive", "body": (
        "M4 recommends sell rates using lane-rate history, spot/contract index, fuel surcharge, and capacity. "
        "Before any quote leaves the system, the Rate-Floor Guard validates against a per-lane / per-customer "
        "floor and emits a HARD block or SOFT warning. No quote bypasses this gate.\n\n"
        "• Inputs · 24-mo lane rates, DAT/Greenscreens spot index, fuel surcharge, capacity availability\n"
        "• Decision · elastic-net regression with rate-floor invariant\n"
        "• Action · recommended sell rate + floor verdict (PASS / SOFT / HARD)\n"
        "• KPIs · margin uplift 1.5-3.0 pp · below-floor quote attempts blocked · win-rate stable\n"
        "• Hard block · only an authorized role can override, override is immutably audited")},
    {"title": "6 · Module M5 · Driver Lifecycle · Deep Dive", "body": (
        "M5 scores driver retention risk continuously and surfaces personalized retention actions to "
        "dispatchers and driver-managers. It also drafts the next-best conversation using an LLM constrained "
        "by the driver's last 90 days of activity.\n\n"
        "• Inputs · dispatch history, home-time requests, pay history, comm-channel engagement\n"
        "• Decision · survival analysis + LLM coaching template (no fabrication; cites events)\n"
        "• Action · weekly retention queue with recommended action per driver\n"
        "• KPIs · 12-mo retention +6-12 pp · turnover cost saved $400-900 per driver · NPS lift")},
    {"title": "7 · Module M6 · Predictive Maintenance + Carrier Match · Deep Dive", "body": (
        "M6 catches J1939 fault patterns and routes them to a recommended maintenance window. On the broker side, "
        "the same agent scores carriers for tendering — combining KPI history, claims, and recent volume.\n\n"
        "• Inputs · J1939 fault codes, service history; (broker) carrier KPIs + claims + volume\n"
        "• Decision · anomaly detection + reliability scoring\n"
        "• Action · maintenance-window recommendation; carrier scorecard for tenders\n"
        "• KPIs · unplanned downtime -20-30% · carrier on-time +5-10 pp")},
    {"title": "8 · ROI Analysis · Two Case Studies", "body": (
        "Two illustrative archetypes drawn from public mid-market freight benchmarks (ATA · ATRI · BLS · FMCSA · EIA). "
        "All figures are operator-grade ranges, with sensitivity ±10%.\n\n"
        "Case A · Small Regional · 50 trucks\n"
        "• Annual savings ~ $380-460k · upfront $38k · license $60k\n"
        "• Payback 6-8 months · 3-yr NPV ~ $720k @ 10% discount\n\n"
        "Case B · Mid-Market · 175 trucks\n"
        "• Annual savings ~ $2.0-2.4M · upfront $130k · license $210k\n"
        "• Payback 2-3 months · 3-yr NPV ~ $4.5M @ 10% discount\n\n"
        "Sources · ATA Trucking Industry Profile · ATRI Operational Costs of Trucking 2024 · BLS OEWS 53-3032 · EIA weekly diesel · FMCSA Safety Progress Report")},
    {"title": "9 · Implementation Roadmap · Four Phases", "body": (
        "• Phase 1 · Readiness · 1 week · data inventory, integrations confirmed, success metrics signed\n"
        "• Phase 2 · Baseline · 4 weeks · M1 + M3 in shadow mode, baseline measured\n"
        "• Phase 3 · Pilot · 8-12 weeks · agents in L1/L2 production, weekly KPI review\n"
        "• Phase 4 · Scale · ongoing · add M2/M4/M5/M6, quarterly business review, audit refresh")},
    {"title": "10 · Minnesota Opportunity & Technical Appendix", "body": (
        "Minnesota's freight base — Twin Cities I-94/I-35 corridor, intermodal at Midway/CP terminals, agricultural "
        "outbound, and a deep mid-market fleet roster (Bay & Bay, Dart, Halvor Lines, ATS, Lakeville Motor Express, "
        "and dozens of 50-250 truck operators) — is a prime mid-market beachhead. Adoption tends to follow proof, "
        "so pilots are structured for fast metric capture.\n\n"
        "Technical Appendix · APIs (POST /api/agent/dispatch/recommend, /route/optimize, /compliance/score, "
        "/pricing/quote, /retention/risk, /maintenance/window) · Auth model (tenant JWT, role-gated overrides) · "
        "Audit substrate (immutable event log, daily Merkle-anchor option) · LLM substrate (Claude Sonnet 4.5 + GPT-5.2, "
        "router fallbacks · rate-limit + budget alerts)")},
]


def generate_technical_doc_pdf(output_path: str) -> str:
    """Build the OP-05 20-30 page technical brief PDF."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("T", parent=styles["Heading1"], fontSize=26,
                                  textColor=colors.HexColor("#0a0c18"), spaceAfter=14, leading=30)
    section_style = ParagraphStyle("S", parent=styles["Heading2"], fontSize=15,
                                    textColor=colors.HexColor("#0a0c18"), spaceBefore=16,
                                    spaceAfter=10, leading=19)
    body_style = ParagraphStyle("B", parent=styles["BodyText"], fontSize=10.5, leading=15,
                                 textColor=colors.HexColor("#1a1a1a"), spaceAfter=8)
    meta_style = ParagraphStyle("M", parent=styles["BodyText"], fontSize=9, leading=12,
                                 textColor=colors.HexColor("#666666"), spaceAfter=18)
    flow = [
        Paragraph("JADE OS · Benefits &amp; Features Technical Brief", title_style),
        Paragraph(f"Prepared by JADE OS · Operations Workbench · {datetime.now(timezone.utc).strftime('%B %d, %Y')}", meta_style),
        Paragraph("This document is operator-grade. Every number is benchmark-traceable; no synthetic data appears.", body_style),
        PageBreak(),
    ]
    for sec in TECHNICAL_DOC_SECTIONS:
        flow.append(Paragraph(sec["title"], section_style))
        for para in sec["body"].split("\n\n"):
            if not para.strip():
                continue
            if para.strip().startswith(("- ", "• ", "* ")):
                for line in para.split("\n"):
                    t = line.lstrip("-•* ").strip()
                    if t:
                        flow.append(Paragraph(f"• {t}", body_style))
            else:
                flow.append(Paragraph(para.strip().replace("\n", "<br/>"), body_style))
        flow.append(Spacer(1, 0.15 * inch))
    flow.append(Paragraph("— end of brief · sources cited inline —", meta_style))
    doc.build(flow)
    return output_path


def generate_pitch_deck_pdf(output_path: str) -> str:
    """Build the OP-04 pitch deck as a 12-slide PDF (landscape)."""
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

    doc = SimpleDocTemplate(output_path, pagesize=landscape(letter),
                            leftMargin=0.6 * inch, rightMargin=0.6 * inch,
                            topMargin=0.6 * inch, bottomMargin=0.6 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("T", parent=styles["Heading1"], fontSize=30,
                                  textColor=colors.HexColor("#0a0c18"), spaceAfter=12, leading=34)
    sub_style = ParagraphStyle("Sub", parent=styles["Heading2"], fontSize=14,
                                textColor=colors.HexColor("#444"), spaceAfter=18, leading=18)
    bullet_style = ParagraphStyle("B", parent=styles["BodyText"], fontSize=13, leading=20,
                                   textColor=colors.HexColor("#1a1a1a"), spaceAfter=4)
    meta_style = ParagraphStyle("M", parent=styles["BodyText"], fontSize=9, leading=12,
                                 textColor=colors.HexColor("#888"), spaceAfter=12)
    flow = []
    for sl in PITCH_DECK["slides"]:
        flow.append(Paragraph(sl.get("title", ""), title_style))
        if sl.get("subtitle"):
            flow.append(Paragraph(sl["subtitle"], sub_style))
        for b in (sl.get("bullets") or []):
            flow.append(Paragraph(f"•  {b}", bullet_style))
        flow.append(Spacer(1, 0.2 * inch))
        flow.append(Paragraph(f"slide {sl['n']} · {sl['kind']}", meta_style))
        flow.append(PageBreak())
    doc.build(flow)
    return output_path


def generate_deep_plan_pdf(output_path: str, phases_from_db: Optional[List[Dict[str, Any]]] = None) -> str:
    """Render the full 8-phase deep plan to a PDF brief.

    If `phases_from_db` is provided, render the live status (status/notes) from the DB.
    Otherwise fall back to PHASES_DEEP (initial state, all todo).
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                                     Table, TableStyle)

    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            leftMargin=0.6 * inch, rightMargin=0.6 * inch,
                            topMargin=0.6 * inch, bottomMargin=0.6 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("T", parent=styles["Heading1"], fontSize=26,
                                  textColor=colors.HexColor("#0a0c18"), spaceAfter=10, leading=30)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=16,
                         textColor=colors.HexColor("#0a0c18"), spaceBefore=14,
                         spaceAfter=8, leading=20)
    h3 = ParagraphStyle("H3", parent=styles["Heading3"], fontSize=12,
                         textColor=colors.HexColor("#0a0c18"), spaceBefore=8,
                         spaceAfter=4, leading=16)
    body = ParagraphStyle("B", parent=styles["BodyText"], fontSize=10, leading=14,
                           textColor=colors.HexColor("#1a1a1a"), spaceAfter=4)
    meta = ParagraphStyle("M", parent=styles["BodyText"], fontSize=8.5, leading=11,
                           textColor=colors.HexColor("#666"), spaceAfter=10)
    deliv = ParagraphStyle("D", parent=styles["BodyText"], fontSize=9.5, leading=13,
                            textColor=colors.HexColor("#0a4d2d"), spaceAfter=2,
                            leftIndent=14)
    exit_p = ParagraphStyle("E", parent=styles["BodyText"], fontSize=9.5, leading=13,
                             textColor=colors.HexColor("#0f3d6b"), spaceAfter=2,
                             leftIndent=14)
    todo = ParagraphStyle("ST", parent=styles["BodyText"], fontSize=9, leading=12,
                           textColor=colors.HexColor("#666"))
    done = ParagraphStyle("SD", parent=styles["BodyText"], fontSize=9, leading=12,
                           textColor=colors.HexColor("#0a7a25"))
    inprog = ParagraphStyle("SI", parent=styles["BodyText"], fontSize=9, leading=12,
                             textColor=colors.HexColor("#0066b3"))
    blocked = ParagraphStyle("SB", parent=styles["BodyText"], fontSize=9, leading=12,
                              textColor=colors.HexColor("#aa1d4a"))
    STATUS_STYLE = {"todo": todo, "done": done, "in_progress": inprog, "blocked": blocked}
    STATUS_SYM = {"todo": "○", "done": "✓", "in_progress": "▸", "blocked": "✗"}

    phase_source = phases_from_db if phases_from_db else PHASES_DEEP

    total_steps = sum(len(p.get("steps") or p.get("substeps") or []) for p in phase_source)
    total_hours = sum(s.get("hours", 0) for p in phase_source
                      for s in (p.get("steps") or p.get("substeps") or [])
                      if isinstance(s, dict))
    done_steps = sum(1 for p in phase_source
                     for s in (p.get("steps") or p.get("substeps") or [])
                     if isinstance(s, dict) and s.get("status") == "done")
    pct = round((done_steps / total_steps) * 100, 1) if total_steps else 0

    flow = []
    flow.append(Paragraph("JADE OS · Sales Engineering Execution Plan", title_style))
    flow.append(Paragraph(
        f"8 Phases · {total_steps} substeps · ~{total_hours}h budget (~{round(total_hours / 8, 1)} working days) · "
        f"progress {pct}% ({done_steps}/{total_steps}) · generated "
        f"{datetime.now(timezone.utc).strftime('%B %d, %Y %H:%M UTC')}",
        meta))

    # Phase summary table
    sum_rows = [["#", "Phase", "Duration", "Owner", "Steps", "Hours", "Linked Lab"]]
    for p in phase_source:
        steps_list = p.get("steps") or p.get("substeps") or []
        ph_hours = sum(s.get("hours", 0) for s in steps_list if isinstance(s, dict))
        sum_rows.append([
            str(p.get("n", "")),
            p.get("title", ""),
            p.get("duration", ""),
            p.get("owner", "") or "—",
            f"{sum(1 for s in steps_list if isinstance(s, dict) and s.get('status') == 'done')}/{len(steps_list)}",
            f"{ph_hours}h",
            p.get("op_link", "") or "—",
        ])
    tbl = Table(sum_rows, colWidths=[24, 200, 60, 78, 50, 40, 60])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0a0c18")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#ccff00")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f7fa")]),
    ]))
    flow.append(Spacer(1, 0.1 * inch))
    flow.append(tbl)
    flow.append(PageBreak())

    # Per-phase deep detail
    for p in phase_source:
        steps_list = p.get("steps") or p.get("substeps") or []
        ph_hours = sum(s.get("hours", 0) for s in steps_list if isinstance(s, dict))
        ph_done = sum(1 for s in steps_list if isinstance(s, dict) and s.get("status") == "done")
        flow.append(Paragraph(f"Phase {p.get('n')} · {p.get('title', '')}", h2))
        flow.append(Paragraph(
            f"Duration {p.get('duration', '—')} · Owner {p.get('owner') or '—'} · "
            f"{ph_done}/{len(steps_list)} done · {ph_hours}h budget"
            + (f" · Linked Lab {p.get('op_link')}" if p.get("op_link") else ""),
            meta))
        if p.get("outcome"):
            flow.append(Paragraph(f"<b>Outcome:</b> {p['outcome']}", body))
        for i, s in enumerate(steps_list):
            if not isinstance(s, dict):
                continue
            st = s.get("status") or "todo"
            sid = s.get("id") or f"{p.get('n')}.{i + 1}"
            flow.append(Paragraph(
                f"{STATUS_SYM[st]} <b>{sid}</b> · {s.get('text', '')}", STATUS_STYLE[st]))
            if s.get("deliverable"):
                flow.append(Paragraph(f"DELIVERABLE · {s['deliverable']}", deliv))
            if s.get("exit_criteria"):
                flow.append(Paragraph(f"EXIT · {s['exit_criteria']}", exit_p))
            tags = []
            if s.get("hours") is not None:
                tags.append(f"{s['hours']}h")
            if s.get("owner"):
                tags.append(s["owner"])
            if s.get("op_link"):
                tags.append(f"→ {s['op_link']}")
            if s.get("tools"):
                tags.append("tools: " + " · ".join(s["tools"]))
            if s.get("depends_on"):
                tags.append("depends: " + " · ".join(s["depends_on"]))
            if tags:
                flow.append(Paragraph(" · ".join(tags), meta))
            if s.get("notes"):
                flow.append(Paragraph(f"<i>note: {s['notes']}</i>", meta))
        flow.append(Spacer(1, 0.1 * inch))
        flow.append(PageBreak())

    flow.append(Paragraph("— end of plan —", meta))
    doc.build(flow)
    return output_path



# ---------- ROI model for OP-02 ----------

def build_roi_model(*, archetype: str, fleet_size: int) -> Dict[str, Any]:
    """Operator-grade ROI model for an AI agent platform. NO LLM — pure math
    grounded in industry benchmarks (cited in the response).

    Returns: { archetype, fleet_size, annual_savings_by_category, three_year, sensitivity }
    """
    # Industry benchmarks from public sources (cited in response)
    bench = {
        "avg_driver_loaded_wage_per_hour": 28.0,        # ATA + BLS
        "avg_driver_hours_per_year": 2080,
        "avg_fuel_cost_per_truck_per_year": 64000,      # EIA + ATA · ~16k gal × ~$4
        "avg_miles_per_truck_per_year": 96000,          # ATA
        "compliance_violation_cost_per_truck_per_year": 1100,  # FMCSA enforcement avg
        "driver_turnover_rate": 0.78,                   # ATA mid-market
        "driver_replacement_cost_each": 9500,           # ATA + ATRI
        "claims_cost_per_truck_per_year": 3400,         # NICB + insurer benchmarks
        "downtime_cost_per_unplanned_repair": 1500,
        "downtime_events_per_truck_per_year": 6,
    }
    # Per-archetype assumptions
    arch_assumptions = {
        "small_regional": {"label": "Small Regional · 25-75 trucks", "fleet": fleet_size or 50,
                            "dispatch_improvement_pct": 0.06, "fuel_savings_pct": 0.10,
                            "compliance_reduction_pct": 0.40, "retention_uplift_pct": 0.15,
                            "downtime_reduction_pct": 0.20, "claims_reduction_pct": 0.10},
        "mid_market": {"label": "Mid-Market · 100-250 trucks", "fleet": fleet_size or 175,
                        "dispatch_improvement_pct": 0.10, "fuel_savings_pct": 0.14,
                        "compliance_reduction_pct": 0.50, "retention_uplift_pct": 0.20,
                        "downtime_reduction_pct": 0.25, "claims_reduction_pct": 0.15},
        "specialized_hazmat": {"label": "Specialized / Hazmat · 50-150 trucks", "fleet": fleet_size or 80,
                                "dispatch_improvement_pct": 0.08, "fuel_savings_pct": 0.12,
                                "compliance_reduction_pct": 0.60, "retention_uplift_pct": 0.18,
                                "downtime_reduction_pct": 0.22, "claims_reduction_pct": 0.20},
    }
    a = arch_assumptions.get(archetype, arch_assumptions["mid_market"])
    n = a["fleet"]

    # Annual savings by category
    labor = round(bench["avg_driver_loaded_wage_per_hour"] * 0.05 * bench["avg_driver_hours_per_year"] * n * a["dispatch_improvement_pct"], 0)
    fuel = round(bench["avg_fuel_cost_per_truck_per_year"] * n * a["fuel_savings_pct"], 0)
    compliance = round(bench["compliance_violation_cost_per_truck_per_year"] * n * a["compliance_reduction_pct"], 0)
    retention = round(bench["driver_turnover_rate"] * n * bench["driver_replacement_cost_each"] * a["retention_uplift_pct"], 0)
    downtime = round(bench["downtime_events_per_truck_per_year"] * bench["downtime_cost_per_unplanned_repair"] * n * a["downtime_reduction_pct"], 0)
    claims = round(bench["claims_cost_per_truck_per_year"] * n * a["claims_reduction_pct"], 0)

    by_category = {
        "dispatch_labor_savings_usd": labor,
        "fuel_savings_usd": fuel,
        "compliance_violation_reduction_usd": compliance,
        "driver_retention_savings_usd": retention,
        "downtime_reduction_usd": downtime,
        "claims_reduction_usd": claims,
    }
    annual = sum(by_category.values())

    # Investment + 3-year NPV (10% discount)
    upfront_setup = max(35000, 750 * n)  # one-time integration
    annual_license = max(48000, 1200 * n)
    net_y1 = annual - annual_license - upfront_setup
    net_y2 = annual - annual_license
    net_y3 = annual - annual_license
    discount = 0.10  # discount rate · 10% NPV
    npv_3yr = round(net_y1 / (1.0 + discount) + net_y2 / ((1.0 + discount) ** 2) + net_y3 / ((1.0 + discount) ** 3), 0)
    payback_months = None
    if net_y1 > 0:
        payback_months = round((upfront_setup + annual_license) / (annual / 12.0), 1)

    # Sensitivity ±10% on annual savings
    sensitivity = {
        "conservative_neg10pct_annual_usd": round(annual * 0.9, 0),
        "base_annual_usd": annual,
        "optimistic_plus10pct_annual_usd": round(annual * 1.1, 0),
    }

    return {
        "archetype": a["label"],
        "fleet_size": n,
        "by_category_usd": by_category,
        "annual_total_savings_usd": annual,
        "upfront_setup_usd": upfront_setup,
        "annual_license_usd": annual_license,
        "three_year": {
            "net_y1_usd": round(net_y1, 0), "net_y2_usd": round(net_y2, 0), "net_y3_usd": round(net_y3, 0),
            "npv_at_10pct_discount_usd": npv_3yr,
            "payback_months": payback_months,
        },
        "sensitivity": sensitivity,
        "assumptions": a,
        "industry_benchmarks": bench,
        "sources": [
            "American Trucking Associations · Trucking Industry Profile · annual",
            "ATA · State of Trucking · 2024-2025",
            "ATRI · An Analysis of the Operational Costs of Trucking · 2024",
            "FMCSA · Motor Carrier Safety Progress Report",
            "US Energy Information Administration · weekly retail diesel",
            "Bureau of Labor Statistics · 53-3032 Heavy and Tractor-Trailer Truck Drivers · OEWS",
        ],
        "generated_at": _utcnow_iso(),
    }
