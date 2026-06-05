"""JADE OS · Competitive Moat — the operator's positioning weapon.

The six structural advantages we have over HubSpot / ServiceTitan / Big Four
wrappers, plus the five highest-ROI workflows we built around them, plus the
ready-to-paste pitch language.

Pure data. The frontend renders this as the admin COMPETITIVE EDGE tab and the
public marketing pages can pull slices.
"""
from typing import Dict, List


MOATS: List[Dict] = [
    {
        "id": "vertical_workflows",
        "rank": 1,
        "title": "Vertical-specific workflow automation",
        "color": "#ccff00",
        "competitor_does": "HubSpot / ServiceTitan wrap a generic AI copilot. 'Summarize this ticket.' 'Draft a response.' Useful, shallow, domain-blind.",
        "jade_does": "JADE knows the shape of freight. Load board semantics. DOT regs. HOS rules. Hazmat. Carrier capacity. Shipper negotiation patterns. Lives in this world.",
        "concrete_example": "Shipper asks: '18k lbs machinery, Chicago to Memphis, 3 days, REEFER, budget $1,200.' Generic AI: 'Draft a response asking for more details.' JADE: flags reefer + 18k = reefer van not dry, checks HOS feasibility on the timeline, calculates that $1,200 is below market for that lane (real # ~$1,650-1,900), surfaces 4 carriers with capacity + lane history, drafts the response with realistic counter-quote, sets 4-hour follow-up reminder if shipper goes silent. 45 seconds vs 15 minutes.",
        "why_competitor_cant": "A generic platform can't do this without becoming a freight-specific app. Doing so defeats the genericness that makes it sellable to 50 other verticals.",
    },
    {
        "id": "integration_depth",
        "rank": 2,
        "title": "Integration depth — we layer, they replace",
        "color": "#00ffff",
        "competitor_does": "Big Four says 'rip out your TMS, use ours.' 4-month implementation. $50-100k consulting bill.",
        "jade_does": "JADE reads from your existing TMS / CRM / accounting / Excel sheet. Enriches data. Makes decisions. Writes back confirmations, quotes, exception flags. Your workflow doesn't change — your tools just get smarter.",
        "concrete_example": "Customer keeps McLeod LoadMaster. JADE connects via read-only API + draft-write scope. Broker still works in McLeod. JADE handles 87% of the work invisibly inside it.",
        "why_competitor_cant": "HubSpot wants to BE the hub. JADE is the invisible hand making their existing hub smarter. Lower friction = faster conversion = stickier product.",
    },
    {
        "id": "outcome_metrics",
        "rank": 3,
        "title": "Outcome-specific metrics — not activity metrics",
        "color": "#7c5cff",
        "competitor_does": "Measures: 'AI copilot generated 50 responses this week.'",
        "jade_does": "Measures: '$12k saved in ops labor · 6 hours/day exception handling cut · quote-to-load conversion +8%.' Revenue and margin — the only metrics that matter.",
        "concrete_example": "Pilot guarantee: 'Run JADE on your last 100 shipper inquiries. We'll show you how many quotes we'd auto-generate, how many carriers we'd match, how much labor we'd save. If less than 5 hours/week, first month free.'",
        "why_competitor_cant": "Generic platforms can't offer outcome guarantees because they don't know your ops well enough to commit to them.",
    },
    {
        "id": "speed_simplicity",
        "rank": 4,
        "title": "Speed + simplicity — 2 days, not 6 months",
        "color": "#ff3b8a",
        "competitor_does": "ServiceTitan / Big Four: 4-month implementation. $50-100k consulting engagement. Six-month software project.",
        "jade_does": "Connect TMS API + shipper email. Live in 2 days. $3,500/month flat. No consulting bill.",
        "concrete_example": "Day 1: connect Outlook OAuth + TMS API. Day 2: load your carrier directory + 30 sample BOLs. Day 3: agent runs against today's inbox under supervision. Week 2: agent runs unsupervised on the cleared cases.",
        "why_competitor_cant": "Big consultancies bill the engagement. JADE bills the result.",
    },
    {
        "id": "compliance_liability",
        "rank": 5,
        "title": "Industry-specific compliance + liability model",
        "color": "#ffce4f",
        "competitor_does": "HubSpot doesn't understand freight broker liability — they sell software, not domain insurance.",
        "jade_does": "Contractual: (1) rate-review guarantee — if JADE quotes below cost, we flag it. (2) Carrier vetting — only FMCSA-compliant carriers in the match pool. (3) Exception flagging — every regulatory / capacity concern surfaced; broker makes final call. (4) Liability cap with E&O insurance on file.",
        "concrete_example": "Pilot agreement includes a $1M E&O coverage statement and a specific carve-out: 'JADE provides software-only suggestions. Broker retains final decisioning authority on every quote, match, and confirmation.'",
        "why_competitor_cant": "A generic SaaS platform won't take on domain liability because they don't understand the domain risk.",
    },
    {
        "id": "founder_domain",
        "rank": 6,
        "title": "Founder domain expertise — operator-built",
        "color": "#ccff00",
        "competitor_does": "Big Four consultants and HubSpot PMs have never run a load. Sales reps reading scripts.",
        "jade_does": "Built by an operator who's lived the problem. Sat in the dispatch office. Knows what 2 AM shipper calls sound like. Knows why a carrier ghosted. That trust compresses the sales cycle by 2-3 months.",
        "concrete_example": "In every Lighthouse kickoff: 30-minute sit-down with the operator. No deck. Just 'tell me what your worst Tuesday looked like' — then JADE is configured to that exact pain by Friday.",
        "why_competitor_cant": "You can hire domain expertise. You can't fake it. Brokers can smell a script in 90 seconds.",
    },
]


HIGHEST_ROI_WORKFLOWS: List[Dict] = [
    {
        "id": "shipper_qualification",
        "rank": 1,
        "name": "Shipper Qualification",
        "what_it_does": "Inbound shipper inquiry → JADE extracts lane, commodity, weight, equipment, timeline, budget. Scores it Tier-1/2/3. Routes to the right broker.",
        "manual_time": "8-12 min/inquiry",
        "jade_time": "30 seconds",
        "hours_saved_week": 6,
        "revenue_lift_pct": "+4%",
        "endpoint": "/api/agent/qualify",
    },
    {
        "id": "carrier_matching",
        "rank": 2,
        "name": "Carrier Matching + Exception Flagging",
        "what_it_does": "Searches your carrier network, checks lane history, equipment match, HOS feasibility, rate band. Surfaces top-3 with fit-rationale + flagged exceptions (overweight, hazmat-no-cert, etc).",
        "manual_time": "10-15 min/load",
        "jade_time": "30 seconds",
        "hours_saved_week": 14,
        "revenue_lift_pct": "+6%",
        "endpoint": "/api/agent/freight/load-match",
    },
    {
        "id": "rate_comparison",
        "rank": 3,
        "name": "Rate Comparison + Quote Drafting",
        "what_it_does": "Pulls market rate for the lane, compares to shipper budget, flags below-cost quotes, drafts counter with rationale.",
        "manual_time": "12-18 min/quote",
        "jade_time": "45 seconds",
        "hours_saved_week": 8,
        "revenue_lift_pct": "+5% margin",
        "endpoint": "/api/agent/freight/shipper-comm",
    },
    {
        "id": "exception_flagging",
        "rank": 4,
        "name": "Exception Flagging + Follow-up",
        "what_it_does": "Hazmat / oversize / weight / equipment / driver-HOS issues surfaced on every load. Auto-sets follow-up timer if shipper or carrier goes silent.",
        "manual_time": "Hidden — usually caught too late",
        "jade_time": "Real-time",
        "hours_saved_week": 4,
        "revenue_lift_pct": "+3% (avoided fines)",
        "endpoint": "/api/agent/freight/load-match (in match payload)",
    },
    {
        "id": "carrier_outreach",
        "rank": 5,
        "name": "Carrier Outreach + Follow-up",
        "what_it_does": "Drafts SMS/email outreach to matched carriers. Tracks responses. Flags no-shows after 90 minutes. Escalates to backup tier.",
        "manual_time": "6-10 min/load (phone tag)",
        "jade_time": "20 seconds + auto-followup",
        "hours_saved_week": 12,
        "revenue_lift_pct": "+8% load coverage",
        "endpoint": "/api/agent/freight/carrier-outreach",
    },
]


COMPARISON_TABLE: List[Dict] = [
    {"dimension": "Time to first value", "hubspot": "4 weeks (setup + onboard)", "servicetitan": "8-12 weeks", "big_four": "4-6 months", "jade_os": "2 days"},
    {"dimension": "Implementation cost", "hubspot": "$5-15k", "servicetitan": "$15-30k", "big_four": "$50-100k", "jade_os": "$0"},
    {"dimension": "Monthly cost (mid-market)", "hubspot": "$3-8k", "servicetitan": "$5-12k", "big_four": "$8-25k", "jade_os": "$3k"},
    {"dimension": "Freight domain depth", "hubspot": "Generic AI", "servicetitan": "Field-service only", "big_four": "Bespoke per engagement", "jade_os": "Built for freight from day one"},
    {"dimension": "TMS integration", "hubspot": "Limited, generic", "servicetitan": "Their own only", "big_four": "Custom, billable", "jade_os": "Layers on McLeod/Aljex/Turvo/MercuryGate"},
    {"dimension": "Outcome guarantee", "hubspot": "None", "servicetitan": "None", "big_four": "None (you pay for the work)", "jade_os": "Refund month 1 if <4 hrs/week saved"},
    {"dimension": "Liability model", "hubspot": "SaaS — no domain liability", "servicetitan": "SaaS — no domain liability", "big_four": "Engagement-scoped only", "jade_os": "$1M E&O · rate-review guarantee · FMCSA carrier-vetting"},
    {"dimension": "Founder domain experience", "hubspot": "PMs · no freight ops", "servicetitan": "Field-service originator", "big_four": "Senior consultant turnover", "jade_os": "Operator-built · network in MSP"},
]


PITCH_LANGUAGE = {
    "elevator_30s": (
        "We've automated the 5 highest-ROI workflows in freight brokerage — shipper qualification, "
        "carrier matching, rate comparison, exception flagging, and follow-up scheduling. On average, "
        "brokers save 6-8 hours/week and lift quote-to-load conversion by 7-12%. We integrate with your "
        "existing TMS in 2 days. No implementation fee. $3,500/month. And if you don't see 4 hours/week "
        "of labor savings in the first 30 days, we refund the month."
    ),
    "cold_email_120w": (
        "Subject: 6 hours of your Tuesday back\n\n"
        "Hey {name} —\n\n"
        "I run JADE OS out of Minneapolis. We built an AI agent platform specifically for freight "
        "brokers — not the generic 'AI copilot' that wraps every other SaaS tool right now.\n\n"
        "On a benchmark MSP-area workload, we auto-triaged 184 shipper inquiries/day, surfaced top-3 "
        "carrier matches in 30 seconds (vs 10 minutes of TMS searching), and drafted comms that brokers "
        "sent without editing 84% of the time.\n\n"
        "We integrate with your existing TMS (McLeod, Aljex, Turvo, Mercury — or even a custom spreadsheet) "
        "in 2 days. No consulting bill. $3,500/month flat. If you don't see 4 hours/week saved in the "
        "first 30 days, the month is refunded.\n\n"
        "Worth a 20-minute walkthrough this week?\n\n"
        "— Oliver · onejades.com"
    ),
    "linkedin_inmail_4lines": (
        "{name} — built JADE OS for freight brokers in MSP. We layer on your existing TMS in 2 days, "
        "auto-handle 5 of the highest-ROI workflows (qualification, matching, rate compare, exceptions, "
        "follow-up). $3.5k/mo flat, refund if <4hrs/wk saved. 20-min walkthrough?"
    ),
    "objection_handlers": [
        {"objection": "We're already evaluating HubSpot / Salesforce for AI",
         "response": "HubSpot wraps a generic AI copilot. It doesn't know what a 53' reefer is, doesn't check HOS feasibility, doesn't flag if a quote's below market. JADE was built freight-first. We can run side-by-side on your last 50 inquiries — you'll see the depth gap inside an hour."},
        {"objection": "We don't have budget for new software",
         "response": "If JADE doesn't save you at least 4 hours/week in the first 30 days, the month is refunded. Worst case you lose nothing. Best case you reclaim 25-30 hours/month of broker time which at $55-75/hr fully loaded is $1,650-2,250 in labor on a $3,500 product."},
        {"objection": "How do we know your AI won't make a bad match?",
         "response": "Two answers. One — every match surfaces with a fit-rationale and exception flags. The broker always makes the final call. Two — we carry $1M E&O. If our matching causes a loss, we're indemnified. Generic platforms won't take on this liability because they don't understand the domain risk."},
        {"objection": "We tried freight AI tools before — they didn't work",
         "response": "What did they get wrong? — usually it was treating freight like a generic doc-extraction task. JADE was built around the exception logic, not the happy path. We can run JADE on the same data they failed on and show you the delta."},
        {"objection": "We need SOC 2 before we can sign",
         "response": "SOC 2 Type II audit window started — certification expected by Month 6. Until then we offer a SOC 2-ready pilot agreement with the same controls (encryption, audit logs, access reviews) without the cert. Most pilot customers find this acceptable for a 6-month Lighthouse pilot."},
    ],
}


def build_competitive_moat() -> Dict:
    return {
        "name": "JADE OS · Competitive Moat · Weapon Kit",
        "subtitle": "Six structural advantages. Five highest-ROI workflows. One pitch.",
        "moats": MOATS,
        "highest_roi_workflows": HIGHEST_ROI_WORKFLOWS,
        "comparison_table": COMPARISON_TABLE,
        "pitch_language": PITCH_LANGUAGE,
        "weaponization_principles": [
            "Lead with outcome, never with technology. '$12k saved' beats 'AI agent' every time.",
            "Show the depth gap in 90 seconds — pull up a real example and run it on JADE + screenshot of HubSpot's generic response.",
            "Sell the speed: 2 days to live vs 4 months. Brokers hate software projects.",
            "Anchor with the refund guarantee. It costs you nothing and disarms every budget objection.",
            "Lead with your story (operator-built) before you lead with the product. Domain credibility comes first.",
        ],
    }
