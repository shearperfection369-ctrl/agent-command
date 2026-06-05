"""JADE OS · Operations · Lighthouse program operating system.

Codifies the 5-client lighthouse plan as structured operating data:
  • Team roster + monthly burn
  • Infrastructure cost matrix
  • SLA tiers (P1/P2/P3)
  • 5-phase onboarding playbook (2-3 weeks/client)
  • Roadmap prioritization matrix
  • Year-1 financial model
  • 12-month milestone timeline

Pure-data module. Per-client ticket CRUD lives in server.py via the
`pilot_tickets` collection (see /api/admin/pilot-tickets/*).
"""
from typing import Dict, List


TEAM_ROSTER: List[Dict] = [
    {
        "id": "ceo",
        "role": "Founder / CEO",
        "name_or_status": "Oliver Cummins",
        "fte": 1.0,
        "monthly_cost": 0,  # founder takes equity not salary in lighthouse phase
        "weekly_hours": 40,
        "responsibilities": [
            "Design-partner onboarding & iteration (8-10 hrs/week)",
            "Strategic customer conversations & roadmap input (5-8 hrs/week)",
            "Sales / biz-dev to next 3-5 customers (10-15 hrs/week)",
            "Crisis management when something breaks (variable on-call)",
        ],
        "status": "active",
    },
    {
        "id": "cs_lead",
        "role": "Head of Customer Success / Ops",
        "name_or_status": "TBD · contractor first, FTE post-customer-5",
        "fte": 1.0,
        "monthly_cost": 3500,  # contractor rate
        "monthly_cost_fte": 6250,  # $75k salary fully-loaded
        "weekly_hours": 40,
        "responsibilities": [
            "Daily standup with each client (30min × 5 = 2.5 hrs/day)",
            "Monitoring agent performance + tuning workflows (10-15 hrs/week)",
            "Quarterly business reviews + ROI tracking + expansion conversations (5 hrs/week)",
            "Primary escalation point for issues",
        ],
        "status": "needed_by_month_3",
        "criticality": "Without this person, founder is personally handling every support ticket and will burn out by month 4.",
    },
    {
        "id": "engineer",
        "role": "Engineer / Technical Lead",
        "name_or_status": "TBD · contractor first, FTE post-customer-3",
        "fte": 1.0,
        "monthly_cost": 6000,  # contractor rate
        "monthly_cost_fte": 10000,  # $120k salary fully-loaded
        "weekly_hours": 40,
        "responsibilities": [
            "Debug integration issues (API failures, rate limits, TMS sync bugs)",
            "Ship bug fixes / hotfixes within 24 hours of escalation",
            "Monitor infrastructure (uptime, latency, error rates)",
            "Build client-specific customizations (each of 5 will want something different)",
        ],
        "status": "needed_by_month_2",
        "criticality": "Founder cannot do this while also fundraising + selling. An engineer buys time.",
    },
    {
        "id": "qa",
        "role": "Part-time QA / Testing",
        "name_or_status": "TBD · contractor only",
        "fte": 0.5,
        "monthly_cost": 1750,
        "monthly_cost_fte": 2500,
        "weekly_hours": 20,
        "responsibilities": [
            "Test new agent workflows before production rollout",
            "Regression testing on every deploy",
            "Document edge cases clients discover",
        ],
        "status": "needed_by_month_4",
        "criticality": "Catches regressions before they hit a paying customer. $1.7k/mo insurance against a churned client.",
    },
]


INFRASTRUCTURE_COSTS: List[Dict] = [
    {"id": "llm", "category": "LLM API (Claude / GPT-5.2 via Universal Key)", "monthly_low": 750, "monthly_high": 3500, "per_client_scale": True, "notes": "500-1000 agent executions/client/day. $0.10-0.50/execution. Universal Key budget cap is the operating constraint."},
    {"id": "infra", "category": "Infrastructure (compute, DB, monitoring, logging)", "monthly_low": 500, "monthly_high": 1500, "per_client_scale": True, "notes": "Currently Emergent-hosted. Migrate to AWS / Mongo Atlas at customer #25."},
    {"id": "tms_apis", "category": "Third-party APIs (TMS integrations, carrier feeds)", "monthly_low": 400, "monthly_high": 900, "per_client_scale": True, "notes": "Macropoint ~$200-500/mo, FMCSA/IFTA lookup ~$200-400/mo. Pass through to customer above $X threshold."},
    {"id": "monitoring", "category": "Monitoring + security (Sentry, Datadog, scanning)", "monthly_low": 200, "monthly_high": 400, "per_client_scale": False, "notes": "Fixed baseline. Sentry scaffolded; drop DSN to activate. Datadog deferred to customer #25."},
    {"id": "communication", "category": "Twilio + Resend (SMS + email)", "monthly_low": 100, "monthly_high": 500, "per_client_scale": True, "notes": "Twilio already wired; Resend scaffolded waiting for key. Pass through to client above 5k msgs/mo."},
]


SLA_TIERS: List[Dict] = [
    {
        "priority": "P1",
        "label": "P1 · BLOCKER",
        "color": "#ff3b8a",
        "definition": "Agent down · data loss · customer-facing system unusable",
        "response_target_hours": 2,
        "fix_target_hours": 4,
        "examples": ["Agent returning 500 on every request", "Webhook posting wrong data to customer's TMS", "Auth completely broken"],
        "penalty_if_missed": "Customer credit · 5% of monthly fee per missed hour past target",
    },
    {
        "priority": "P2",
        "label": "P2 · DEGRADED",
        "color": "#ffce4f",
        "definition": "Degraded performance · wrong output on subset of cases · workaround exists",
        "response_target_hours": 8,
        "fix_target_hours": 24,
        "examples": ["Carrier match returning fewer than 4 results", "BOL extraction accuracy dropping below 90% for one customer", "Slack notification delays"],
        "penalty_if_missed": "Customer credit · 2% of monthly fee per missed day past target",
    },
    {
        "priority": "P3",
        "label": "P3 · ENHANCEMENT",
        "color": "#7c5cff",
        "definition": "Feature request · nice-to-have · no production impact",
        "response_target_hours": 48,
        "fix_target_hours": "next sprint",
        "examples": ["Add reefer auto-quote rate multiplier", "New TMS field mapping", "UI copy tweaks"],
        "penalty_if_missed": "None · communicate timing honestly",
    },
]


ONBOARDING_PLAYBOOK: List[Dict] = [
    {
        "phase": 1,
        "label": "WEEK 0 · CONTRACT + DATA",
        "color": "#7c5cff",
        "duration_days": 5,
        "owner": "CEO + Client",
        "tasks": [
            "Sign Lighthouse pilot agreement (ToS · DPA · AI-disclosure · E&O cap)",
            "Schedule 30-min kickoff with operator decision-maker",
            "Collect data drops: 90d rate confirmations · carrier directory CSV · 50 sample BOLs · 25 shipper inquiries",
            "Confirm hardware + software meets minimum bar (PARTNER PACKAGE tab → requirements)",
            "Identify primary integration target (TMS API or email-first)",
        ],
        "exit_criteria": "Contract signed · data drops received · TMS confirmed",
    },
    {
        "phase": 2,
        "label": "WEEK 1 · INTEGRATION + TRAINING",
        "color": "#00ffff",
        "duration_days": 7,
        "owner": "Engineer + CS Lead",
        "tasks": [
            "Connect OAuth (Outlook / Gmail) + TMS API (or CSV bridge)",
            "Load carrier directory + sample BOLs into customer's tenant",
            "Tune freight schema corrections from sample data (24-48 hrs)",
            "2-3 hour training session with ops team",
            "Capture baseline metrics: before/after labor time · quote volume · conversion rate",
        ],
        "exit_criteria": "OAuth + TMS connected · baseline captured · ops team trained",
    },
    {
        "phase": 3,
        "label": "WEEK 2 · SUPERVISED RUN",
        "color": "#ffce4f",
        "duration_days": 7,
        "owner": "CS Lead",
        "tasks": [
            "Agent runs against TODAY's inbox under broker supervision · every output reviewed",
            "Daily 30-min standup · capture every false-positive / wrong-match",
            "Tune schemas / prompts to address corrections by EOD each day",
            "First customer-side weekly performance review · hrs saved · quotes generated · exceptions caught",
        ],
        "exit_criteria": "<5% correction rate on agent outputs · customer signoff on go-live",
    },
    {
        "phase": 4,
        "label": "WEEK 3 · GO LIVE + MONITORING",
        "color": "#ccff00",
        "duration_days": 7,
        "owner": "CS Lead + Engineer on-call",
        "tasks": [
            "Agent runs unsupervised on cleared workflows",
            "Engineer monitors error rates · alerts wired to Slack",
            "Daily standup continues · 30 min",
            "First 30-day ROI snapshot collected: hours saved · conversion lift · $-savings estimate",
        ],
        "exit_criteria": "Agent runs unsupervised for 5 consecutive business days · zero P1 incidents",
    },
    {
        "phase": 5,
        "label": "MONTH 2-6 · STEADY STATE + QBR",
        "color": "#ff3b8a",
        "duration_days": 150,
        "owner": "CS Lead",
        "tasks": [
            "Bi-weekly performance review · move from daily to weekly standup at week 6",
            "Monthly ROI deck · share publishable proof points with broker",
            "Quarterly business review · show expansion opportunities (new workflows / teams)",
            "Co-author case study around month 4-5 for the BIG BANG CONVERT phase",
            "Renewal conversation at month 5",
        ],
        "exit_criteria": "Pilot → annual contract signed at month 6 · OR honest no-renewal w/ written learnings",
    },
]


ROADMAP_PRIORITIZATION: Dict = {
    "build_now": {
        "rule": "Does this request benefit 2+ clients? → Build it.",
        "color": "#ccff00",
        "examples": ["Slack alerts on high-priority loads", "Standard QuickBooks export", "Configurable tone profiles"],
    },
    "expand_revenue": {
        "rule": "Does this unlock $5k+ in expansion revenue? → Build it.",
        "color": "#00ffff",
        "examples": ["BI dashboard API for Client A", "Auto load-board posting for Client E"],
    },
    "backlog": {
        "rule": "Is it a 1-off nice-to-have? → Backlog, revisit at customer #10.",
        "color": "#7c5cff",
        "examples": ["Custom UI theming", "Niche carrier integrations", "Single-customer reporting formats"],
    },
    "reject": {
        "rule": "Does this require breaking another customer? → Decline politely with explanation.",
        "color": "#ff3b8a",
        "examples": ["Disabling PHI redaction", "Removing AI-disclosure clause", "Custom auth bypass"],
    },
    "engineer_time_allocation": "Expect 30-40% of engineer time to go to client-specific work. Other 60-70% on core product (bug fixes, performance, new agents).",
}


YEAR_1_FINANCIAL_MODEL: Dict = {
    "annual_costs": [
        {"item": "Team (CEO + CS Lead + Engineer + QA)", "low": 100000, "high": 144000, "notes": "Partially founder equity, partially contractor rates"},
        {"item": "Infrastructure (LLM + compute + APIs + monitoring)", "low": 22000, "high": 76000, "notes": "Scales with customer count"},
        {"item": "Legal / Compliance (SOC 2 audit, DPA, BAA prep)", "low": 20000, "high": 25000, "notes": "$20k upfront, $5k annual renewal"},
        {"item": "Hosting, domains, dev tooling", "low": 2000, "high": 3000, "notes": "Stable"},
        {"item": "E&O Insurance (SaaS liability)", "low": 3000, "high": 5000, "notes": "Required for freight indemnification"},
        {"item": "Operations contingency", "low": 10000, "high": 15000, "notes": "Things break. You ship fixes fast. This is the war chest."},
    ],
    "annual_revenue": [
        {"item": "5 clients × $3,500 MRR", "low": 210000, "high": 210000},
        {"item": "Expansion (1-2 upgrade to $5k MRR)", "low": 12000, "high": 24000},
    ],
    "summary": {
        "total_cost_low": 157000,
        "total_cost_high": 268000,
        "total_revenue_low": 222000,
        "total_revenue_high": 234000,
        "gross_margin_low_pct": 0,
        "gross_margin_high_pct": 23,
        "verdict": "Year 1 is break-even to lightly profitable. This is NORMAL for lighthouse customers — they're getting white-glove service.",
        "compounding_unlock": "By customer #10: warm inbound + standardized workflows + reduced support load → margin flips to 40-50%.",
    },
}


MILESTONES: List[Dict] = [
    {"month": "1-2", "label": "FOUNDATION", "color": "#7c5cff", "items": [
        "Hire or contract CS Lead (or you wear this hat initially)",
        "Hire or contract Engineer",
        "Define onboarding, monitoring, escalation playbooks (THIS TAB)",
        "Top up Universal LLM Key budget to $750+ for 5 pilots",
        "Wire Resend + Sentry keys",
    ]},
    {"month": "3-4", "label": "FIRST PILOT LIVE", "color": "#00ffff", "items": [
        "Launch Client 1 (warmest design partner from your network)",
        "Iterate heavily for 2-3 weeks — expect 'agent isn't matching correctly' + 'TMS sync dropping data'",
        "Ship first set of bug fixes + customizations",
        "Capture first ROI receipts at day 30",
    ]},
    {"month": "5-6", "label": "SECOND PILOT + STEADY STATE", "color": "#ccff00", "items": [
        "Launch Client 2 (referral or 2nd design partner)",
        "Client 1 moves to steady state · CS Lead owns daily health",
        "Engineer splits time: 50% supporting both clients · 50% core product",
        "First case study published from Client 1",
    ]},
    {"month": "7-9", "label": "PILOTS 3-5 + HIGH TOUCH", "color": "#ffce4f", "items": [
        "Launch Clients 3, 4, 5 (one per month)",
        "High-touch mode: flying to offices · training · sitting in on ops calls",
        "Engineer at capacity · evaluate hiring a second engineer or contract dev",
        "SOC 2 Type II audit mid-cycle observation period",
    ]},
    {"month": "10-12", "label": "REFERRAL FLYWHEEL + RENEWAL", "color": "#ff3b8a", "items": [
        "Clients 1-3 in steady state · case studies + ROI data published",
        "Selling Clients 6-8 from Client 1-3 referrals · CAC drops 60%+",
        "SOC 2 Type II achieved · enterprise SaaS / mid-market insurance unlocks",
        "Pilot → annual contract renewals at month 6+ for first cohort",
    ]},
]


def build_operations() -> Dict:
    team_monthly_burn_low = sum(t.get("monthly_cost", 0) for t in TEAM_ROSTER)
    team_monthly_burn_high = sum(t.get("monthly_cost_fte", t.get("monthly_cost", 0)) for t in TEAM_ROSTER)
    infra_low = sum(c["monthly_low"] for c in INFRASTRUCTURE_COSTS)
    infra_high = sum(c["monthly_high"] for c in INFRASTRUCTURE_COSTS)
    return {
        "name": "JADE OS · Operations · Lighthouse Program Operating System",
        "subtitle": "5 clients · $17.5k MRR target · the operating tooling to ship without burning out.",
        "team": TEAM_ROSTER,
        "team_burn": {
            "monthly_contractor_floor": team_monthly_burn_low,
            "monthly_fte_ceiling": team_monthly_burn_high,
            "annualized_contractor": team_monthly_burn_low * 12,
            "annualized_fte": team_monthly_burn_high * 12,
        },
        "infrastructure": INFRASTRUCTURE_COSTS,
        "infrastructure_burn": {
            "monthly_low": infra_low,
            "monthly_high": infra_high,
            "annualized_low": infra_low * 12,
            "annualized_high": infra_high * 12,
            "per_client_5_low": infra_low,
            "per_client_5_high": infra_high,
        },
        "sla_tiers": SLA_TIERS,
        "onboarding_playbook": ONBOARDING_PLAYBOOK,
        "roadmap_prioritization": ROADMAP_PRIORITIZATION,
        "year_1_financial_model": YEAR_1_FINANCIAL_MODEL,
        "milestones": MILESTONES,
        "operating_principles": [
            "Your 5 lighthouse clients are NOT supposed to be profitable. They're proof.",
            "By customer #10, unit economics flip. Stay disciplined until then.",
            "Engineer time: 30-40% client-specific · 60-70% core product. Enforce this ratio.",
            "Every customer credit issued under SLA is a future-renewal investment. Pay it without hesitation.",
            "Onboarding = white-glove. Steady-state = data-driven. Renewal = case-study-led.",
        ],
    }
