export const INDUSTRIES = [
  { id: "freight_brokerage", label: "FREIGHT · 3PL", color: "#ccff00", compliance: "go_now" },
  { id: "logistics", label: "LOGISTICS", color: "#00ffff", compliance: "go_now" },
  { id: "manufacturing", label: "MANUFACTURING", color: "#7c5cff", compliance: "go_now" },
  { id: "healthcare", label: "HEALTHCARE", color: "#ff3b8a", compliance: "blocked", gate: "HIPAA" },
  { id: "saas", label: "SAAS · TECH", color: "#ccff00", compliance: "go_now" },
  { id: "ecommerce", label: "E-COMMERCE", color: "#00ffff", compliance: "go_now" },
  { id: "insurance", label: "INSURANCE", color: "#7c5cff", compliance: "go_with_tos", gate: "ToS · AI disclosure" },
  { id: "legal", label: "LEGAL", color: "#ff3b8a", compliance: "go_with_tos", gate: "ToS · UPL carve-out" },
  { id: "real_estate", label: "REAL ESTATE", color: "#ccff00", compliance: "go_now" },
  { id: "professional_services", label: "PRO SERVICES", color: "#00ffff", compliance: "go_now" },
  { id: "general", label: "GENERAL · OTHER", color: "#ffffff", compliance: "go_now" },
];

export const INDUSTRY_BY_ID = Object.fromEntries(INDUSTRIES.map((i) => [i.id, i]));

export const SAMPLES = {
  freight_brokerage: {
    chat_prompts: [
      "What's a fair RPM for Eagan→Joliet 53' reefer this week?",
      "Draft a follow-up to a carrier who ghosted me yesterday.",
      "How do I qualify a shipper who keeps lowballing?",
    ],
    extract: `LOAD ID: 88421-MN
Pickup: 02/15 08:00-12:00, Eagan, MN 55121
Delivery: 02/16 14:00-18:00, Joliet, IL 60432
Equipment: 53' Reefer, 38,000 lbs, Temp 34F
Commodity: General Mills frozen breakfast
Miles: 482
Rate: $1,950 ALL-IN
Broker: Northstar Logistics, MC 654321
Contact: Dana B. — (612) 555-0117 — dana@northstar.co`,
    outreach_summary: "53' reefer, Eagan MN→Joliet IL, pickup 02/15, $1,950 ALL-IN, drop & hook, MC 654321",
    outreach_recipient: "Bay & Bay Transportation",
    ticket: "Driver showed up 90 min early at the receiver, was told to leave. Now demanding detention from broker. Load 88421-MN.",
  },
  manufacturing: {
    chat_prompts: [
      "Production line 2 is running 12% under takt. Triage steps?",
      "Draft a vendor follow-up on PO #44218 — 5 days late.",
      "Write an OEE escalation note for management.",
    ],
    extract: `Purchase Order #PO-44218
Vendor: Acme Steel Supply
Items:
  - 250x Bar Stock 1018 CRS 1/2" — $4.20/ea
  - 100x Plate 304 SS 1/4" 4x8 — $185.00/ea
Total: $19,550.00
Required by: 03/04
Buyer: J. Sundberg, Pentair MN
Terms: Net 30`,
    outreach_summary: "PO #PO-44218 is 5 business days past due. Need updated ship date. Production line down by Friday if not received.",
    outreach_recipient: "Acme Steel Supply",
    ticket: "Line 3 stopped — defect rate jumped from 0.4% to 6.8% in the last hour. Operator suspects bad batch on hopper feed.",
  },
  healthcare: {
    chat_prompts: [
      "Patient asking why prior auth was denied — talking points?",
      "Draft a referral confirmation email to a primary care office.",
      "How do I triage an angry call about a $4,200 surprise bill?",
    ],
    extract: `Patient Intake Form
Name: J. Sample
DOB: 1971-04-22
Insurer: BlueCross MN — Member ID 8842XXXX
Visit: 02/12, Dr. Patel, Allina Clinic
Reason: chest pain follow-up
Prior auth: PA-2024-0911, status APPROVED
Diagnosis (provisional): I20.9
CPT planned: 93306, 93000
Notes: Patient prefers afternoon scheduling.`,
    outreach_summary: "Patient J. Sample needs a referral confirmation to Allina cardiology, visit 02/12 with Dr. Patel. Prior auth approved.",
    outreach_recipient: "Allina Cardiology Scheduling",
    ticket: "Patient called twice today: insurance denied her MRI, says she was told it would be covered. Spoke to scheduler last Friday.",
  },
  saas: {
    chat_prompts: [
      "Why is our enterprise NPS dipping in Q3? Diagnose.",
      "Draft a renewal email for an account that flagged churn risk.",
      "How should we qualify a 200-seat SMB inbound that wants discount?",
    ],
    extract: `Order Form — JADE Acme Inc.
Plan: Enterprise · 250 seats
MRR: $14,250
Term: 24 months
Start: 03/01
Renewal: 02/28 next year
Owner: K. Chen
Notes: Includes SSO + API priority + 24/7 P1.`,
    outreach_summary: "Acme Inc., 250-seat enterprise renewal in 30 days. Usage up 40% YoY. Want to propose 12-month renewal with 8% increase.",
    outreach_recipient: "K. Chen, VP Eng at Acme Inc.",
    ticket: "Customer says they're being charged for 250 seats but only have 180 active users. CSV attached. Asking for refund.",
  },
  ecommerce: {
    chat_prompts: [
      "AOV dropped 14% last week. Top 3 things to check.",
      "Draft a personalized win-back email for a lapsed VIP.",
      "How do I respond to a flood of 1-star reviews on the new SKU?",
    ],
    extract: `Order #SHO-220314
Customer: M. Lindgren — mlindgren@example.com
Items:
  - 1x WIDGET-RED-L — $48.00
  - 2x BANDANA-BLK — $12.00 ea
Subtotal: $72.00
Shipping: $7.50 USPS
Total: $79.50
Ship to: 600 1st St N, Minneapolis MN 55401
Status: PAID, awaiting fulfillment`,
    outreach_summary: "VIP customer hasn't ordered in 90 days. Lifetime value $480. Send win-back with 15% off + new arrivals preview.",
    outreach_recipient: "M. Lindgren",
    ticket: "Order #SHO-220314 says delivered but customer never received it. Tracking shows porch drop. Wants refund AND replacement.",
  },
  insurance: {
    chat_prompts: [
      "Reserve guidance for a $25k auto BI claim, no priors?",
      "Draft a status update to insured on subrogation in progress.",
      "Triage a claim where insured's story differs from police report.",
    ],
    extract: `FNOL — Claim #CL-558119
Insured: T. Olson — Policy POL-77231
DOL: 02/08
Loss type: Auto comprehensive — hail
Vehicle: 2021 Subaru Outback
Adjuster: assigned · L. Park
Reserve: $4,200
Estimated repair: $6,800 (body shop est.)
Status: Open, awaiting photos`,
    outreach_summary: "Hail damage claim CL-558119. Body shop estimate exceeds initial reserve. Need to update insured on next steps and revised timeline.",
    outreach_recipient: "T. Olson (insured)",
    ticket: "Insured calling for the 3rd time — wants ETA on payout. Adjuster L. Park on PTO. Claim CL-558119, hail damage.",
  },
  legal: {
    chat_prompts: [
      "How do I run a conflict check on a new corporate matter?",
      "Draft a polite delay notice to opposing counsel.",
      "Tier-1 intake script for a slip-and-fall PI inquiry.",
    ],
    extract: `Client Intake — Matter #M-22041
Client: Acme Industries LLC
Conflict check: CLEARED
Jurisdiction: D. Minn.
Practice area: Commercial litigation
Opposing party: Globex Corp.
Counsel: Skadden
Date of incident: 11/14
Statute deadline: 11/14 + 6 years
Retainer requested: $25,000`,
    outreach_summary: "New commercial litigation matter M-22041 for Acme Industries. Need to confirm scope, fee structure, retainer wire instructions.",
    outreach_recipient: "Acme Industries General Counsel",
    ticket: "Prospective client called about a slip-and-fall at a Target store last August. Wants free consult. Out-of-state.",
  },
  real_estate: {
    chat_prompts: [
      "How do I price a 2,400 sqft retail unit in North Loop right now?",
      "Draft a lease renewal email for a tenant 60 days out.",
      "Tier-1 maintenance triage script for an after-hours water leak call.",
    ],
    extract: `Lease Summary — Unit 412, North Loop Tower
Tenant: Riverline Coffee LLC
Term: 03/01 → 02/28 +5 years
Base rent: $4,800/mo
CAM: $620/mo
Property mgmt: Twin Cities CRE Group
Notes: 2 months free at start; renewal option +3.`,
    outreach_summary: "Tenant Riverline Coffee, Unit 412, lease ends in 60 days. Want to extend 3 years with 4% annual escalator.",
    outreach_recipient: "Riverline Coffee LLC",
    ticket: "Tenant in Unit 412 — water leaking from ceiling. Coming through light fixture. Reported 11:42pm Friday.",
  },
  professional_services: {
    chat_prompts: [
      "How do I scope a 3-month brand redesign for a B2B SaaS?",
      "Draft a status update on a delayed deliverable.",
      "Triage a client complaint about a missed deadline.",
    ],
    extract: `SOW — Project P-1188
Client: Northpoint SaaS Inc.
Scope: Brand strategy + visual identity + website rebuild
Deliverables: Brand book, identity system, 12-page Webflow site
Fee: $48,000 fixed
Term: 14 weeks · kickoff 03/04
Owner: D. Hayes
Milestones: Discovery 3w, Identity 5w, Web 6w`,
    outreach_summary: "Project P-1188 kickoff with Northpoint SaaS next Monday. Need to confirm stakeholders, attendees, kickoff agenda.",
    outreach_recipient: "Northpoint SaaS Inc.",
    ticket: "Client emailed: brand book draft was due Friday, didn't receive it. Asking if project is in trouble.",
  },
  logistics: {
    chat_prompts: [
      "Average dwell time at our top 10 docks last month?",
      "Draft a carrier service update on a delayed shipment.",
      "Triage a frustrated customer asking where their pallet is.",
    ],
    extract: `Shipment #SHP-99841
Carrier: XPO
Origin: Eden Prairie, MN
Destination: Memphis, TN
Pieces: 4 pallets, 2,100 lbs
Tracking: 11ZX...
Status: In transit, ETA 02/16 14:00
Notes: Liftgate required at delivery.`,
    outreach_summary: "Shipment SHP-99841 to Memphis arriving 02/16. Customer needs liftgate confirmation and ETA window narrowed.",
    outreach_recipient: "Memphis receiver dock manager",
    ticket: "Customer service ticket: shipment SHP-99841 hasn't moved in 36 hours per tracking. Customer escalating.",
  },
  general: {
    chat_prompts: [
      "What's the fastest way to triage 200 unread support tickets?",
      "Draft a follow-up to a prospect who hasn't replied in 10 days.",
      "How do I score inbound leads without firmographic data?",
    ],
    extract: `Order #INV-2034
Customer: Pioneer Co.
Total: $4,820.00
Date: 02/12
Items: 12 line items
Payment: Net 30, due 03/14
Contact: J. Patel — j.patel@pioneer.co`,
    outreach_summary: "Pioneer Co. ordered $4,820, Net 30. Want to upsell to annual contract for 12% discount.",
    outreach_recipient: "J. Patel at Pioneer Co.",
    ticket: "Customer emailed twice with no response from our team. Says they're considering switching to a competitor.",
  },
};

export const sampleFor = (industry) => SAMPLES[industry] || SAMPLES.general;
