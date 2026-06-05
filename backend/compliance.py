"""JADE OS · Compliance & Industry Go-To-Market routing.

Pure-data module. Encodes:
  • Which industries we can sell to RIGHT NOW (no SOC 2 / no special compliance)
  • Which industries require SOC 2 Type II before launch
  • Which require HIPAA / state-specific health-data law
  • Which require special ToS guardrails (UPL, FMCSA, EEOC bias-audit)
  • Universal compliance work (Privacy Policy, ToS, DPA, AI disclosure)
  • A 8-month routing roadmap with milestones, costs, and what each unlocks

Returned shape is consumed by the admin COMPLIANCE tab.
"""
from typing import Dict, List


# ============================================================
# INDUSTRY ROUTING — sortable, filterable, color-coded
# Status enum:
#   "go_now"      — ship today, no compliance gate
#   "go_with_tos" — ship today with a clear contractual carve-out
#   "blocked"     — cannot sell until specific certification achieved
# ============================================================

INDUSTRIES: List[Dict] = [
    {
        "id": "freight_brokerage",
        "label": "Freight Brokerage",
        "status": "go_now",
        "color": "#ccff00",
        "headline": "Primary lead vertical · ship today",
        "summary": "No AI-specific licensing. FMCSA regulates brokers, not software providers. Position JADE as a tool for licensed brokers.",
        "gates": [],
        "tos_must_have": [
            "Clear 'JADE OS is software for licensed brokers; we do not act as a broker' clause",
            "Indemnification clause covering bad-match liability",
            "Recommend operators carry E&O insurance ($2-5k/year)",
        ],
        "estimated_market_size_msp": "~180 brokerages in MSP-region",
        "ready_to_sell": True,
    },
    {
        "id": "logistics",
        "label": "Logistics / 3PL",
        "status": "go_now",
        "color": "#ccff00",
        "headline": "Adjacent to freight · ship today",
        "summary": "Same regulatory footprint as freight brokerage. Operators care about uptime + extraction accuracy.",
        "gates": [],
        "tos_must_have": [
            "SLA carve-outs for shipment data accuracy (we extract, you verify)",
        ],
        "estimated_market_size_msp": "~240 logistics ops in MSP-region",
        "ready_to_sell": True,
    },
    {
        "id": "manufacturing",
        "label": "Manufacturing",
        "status": "go_now",
        "color": "#ccff00",
        "headline": "Open territory · ship today",
        "summary": "No federal AI compliance for PO/work-order extraction. Customers may want SOC 2 for ERP-adjacent integrations — flag it during negotiation.",
        "gates": [],
        "tos_must_have": [
            "Disclosure that extraction is AI-generated; human review recommended on high-value POs",
        ],
        "estimated_market_size_msp": "~310 mfg shops in MSP-region",
        "ready_to_sell": True,
    },
    {
        "id": "ecommerce",
        "label": "E-commerce",
        "status": "go_now",
        "color": "#ccff00",
        "headline": "Open territory · ship today",
        "summary": "Order processing, return triage, support ticket routing — no special compliance.",
        "gates": [],
        "tos_must_have": [
            "Standard data-handling clause (CCPA-ready if any CA customers)",
        ],
        "estimated_market_size_msp": "~410 ecom shops in MSP-region",
        "ready_to_sell": True,
    },
    {
        "id": "real_estate",
        "label": "Real Estate",
        "status": "go_now",
        "color": "#ccff00",
        "headline": "Property management · ship today",
        "summary": "Property mgmt / leasing workflows. Title companies + closing agents are separately regulated — they handle their compliance, you provide the tool.",
        "gates": [],
        "tos_must_have": [
            "Explicit carve-out: 'JADE OS does not provide legal advice on real-estate transactions; closing-agent functions remain with licensed professionals.'",
        ],
        "estimated_market_size_msp": "~150 mgmt firms in MSP-region",
        "ready_to_sell": True,
    },
    {
        "id": "professional_services",
        "label": "Professional Services",
        "status": "go_now",
        "color": "#ccff00",
        "headline": "Agencies, consultancies · ship today",
        "summary": "Client intake, proposal generation, outreach — no special compliance gate.",
        "gates": [],
        "tos_must_have": [],
        "estimated_market_size_msp": "~520 firms in MSP-region",
        "ready_to_sell": True,
    },
    {
        "id": "saas",
        "label": "SaaS · SMB tier",
        "status": "go_now",
        "color": "#ccff00",
        "headline": "Sub-enterprise SaaS · ship today",
        "summary": "SMB-tier SaaS companies under ~50 employees rarely require SOC 2 Type II. Position to teams, not procurement.",
        "gates": [],
        "tos_must_have": [
            "Disclosure of AI use in customer-facing automations",
        ],
        "estimated_market_size_msp": "~290 SaaS startups in MSP-region",
        "ready_to_sell": True,
        "expansion_path": "→ requires SOC 2 Type II to move upmarket to mid-market and enterprise SaaS buyers",
    },
    {
        "id": "general",
        "label": "General Ops",
        "status": "go_now",
        "color": "#ccff00",
        "headline": "Universal fallback · ship today",
        "summary": "Default profile for any vertical not above. Mostly small-business co-pilot use.",
        "gates": [],
        "tos_must_have": [],
        "estimated_market_size_msp": "—",
        "ready_to_sell": True,
    },
    # ---- GATED -----------------------------------------------------------
    {
        "id": "legal",
        "label": "Legal / Contracts",
        "status": "go_with_tos",
        "color": "#ffce4f",
        "headline": "Ship with strict ToS guardrails · today",
        "summary": "Minnesota prohibits unauthorized practice of law (UPL). JADE can EXTRACT and ORGANIZE legal docs but cannot ADVISE on legal strategy. Set this boundary in the product copy and the contract.",
        "gates": [
            {"label": "ToS with explicit UPL carve-out", "status": "required", "cost_est": "$1-2k legal review"},
        ],
        "tos_must_have": [
            "'JADE OS extracts and organizes documents. It does not provide legal advice or constitute the practice of law.'",
            "'Customer remains responsible for legal interpretation and decisions.'",
            "Indemnification carve-out for legal-strategy outputs",
        ],
        "estimated_market_size_msp": "~280 firms in MSP-region (small-firm focused)",
        "ready_to_sell": True,
    },
    {
        "id": "insurance",
        "label": "Insurance · Brokerage tier",
        "status": "go_with_tos",
        "color": "#ffce4f",
        "headline": "Brokerage / agency tier · ship with disclosure",
        "summary": "MN Dept of Commerce regulates insurance carriers + brokers — not their software vendors. Small brokerages are fine. Carriers + national underwriters WILL ask for SOC 2 Type II.",
        "gates": [
            {"label": "AI-decision disclosure clause in ToS", "status": "required", "cost_est": "$1k"},
        ],
        "tos_must_have": [
            "'This system uses AI agents to automate workflows; a human can review and override any automated decision.'",
            "Audit trail of every claim / policy decision the agent makes",
        ],
        "estimated_market_size_msp": "~190 brokerages in MSP-region",
        "ready_to_sell": True,
        "expansion_path": "→ requires SOC 2 Type II to sell to carriers / national underwriters",
    },
    {
        "id": "healthcare",
        "label": "Healthcare",
        "status": "blocked",
        "color": "#ff3b8a",
        "headline": "BLOCKED · HIPAA + MN § 144 required",
        "summary": "Touching PHI (Protected Health Information) makes JADE a Business Associate under federal HIPAA law. Non-negotiable. Add MN Stat. § 144.291–295 for in-state customers. ESTIMATED $15-30k upfront + annual audits.",
        "gates": [
            {"label": "HIPAA Business Associate Agreement (BAA) framework", "status": "blocking", "cost_est": "$5-10k legal"},
            {"label": "Encryption + audit-log architecture", "status": "blocking", "cost_est": "$3-8k engineering"},
            {"label": "Breach notification protocol", "status": "blocking", "cost_est": "$1-2k legal"},
            {"label": "MN § 144 data retention + consent policies", "status": "blocking", "cost_est": "$2-3k legal"},
            {"label": "Annual third-party HIPAA audit", "status": "blocking", "cost_est": "$5-10k/year"},
        ],
        "tos_must_have": [
            "Currently we DO NOT ACCEPT PHI. Make this explicit in the demo + intake.",
            "PHI redaction at the extraction layer is ALREADY ON for healthcare profile — keep it on.",
        ],
        "estimated_market_size_msp": "~620 healthcare ops in MSP-region",
        "ready_to_sell": False,
        "unlock_path": "Engage a HIPAA consultant + design BAA architecture → 3-4 months → unlocks the single largest MSP-area vertical",
    },
    {
        "id": "saas_enterprise",
        "label": "SaaS · Mid-market + Enterprise",
        "status": "blocked",
        "color": "#ff3b8a",
        "headline": "BLOCKED · SOC 2 Type II required",
        "summary": "Fortune 500 + mid-market procurement teams universally require SOC 2 Type II before signing. Takes 6 months, costs $8-15k. Run it in parallel with selling to SMB SaaS now.",
        "gates": [
            {"label": "SOC 2 Type II audit (6-month observation window)", "status": "blocking", "cost_est": "$8-15k upfront + $3-5k/year"},
        ],
        "tos_must_have": [],
        "estimated_market_size_msp": "Massive — every enterprise SaaS HQ in Twin Cities",
        "ready_to_sell": False,
        "unlock_path": "Start the audit NOW (it runs in parallel with product work). Achieve cert in month 6.",
    },
    {
        "id": "finance",
        "label": "Finance / Banking",
        "status": "blocked",
        "color": "#ff3b8a",
        "headline": "BLOCKED · SOC 2 Type II + sector-specific controls",
        "summary": "Banks + fintechs require SOC 2 Type II minimum. Many additionally require PCI-DSS, SOX, GLBA controls depending on data touched.",
        "gates": [
            {"label": "SOC 2 Type II", "status": "blocking", "cost_est": "$8-15k"},
            {"label": "GLBA / PCI controls if touching payment / account data", "status": "blocking", "cost_est": "$10-25k"},
        ],
        "tos_must_have": [],
        "estimated_market_size_msp": "Large but gated · 9 major banks HQ'd MSP",
        "ready_to_sell": False,
        "unlock_path": "Tackle after SOC 2 cert. Skip unless a specific lead pulls you in.",
    },
    {
        "id": "hr",
        "label": "HR / Hiring",
        "status": "go_with_tos",
        "color": "#ffce4f",
        "headline": "Ship with bias-audit caveat",
        "summary": "If JADE screens resumes or candidates, EEOC requires a bias-audit report. Not a license but a disclosure obligation. Document the audit + log every screening decision.",
        "gates": [
            {"label": "Bias-audit report on resume/candidate screening", "status": "required", "cost_est": "$2-4k consultant"},
        ],
        "tos_must_have": [
            "Disclosure that AI is used in screening; candidates can request human review",
            "Equal-employment-opportunity compliance language",
        ],
        "estimated_market_size_msp": "~360 mid-market employers in MSP-region",
        "ready_to_sell": True,
    },
]


UNIVERSAL_REQUIREMENTS: List[Dict] = [
    {
        "id": "privacy_policy",
        "label": "Privacy Policy",
        "status": "required",
        "priority": "P0",
        "cost_est": "$1-3k legal review",
        "effort_weeks": 1,
        "purpose": "Clear language on data retention, deletion, customer-data handling. Required for every B2B contract.",
    },
    {
        "id": "terms_of_service",
        "label": "Terms of Service",
        "status": "required",
        "priority": "P0",
        "cost_est": "$1-2k legal review",
        "effort_weeks": 1,
        "purpose": "Limitation of liability, indemnification, AI-output disclaimer.",
    },
    {
        "id": "dpa",
        "label": "Data Processing Agreement (DPA)",
        "status": "required",
        "priority": "P0",
        "cost_est": "$1-2k legal review",
        "effort_weeks": 1,
        "purpose": "CCPA + MN data-privacy compliant. Customers will append it to their MSA.",
    },
    {
        "id": "ai_disclosure",
        "label": "AI-Use Disclosure Clause",
        "status": "required",
        "priority": "P0",
        "cost_est": "Included in ToS",
        "effort_weeks": 0,
        "purpose": "'This system uses AI agents; a human can review and override decisions.' Growing state-by-state norm.",
    },
    {
        "id": "soc2",
        "label": "SOC 2 Type II Audit",
        "status": "milestone",
        "priority": "P1",
        "cost_est": "$8-15k upfront + $3-5k/year",
        "effort_weeks": 26,
        "purpose": "Gold standard for SaaS. Unlocks enterprise SaaS, finance, mid-market insurance, and most procurement-led deals.",
    },
    {
        "id": "eo_insurance",
        "label": "E&O Insurance",
        "status": "required",
        "priority": "P0",
        "cost_est": "$2-5k/year premium",
        "effort_weeks": 1,
        "purpose": "Liability cover for AI-output errors. Required for freight brokerage indemnification clauses.",
    },
]


ROADMAP: List[Dict] = [
    {
        "month": "1-2",
        "label": "Month 1-2 · LEGAL FOUNDATION",
        "color": "#ccff00",
        "actions": [
            "Engage lawyer · draft SOC 2-ready Privacy Policy + ToS + DPA ($3-5k)",
            "Add AI-disclosure clause to every contract template",
            "Purchase E&O insurance ($2-5k/year)",
            "Start SOC 2 Type II audit observation period (runs parallel)",
        ],
        "unlocks": [
            "All 8 'go_now' verticals fully sellable",
            "Legal + Insurance brokerage (small-tier) sellable with proper ToS",
            "HR sellable with bias-audit caveat",
        ],
    },
    {
        "month": "3-4",
        "label": "Month 3-4 · HEALTHCARE PREP (optional)",
        "color": "#7c5cff",
        "actions": [
            "ONLY if healthcare is a priority vertical",
            "Engage HIPAA compliance consultant (~$5k)",
            "Design BAA framework + breach notification protocol",
            "Implement encryption-at-rest + audit logging architecture",
            "Add MN § 144 retention + consent policies",
        ],
        "unlocks": [
            "Healthcare vertical (~620 ops in MSP-region) unlocks for sale",
        ],
    },
    {
        "month": "6",
        "label": "Month 6 · SOC 2 TYPE II CERT ACHIEVED",
        "color": "#00ffff",
        "actions": [
            "Final SOC 2 audit; receive certification",
            "Update pitch deck + sales materials with SOC 2 badge",
            "Re-engage enterprise leads that asked for it",
        ],
        "unlocks": [
            "Mid-market + Enterprise SaaS verticals fully sellable",
            "Insurance carriers + national underwriters sellable",
            "Mid-market finance prospects sellable (with sector-specific add-ons as needed)",
        ],
    },
    {
        "month": "8+",
        "label": "Month 8+ · MULTI-VERTICAL EXPANSION",
        "color": "#ff3b8a",
        "actions": [
            "Confirm unit economics of healthcare or finance pilots",
            "Stack additional sector-specific controls only when a deal pulls you in",
            "Annual SOC 2 renewal · HIPAA audit cycle if applicable",
        ],
        "unlocks": [
            "Full vertical coverage · 11+ industries · enterprise + SMB tiers",
        ],
    },
]


def build_compliance() -> Dict:
    by_status = {"go_now": [], "go_with_tos": [], "blocked": []}
    for ind in INDUSTRIES:
        by_status[ind["status"]].append(ind)

    return {
        "name": "JADE OS · Route to Full Compliance",
        "subtitle": "Sell what you can sell today. Build the rest in parallel.",
        "summary": {
            "total_industries": len(INDUSTRIES),
            "go_now": len(by_status["go_now"]),
            "go_with_tos": len(by_status["go_with_tos"]),
            "blocked": len(by_status["blocked"]),
        },
        "industries_by_status": by_status,
        "industries": INDUSTRIES,
        "universal_requirements": UNIVERSAL_REQUIREMENTS,
        "roadmap": ROADMAP,
        "headline_principles": [
            "Sell to the green-light verticals THIS WEEK. Don't wait on SOC 2.",
            "Start the SOC 2 audit in parallel with selling — it runs 6 months on its own clock.",
            "Healthcare is the biggest single MSP vertical but the most expensive gate ($15-30k + ongoing). Only chase it if a specific prospect signals high intent.",
            "Every contract gets the AI-disclosure clause. Every contract.",
            "Indemnification + E&O insurance are non-negotiable for freight + logistics — your largest near-term verticals.",
        ],
    }
