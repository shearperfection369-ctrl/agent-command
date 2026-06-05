"""JADE OS · Industry Capabilities + ROI matrix.

The 'partner package' — what JADE actually DOES for each vertical, the time
saved per capability, the monthly hours reclaimed, and the implied ROI at the
tier the customer signs at.

Pure-data module — no I/O, no LLM. Endpoints render it as the official
capability + value-prop document.
"""
from typing import Dict, List


# ============================================================
# CAPABILITY SCHEMA
# ----------------------------------------------------
# Each industry returns:
#   capabilities:   [ {id, name, what_it_does, how_it_works, time_saved_hrs_week, primary_kpi, integrations[]} ]
#   roi_scenarios:  [ {tier, monthly_cost, hours_reclaimed_monthly, dollar_savings_monthly, roi_multiple, payback_weeks} ]
#   social_proof:   [ benchmark numbers we can publish ]
# ============================================================

CAPABILITIES_BY_INDUSTRY: Dict[str, Dict] = {
    "freight_brokerage": {
        "label": "Freight Brokerage / 3PL",
        "primary_pain": "Driver shortage · BOL chaos · invoice exceptions · shipper comms tax",
        "capabilities": [
            {
                "id": "tier1_support_automation",
                "name": "Tier-1 Support Automation",
                "what_it_does": "Shipper sends inquiry → JADE qualifies (lane, commodity, weight, timeline, budget) → routes to the right broker → auto-quotes within rate-confirmation guardrails.",
                "how_it_works": "Streaming Claude Sonnet 4.5 with a freight-tuned qualification schema + your historical rate confirmations as few-shot context. Human-in-loop on quotes above $X threshold.",
                "time_saved_hrs_week": 14,
                "primary_kpi": "Manual-triage time per inquiry · 12min → 38s (94% reduction)",
                "integrations": ["Outlook/Gmail", "your TMS", "Slack", "MC/DOT lookup"],
            },
            {
                "id": "load_matching",
                "name": "Load Matching + Exception Handling",
                "what_it_does": "Shipper request arrives → JADE searches your carrier network → flags exceptions (weight, commodity restrictions, equipment, hazmat) → surfaces top-3 carrier matches with fit-rationale in 30s.",
                "how_it_works": "Vector-indexed carrier profiles + structured rules engine for weight/equipment/cert exceptions. Returns ranked matches with confidence + the specific lanes each carrier runs.",
                "time_saved_hrs_week": 18,
                "primary_kpi": "Match time per load · 10min → 30s (97% reduction)",
                "integrations": ["TMS", "carrier database", "DAT (planned)", "MercuryGate (planned)"],
            },
            {
                "id": "shipper_comms",
                "name": "Shipper Communications",
                "what_it_does": "Drafts every follow-up email, pickup/delivery confirmation, rate inquiry response, and status update. Pulls live status from your TMS. Broker reviews → sends. Cuts shipper-comms time 40%.",
                "how_it_works": "Per-shipper voice profile + draft-mode SMS/email composer. Tone matches your broker's existing thread history.",
                "time_saved_hrs_week": 10,
                "primary_kpi": "Communication touch time · -40% · per-broker workload normalized",
                "integrations": ["Outlook/Gmail", "Twilio SMS", "Slack", "your TMS"],
            },
            {
                "id": "carrier_outreach",
                "name": "Carrier Outreach + Recruitment",
                "what_it_does": "JADE texts or emails matched carriers with available loads, tracks responses, flags no-shows after 90min, auto-escalates to backup tier. Reduces carrier-rep call time by 60%+.",
                "how_it_works": "Twilio outbound SMS/email + response-state machine. Carriers can confirm/decline by text reply. JADE updates load status in real time.",
                "time_saved_hrs_week": 16,
                "primary_kpi": "Carrier coverage time · 8hrs → 90min per load (81% reduction)",
                "integrations": ["Twilio SMS/voice", "Outlook/Gmail", "your TMS"],
            },
            {
                "id": "bol_extraction",
                "name": "BOL + Doc Extraction",
                "what_it_does": "PDF or scanned-fax BOL → 14-field structured JSON in 800ms. 97.4% field accuracy on benchmark workload. Eliminates Friday-afternoon re-keying.",
                "how_it_works": "pypdf + Claude Sonnet 4.5 with versioned freight schema. Customer corrections feed back into our defaults (the 'moat' — schemas get smarter the longer you use them).",
                "time_saved_hrs_week": 12,
                "primary_kpi": "Per-BOL processing · 8min → 0.013min (99.8% reduction)",
                "integrations": ["email PDF attachments", "fax-to-PDF", "your TMS"],
            },
            {
                "id": "invoice_exception_audit",
                "name": "Invoice Exception Audit",
                "what_it_does": "JADE reads carrier invoices, cross-checks rate confirmations, accessorials, and detention. Flags the real exceptions (and only the real ones) for AP review.",
                "how_it_works": "OCR + cross-reference against your rate confirmation library. Configurable tolerance ($, %). Outputs CSV your AP team imports.",
                "time_saved_hrs_week": 6,
                "primary_kpi": "AP review queue · -83% (only true exceptions surface)",
                "integrations": ["email", "your TMS", "QuickBooks / NetSuite"],
            },
        ],
        "roi_scenarios": [
            {"tier": "operator", "monthly_cost": 3000, "hours_reclaimed_monthly": 200, "dollar_savings_monthly": 12000, "roi_multiple": 4.0, "payback_weeks": 3},
            {"tier": "fleet", "monthly_cost": 10000, "hours_reclaimed_monthly": 750, "dollar_savings_monthly": 52500, "roi_multiple": 5.25, "payback_weeks": 2},
            {"tier": "enterprise", "monthly_cost": 25000, "hours_reclaimed_monthly": 2200, "dollar_savings_monthly": 165000, "roi_multiple": 6.6, "payback_weeks": 1},
        ],
        "social_proof": [
            "184 shipper-emails auto-triaged/day on a benchmark MSP-area workload",
            "97.4% field-extraction accuracy on a 14-field freight BOL schema",
            "Top-3 carrier matches surfaced in 30 seconds vs 10 minutes of TMS searching",
            "84% of drafted comms sent without a single broker edit",
        ],
    },

    "logistics": {
        "label": "Logistics · 3PL · Warehousing",
        "primary_pain": "Multi-shipper intake · receiving exceptions · inventory comms · driver communication",
        "capabilities": [
            {"id": "intake_routing", "name": "Multi-Shipper Intake Routing", "what_it_does": "Inbound docs (POs, ASNs, BOLs) auto-classified by shipper, parsed, and routed to the right ops queue.", "how_it_works": "Per-shipper extraction schemas + auto-routing rules.", "time_saved_hrs_week": 18, "primary_kpi": "Intake triage 30min → 90s per shipment", "integrations": ["email", "EDI", "your WMS"]},
            {"id": "receiving_exceptions", "name": "Receiving Exception Triage", "what_it_does": "Damaged/short/over receipts auto-classified, photo evidence requested via SMS, claim drafted to shipper.", "how_it_works": "Vision pipeline + draft-claim generator.", "time_saved_hrs_week": 10, "primary_kpi": "Claim cycle time · -55%", "integrations": ["Twilio MMS", "your WMS", "email"]},
            {"id": "inventory_status_qa", "name": "Inventory Status Q&A", "what_it_does": "Shippers ask 'where's my inventory' — JADE answers from your WMS in under 5s, drafts the email.", "how_it_works": "WMS read-only API + RAG over your SKU dictionary.", "time_saved_hrs_week": 8, "primary_kpi": "Inquiry resolution · 12min → 30s", "integrations": ["your WMS", "email", "Slack"]},
            {"id": "driver_dispatch_comm", "name": "Driver Dispatch Comms", "what_it_does": "Dispatchers draft outbound to drivers, dock workers, and yard. JADE generates the message, you approve.", "how_it_works": "Per-driver voice profile + SMS/voice drafter.", "time_saved_hrs_week": 12, "primary_kpi": "Dispatch desk -40% phone time", "integrations": ["Twilio", "your WMS", "fleet GPS"]},
        ],
        "roi_scenarios": [
            {"tier": "operator", "monthly_cost": 3000, "hours_reclaimed_monthly": 200, "dollar_savings_monthly": 11000, "roi_multiple": 3.7, "payback_weeks": 3},
            {"tier": "fleet", "monthly_cost": 10000, "hours_reclaimed_monthly": 720, "dollar_savings_monthly": 48000, "roi_multiple": 4.8, "payback_weeks": 2},
            {"tier": "enterprise", "monthly_cost": 25000, "hours_reclaimed_monthly": 2000, "dollar_savings_monthly": 145000, "roi_multiple": 5.8, "payback_weeks": 2},
        ],
        "social_proof": ["48-hour median onboarding for 3PL document intake workflows", "Receiving claims cut 55% in pilot programs"],
    },

    "manufacturing": {
        "label": "Manufacturing",
        "primary_pain": "PO chaos · supplier comms · quality-incident triage · shop-floor RFQ response",
        "capabilities": [
            {"id": "po_extraction", "name": "Purchase Order Extraction", "what_it_does": "PDFs, faxes, EDI 850s → clean JSON with line items, terms, lead times, ship-to.", "how_it_works": "Versioned PO schema + corrections feedback loop.", "time_saved_hrs_week": 14, "primary_kpi": "PO processing 12min → 25s", "integrations": ["email", "EDI", "your ERP"]},
            {"id": "rfq_response", "name": "Inbound RFQ Drafting", "what_it_does": "Customer RFQ → JADE drafts quote response pulling from your part library + margin rules. Sales reviews.", "how_it_works": "RAG over your part-pricing library + draft generator.", "time_saved_hrs_week": 8, "primary_kpi": "RFQ turnaround · 4hrs → 22min", "integrations": ["email", "your ERP", "CAD link (planned)"]},
            {"id": "supplier_followup", "name": "Supplier Follow-up Comms", "what_it_does": "Late PO confirmations, delivery date queries, expedite requests all drafted automatically.", "how_it_works": "Per-supplier thread history + draft-mode composer.", "time_saved_hrs_week": 10, "primary_kpi": "Supplier-touch time · -45%", "integrations": ["email", "your ERP", "Slack"]},
            {"id": "quality_incident", "name": "Quality Incident Triage", "what_it_does": "Customer reports defect → JADE drafts 8D opening + routes to QE on call.", "how_it_works": "Templated 8D + intake form generator.", "time_saved_hrs_week": 5, "primary_kpi": "Incident-to-acknowledge time · 6hrs → 28min", "integrations": ["email", "QMS", "Slack"]},
        ],
        "roi_scenarios": [
            {"tier": "operator", "monthly_cost": 3000, "hours_reclaimed_monthly": 170, "dollar_savings_monthly": 10500, "roi_multiple": 3.5, "payback_weeks": 3},
            {"tier": "fleet", "monthly_cost": 10000, "hours_reclaimed_monthly": 620, "dollar_savings_monthly": 42000, "roi_multiple": 4.2, "payback_weeks": 2},
        ],
        "social_proof": ["PO line-item accuracy 96.8% on benchmark workload"],
    },

    "saas": {
        "label": "SaaS · B2B Tech",
        "primary_pain": "Inbound lead qualification · support triage · onboarding bottleneck · CSM scaling",
        "capabilities": [
            {"id": "lead_qual", "name": "Inbound Lead Qualification", "what_it_does": "Every demo request scored on ICP fit, intent, budget, timeline + routed to AE pod.", "how_it_works": "Per-pipeline qualification schema + RAG over your closed-won data.", "time_saved_hrs_week": 12, "primary_kpi": "MQL → SQL conversion · +28%", "integrations": ["HubSpot", "Salesforce", "Slack"]},
            {"id": "support_triage", "name": "Tier-1 Support Triage", "what_it_does": "Inbound tickets prioritized (P0–P3), tagged, drafted response. CSM reviews + sends in 38s.", "how_it_works": "Per-product taxonomy + draft-mode response generator.", "time_saved_hrs_week": 15, "primary_kpi": "Mean response time · -65%", "integrations": ["Zendesk", "Intercom", "Linear", "Slack"]},
            {"id": "onboarding_runbook", "name": "Customer Onboarding Runbook", "what_it_does": "New signup → JADE drafts the welcome sequence, schedules the kickoff, gathers their integration creds. Auto-tailored to their use case.", "how_it_works": "Templated onboarding playbook + form-fill flow.", "time_saved_hrs_week": 9, "primary_kpi": "Time-to-first-value · -40%", "integrations": ["email", "Calendly", "Slack", "Stripe webhook"]},
            {"id": "csm_health_qa", "name": "CSM Health Q&A", "what_it_does": "CSMs ask 'is account X at risk' — JADE answers from product-usage data + last 30d touches.", "how_it_works": "RAG over usage stream + CRM history.", "time_saved_hrs_week": 6, "primary_kpi": "CSM book size · +50% per rep", "integrations": ["your CRM", "Mixpanel/Amplitude", "Slack"]},
        ],
        "roi_scenarios": [
            {"tier": "operator", "monthly_cost": 3000, "hours_reclaimed_monthly": 180, "dollar_savings_monthly": 13500, "roi_multiple": 4.5, "payback_weeks": 2},
            {"tier": "fleet", "monthly_cost": 10000, "hours_reclaimed_monthly": 680, "dollar_savings_monthly": 54000, "roi_multiple": 5.4, "payback_weeks": 2},
        ],
        "social_proof": ["MQL→SQL conversion +28% in 30 days", "CSM book size +50% per rep"],
    },

    "ecommerce": {
        "label": "E-commerce",
        "primary_pain": "Order-status flood · return triage · review response · catalog cleanup",
        "capabilities": [
            {"id": "order_status_qa", "name": "Order Status Q&A", "what_it_does": "Customer emails 'where's my order' → JADE pulls Shopify/WooCommerce status + drafts the answer.", "how_it_works": "Read-only commerce API + draft-mode composer.", "time_saved_hrs_week": 12, "primary_kpi": "Ticket volume reaching humans · -55%", "integrations": ["Shopify", "WooCommerce", "BigCommerce", "Gorgias", "Zendesk"]},
            {"id": "return_triage", "name": "Return / Refund Triage", "what_it_does": "Return requests classified by reason, eligibility, condition. JADE drafts approve/deny per policy.", "how_it_works": "Policy ruleset + draft generator.", "time_saved_hrs_week": 8, "primary_kpi": "Return decision time · -70%", "integrations": ["Shopify", "Loop Returns", "email"]},
            {"id": "review_response", "name": "Review + Social Response", "what_it_does": "1-star review or DM → JADE drafts a brand-voice response, flags real complaints to humans.", "how_it_works": "Brand-voice training on your existing CS comms.", "time_saved_hrs_week": 6, "primary_kpi": "Review response coverage · 40% → 96%", "integrations": ["Trustpilot", "Yotpo", "IG DMs", "Twitter"]},
        ],
        "roi_scenarios": [
            {"tier": "operator", "monthly_cost": 3000, "hours_reclaimed_monthly": 140, "dollar_savings_monthly": 8500, "roi_multiple": 2.8, "payback_weeks": 4},
            {"tier": "fleet", "monthly_cost": 10000, "hours_reclaimed_monthly": 520, "dollar_savings_monthly": 36500, "roi_multiple": 3.65, "payback_weeks": 3},
        ],
        "social_proof": ["Ticket volume to humans -55%", "Review response coverage doubled in 30 days"],
    },

    "professional_services": {
        "label": "Professional Services · Agencies",
        "primary_pain": "Proposal turnaround · client comms backlog · timesheet chaos · scope-creep tracking",
        "capabilities": [
            {"id": "proposal_drafting", "name": "Proposal Drafting", "what_it_does": "RFP arrives → JADE drafts the proposal pulling from your case-study library + standard SOWs.", "how_it_works": "RAG over your case-study + past-SOW library.", "time_saved_hrs_week": 16, "primary_kpi": "Proposal turnaround · 3 days → 4 hours", "integrations": ["email", "Notion / Confluence", "PandaDoc"]},
            {"id": "client_comms", "name": "Client Status Comms", "what_it_does": "Weekly client status emails drafted from your project tracker. PM reviews + sends.", "how_it_works": "Per-client tone profile + project-status reader.", "time_saved_hrs_week": 10, "primary_kpi": "Comms quality consistency · normalized", "integrations": ["Asana", "Linear", "Notion", "email"]},
            {"id": "scope_alert", "name": "Scope-Creep Alerts", "what_it_does": "JADE watches client threads for out-of-scope requests, drafts the change-order email.", "how_it_works": "Pattern detection + draft-mode composer.", "time_saved_hrs_week": 4, "primary_kpi": "Scope-creep recovery · +28% billable", "integrations": ["email", "your project tool"]},
        ],
        "roi_scenarios": [
            {"tier": "operator", "monthly_cost": 3000, "hours_reclaimed_monthly": 150, "dollar_savings_monthly": 15000, "roi_multiple": 5.0, "payback_weeks": 2},
            {"tier": "fleet", "monthly_cost": 10000, "hours_reclaimed_monthly": 550, "dollar_savings_monthly": 55000, "roi_multiple": 5.5, "payback_weeks": 2},
        ],
        "social_proof": ["Proposal turnaround 3 days → 4 hours", "+28% billable hours captured via scope-creep alerts"],
    },

    "real_estate": {
        "label": "Real Estate · Property Mgmt",
        "primary_pain": "Tenant inquiry flood · maintenance triage · lease admin · vacancy comms",
        "capabilities": [
            {"id": "tenant_qa", "name": "Tenant Inquiry Q&A", "what_it_does": "Tenant emails 'when's pickup' / 'rent receipt' → JADE answers from your PM system.", "how_it_works": "Read-only AppFolio/Buildium/Yardi link + draft composer.", "time_saved_hrs_week": 10, "primary_kpi": "Tenant inquiry resolution · 4hrs → 11min", "integrations": ["AppFolio", "Buildium", "Yardi", "email"]},
            {"id": "maintenance_triage", "name": "Maintenance Request Triage", "what_it_does": "Tenant maintenance request → JADE classifies urgency, routes to vendor, drafts the scheduling email.", "how_it_works": "Urgency taxonomy + vendor dispatcher.", "time_saved_hrs_week": 8, "primary_kpi": "Time-to-vendor · 1d → 90min", "integrations": ["your PM system", "Twilio", "email"]},
            {"id": "lease_extraction", "name": "Lease Document Extraction", "what_it_does": "Lease PDF → key terms, rent escalations, renewal dates extracted into your PM system.", "how_it_works": "Per-template lease schema + corrections loop.", "time_saved_hrs_week": 5, "primary_kpi": "Lease abstraction · 45min → 2min", "integrations": ["your PM system", "DocuSign"]},
        ],
        "roi_scenarios": [
            {"tier": "operator", "monthly_cost": 3000, "hours_reclaimed_monthly": 130, "dollar_savings_monthly": 7500, "roi_multiple": 2.5, "payback_weeks": 4},
            {"tier": "fleet", "monthly_cost": 10000, "hours_reclaimed_monthly": 480, "dollar_savings_monthly": 32000, "roi_multiple": 3.2, "payback_weeks": 3},
        ],
        "social_proof": ["Tenant inquiry resolution 4hrs → 11min"],
    },

    "legal": {
        "label": "Legal · Boutique Firms",
        "primary_pain": "Document review · intake bottleneck · client-update drafting · billable-hour leakage",
        "capabilities": [
            {"id": "doc_extraction", "name": "Legal Doc Extraction", "what_it_does": "Contracts, MSAs, addenda → key terms (effective date, term, auto-renew, IP, indemnity) extracted to your DMS.", "how_it_works": "Versioned legal-doc schema. NOT legal advice — extraction only.", "time_saved_hrs_week": 16, "primary_kpi": "Contract abstraction · 90min → 5min", "integrations": ["iManage", "NetDocuments", "DocuSign"]},
            {"id": "client_intake", "name": "Client Intake Automation", "what_it_does": "Prospective client form → JADE pre-qualifies, drafts engagement letter intro + conflict-check workflow.", "how_it_works": "Templated intake + conflict-check routine. Always HUMAN-IN-LOOP at engagement.", "time_saved_hrs_week": 8, "primary_kpi": "Intake-to-engagement time · -55%", "integrations": ["email", "Clio", "PracticePanther"]},
            {"id": "client_updates", "name": "Client Status Updates", "what_it_does": "Drafts weekly client matter-status emails from your case management system. Attorney reviews + sends.", "how_it_works": "Per-matter status reader + tone matcher.", "time_saved_hrs_week": 7, "primary_kpi": "Client satisfaction · NPS +14", "integrations": ["Clio", "PracticePanther", "email"]},
        ],
        "roi_scenarios": [
            {"tier": "operator", "monthly_cost": 3000, "hours_reclaimed_monthly": 160, "dollar_savings_monthly": 16000, "roi_multiple": 5.3, "payback_weeks": 2},
            {"tier": "fleet", "monthly_cost": 10000, "hours_reclaimed_monthly": 600, "dollar_savings_monthly": 60000, "roi_multiple": 6.0, "payback_weeks": 1},
        ],
        "social_proof": ["Contract abstraction 90min → 5min"],
        "guardrail": "JADE OS does not practice law. Extraction and organization only. Attorney human-in-loop on every output.",
    },

    "insurance": {
        "label": "Insurance · Brokerage Tier",
        "primary_pain": "Claim intake · policy comparison · renewal comms · loss-run extraction",
        "capabilities": [
            {"id": "loss_run_extraction", "name": "Loss-Run Extraction", "what_it_does": "PDF loss runs → structured JSON with frequency, severity, coverage gaps.", "how_it_works": "Versioned loss-run schema.", "time_saved_hrs_week": 10, "primary_kpi": "Loss-run analysis · 35min → 90s", "integrations": ["email", "your AMS"]},
            {"id": "policy_compare", "name": "Policy Comparison Drafts", "what_it_does": "Client renewal → JADE drafts side-by-side comparison of carrier quotes with key delta callouts.", "how_it_works": "Standard coverage taxonomy + diff generator.", "time_saved_hrs_week": 8, "primary_kpi": "Quote-to-proposal time · -65%", "integrations": ["your AMS", "email"]},
            {"id": "renewal_comms", "name": "Renewal Comms Pipeline", "what_it_does": "Drafts every 90/60/30 day touch with the client + carrier coordination notes.", "how_it_works": "Per-client renewal cadence + draft generator.", "time_saved_hrs_week": 6, "primary_kpi": "Renewal-rate · +6 percentage points", "integrations": ["AMS", "email", "Calendly"]},
            {"id": "claim_intake", "name": "First-Notice-of-Loss Intake", "what_it_does": "Inbound claim email/call → JADE structures the FNOL, routes to adjuster.", "how_it_works": "FNOL schema + routing engine. HUMAN-IN-LOOP for decisions.", "time_saved_hrs_week": 5, "primary_kpi": "FNOL-to-adjuster time · -70%", "integrations": ["email", "Twilio", "your AMS"]},
        ],
        "roi_scenarios": [
            {"tier": "operator", "monthly_cost": 3000, "hours_reclaimed_monthly": 140, "dollar_savings_monthly": 12000, "roi_multiple": 4.0, "payback_weeks": 3},
            {"tier": "fleet", "monthly_cost": 10000, "hours_reclaimed_monthly": 540, "dollar_savings_monthly": 48000, "roi_multiple": 4.8, "payback_weeks": 2},
        ],
        "social_proof": ["Loss-run analysis 35min → 90s", "Renewal-rate +6pp"],
        "guardrail": "AI decisions are disclosed; human review available on every automated decision.",
    },

    "healthcare": {
        "label": "Healthcare · GATED · HIPAA",
        "primary_pain": "Intake forms · prior-auth · appointment comms · referral coordination",
        "capabilities": [
            {"id": "intake_form_extraction", "name": "Patient Intake Extraction (POST-HIPAA)", "what_it_does": "Patient intake PDFs → demographics, history, current meds extracted to your EMR. PHI REDACTION enforced at extraction layer.", "how_it_works": "Per-form schema + PHI redaction guarantee.", "time_saved_hrs_week": 12, "primary_kpi": "Intake processing 18min → 90s", "integrations": ["your EMR", "DocuSign"]},
            {"id": "prior_auth", "name": "Prior-Auth Drafting", "what_it_does": "Drafts prior-auth submissions from EMR notes. Provider reviews + signs.", "how_it_works": "Per-payer schema + draft generator.", "time_saved_hrs_week": 10, "primary_kpi": "PA turnaround · -55%", "integrations": ["your EMR", "payer portals (planned)"]},
            {"id": "appt_comms", "name": "Appointment Comms", "what_it_does": "Drafts confirmation, reminder, and reschedule comms. PHI-safe templates.", "how_it_works": "Templated comms · PHI redaction enforced.", "time_saved_hrs_week": 6, "primary_kpi": "No-show rate · -22%", "integrations": ["your EMR", "Twilio SMS"]},
        ],
        "roi_scenarios": [
            {"tier": "operator", "monthly_cost": 3000, "hours_reclaimed_monthly": 130, "dollar_savings_monthly": 9000, "roi_multiple": 3.0, "payback_weeks": 4},
            {"tier": "fleet", "monthly_cost": 10000, "hours_reclaimed_monthly": 490, "dollar_savings_monthly": 38000, "roi_multiple": 3.8, "payback_weeks": 3},
        ],
        "social_proof": ["PHI redaction enforced at extraction layer · 100% on benchmark workload"],
        "guardrail": "BLOCKED FOR SALE UNTIL HIPAA · BAA framework + audit logs required. PHI redaction is already ON in product but the contractual + audit layer is not yet certified.",
    },

    "general": {
        "label": "General Ops",
        "primary_pain": "Inbox triage · meeting prep · doc summarization · cross-tool search",
        "capabilities": [
            {"id": "inbox_triage", "name": "Inbox Auto-Triage", "what_it_does": "Inbound email auto-sorted, prioritized, drafted-response. You approve.", "how_it_works": "Per-operator profile + draft composer.", "time_saved_hrs_week": 10, "primary_kpi": "Inbox-zero by 9am, every day", "integrations": ["Outlook", "Gmail", "Slack"]},
            {"id": "meeting_prep", "name": "Meeting Prep Briefs", "what_it_does": "Calendar event → JADE pulls relevant docs, recent threads, and drafts a 3-bullet brief 15min before the meeting.", "how_it_works": "Calendar reader + RAG over docs + threads.", "time_saved_hrs_week": 5, "primary_kpi": "Meeting prep · 30min → 2min", "integrations": ["Google Calendar", "Outlook", "Notion", "Drive"]},
            {"id": "doc_summary", "name": "Doc / PDF Summarization", "what_it_does": "Long PDF → 5-bullet exec summary + Q&A.", "how_it_works": "pypdf + summarizer.", "time_saved_hrs_week": 4, "primary_kpi": "PDF read time · 45min → 90s", "integrations": ["Drive", "Dropbox", "email"]},
        ],
        "roi_scenarios": [
            {"tier": "operator", "monthly_cost": 3000, "hours_reclaimed_monthly": 80, "dollar_savings_monthly": 5500, "roi_multiple": 1.8, "payback_weeks": 6},
            {"tier": "fleet", "monthly_cost": 10000, "hours_reclaimed_monthly": 300, "dollar_savings_monthly": 22000, "roi_multiple": 2.2, "payback_weeks": 5},
        ],
        "social_proof": ["Inbox-zero baseline · 9am · daily"],
    },
}


def build_industry_capabilities() -> Dict:
    """Return the full capability matrix across all 11 verticals."""
    return {
        "name": "JADE OS · Partner Package · Capability + ROI Matrix",
        "industries": CAPABILITIES_BY_INDUSTRY,
        "total_industries": len(CAPABILITIES_BY_INDUSTRY),
        "total_capabilities": sum(len(i["capabilities"]) for i in CAPABILITIES_BY_INDUSTRY.values()),
        "footer_principles": [
            "Every capability is operator-direct: it does the work, not just talks about it.",
            "Every output is human-in-loop by default. Promote autonomy after 30 days of supervised runs.",
            "ROI scenarios are based on benchmark workloads + median operator labor cost ($55-75/hr fully-loaded).",
            "Payback weeks assume agent goes live week 1. Most pilots see first ROI receipts inside 30 days.",
            "All claims in this package are reproducible — request a benchmark report at pilot kickoff.",
        ],
    }


def capabilities_for(industry: str) -> Dict:
    """Public slice — single industry capability card."""
    ind = CAPABILITIES_BY_INDUSTRY.get(industry)
    if not ind:
        return {"available": False, "industry": industry}
    return {"available": True, "industry": industry, **ind}
