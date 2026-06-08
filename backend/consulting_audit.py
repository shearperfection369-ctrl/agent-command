"""JadeOS · AI Readiness Audit (consulting engine).

A structured questionnaire + LLM analysis pipeline that lets the operator
walk a prospect through an industry-tailored discovery session, then
produces a 12-page PowerPoint-style PDF report with:

  • Overall AI Readiness Score (0-100) → tier (PIONEER / BUILDER / CURIOUS / LEARNING)
  • 6 universal dimension scores (DATA, PROCESS, TOOLS, CHANGE, ROI, TECH)
  • 4-6 industry-specific KPI scores
  • Recommended JadeOS agents matched to the company's gaps
  • 90-day pilot proposal with success metrics declared upfront
  • Risk register and mitigation playbook
  • Estimated annual savings (range + central estimate)

The question bank is curated, not LLM-generated, so every audit is
reproducible from the same answers. The LLM only runs the synthesis
(scoring + narrative + recommendations), not the questions themselves.

PUBLIC entry points (self-service prospect):
  POST   /api/audit/start                  → create audit
  GET    /api/audit/{id}/questions         → fetch question battery
  POST   /api/audit/{id}/respond           → save response(s)
  POST   /api/audit/{id}/analyze           → run LLM synthesis
  GET    /api/audit/{id}                   → fetch audit (results)
  GET    /api/audit/{id}/report.pdf        → download PDF
  GET    /api/audit/dimensions             → static metadata

ADMIN entry points:
  GET    /api/admin/audits                 → list all audits (filterable)
  DELETE /api/admin/audits/{id}            → delete audit
"""
from __future__ import annotations

import io
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional, Any

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from emergentintegrations.llm.chat import LlmChat, UserMessage  # type: ignore

EMERGENT_LLM_KEY = os.environ["EMERGENT_LLM_KEY"]
AUDIT_MODEL = "claude-sonnet-4-5-20250929"

# Industries we cover (must match /app/frontend/src/lib/industries.js).
INDUSTRY_IDS = [
    "freight_brokerage", "logistics", "manufacturing", "healthcare",
    "saas_tech", "e_commerce", "insurance", "legal", "real_estate",
    "professional_services", "general",
]


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ============================================================
# DIMENSION + QUESTION BANK
# ============================================================

# Each universal dimension carries 4 questions on a 0-5 Likert (very_low → very_high)
# whose unweighted average is mapped to 0-100. Industry-specific KPIs are appended.

DIMENSIONS: dict[str, dict] = {
    "DATA": {
        "label": "Data Maturity",
        "color": "#00ffff",
        "weight": 0.20,
        "blurb": "Volume, structure, accessibility, quality of data agents can act on.",
        "questions": [
            {"id": "DATA-1", "text": "How much of your operational data is in structured systems (not paper, email threads, or spreadsheets)?",
             "low": "Mostly paper / email", "high": "Fully digital · system-of-record everywhere"},
            {"id": "DATA-2", "text": "How easily can your team pull a clean export of the last 90 days of operations data?",
             "low": "Days to compile", "high": "One-click export"},
            {"id": "DATA-3", "text": "How frequently is your data updated (real-time vs daily/weekly batches)?",
             "low": "Stale · weekly+", "high": "Real-time streams"},
            {"id": "DATA-4", "text": "Rate the quality of your operational data (completeness, accuracy, dedup'd, schema-consistent).",
             "low": "Inconsistent · gaps", "high": "Audit-ready"},
        ],
    },
    "PROCESS": {
        "label": "Process Density",
        "color": "#ccff00",
        "weight": 0.20,
        "blurb": "Repetitive decisions and manual rework that agents can absorb.",
        "questions": [
            {"id": "PROC-1", "text": "How many repetitive decisions does the team make per day that follow a known playbook?",
             "low": "Few / one-off", "high": "Hundreds · same shape"},
            {"id": "PROC-2", "text": "What share of an employee's day is spent on copy/paste, manual lookups, or status updates?",
             "low": "<10% of day", "high": ">50% of day"},
            {"id": "PROC-3", "text": "How often does the team re-do work because a previous step was missed or wrong?",
             "low": "Rare", "high": "Daily"},
            {"id": "PROC-4", "text": "How documented are your core operating procedures (SOPs)?",
             "low": "Tribal / in heads", "high": "Versioned · enforced"},
        ],
    },
    "TOOLS": {
        "label": "Tools & Integrations",
        "color": "#7c5cff",
        "weight": 0.15,
        "blurb": "Existing stack maturity and API openness for agents to plug into.",
        "questions": [
            {"id": "TOOL-1", "text": "How modern is your core operational software (cloud, API-first vs on-prem legacy)?",
             "low": "On-prem · no APIs", "high": "Cloud-native · open APIs"},
            {"id": "TOOL-2", "text": "How many systems would an agent need to touch to complete one workflow end-to-end?",
             "low": "Many disconnected", "high": "1-2 well-integrated"},
            {"id": "TOOL-3", "text": "Do you already use any AI / automation tools (RPA, Zapier, custom scripts)?",
             "low": "None", "high": "Multiple in production"},
            {"id": "TOOL-4", "text": "How easily can a new tool be tested in your environment (security review, IT velocity)?",
             "low": "6+ months", "high": "Sandbox in days"},
        ],
    },
    "CHANGE": {
        "label": "Change Capacity",
        "color": "#ff3b8a",
        "weight": 0.15,
        "blurb": "Leadership buy-in and team appetite for adopting new ways of working.",
        "questions": [
            {"id": "CHG-1", "text": "How strongly does executive leadership champion AI / automation?",
             "low": "Skeptical", "high": "Top-3 strategic priority"},
            {"id": "CHG-2", "text": "How would your front-line team react to working alongside an AI agent?",
             "low": "Resistant", "high": "Eager / already asking"},
            {"id": "CHG-3", "text": "How recently did you successfully roll out a new operational tool?",
             "low": "5+ years / never", "high": "Within last 6 months"},
            {"id": "CHG-4", "text": "How much training time can the team realistically commit to onboarding?",
             "low": "<2 hrs / week", "high": "Dedicated rollout team"},
        ],
    },
    "ROI": {
        "label": "ROI Signal",
        "color": "#ffce4f",
        "weight": 0.15,
        "blurb": "Measurable savings potential and payback velocity.",
        "questions": [
            {"id": "ROI-1", "text": "What is your annual labor spend on the workflows we'd target with AI?",
             "low": "<$250k / yr", "high": ">$5M / yr"},
            {"id": "ROI-2", "text": "How visible are your current costs (per-decision, per-ticket, per-load)?",
             "low": "Opaque", "high": "Tracked weekly"},
            {"id": "ROI-3", "text": "How much would a 20% reduction in time-per-decision be worth annually?",
             "low": "Minimal", "high": "Material to P&L"},
            {"id": "ROI-4", "text": "How quickly does your organization typically demand payback on tooling spend?",
             "low": "Year+", "high": "Within 6 months · easy sell"},
        ],
    },
    "TECH": {
        "label": "Technical Maturity",
        "color": "#ccff00",
        "weight": 0.15,
        "blurb": "IT maturity, cloud posture, security baseline.",
        "questions": [
            {"id": "TECH-1", "text": "Do you have in-house engineering / IT resources to support an integration?",
             "low": "None", "high": "Dedicated team"},
            {"id": "TECH-2", "text": "What is your current cloud posture (on-prem / hybrid / cloud-native)?",
             "low": "On-prem only", "high": "Cloud-native"},
            {"id": "TECH-3", "text": "Do you have a documented security review process for new vendors?",
             "low": "Ad-hoc", "high": "SOC 2 / SIG / formal"},
            {"id": "TECH-4", "text": "How important is on-shore data residency or specific compliance (HIPAA, SOC 2, FedRAMP)?",
             "low": "Not required", "high": "Hard requirement"},
        ],
    },
}

# Industry-specific KPI questions (4-6 each). These score independently and feed the LLM
# as context for the recommended-agents and pilot-proposal sections.
INDUSTRY_KPIS: dict[str, list[dict]] = {
    "freight_brokerage": [
        {"id": "FB-1", "text": "What % of fleet hours are empty miles today?", "low": "<8%", "high": ">22%"},
        {"id": "FB-2", "text": "How many quotes / day does an average broker handle?", "low": "<10", "high": ">60"},
        {"id": "FB-3", "text": "How often do you quote below cost-basis (rate-floor breach risk)?", "low": "Never", "high": "Weekly"},
        {"id": "FB-4", "text": "What is your annualized driver turnover rate?", "low": "<25%", "high": ">90%"},
        {"id": "FB-5", "text": "How much time per shift do dispatchers spend on manual carrier sourcing?", "low": "<15 min", "high": ">2 hrs"},
    ],
    "logistics": [
        {"id": "LOG-1", "text": "How tightly are your TMS, WMS, and OMS systems integrated?", "low": "Manual hand-offs", "high": "API-stitched"},
        {"id": "LOG-2", "text": "What % of shipments require manual exception handling?", "low": "<5%", "high": ">25%"},
        {"id": "LOG-3", "text": "How quickly can you re-route around a disrupted lane?", "low": "Hours+", "high": "Minutes"},
        {"id": "LOG-4", "text": "How much of your accessorial billing is auto-captured today?", "low": "<30%", "high": ">90%"},
        {"id": "LOG-5", "text": "How often do POD / BOL documents require manual re-entry?", "low": "Rare", "high": "Daily"},
    ],
    "manufacturing": [
        {"id": "MFG-1", "text": "How often does a production run get rescheduled because of unplanned downtime?", "low": "Quarterly", "high": "Weekly"},
        {"id": "MFG-2", "text": "How much of your quality-control sampling is human-eye vs automated?", "low": "Mostly automated", "high": "All human"},
        {"id": "MFG-3", "text": "How are PO acknowledgments processed (manual data entry vs system)?", "low": "Auto-ingested", "high": "Manual entry"},
        {"id": "MFG-4", "text": "How precise is your demand forecasting today?", "low": "±5%", "high": "±25%+"},
        {"id": "MFG-5", "text": "How much technician time is spent on paperwork vs wrench-time?", "low": "<10%", "high": ">40%"},
    ],
    "healthcare": [
        {"id": "HC-1", "text": "How many patient intake forms / day does your front office process?", "low": "<10", "high": ">200"},
        {"id": "HC-2", "text": "Are you HIPAA-trained with documented BAAs for vendors?", "low": "Not yet", "high": "Full program"},
        {"id": "HC-3", "text": "How much time does prior-auth eat per case?", "low": "<5 min", "high": ">45 min"},
        {"id": "HC-4", "text": "What's your no-show rate, and do you have AI / SMS reminders today?", "low": "<5% / yes", "high": ">25% / none"},
        {"id": "HC-5", "text": "How burdensome is referral coordination for your staff?", "low": "Minimal", "high": "Full FTE"},
        {"id": "HC-6", "text": "How much of clinical documentation is voice-dictated vs typed?", "low": "Voice", "high": "All typed"},
    ],
    "saas_tech": [
        {"id": "SAAS-1", "text": "What is your Tier-1 support deflection rate today?", "low": ">60%", "high": "<10%"},
        {"id": "SAAS-2", "text": "How many inbound support tickets / week per support FTE?", "low": "<50", "high": ">300"},
        {"id": "SAAS-3", "text": "How much of your onboarding is documented + automated?", "low": "Fully automated", "high": "Hand-held"},
        {"id": "SAAS-4", "text": "How quickly does your team respond to inbound lead forms?", "low": "<5 min", "high": ">24 hrs"},
        {"id": "SAAS-5", "text": "What % of your customer health data is action-triggering (vs dashboard-only)?", "low": ">50%", "high": "<10%"},
    ],
    "e_commerce": [
        {"id": "EC-1", "text": "What's your customer service contact rate (% of orders that contact support)?", "low": "<3%", "high": ">12%"},
        {"id": "EC-2", "text": "How much of your product catalog enrichment (descriptions, attributes) is manual?", "low": "Mostly auto", "high": "All hand-keyed"},
        {"id": "EC-3", "text": "What's your return rate, and how is RMA processing handled?", "low": "<5% / auto", "high": ">15% / manual"},
        {"id": "EC-4", "text": "How fast does your team respond to lost-package inquiries?", "low": "<30 min", "high": ">24 hrs"},
        {"id": "EC-5", "text": "How dynamic is your pricing / promo deployment?", "low": "Hourly", "high": "Quarterly"},
    ],
    "insurance": [
        {"id": "INS-1", "text": "What's your average first-touch claim acknowledgment time?", "low": "<10 min", "high": ">4 hrs"},
        {"id": "INS-2", "text": "How much of underwriting submission triage is automated?", "low": "Fully", "high": "All manual"},
        {"id": "INS-3", "text": "How accurate is your fraud-flag rate (false positives)?", "low": "<10% FP", "high": ">40% FP"},
        {"id": "INS-4", "text": "How much agent time is spent on data re-entry across forms?", "low": "<10%", "high": ">50%"},
        {"id": "INS-5", "text": "How robust is your audit trail for adjudication decisions?", "low": "Full audit", "high": "Spotty"},
    ],
    "legal": [
        {"id": "LGL-1", "text": "How much of discovery review is automated (predictive coding, clustering)?", "low": "Fully", "high": "All human"},
        {"id": "LGL-2", "text": "What % of paralegal time is spent on document drafting from templates?", "low": "<10%", "high": ">60%"},
        {"id": "LGL-3", "text": "How quickly can your team locate a specific clause across the matter library?", "low": "Minutes", "high": "Hours+"},
        {"id": "LGL-4", "text": "How structured is your matter-management system?", "low": "Modern · structured", "high": "Email folders"},
        {"id": "LGL-5", "text": "How often does conflict-check or KYC delay matter intake?", "low": "Rarely", "high": "Most matters"},
    ],
    "real_estate": [
        {"id": "RE-1", "text": "How fast does your team respond to inbound listing inquiries?", "low": "<5 min", "high": ">12 hrs"},
        {"id": "RE-2", "text": "How much CMA prep is auto-generated vs hand-built?", "low": "Auto", "high": "Hand-built"},
        {"id": "RE-3", "text": "How streamlined is your lease-abstraction or contract review?", "low": "AI-assisted", "high": "All manual"},
        {"id": "RE-4", "text": "How well-documented is each property's history (showings, offers, inspections)?", "low": "Full system", "high": "Notes in heads"},
        {"id": "RE-5", "text": "How dynamic is your listing-price / strategy adjustment?", "low": "Weekly", "high": "Static"},
    ],
    "professional_services": [
        {"id": "PS-1", "text": "How much of project status reporting is manual?", "low": "Auto from tools", "high": "Weekly slides"},
        {"id": "PS-2", "text": "How much time goes into invoice generation per month?", "low": "<2 hrs", "high": ">20 hrs"},
        {"id": "PS-3", "text": "How well-tracked is your utilization vs billable hours?", "low": "Real-time", "high": "Monthly review"},
        {"id": "PS-4", "text": "How structured is your knowledge / IP capture across projects?", "low": "Searchable KB", "high": "Tribal"},
        {"id": "PS-5", "text": "How much of new-business research is templated vs from scratch?", "low": "Templated", "high": "Always from scratch"},
    ],
    "general": [
        {"id": "GEN-1", "text": "What is your single biggest operational pain point today?", "low": "Minor friction", "high": "Existential"},
        {"id": "GEN-2", "text": "How much time per week does your team waste on coordination overhead (meetings, status, follow-up)?", "low": "<5 hrs", "high": ">25 hrs"},
        {"id": "GEN-3", "text": "How quickly can you onboard a new hire to be productive?", "low": "<1 week", "high": ">3 months"},
        {"id": "GEN-4", "text": "How well-instrumented is your current operational dashboard?", "low": "Live KPIs", "high": "Whiteboard"},
        {"id": "GEN-5", "text": "How experimental is your culture (try-fast-fail-fast)?", "low": "Very", "high": "Risk-averse"},
    ],
}

# JadeOS agent catalog used for recommendation matching.
AGENT_CATALOG = [
    {"id": "M1", "name": "Dispatch Optimizer",      "best_for": ["freight_brokerage", "logistics"]},
    {"id": "M2", "name": "Route + Fuel Agent",      "best_for": ["freight_brokerage", "logistics"]},
    {"id": "M3", "name": "Compliance + Safety",     "best_for": ["freight_brokerage", "logistics", "healthcare", "insurance"]},
    {"id": "M4", "name": "Pricing + Rate-Floor",    "best_for": ["freight_brokerage", "logistics", "saas_tech", "real_estate"]},
    {"id": "M5", "name": "Driver / Talent Lifecycle","best_for": ["freight_brokerage", "logistics", "professional_services"]},
    {"id": "M6", "name": "Predictive Maintenance",  "best_for": ["manufacturing", "logistics"]},
    {"id": "A1", "name": "Doc Extract · BOL/PO/Invoice", "best_for": ["freight_brokerage", "logistics", "manufacturing", "insurance"]},
    {"id": "A2", "name": "Lead Qualification",      "best_for": ["saas_tech", "e_commerce", "real_estate", "professional_services"]},
    {"id": "A3", "name": "Support Triage · Tier-1", "best_for": ["saas_tech", "e_commerce", "healthcare", "insurance"]},
    {"id": "A4", "name": "Outreach Drafting",       "best_for": ["saas_tech", "e_commerce", "real_estate", "professional_services"]},
    {"id": "A5", "name": "Workflow Memory",         "best_for": ["legal", "professional_services", "healthcare"]},
    {"id": "A6", "name": "Claims Filing",           "best_for": ["insurance", "logistics", "freight_brokerage"]},
]


# ============================================================
# MODELS
# ============================================================

ResponseValue = Literal[1, 2, 3, 4, 5]


class StartBody(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    industry: str
    operator_name: Optional[str] = None
    operator_email: Optional[str] = None
    fleet_or_team_size: Optional[str] = None
    source: Literal["admin", "self_serve"] = "self_serve"
    lead_magnet: Optional[str] = None  # e.g. "free_90_day"


class RespondBody(BaseModel):
    responses: dict[str, ResponseValue]
    notes: Optional[dict[str, str]] = None  # question_id → free-text


class AuditDoc(BaseModel):
    id: str
    company_name: str
    industry: str
    operator_name: Optional[str] = None
    operator_email: Optional[str] = None
    fleet_or_team_size: Optional[str] = None
    source: str = "self_serve"
    lead_magnet: Optional[str] = None
    created_at: str
    updated_at: str
    status: Literal["draft", "complete", "analyzed"] = "draft"
    responses: dict[str, int] = Field(default_factory=dict)
    notes: dict[str, str] = Field(default_factory=dict)
    analysis: Optional[dict[str, Any]] = None


# ============================================================
# QUESTION BANK ASSEMBLY
# ============================================================

def build_question_battery(industry: str) -> dict:
    """Return the full question battery for an industry, broken into sections."""
    if industry not in INDUSTRY_IDS:
        industry = "general"

    sections = []
    for dim_id, dim in DIMENSIONS.items():
        sections.append({
            "id": dim_id,
            "label": dim["label"],
            "color": dim["color"],
            "weight": dim["weight"],
            "blurb": dim["blurb"],
            "kind": "universal",
            "questions": dim["questions"],
        })
    sections.append({
        "id": "INDUSTRY",
        "label": f"Industry KPIs · {industry.replace('_', ' ').title()}",
        "color": "#00ffff",
        "weight": 0.0,  # informational; LLM uses these contextually
        "blurb": "Specific operational indicators that shape agent recommendations.",
        "kind": "industry",
        "questions": INDUSTRY_KPIS.get(industry, INDUSTRY_KPIS["general"]),
    })
    total_q = sum(len(s["questions"]) for s in sections)
    return {"industry": industry, "sections": sections, "total_questions": total_q}


def score_audit(responses: dict[str, int], industry: str) -> dict:
    """Deterministic scoring. LLM picks up from here to add narrative."""
    dim_scores: dict[str, float] = {}
    for dim_id, dim in DIMENSIONS.items():
        qs = dim["questions"]
        vals = [responses.get(q["id"]) for q in qs if responses.get(q["id"]) is not None]
        if not vals:
            dim_scores[dim_id] = 0.0
            continue
        # Likert 1-5 → 0-100 (1 → 0, 5 → 100, linear)
        norm = [(v - 1) * 25.0 for v in vals]
        dim_scores[dim_id] = round(sum(norm) / len(norm), 1)

    overall = round(
        sum(dim_scores[d] * DIMENSIONS[d]["weight"] for d in DIMENSIONS) /
        sum(DIMENSIONS[d]["weight"] for d in DIMENSIONS),
        1,
    )

    # Industry KPI raw scores (informational, not weighted into overall)
    industry_qs = INDUSTRY_KPIS.get(industry, INDUSTRY_KPIS["general"])
    industry_scores = {
        q["id"]: (responses.get(q["id"], 0) - 1) * 25.0
        for q in industry_qs
        if responses.get(q["id"]) is not None
    }

    if overall >= 75:
        tier, tier_color, tier_blurb = "PIONEER", "#ccff00", "Ready to deploy AI agents into production within 30-60 days."
    elif overall >= 55:
        tier, tier_color, tier_blurb = "BUILDER", "#00ffff", "Strong foundation. 60-90 day pilot is the right next step."
    elif overall >= 35:
        tier, tier_color, tier_blurb = "CURIOUS", "#7c5cff", "Foundational work needed alongside a tightly-scoped pilot."
    else:
        tier, tier_color, tier_blurb = "LEARNING", "#ffce4f", "Data + process maturity is the first investment. Then pilot."

    return {
        "overall_score": overall,
        "tier": tier,
        "tier_color": tier_color,
        "tier_blurb": tier_blurb,
        "dimension_scores": dim_scores,
        "industry_scores": industry_scores,
    }


def recommend_agents(scores: dict, industry: str, top_n: int = 4) -> list[dict]:
    """Deterministic agent shortlist. Prioritizes agents matched to the industry,
    then weights by where the company's biggest dimension gaps are."""
    base = [a for a in AGENT_CATALOG if industry in a["best_for"]]
    if len(base) < top_n:
        for a in AGENT_CATALOG:
            if a not in base:
                base.append(a)
            if len(base) >= top_n + 2:
                break

    weakest_dims = sorted(scores["dimension_scores"].items(), key=lambda kv: kv[1])[:3]
    weak_summary = ", ".join(f"{d.title()} ({v:.0f})" for d, v in weakest_dims)

    return [
        {
            "id": a["id"],
            "name": a["name"],
            "rationale": f"Direct fit for {industry.replace('_', ' ')} · targets gaps in {weak_summary}",
        }
        for a in base[:top_n]
    ]


def estimate_savings_usd(scores: dict, industry: str, fleet_or_team_size: Optional[str]) -> dict:
    """Rough annual savings band. Uses industry benchmarks scaled by tier and size hint."""
    base_per_seat = {
        "freight_brokerage": 18000, "logistics": 16000, "manufacturing": 14000,
        "healthcare": 22000, "saas_tech": 12000, "e_commerce": 9000,
        "insurance": 17000, "legal": 24000, "real_estate": 11000,
        "professional_services": 15000, "general": 10000,
    }.get(industry, 10000)

    # Parse team size hint
    try:
        size_n = int("".join(ch for ch in (fleet_or_team_size or "") if ch.isdigit()) or "25")
    except ValueError:
        size_n = 25
    size_n = max(5, min(size_n, 5000))

    tier_factor = {"PIONEER": 1.25, "BUILDER": 1.0, "CURIOUS": 0.65, "LEARNING": 0.40}[scores["tier"]]
    central = base_per_seat * size_n * tier_factor * 0.18  # 18% of indirect labor benchmark
    low = round(central * 0.80, -3)
    high = round(central * 1.30, -3)
    return {
        "annual_savings_low_usd": int(low),
        "annual_savings_central_usd": int(central),
        "annual_savings_high_usd": int(high),
        "size_used": size_n,
        "payback_months_estimate": max(2, int(12 / tier_factor)),
    }


# ============================================================
# LLM SYNTHESIS
# ============================================================

ANALYSIS_PROMPT = """You are JadeOS — an operator-grade AI agent platform. You are running a consulting
audit on a prospective customer. You are senior, decisive, never sycophantic. Write like a
veteran operator who has lived this industry, not a salesperson.

You receive:
  - Company name + industry
  - Deterministic scoring (already computed: overall, dimension, industry KPI)
  - Tier classification (PIONEER / BUILDER / CURIOUS / LEARNING)
  - Recommended agent shortlist (already chosen)
  - Annual savings estimate band

Return ONLY a JSON object (no prose, no fences) with EXACTLY this shape:
{
  "executive_summary": "120-180 word narrative of where this company sits and what to do.",
  "strengths": ["3-5 short, specific strengths grounded in the dimension scores"],
  "gaps": ["3-5 short, specific gaps grounded in the lowest dimension scores"],
  "pilot_proposal": {
    "duration_days": 90,
    "scope": "1-2 sentences describing what gets piloted",
    "success_metrics": ["3-4 measurable, time-bound metrics, declared upfront"],
    "team_required": "1 sentence on who from their side must be in the room",
    "investment_usd": 35000
  },
  "risks": [
    {"risk": "Specific risk", "severity": "high|med|low", "mitigation": "1-sentence mitigation"}
  ],
  "next_30_days": ["3-5 concrete actions starting Monday — verb-led"],
  "callout": "One bold operator quote summarising the punchline (≤30 words)."
}
Keep every string concrete, specific to this company's industry and scores. No filler."""


async def llm_synthesize(audit_payload: dict) -> dict:
    """Call Claude Sonnet 4.5 to add narrative on top of deterministic scoring.
    Falls back to a deterministic stub if the LLM is unavailable."""
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"audit-{audit_payload['id']}",
            system_message=ANALYSIS_PROMPT,
        ).with_model("anthropic", AUDIT_MODEL)

        msg = UserMessage(text=json.dumps(audit_payload, separators=(",", ":")))
        out = await chat.send_message(msg)
        text = out if isinstance(out, str) else getattr(out, "content", str(out))

        # Robust JSON extraction
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1:
            text = text[start : end + 1]
        return json.loads(text)
    except Exception as e:
        # Deterministic fallback — never lets the audit fail
        scores = audit_payload["scores"]
        return {
            "executive_summary": (
                f"{audit_payload['company_name']} sits at {scores['overall_score']:.0f}/100 — "
                f"{scores['tier']}. {scores['tier_blurb']} Lead with the recommended agent shortlist "
                f"on a 90-day pilot with success metrics declared in writing before kickoff."
            ),
            "strengths": [
                f"Strongest dimension · {max(scores['dimension_scores'], key=scores['dimension_scores'].get)}",
                "Industry vertical fit · agents purpose-built for this sector",
                "Operator-grade audit substrate ready on day one",
            ],
            "gaps": [
                f"Weakest dimension · {min(scores['dimension_scores'], key=scores['dimension_scores'].get)}",
                "Manual processes consuming material team hours",
                "Limited data structure for agent ingestion",
            ],
            "pilot_proposal": {
                "duration_days": 90,
                "scope": "Deploy top-recommended agent on the highest-density workflow with full audit log.",
                "success_metrics": [
                    "≥20% reduction in time-per-decision",
                    "≥95% audit chain coverage of agent actions",
                    "User satisfaction score ≥4.2/5",
                    "Documented ROI in pilot exit memo",
                ],
                "team_required": "Executive sponsor + 1 ops lead + 1 IT/data contact.",
                "investment_usd": 35000,
            },
            "risks": [
                {"risk": "Data quality below threshold for agent training", "severity": "med",
                 "mitigation": "First 2 weeks dedicated to data audit + cleanup playbook."},
                {"risk": "Change-management drag on rollout", "severity": "med",
                 "mitigation": "Identify a front-line champion before pilot starts."},
            ],
            "next_30_days": [
                "Sign 1-page pilot agreement with success metrics named.",
                "Identify executive sponsor + ops lead + IT contact.",
                "Schedule a 60-minute data walk-through.",
                "Cut a sandbox workspace in JadeOS for the pilot tenant.",
            ],
            "callout": f"Build complete. Ready to deploy. Score: {scores['overall_score']:.0f}/100 · {scores['tier']}.",
            "_source": f"deterministic_fallback ({type(e).__name__})",
        }


# ============================================================
# PDF GENERATION (PowerPoint-style, matches pitch deck)
# ============================================================

def generate_audit_pdf(audit: dict) -> bytes:
    """12-page landscape-letter PDF report. Same visual language as the pitch deck."""
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib.colors import HexColor, white
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch

    PAGE_W, PAGE_H = landscape(letter)
    BG = HexColor("#06070d")
    JADE = HexColor("#ccff00")
    CYAN = HexColor("#00ffff")
    VIOLET = HexColor("#7c5cff")
    MAGENTA = HexColor("#ff3b8a")
    AMBER = HexColor("#ffce4f")
    WHITE_DIM = HexColor("#cccccc")

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(letter))

    def fill_bg(c):
        c.setFillColor(BG)
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    def page_chrome(c, page_n, total, accent):
        c.setFillColor(accent)
        c.rect(0, PAGE_H - 24, PAGE_W, 4, fill=1, stroke=0)
        c.setFillColor(HexColor("#777777"))
        c.setFont("Helvetica", 8)
        c.drawString(40, 24, f"JadeOS · AI Readiness Audit · {audit['company_name']}")
        c.drawRightString(PAGE_W - 40, 24, f"{page_n:02d} / {total:02d}")

    def title(c, text, color, y=PAGE_H - 80):
        c.setFillColor(color)
        c.setFont("Helvetica-Bold", 28)
        c.drawString(48, y, text)

    def bullet(c, text, y, color=WHITE_DIM, size=11, x=72):
        c.setFillColor(color)
        c.setFont("Helvetica", size)
        c.drawString(x, y, "•")
        c.setFillColor(white)
        # Soft wrap at ~95 chars
        words = text.split(" ")
        line, lines = [], []
        for w in words:
            if sum(len(s) + 1 for s in line) + len(w) > 95:
                lines.append(" ".join(line))
                line = [w]
            else:
                line.append(w)
        if line:
            lines.append(" ".join(line))
        for i, ln in enumerate(lines):
            c.drawString(x + 14, y - (i * 14), ln)
        return y - (len(lines) * 14) - 6

    scores = audit["analysis"]["scores"]
    narrative = audit["analysis"]["narrative"]
    rec = audit["analysis"]["recommended_agents"]
    sav = audit["analysis"]["savings"]
    total_pages = 12

    # ----- PAGE 1 · COVER -----
    fill_bg(c)
    c.setFillColor(JADE)
    c.setFont("Helvetica-Bold", 60)
    c.drawString(48, PAGE_H - 220, "AI Readiness Audit")
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 36)
    c.drawString(48, PAGE_H - 270, audit["company_name"])
    c.setFillColor(CYAN)
    c.setFont("Helvetica", 14)
    c.drawString(48, PAGE_H - 295, f"{audit['industry'].replace('_', ' ').upper()}  ·  "
                                   f"Prepared by JadeOS  ·  {datetime.now(timezone.utc).strftime('%B %d, %Y')}")
    c.setFillColor(HexColor(scores["tier_color"]))
    c.setFont("Helvetica-Bold", 84)
    c.drawString(48, 180, f"{scores['overall_score']:.0f}")
    c.setFont("Helvetica", 12)
    c.drawString(48, 158, "OVERALL SCORE / 100")
    c.setFillColor(HexColor(scores["tier_color"]))
    c.setFont("Helvetica-Bold", 22)
    c.drawString(220, 200, f"TIER · {scores['tier']}")
    c.setFillColor(WHITE_DIM)
    c.setFont("Helvetica", 12)
    c.drawString(220, 180, scores["tier_blurb"])
    page_chrome(c, 1, total_pages, JADE)
    c.showPage()

    # ----- PAGE 2 · EXECUTIVE SUMMARY -----
    fill_bg(c)
    title(c, "Executive Summary", CYAN)
    c.setFillColor(white)
    c.setFont("Helvetica", 13)
    words = narrative["executive_summary"].split(" ")
    line, y = [], PAGE_H - 140
    for w in words:
        if sum(len(s) + 1 for s in line) + len(w) > 100:
            c.drawString(48, y, " ".join(line))
            y -= 20; line = [w]
        else:
            line.append(w)
    if line:
        c.drawString(48, y, " ".join(line))
    # Callout
    c.setFillColor(JADE)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(48, 140, f"\u201C{narrative['callout']}\u201D")
    page_chrome(c, 2, total_pages, CYAN)
    c.showPage()

    # ----- PAGE 3 · DIMENSION RADAR (text-rendered bar chart fallback) -----
    fill_bg(c)
    title(c, "6 Dimensions of AI Readiness", VIOLET)
    y = PAGE_H - 150
    for dim_id, dim in DIMENSIONS.items():
        score = scores["dimension_scores"].get(dim_id, 0)
        bar_w = (score / 100.0) * (PAGE_W - 320)
        c.setFillColor(HexColor(dim["color"]))
        c.setFont("Helvetica-Bold", 13)
        c.drawString(48, y, dim["label"])
        c.setFont("Helvetica", 10)
        c.setFillColor(WHITE_DIM)
        c.drawString(48, y - 14, dim["blurb"])
        # bar background
        c.setFillColor(HexColor("#1a1d2e"))
        c.rect(220, y - 8, PAGE_W - 320, 20, fill=1, stroke=0)
        # filled bar
        c.setFillColor(HexColor(dim["color"]))
        c.rect(220, y - 8, bar_w, 20, fill=1, stroke=0)
        # score
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(PAGE_W - 60, y - 4, f"{score:.0f}")
        y -= 60
    page_chrome(c, 3, total_pages, VIOLET)
    c.showPage()

    # ----- PAGE 4 · STRENGTHS -----
    fill_bg(c)
    title(c, "Strengths", JADE)
    y = PAGE_H - 140
    for s in narrative["strengths"]:
        y = bullet(c, s, y, color=JADE)
    page_chrome(c, 4, total_pages, JADE)
    c.showPage()

    # ----- PAGE 5 · GAPS -----
    fill_bg(c)
    title(c, "Gaps", MAGENTA)
    y = PAGE_H - 140
    for g in narrative["gaps"]:
        y = bullet(c, g, y, color=MAGENTA)
    page_chrome(c, 5, total_pages, MAGENTA)
    c.showPage()

    # ----- PAGE 6 · INDUSTRY KPIs -----
    fill_bg(c)
    title(c, f"Industry KPIs · {audit['industry'].replace('_', ' ').title()}", CYAN)
    y = PAGE_H - 150
    industry_qs = INDUSTRY_KPIS.get(audit["industry"], INDUSTRY_KPIS["general"])
    for q in industry_qs:
        v = audit.get("responses", {}).get(q["id"], 0)
        score = (v - 1) * 25 if v else 0
        bar_w = (score / 100.0) * 400
        c.setFillColor(white)
        c.setFont("Helvetica", 10)
        c.drawString(48, y, q["text"][:90])
        c.setFillColor(HexColor("#1a1d2e"))
        c.rect(48, y - 16, 400, 8, fill=1, stroke=0)
        c.setFillColor(CYAN)
        c.rect(48, y - 16, bar_w, 8, fill=1, stroke=0)
        c.setFillColor(WHITE_DIM)
        c.setFont("Helvetica", 9)
        c.drawString(48, y - 30, f"{q['low']}   →   {q['high']}")
        y -= 50
    page_chrome(c, 6, total_pages, CYAN)
    c.showPage()

    # ----- PAGE 7 · RECOMMENDED AGENTS -----
    fill_bg(c)
    title(c, "Recommended JadeOS Agents", JADE)
    y = PAGE_H - 140
    for a in rec:
        c.setFillColor(JADE)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(48, y, f"{a['id']} · {a['name']}")
        c.setFillColor(WHITE_DIM)
        c.setFont("Helvetica", 11)
        c.drawString(48, y - 18, a["rationale"][:120])
        y -= 50
    page_chrome(c, 7, total_pages, JADE)
    c.showPage()

    # ----- PAGE 8 · 90-DAY PILOT -----
    fill_bg(c)
    title(c, "Proposed 90-Day Pilot", VIOLET)
    p = narrative["pilot_proposal"]
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(48, PAGE_H - 140, f"DURATION · {p['duration_days']} days     INVESTMENT · ${p['investment_usd']:,}")
    c.setFillColor(WHITE_DIM)
    c.setFont("Helvetica", 12)
    c.drawString(48, PAGE_H - 170, f"SCOPE · {p['scope']}")
    c.setFillColor(JADE)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(48, PAGE_H - 210, "SUCCESS METRICS")
    y = PAGE_H - 230
    for m in p["success_metrics"]:
        y = bullet(c, m, y, color=JADE)
    c.setFillColor(CYAN)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(48, y - 14, "TEAM REQUIRED")
    c.setFillColor(WHITE_DIM)
    c.setFont("Helvetica", 11)
    c.drawString(48, y - 30, p["team_required"][:120])
    page_chrome(c, 8, total_pages, VIOLET)
    c.showPage()

    # ----- PAGE 9 · ROI -----
    fill_bg(c)
    title(c, "Estimated Annual Savings", JADE)
    c.setFillColor(JADE)
    c.setFont("Helvetica-Bold", 58)
    c.drawString(48, PAGE_H - 220, f"${sav['annual_savings_central_usd']:,}")
    c.setFillColor(WHITE_DIM)
    c.setFont("Helvetica", 12)
    c.drawString(48, PAGE_H - 245, f"central estimate · range ${sav['annual_savings_low_usd']:,} – ${sav['annual_savings_high_usd']:,}")
    c.setFillColor(CYAN)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(48, PAGE_H - 310, f"PAYBACK · ~{sav['payback_months_estimate']} months")
    c.setFillColor(WHITE_DIM)
    c.setFont("Helvetica", 10)
    c.drawString(48, 70, f"Basis · {sav['size_used']} seats · industry benchmark ($/seat) · tier factor "
                          f"({scores['tier']}) · 18% indirect-labor capture.")
    page_chrome(c, 9, total_pages, JADE)
    c.showPage()

    # ----- PAGE 10 · RISKS -----
    fill_bg(c)
    title(c, "Risk Register", AMBER)
    y = PAGE_H - 140
    sev_color = {"high": MAGENTA, "med": AMBER, "low": JADE}
    for r in narrative["risks"]:
        c.setFillColor(sev_color.get(r["severity"], AMBER))
        c.setFont("Helvetica-Bold", 12)
        c.drawString(48, y, f"[{r['severity'].upper()}]")
        c.setFillColor(white)
        c.drawString(110, y, r["risk"][:90])
        c.setFillColor(WHITE_DIM)
        c.setFont("Helvetica", 10)
        c.drawString(110, y - 14, f"Mitigation · {r['mitigation'][:100]}")
        y -= 44
    page_chrome(c, 10, total_pages, AMBER)
    c.showPage()

    # ----- PAGE 11 · NEXT 30 DAYS -----
    fill_bg(c)
    title(c, "Next 30 Days", CYAN)
    y = PAGE_H - 140
    for s in narrative["next_30_days"]:
        y = bullet(c, s, y, color=CYAN)
    page_chrome(c, 11, total_pages, CYAN)
    c.showPage()

    # ----- PAGE 12 · CONTACT / CALL TO ACTION -----
    fill_bg(c)
    title(c, "Ready to deploy.", JADE)
    c.setFillColor(white)
    c.setFont("Helvetica", 14)
    c.drawString(48, PAGE_H - 180,
                 "JadeOS Quantum AI · JadeOS-Agent Suite · Hot Shot TMS — built solo by a 13-year operator.")
    c.setFillColor(CYAN)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(48, PAGE_H - 240, "founder@jadeos.ai")
    c.drawString(48, PAGE_H - 270, "onejades.com")
    c.setFillColor(WHITE_DIM)
    c.setFont("Helvetica", 11)
    c.drawString(48, 50,
                 "All scoring is reproducible from the question responses. Every action recommendation "
                 "is grounded in the deterministic scoring layer, not LLM speculation.")
    page_chrome(c, 12, total_pages, JADE)
    c.showPage()
    c.save()
    return buf.getvalue()


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/dimensions")
async def list_dimensions():
    """Public metadata about the universal dimensions + supported industries."""
    return {
        "dimensions": [
            {"id": k, **{kk: vv for kk, vv in v.items() if kk != "questions"},
             "question_count": len(v["questions"])}
            for k, v in DIMENSIONS.items()
        ],
        "industries": INDUSTRY_IDS,
        "agent_catalog": AGENT_CATALOG,
    }


def _db():
    """Lazy import to avoid circular dep with server.py at module load time."""
    from server import db  # noqa: WPS433
    return db


@router.post("/start")
async def start_audit(body: StartBody):
    if body.industry not in INDUSTRY_IDS:
        body.industry = "general"
    audit_id = uuid.uuid4().hex[:16]
    doc = AuditDoc(
        id=audit_id,
        company_name=body.company_name,
        industry=body.industry,
        operator_name=body.operator_name,
        operator_email=body.operator_email,
        fleet_or_team_size=body.fleet_or_team_size,
        source=body.source,
        lead_magnet=body.lead_magnet,
        created_at=_utcnow_iso(),
        updated_at=_utcnow_iso(),
    )
    await _db().audits.insert_one(doc.model_dump())
    return {"id": audit_id, "industry": body.industry, "status": "draft"}


@router.get("/{audit_id}/questions")
async def get_questions(audit_id: str):
    doc = await _db().audits.find_one({"id": audit_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "audit not found")
    battery = build_question_battery(doc["industry"])
    return {"audit_id": audit_id, "company_name": doc["company_name"], **battery}


@router.post("/{audit_id}/respond")
async def respond_audit(audit_id: str, body: RespondBody):
    doc = await _db().audits.find_one({"id": audit_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "audit not found")
    merged = {**doc.get("responses", {}), **{k: int(v) for k, v in body.responses.items()}}
    notes_merged = {**doc.get("notes", {}), **(body.notes or {})}
    # Determine if all questions for this industry have been answered
    battery = build_question_battery(doc["industry"])
    total = battery["total_questions"]
    answered = sum(1 for s in battery["sections"] for q in s["questions"] if q["id"] in merged)
    status = "complete" if answered >= total else "draft"
    await _db().audits.update_one(
        {"id": audit_id},
        {"$set": {"responses": merged, "notes": notes_merged, "updated_at": _utcnow_iso(), "status": status}},
    )
    return {"audit_id": audit_id, "answered": answered, "total": total, "status": status}


@router.post("/{audit_id}/analyze")
async def analyze_audit(audit_id: str):
    doc = await _db().audits.find_one({"id": audit_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "audit not found")
    if not doc.get("responses"):
        raise HTTPException(400, "no responses to analyze")

    scores = score_audit(doc["responses"], doc["industry"])
    rec = recommend_agents(scores, doc["industry"])
    sav = estimate_savings_usd(scores, doc["industry"], doc.get("fleet_or_team_size"))
    payload = {
        "id": audit_id,
        "company_name": doc["company_name"],
        "industry": doc["industry"],
        "scores": scores,
        "recommended_agents": rec,
        "savings": sav,
    }
    narrative = await llm_synthesize(payload)
    analysis = {
        "scores": scores,
        "recommended_agents": rec,
        "savings": sav,
        "narrative": narrative,
        "analyzed_at": _utcnow_iso(),
    }
    await _db().audits.update_one(
        {"id": audit_id},
        {"$set": {"analysis": analysis, "status": "analyzed", "updated_at": _utcnow_iso()}},
    )
    return analysis


@router.get("/{audit_id}")
async def get_audit(audit_id: str):
    doc = await _db().audits.find_one({"id": audit_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "audit not found")
    return doc


@router.get("/{audit_id}/report.pdf")
async def audit_report_pdf(audit_id: str):
    doc = await _db().audits.find_one({"id": audit_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "audit not found")
    if not doc.get("analysis"):
        raise HTTPException(400, "audit not yet analyzed")
    pdf = generate_audit_pdf(doc)
    safe = "".join(ch if ch.isalnum() else "_" for ch in doc["company_name"])[:40]
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="JadeOS_Audit_{safe}.pdf"'},
    )


# ---------- ADMIN ----------

admin_router = APIRouter(prefix="/admin/audits", tags=["audit-admin"])


@admin_router.get("")
async def list_audits(industry: Optional[str] = None, status: Optional[str] = None, limit: int = 200):
    q: dict[str, Any] = {}
    if industry:
        q["industry"] = industry
    if status:
        q["status"] = status
    docs = await _db().audits.find(q, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return {"audits": docs, "total": len(docs)}


@admin_router.delete("/{audit_id}")
async def delete_audit(audit_id: str):
    res = await _db().audits.delete_one({"id": audit_id})
    return {"deleted": res.deleted_count}
