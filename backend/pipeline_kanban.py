"""JadeOS · Lighthouse Pipeline (kanban).

Single source of truth for the revenue funnel that links audits + outreach + lighthouse.

A "pipeline card" represents ONE company across its entire JadeOS lifecycle, with a
stage drawn from a fixed 6-step funnel:

  cold              → outreach logged, no audit yet
  audit_started     → audit created but not yet analyzed
  audit_analyzed    → audit complete with AI Readiness Score
  pilot_discussed   → meeting booked / pricing conversation in flight
  pilot_signed      → engagement agreement signed · into production
  passed            → declined / dead

Cards are auto-created when:
  • POST /api/audit/start                       → cold or audit_started
  • POST /api/outreach/log                      → cold (if no card yet)

Stage transitions are explicit (no silent auto-advance past audit_analyzed) so the
operator stays in control of qualifying / disqualifying prospects.

Endpoints (admin):
  GET    /api/admin/pipeline               → cards grouped by stage + aggregates
  POST   /api/admin/pipeline               → create card manually
  PATCH  /api/admin/pipeline/{id}          → update stage / notes
  DELETE /api/admin/pipeline/{id}
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal, Optional, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


STAGES = ["cold", "audit_started", "audit_analyzed", "pilot_discussed", "pilot_signed", "passed"]
Stage = Literal["cold", "audit_started", "audit_analyzed", "pilot_discussed", "pilot_signed", "passed"]

STAGE_META = {
    "cold":             {"label": "COLD",            "color": "#7c5cff", "order": 0},
    "audit_started":    {"label": "AUDIT STARTED",   "color": "#ffce4f", "order": 1},
    "audit_analyzed":   {"label": "AUDIT ANALYZED",  "color": "#00ffff", "order": 2},
    "pilot_discussed":  {"label": "PILOT DISCUSSED", "color": "#ff3b8a", "order": 3},
    "pilot_signed":     {"label": "PILOT SIGNED",    "color": "#ccff00", "order": 4},
    "passed":           {"label": "PASSED / LOST",   "color": "#666666", "order": 5},
}


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _company_key(name: str) -> str:
    """Stable lower-case slug used to deduplicate cards across audits + outreach."""
    return "".join(ch for ch in name.lower() if ch.isalnum())


class CreateBody(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    industry: Optional[str] = None
    stage: Stage = "cold"
    audit_id: Optional[str] = None
    notes: Optional[str] = None


class PatchBody(BaseModel):
    stage: Optional[Stage] = None
    notes: Optional[str] = None
    industry: Optional[str] = None
    audit_id: Optional[str] = None


def _db():
    from server import db  # noqa: WPS433
    return db


async def upsert_card(
    company_name: str,
    industry: Optional[str] = None,
    stage: Stage = "cold",
    audit_id: Optional[str] = None,
    promote_only: bool = True,
) -> dict:
    """Ensure a pipeline card exists for `company_name`.

    If `promote_only` is True and an existing card has a HIGHER stage order than the
    incoming stage, the existing stage is preserved (we never auto-demote from
    pilot_signed back to cold, for example).
    """
    key = _company_key(company_name)
    db = _db()
    existing = await db.pipeline_cards.find_one({"company_key": key}, {"_id": 0})

    now = _utcnow_iso()
    if existing:
        new_stage = existing.get("stage", "cold")
        if not promote_only or STAGE_META[stage]["order"] > STAGE_META[new_stage]["order"]:
            new_stage = stage
        upd: dict[str, Any] = {"updated_at": now, "stage": new_stage}
        if industry and not existing.get("industry"):
            upd["industry"] = industry
        if audit_id and not existing.get("audit_id"):
            upd["audit_id"] = audit_id
        # Always refresh display name (in case casing changed)
        if existing.get("company_name") != company_name:
            upd["company_name"] = company_name
        await db.pipeline_cards.update_one({"company_key": key}, {"$set": upd})
        return {**existing, **upd}

    card = {
        "id": uuid.uuid4().hex[:16],
        "company_key": key,
        "company_name": company_name,
        "industry": industry,
        "stage": stage,
        "audit_id": audit_id,
        "notes": None,
        "created_at": now,
        "updated_at": now,
    }
    await db.pipeline_cards.insert_one(card)
    return card


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(prefix="/admin/pipeline", tags=["pipeline"])


@router.get("")
async def list_pipeline():
    db = _db()
    docs = await db.pipeline_cards.find({}, {"_id": 0}).sort("updated_at", -1).to_list(1000)

    # Enrich each card with the latest audit snapshot (score / tier / savings)
    # and the latest outreach send (campaign_id, sent_at, status).
    audit_index: dict[str, dict] = {}
    keys = list({c["company_key"] for c in docs})
    if keys:
        # Build an audit map keyed by company_key (case-insensitive on company_name)
        async for a in db.audits.find({}, {"_id": 0}):
            k = _company_key(a.get("company_name", ""))
            # Keep most recent analyzed audit, else most recent any
            cur = audit_index.get(k)
            if cur is None or (a.get("status") == "analyzed" and cur.get("status") != "analyzed"):
                audit_index[k] = a

    outreach_index: dict[str, dict] = {}
    if keys:
        async for o in db.outreach_log.find({}, {"_id": 0}).sort("sent_at", -1):
            k = _company_key(o.get("recipient_company") or "")
            if k and k not in outreach_index:
                outreach_index[k] = o

    enriched = []
    for c in docs:
        k = c["company_key"]
        a = audit_index.get(k)
        o = outreach_index.get(k)
        enriched.append({
            **c,
            "score":           a.get("analysis", {}).get("scores", {}).get("overall_score") if a and a.get("analysis") else None,
            "tier":            a.get("analysis", {}).get("scores", {}).get("tier") if a and a.get("analysis") else None,
            "savings_central": a.get("analysis", {}).get("savings", {}).get("annual_savings_central_usd") if a and a.get("analysis") else None,
            "audit_status":    a.get("status") if a else None,
            "audit_id":        c.get("audit_id") or (a.get("id") if a else None),
            "last_outreach_campaign":  o.get("campaign_id") if o else None,
            "last_outreach_sent_at":   o.get("sent_at") if o else None,
            "last_outreach_status":    o.get("status") if o else None,
        })

    # Group by stage
    by_stage: dict[str, list] = {s: [] for s in STAGES}
    total_savings = 0
    for c in enriched:
        by_stage[c.get("stage", "cold")].append(c)
        if c.get("stage") == "pilot_signed" and c.get("savings_central"):
            total_savings += c["savings_central"]

    return {
        "stages": STAGE_META,
        "by_stage": by_stage,
        "total_cards": len(enriched),
        "kpis": {
            "cold":             len(by_stage["cold"]),
            "audit_started":    len(by_stage["audit_started"]),
            "audit_analyzed":   len(by_stage["audit_analyzed"]),
            "pilot_discussed":  len(by_stage["pilot_discussed"]),
            "pilot_signed":     len(by_stage["pilot_signed"]),
            "passed":           len(by_stage["passed"]),
            "annual_savings_signed_usd": total_savings,
        },
    }


@router.post("")
async def create_card(body: CreateBody):
    card = await upsert_card(
        company_name=body.company_name,
        industry=body.industry,
        stage=body.stage,
        audit_id=body.audit_id,
        promote_only=False,  # explicit create can set any stage
    )
    if body.notes:
        await _db().pipeline_cards.update_one(
            {"company_key": card["company_key"]},
            {"$set": {"notes": body.notes}},
        )
        card["notes"] = body.notes
    return card


@router.patch("/{card_id}")
async def patch_card(card_id: str, body: PatchBody):
    upd: dict[str, Any] = {"updated_at": _utcnow_iso()}
    if body.stage is not None:
        if body.stage not in STAGES:
            raise HTTPException(400, "invalid stage")
        upd["stage"] = body.stage
    if body.notes is not None:
        upd["notes"] = body.notes
    if body.industry is not None:
        upd["industry"] = body.industry
    if body.audit_id is not None:
        upd["audit_id"] = body.audit_id
    res = await _db().pipeline_cards.update_one({"id": card_id}, {"$set": upd})
    if res.matched_count == 0:
        raise HTTPException(404, "card not found")
    doc = await _db().pipeline_cards.find_one({"id": card_id}, {"_id": 0})
    return doc


@router.delete("/{card_id}")
async def delete_card(card_id: str):
    res = await _db().pipeline_cards.delete_one({"id": card_id})
    return {"deleted": res.deleted_count}
