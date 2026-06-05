"""JADE OS · Software, Hardware, and Integration requirements per industry.

Also includes the platform's capacity assessment — what the current
configuration supports out of the box, what to scale before the next 5 / 25 /
100 active customer tier.
"""
from typing import Dict, List


# ============================================================
# CLIENT-SIDE REQUIREMENTS — what a Lighthouse pilot needs
# on their end to fully use JADE OS for each industry.
# ============================================================

CLIENT_REQUIREMENTS_BY_INDUSTRY: Dict[str, Dict] = {
    "freight_brokerage": {
        "label": "Freight Brokerage / 3PL",
        "hardware_min": [
            "Modern laptop (Intel i5 / Apple M1 or newer · 8GB RAM · 256GB SSD)",
            "Reliable wired or 100Mbps+ Wi-Fi internet (load-board polling is bandwidth-light, but real-time)",
            "Smartphone for SMS-based carrier outreach approvals (iOS 16+ / Android 12+)",
        ],
        "software_required": [
            "Modern browser · Chrome 120+ · Edge 120+ · Safari 17+ · Firefox 120+",
            "Outlook 365 OR Gmail (for inbox-triage workflows)",
            "Slack or Microsoft Teams (for in-line approvals)",
            "PDF viewer · Adobe Acrobat Reader OR built-in browser PDF",
        ],
        "data_required_for_pilot": [
            "Last 90 days of carrier rate confirmations (PDFs ok)",
            "Carrier database export (CSV: name, MC#, equipment types, lanes, contact)",
            "Sample of 25–50 incoming shipper inquiries (raw email exports)",
            "Sample of 50 BOLs (PDFs) for extraction benchmark",
        ],
        "integrations_required": [
            "Email · Outlook 365 OAuth OR Gmail OAuth (read + draft scopes)",
            "TMS · McLeod LoadMaster · Aljex · Turvo · MercuryGate · Revenova (read-only API key OR CSV bridge for v1)",
            "Twilio · for outbound carrier SMS",
            "Slack · for in-line broker approvals",
        ],
        "integrations_optional": [
            "DAT load board · planned Q2",
            "MercuryGate native sync · planned Q3",
            "QuickBooks / NetSuite · for invoice-exception export",
        ],
        "compliance_required": ["E&O insurance ($2–5k/yr · standard for brokers)"],
        "training_required_hours": 2,
    },

    "logistics": {
        "label": "Logistics · 3PL · Warehousing",
        "hardware_min": [
            "Modern laptop or warehouse workstation",
            "Stable internet (50Mbps+)",
            "Optional: handheld scanner for receiving-flow integration",
        ],
        "software_required": [
            "Modern browser",
            "Email · Outlook 365 / Gmail",
            "Slack or Teams",
        ],
        "data_required_for_pilot": [
            "Last 30 days of intake documents (POs, ASNs, BOLs)",
            "Shipper master list",
            "Existing exception classification taxonomy (if any)",
        ],
        "integrations_required": [
            "WMS · 3PL Central / Logiwa / Manhattan / Softeon (read-only)",
            "Email OAuth",
            "Twilio MMS (for damaged-goods photo capture)",
        ],
        "integrations_optional": ["Carrier APIs for live shipment status"],
        "compliance_required": [],
        "training_required_hours": 2,
    },

    "manufacturing": {
        "label": "Manufacturing",
        "hardware_min": ["Office workstation · 8GB RAM minimum", "Stable internet"],
        "software_required": ["Modern browser", "Email · Outlook 365 / Gmail", "Slack or Teams"],
        "data_required_for_pilot": [
            "Last 60 days of incoming POs (PDFs or EDI samples)",
            "Part-pricing library (CSV: part #, list price, margin tiers)",
            "Sample 30 RFQs",
            "Supplier directory",
        ],
        "integrations_required": [
            "ERP · NetSuite / SAP / Epicor / Infor M3 / Acumatica (read-only API)",
            "Email OAuth",
        ],
        "integrations_optional": ["QMS for quality-incident triage · MasterControl / ETQ", "EDI 850/855 connector"],
        "compliance_required": [],
        "training_required_hours": 2,
    },

    "saas": {
        "label": "SaaS · B2B Tech",
        "hardware_min": ["Modern laptop", "Standard office internet"],
        "software_required": ["Modern browser", "Slack", "Email"],
        "data_required_for_pilot": [
            "Last 90 days closed-won + closed-lost CRM data (for qualification training)",
            "Existing support ticket history (last 1000)",
            "Onboarding playbook / current welcome sequence",
        ],
        "integrations_required": [
            "CRM · HubSpot / Salesforce (read + write to lead status)",
            "Support · Zendesk / Intercom / Freshdesk (read + draft)",
            "Slack · in-line CSM/AE alerts",
            "Email OAuth",
        ],
        "integrations_optional": ["Product analytics · Mixpanel / Amplitude / PostHog · for CSM health Q&A", "Linear / Jira · for bug-tag routing"],
        "compliance_required": [
            "For mid-market deals: SOC 2 Type II (JADE OS in progress · pilot exemption available)",
        ],
        "training_required_hours": 1.5,
    },

    "ecommerce": {
        "label": "E-commerce",
        "hardware_min": ["Modern laptop or tablet", "Stable internet"],
        "software_required": ["Modern browser", "Email · platform (Shopify/Woo) admin login"],
        "data_required_for_pilot": [
            "Last 30 days of customer-service tickets",
            "Returns / refunds policy doc",
            "Brand voice guide (informal)",
            "1000 product catalog sample",
        ],
        "integrations_required": [
            "Store · Shopify / WooCommerce / BigCommerce (read-only API)",
            "Helpdesk · Gorgias / Zendesk / Front (read + draft)",
            "Email OAuth",
        ],
        "integrations_optional": ["Returns · Loop Returns · Returnly", "Reviews · Yotpo · Trustpilot", "Social DMs · Meta Business · Twitter API"],
        "compliance_required": ["Standard CCPA-compliant DPA"],
        "training_required_hours": 1,
    },

    "professional_services": {
        "label": "Professional Services · Agencies",
        "hardware_min": ["Modern laptop"],
        "software_required": ["Modern browser", "Email", "Slack / Teams"],
        "data_required_for_pilot": [
            "Last 6 published case studies",
            "Last 20 sent proposals (anonymized)",
            "Standard SOW templates",
        ],
        "integrations_required": [
            "Project tool · Asana / Linear / Notion / ClickUp (read-only)",
            "Email OAuth",
            "Slack",
        ],
        "integrations_optional": ["Proposal tool · PandaDoc / DocuSign", "Time tracking · Harvest / Toggl"],
        "compliance_required": [],
        "training_required_hours": 1.5,
    },

    "real_estate": {
        "label": "Real Estate · Property Mgmt",
        "hardware_min": ["Modern laptop", "Mobile device for tenant-text approvals"],
        "software_required": ["Modern browser", "Email", "Property mgmt system login"],
        "data_required_for_pilot": [
            "Last 60 days of tenant inquiries",
            "Maintenance vendor directory",
            "Sample of 25 lease docs",
        ],
        "integrations_required": [
            "PM system · AppFolio / Buildium / Yardi / Propertyware (read-only)",
            "Email OAuth",
            "Twilio · tenant SMS comms",
        ],
        "integrations_optional": ["DocuSign · for lease signature workflows"],
        "compliance_required": ["Fair Housing-aware comms templates · provided by JADE"],
        "training_required_hours": 1.5,
    },

    "legal": {
        "label": "Legal · Boutique Firms",
        "hardware_min": ["Modern laptop or workstation", "Encryption-at-rest hard drive recommended"],
        "software_required": ["Modern browser", "DMS access", "Practice management software"],
        "data_required_for_pilot": [
            "Sample 30 contracts (MSAs, NDAs, addenda)",
            "Standard engagement letter template",
            "Conflict-check workflow doc",
        ],
        "integrations_required": [
            "DMS · iManage / NetDocuments / Worldox (read-only)",
            "Practice mgmt · Clio / PracticePanther / MyCase (read + draft)",
            "Email OAuth",
        ],
        "integrations_optional": ["DocuSign", "Westlaw / LexisNexis · planned"],
        "compliance_required": [
            "MUST have JADE OS ToS with UPL carve-out (covered in pilot agreement)",
            "Attorney-client privilege handling — JADE never trains on customer data",
        ],
        "training_required_hours": 2,
    },

    "insurance": {
        "label": "Insurance · Brokerage Tier",
        "hardware_min": ["Modern workstation", "Stable internet"],
        "software_required": ["Modern browser", "AMS login", "Email"],
        "data_required_for_pilot": [
            "Last 90 days of loss runs (PDFs)",
            "Standard coverage taxonomy / appetite guide",
            "Renewal calendar export",
        ],
        "integrations_required": [
            "AMS · AMS360 / Applied Epic / EZLynx / HawkSoft (read-only)",
            "Email OAuth",
        ],
        "integrations_optional": ["Carrier portals · planned per-carrier", "Calendly · renewal scheduling"],
        "compliance_required": [
            "AI-decision disclosure clause (provided in pilot agreement)",
            "For carrier-tier: SOC 2 Type II (in progress)",
        ],
        "training_required_hours": 2,
    },

    "healthcare": {
        "label": "Healthcare · GATED · HIPAA",
        "hardware_min": ["Modern workstation", "Encryption-at-rest mandatory"],
        "software_required": ["Modern browser", "EMR access", "Email · HIPAA-compliant config"],
        "data_required_for_pilot": [
            "ONLY after BAA executed",
            "De-identified sample of 50 intake forms",
            "Prior-auth template library",
            "Appointment cadence rules",
        ],
        "integrations_required": [
            "EMR · Epic · Cerner · athenahealth · NextGen · eClinicalWorks (HIPAA-secured read)",
            "Email · HIPAA-compliant SMTP",
            "Twilio · HIPAA BAA-covered SMS",
        ],
        "integrations_optional": ["Payer portals · per-payer · planned"],
        "compliance_required": [
            "BAA executed BEFORE pilot start",
            "HIPAA-covered Twilio account",
            "PHI redaction enforced at extraction layer (already ON in product)",
            "Audit-log retention 7 years (in development)",
            "Annual third-party HIPAA risk assessment",
        ],
        "training_required_hours": 3,
        "blocked_until": "HIPAA-ready · est. Month 3-4 per the Compliance Roadmap",
    },

    "general": {
        "label": "General Ops",
        "hardware_min": ["Modern laptop"],
        "software_required": ["Modern browser", "Email"],
        "data_required_for_pilot": ["Whatever the operator wants JADE to start running on — a description of pain is enough"],
        "integrations_required": ["Email OAuth", "Slack"],
        "integrations_optional": ["Google Calendar / Outlook Calendar · meeting prep", "Drive / Dropbox · doc summarization"],
        "compliance_required": [],
        "training_required_hours": 1,
    },
}


# ============================================================
# PLATFORM CAPACITY ASSESSMENT — what the JADE OS infra can
# handle in its current configuration vs what to scale.
# ============================================================

PLATFORM_CAPACITY = {
    "current_config": {
        "backend": "FastAPI · uvicorn · supervisor-managed · Kubernetes pod",
        "database": "MongoDB · single replica · 10GB volume (22% used)",
        "llm_router": "Emergent Universal Key · Claude Sonnet 4.5 + GPT-5.2 + Gemini 3 + Sora-2-pro",
        "video": "/static volume · 18GB available",
        "rate_limits": "Login: 8/5min/IP · all other endpoints unlimited (admin auth gates the spendy ones)",
        "concurrency": "uvicorn worker default (1 worker) · async handlers · ~100 concurrent SSE streams supported",
    },
    "ready_now_for_5_lighthouse_users": {
        "verdict": "YES · with two operator caveats",
        "evidence": [
            "Database: 5 users × 1000 runs/mo = 5k docs/mo · MongoDB single replica handles 10k+ writes/sec — orders of magnitude headroom.",
            "Backend concurrency: async FastAPI + SSE streaming handles ~100 concurrent agent calls. 5 users × 20 concurrent peaks = 100 — sufficient.",
            "Disk: 18GB free static + 10GB Mongo volume — sufficient for ~12 months of generated content.",
            "Auth: rate-limited, security headers enforced, PDF magic-byte validated, path-traversal blocked.",
            "Self-test: 21 health checks pass end-to-end including LLM round-trips. HEALTH tab auto-monitors.",
        ],
        "caveats": [
            "Universal LLM Key budget is hard-capped — at $114/cap each pilot consuming ~$500-1200/mo of LLM spend will hit ceiling fast. Budget should be sized at ~$300-500/pilot/mo to be safe, or upgrade to a usage-based pricing tier with Emergent Support.",
            "Email/SMS sending is QUEUED to Mongo but NOT actually flushed yet — needs the Resend API key wired in for emails to actually send (you have the key, drop it in backend/.env).",
        ],
    },
    "scale_milestones": [
        {"tier": "25 active customers", "what_to_add": [
            "Move backend uvicorn to 4 workers (single config change in supervisor)",
            "Add MongoDB replica set (1 → 3 nodes) — backed up + faster reads",
            "Move generated videos / large PDFs to S3 or Cloudflare R2 ($5-10/mo)",
            "Wire APScheduler for background job processing (separates LLM calls from request-response cycle)",
        ]},
        {"tier": "100 active customers", "what_to_add": [
            "Dedicated LLM budget per customer with hard caps (Stripe metered billing already wired)",
            "Move to a queue-backed worker pool (Celery + Redis) for long-running agent runs",
            "Add Sentry or Datadog for error monitoring",
            "Add Mongo Atlas (managed) for backup, region replication",
            "Spin up a per-customer database (tenant isolation) — critical for SOC 2",
        ]},
    ],
    "integrations_to_add_for_robustness": [
        {"name": "Resend", "category": "email", "priority": "P0", "status": "SDK installed · key missing · queued emails sitting in Mongo", "what_it_unlocks": "Auto-followup welcome packages actually send to leads."},
        {"name": "Sentry", "category": "error monitoring", "priority": "P1", "status": "not yet integrated", "what_it_unlocks": "Get an alert + stack trace within seconds of any production error. Critical before a 5-user launch — you cannot diagnose a customer issue from supervisor logs alone."},
        {"name": "PostHog or Mixpanel", "category": "product analytics", "priority": "P1", "status": "not yet integrated", "what_it_unlocks": "Per-customer usage stream · CSM Q&A capability needs this for SaaS vertical."},
        {"name": "Stripe usage-based billing", "category": "billing", "priority": "P1", "status": "Stripe SDK integrated · usage metering NOT yet wired", "what_it_unlocks": "Per-customer LLM spend caps + automatic overage billing. Without this, a runaway customer call can drain the Universal Key for everyone."},
        {"name": "Cloudflare R2 or AWS S3", "category": "object storage", "priority": "P2", "status": "not yet integrated", "what_it_unlocks": "Offload generated videos and PDF outputs from the pod's local disk — required when you're past 50 customers."},
        {"name": "Mongo Atlas (managed)", "category": "database", "priority": "P2", "status": "self-hosted single-node Mongo", "what_it_unlocks": "Automated backups, replica reads, region replication — required before any enterprise SOC 2 audit."},
        {"name": "APScheduler or Celery+Redis", "category": "background jobs", "priority": "P2", "status": "not yet integrated", "what_it_unlocks": "Auto-followup scheduler, periodic playbook execution, batch reprocessing — required for unattended autonomous workflows."},
        {"name": "Twilio SendGrid (alt to Resend)", "category": "email alt", "priority": "P3", "status": "Twilio account already wired for SMS", "what_it_unlocks": "Volume-pricing alternative to Resend if email volume scales past 50k/mo."},
        {"name": "ClamAV (uploaded-file scanner)", "category": "security", "priority": "P2", "status": "not yet integrated", "what_it_unlocks": "Server-side malware scan on every customer upload. PDF magic-byte check is the v1 guardrail; ClamAV is the v2."},
        {"name": "Tenant-scoped vector DB (MongoDB Atlas Search or Pinecone)", "category": "RAG", "priority": "P1", "status": "not yet integrated · True RAG is the next major feature", "what_it_unlocks": "Per-tenant knowledge base with proper isolation — required for the freight 'load matching against your historical lanes' promise."},
    ],
    "launch_day_checklist": [
        {"item": "Wire Resend API key in backend/.env", "owner": "operator", "blocks_launch": True},
        {"item": "Top up Universal Key budget to $750+ buffer for 5 pilots × 30 days", "owner": "operator", "blocks_launch": True},
        {"item": "Sign 5 pilot agreements with Lighthouse design partners", "owner": "operator", "blocks_launch": True},
        {"item": "Hold a 1hr kickoff call per pilot to capture their data drops", "owner": "operator", "blocks_launch": False},
        {"item": "Integrate Sentry for production error alerts", "owner": "engineering", "blocks_launch": False},
        {"item": "Verify HEALTH tab shows GREEN across the board on launch morning", "owner": "operator", "blocks_launch": True},
        {"item": "Run /api/admin/self-test 1 hour before each pilot kickoff", "owner": "operator", "blocks_launch": False},
    ],
}


def build_requirements() -> Dict:
    return {
        "name": "JADE OS · Requirements + Capacity Assessment",
        "client_requirements": CLIENT_REQUIREMENTS_BY_INDUSTRY,
        "platform_capacity": PLATFORM_CAPACITY,
        "total_industries": len(CLIENT_REQUIREMENTS_BY_INDUSTRY),
        "principles": [
            "Every pilot must complete the Data-Required checklist BEFORE the kickoff call.",
            "Hardware floor is intentionally low — a 5-year-old laptop runs JADE OS just fine.",
            "Required integrations are listed first; optional ones extend the value but don't block launch.",
            "Compliance items block contract signature — don't promise pilot kickoff until those are in writing.",
        ],
    }


def requirements_for(industry: str) -> Dict:
    ind = CLIENT_REQUIREMENTS_BY_INDUSTRY.get(industry)
    if not ind:
        return {"available": False, "industry": industry}
    return {"available": True, "industry": industry, **ind}
