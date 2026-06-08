"""JadeOS · Outreach campaign engine.

5 pre-baked campaign templates the operator uses to push the trio (JadeOS Quantum
AI + JadeOS-Agent Suite + Hot Shot TMS) and the consulting audit offer:

  1. broker_cold_email      — cold email to freight brokers · pushes free audit
  2. lighthouse_trio        — pitch the trinity to potential lighthouse customers
  3. consulting_upsell      — post-audit upsell from CURIOUS/LEARNING tier prospects
  4. linkedin_dm            — short LinkedIn DM script
  5. followup_sequence      — 5-step follow-up sequence after first send

Each campaign supports template variables (`{{company}}`, `{{first_name}}`,
`{{industry_pain}}`, etc.). The operator can:
  • Fetch templates                       GET  /api/outreach/campaigns
  • Render with variables                 POST /api/outreach/render
  • Log a send                            POST /api/outreach/log
  • View tracker (admin)                  GET  /api/admin/outreach/log
  • Mark a status update                  PATCH /api/admin/outreach/log/{id}
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ============================================================
# TEMPLATES
# ============================================================

CAMPAIGNS = {
    "broker_cold_email": {
        "id": "broker_cold_email",
        "label": "BROKER COLD EMAIL · FREE AUDIT",
        "channel": "email",
        "color": "#ccff00",
        "audience": "Freight brokers · 5-200 trucks · independents and small fleets",
        "subject": "Free AI readiness audit for {{company}} · 12-page report · $0",
        "body": (
"{{first_name}},\n\n"
"I'm a 13-year freight operator running JadeOS — an AI agent platform purpose-built for "
"brokers like {{company}}. Not another chatbot wrapper. Operator-grade.\n\n"
"I'm running a free AI Readiness Audit for the first 5 brokers who say yes. You walk away "
"with a 12-page report scored 0-100, a 90-day pilot proposal with success metrics declared "
"upfront, and an annual savings estimate. Cost: $0. No obligation.\n\n"
"Takes 30 minutes of your time. I need 90 days of load data + your carrier roster — "
"checklist attached.\n\n"
"Worth 30 minutes? Reply YES and I'll send a calendar link.\n\n"
"Oliver Cummins · Founder\n"
"JadeOS · onejades.com · founder@jadeos.ai\n"
"+1 (763) 443-6659"
        ),
        "cta": "Reply YES · I'll send calendar link",
        "variables": ["first_name", "company"],
        "attach_pdfs": ["data-checklist.pdf"],
    },
    "lighthouse_trio": {
        "id": "lighthouse_trio",
        "label": "LIGHTHOUSE TRINITY PITCH",
        "channel": "email",
        "color": "#00ffff",
        "audience": "Potential Lighthouse customers · operators ready to deploy AI",
        "subject": "{{company}} — three products, one stack, founder-led pilot",
        "body": (
"{{first_name}},\n\n"
"JadeOS ships as a trinity, not one product. Three things that work together:\n\n"
"  1. JadeOS Quantum AI — flagship AI command center · 50+ modules · voice-first 'Hey Jade' · "
"persistent memory · 128-qubit Qiskit Aer\n\n"
"  2. JadeOS-Agent Suite — six freight-vertical agents (Dispatch · Route+Fuel · Compliance · "
"Pricing · Driver Lifecycle · Predictive Maintenance) that sit on top of any TMS\n\n"
"  3. Hot Shot TMS — operator-built system of record for the underserved hot-shot segment\n\n"
"I'm taking on the first 5 Lighthouse customers personally. Founder-led implementation. "
"Free 90-day pilot with success metrics declared in writing before kickoff. After that, "
"production license at per-seat pricing.\n\n"
"30-minute call? Walk you through /demo/quantum + /demo/tms live.\n\n"
"Oliver\n"
"JadeOS · onejades.com · founder@jadeos.ai\n"
"linkedin.com/in/oliver-cummins-a27304a3/"
        ),
        "cta": "Reply with 3 calendar slots",
        "variables": ["first_name", "company"],
        "attach_pdfs": [],
    },
    "consulting_upsell": {
        "id": "consulting_upsell",
        "label": "CONSULTING UPSELL · POST-AUDIT",
        "channel": "email",
        "color": "#7c5cff",
        "audience": "CURIOUS / LEARNING tier prospects after audit — not yet pilot-ready",
        "subject": "{{company}} · your audit score + the 60-day data hygiene sprint",
        "body": (
"{{first_name}},\n\n"
"Your audit came back at {{score}}/100 — tier {{tier}}. You're not pilot-ready today, "
"but you're closer than 80% of the brokers I've audited.\n\n"
"Before we pilot agents, you need 60 days of foundation work — data structure, process "
"documentation, integration cleanup. I run that engagement as a fixed-fee consulting sprint "
"so we de-risk the pilot before any seat-pricing conversation.\n\n"
"  • 60 days · $24,000 flat\n"
"  • Weekly working session · deliverables every Friday\n"
"  • Exit: re-audit at day 60 · target tier BUILDER+\n"
"  • Then we pilot agents with a clean foundation\n\n"
"Worth a 30-minute scope conversation? I'll bring the day-by-day plan.\n\n"
"Oliver\n"
"JadeOS · founder@jadeos.ai"
        ),
        "cta": "Reply with 30-min slot",
        "variables": ["first_name", "company", "score", "tier"],
        "attach_pdfs": [],
    },
    "linkedin_dm": {
        "id": "linkedin_dm",
        "label": "LINKEDIN DM · SHORT",
        "channel": "linkedin",
        "color": "#ff3b8a",
        "audience": "Founders / VPs of Ops at logistics + freight companies",
        "subject": "(LinkedIn DM)",
        "body": (
"{{first_name}} — I run JadeOS, operator-grade AI agents purpose-built for freight. "
"Running a free 12-page AI readiness audit for the first 5 operators I talk to this month. "
"30 min. Worth a look? — Oliver, JadeOS · onejades.com"
        ),
        "cta": "Reply if interested",
        "variables": ["first_name"],
        "attach_pdfs": [],
    },
    "followup_sequence": {
        "id": "followup_sequence",
        "label": "5-STEP FOLLOW-UP SEQUENCE",
        "channel": "email",
        "color": "#ffce4f",
        "audience": "Any prospect who opened the first email but didn't reply",
        "subject": "(5 emails · spaced 3 / 5 / 7 / 14 / 30 days)",
        "body": (
"DAY 3 · 'Re: Free AI readiness audit'\n"
"{{first_name}}, did the audit checklist make it through? Happy to walk you through it on "
"a 15-min call. — Oliver\n\n"
"DAY 5 · 'Quick clarification'\n"
"{{first_name}}, common question: data stays on your side until we mutually decide to pilot. "
"Audit is a desk exercise on the 30 questions only. Easier? — Oliver\n\n"
"DAY 7 · '60 seconds — would this be useful?'\n"
"{{first_name}}, one-line answer is enough — does {{company}} want an AI readiness score and "
"a 90-day pilot proposal? Free, 30 minutes. — Oliver\n\n"
"DAY 14 · 'Looping back · {{company}}'\n"
"{{first_name}}, no pressure — I'll stop pinging after this one. If timing's wrong, just "
"say 'not now' and I'll circle back in Q[N]. — Oliver\n\n"
"DAY 30 · 'Quarter is closing'\n"
"{{first_name}}, end-of-quarter check. Two slots left in this round of free audits. "
"If interested, reply YES. If not, I'll archive the thread. — Oliver"
        ),
        "cta": "One-word reply: YES / NOT NOW / NO",
        "variables": ["first_name", "company"],
        "attach_pdfs": [],
    },
}


# ============================================================
# MODELS
# ============================================================

class RenderBody(BaseModel):
    campaign_id: str
    variables: dict[str, str] = Field(default_factory=dict)


class LogBody(BaseModel):
    campaign_id: str
    recipient_name: str = Field(min_length=1, max_length=120)
    recipient_company: Optional[str] = None
    recipient_email: Optional[str] = None
    recipient_linkedin: Optional[str] = None
    notes: Optional[str] = None


class LogPatchBody(BaseModel):
    status: Optional[Literal["sent", "opened", "replied", "meeting_booked", "passed"]] = None
    notes: Optional[str] = None


# ============================================================
# RENDER
# ============================================================

def render_template(template: str, variables: dict[str, str]) -> str:
    """Replace {{var_name}} with values; leave unmatched vars intact for visibility."""
    def repl(m: re.Match) -> str:
        key = m.group(1).strip()
        return variables.get(key, m.group(0))
    return re.sub(r"\{\{\s*([\w_]+)\s*\}\}", repl, template)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(prefix="/outreach", tags=["outreach"])


@router.get("/campaigns")
async def list_campaigns():
    return {"campaigns": list(CAMPAIGNS.values())}


@router.post("/render")
async def render_campaign(body: RenderBody):
    c = CAMPAIGNS.get(body.campaign_id)
    if not c:
        raise HTTPException(404, "campaign not found")
    return {
        "campaign_id": c["id"],
        "subject": render_template(c["subject"], body.variables),
        "body":    render_template(c["body"],    body.variables),
        "cta":     c["cta"],
        "channel": c["channel"],
        "attach_pdfs": c.get("attach_pdfs", []),
    }


def _db():
    from server import db  # noqa: WPS433
    return db


@router.post("/log")
async def log_send(body: LogBody):
    if body.campaign_id not in CAMPAIGNS:
        raise HTTPException(404, "campaign not found")
    log_id = uuid.uuid4().hex[:16]
    doc = {
        "id": log_id,
        "campaign_id": body.campaign_id,
        "recipient_name": body.recipient_name,
        "recipient_company": body.recipient_company,
        "recipient_email": body.recipient_email,
        "recipient_linkedin": body.recipient_linkedin,
        "status": "sent",
        "sent_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
        "notes": body.notes,
    }
    await _db().outreach_log.insert_one(doc)
    # Ensure a pipeline card exists (stage=cold unless a higher one already set)
    try:
        if body.recipient_company:
            from pipeline_kanban import upsert_card
            await upsert_card(
                company_name=body.recipient_company,
                stage="cold",
            )
    except Exception:
        pass
    return {"id": log_id, **{k: v for k, v in doc.items() if k != "_id"}}


admin_router = APIRouter(prefix="/admin/outreach", tags=["outreach-admin"])


@admin_router.get("/log")
async def list_log(campaign_id: Optional[str] = None, status: Optional[str] = None, limit: int = 500):
    q: dict[str, Any] = {}
    if campaign_id: q["campaign_id"] = campaign_id
    if status:      q["status"] = status
    docs = await _db().outreach_log.find(q, {"_id": 0}).sort("sent_at", -1).to_list(limit)

    # Aggregate stats per campaign
    stats: dict[str, dict[str, int]] = {}
    for d in docs:
        cid = d["campaign_id"]
        s = d["status"]
        stats.setdefault(cid, {"sent": 0, "replied": 0, "meeting_booked": 0, "passed": 0})
        stats[cid].setdefault(s, 0)
        stats[cid][s] = stats[cid].get(s, 0) + 1
    return {"log": docs, "total": len(docs), "stats": stats}


@admin_router.patch("/log/{log_id}")
async def patch_log(log_id: str, body: LogPatchBody):
    upd: dict[str, Any] = {"updated_at": _utcnow_iso()}
    if body.status is not None:
        upd["status"] = body.status
    if body.notes is not None:
        upd["notes"] = body.notes
    res = await _db().outreach_log.update_one({"id": log_id}, {"$set": upd})
    if res.matched_count == 0:
        raise HTTPException(404, "log not found")
    return {"updated": True, "id": log_id}


@admin_router.delete("/log/{log_id}")
async def delete_log(log_id: str):
    res = await _db().outreach_log.delete_one({"id": log_id})
    return {"deleted": res.deleted_count}
