"""JADE OS · Immutable Audit Trail.

Append-only event log scoped for "would-stand-up-in-court" defensibility.

Every materially-risky action lands here:
  • quote.validated · agent submitted a quote · severity + decision
  • quote.review.created · breach queued for human approval
  • quote.review.approved · operator approved a breach (override)
  • quote.review.rejected · operator rejected a breach
  • quote.sent · quote actually went out to customer
  • quote.actual.recorded · post-close actual rate recorded
  • rate_floor.created · operator set a manual floor
  • rate_floor.updated · operator amended a floor
  • alert.fired · alert dispatched to webhook/email
  • claim.created · agent drafted a claim
  • claim.filed · claim filed (auto or manual)
  • memory.thread.created · memory thread opened
  • memory.thread.distilled · facts ledger refreshed

Each event has:
  actor       — "agent" | operator email | "system"
  action      — dotted event name (above)
  target_type — what was acted on (quote_review | claim | rate_floor | memory_thread | etc.)
  target_id   — the id of the target document
  before/after — snapshot of relevant state (best-effort)
  evidence_uris — list of pointers (memory thread, claim, BOL etc.)
  metadata    — free-form bag (severity, dollar amounts, lane, etc.)
  hash_prev   — hash of the previous event, forming a tamper-evident chain
  hash_self   — sha256(event payload + hash_prev)

The chain hashing means anyone can re-verify the log offline. Not
blockchain-grade but enough that any single-event tampering is visible.
"""
from __future__ import annotations

import os
import json
import uuid
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict

log = logging.getLogger("jadeos.audit")

# Retention policy per user — option (a): forever, immutable.
AUDIT_RETENTION_DAYS = int(os.environ.get("AUDIT_RETENTION_DAYS", "0"))  # 0 = forever


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AuditEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    seq: int = 0  # monotonically increasing per process; secondary order
    actor: str
    action: str
    target_type: str
    target_id: Optional[str] = None
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    evidence_uris: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    hash_prev: Optional[str] = None
    hash_self: Optional[str] = None
    created_at: str = Field(default_factory=_utcnow_iso)


def _hash_event(payload: Dict[str, Any], prev_hash: Optional[str]) -> str:
    blob = json.dumps({
        "actor": payload.get("actor"),
        "action": payload.get("action"),
        "target_type": payload.get("target_type"),
        "target_id": payload.get("target_id"),
        "before": payload.get("before"),
        "after": payload.get("after"),
        "metadata": payload.get("metadata"),
        "created_at": payload.get("created_at"),
        "prev": prev_hash or "",
    }, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


async def record(db, *, actor: str, action: str, target_type: str,
                 target_id: Optional[str] = None,
                 before: Optional[Dict[str, Any]] = None,
                 after: Optional[Dict[str, Any]] = None,
                 evidence_uris: Optional[List[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None) -> Dict:
    """Append an immutable audit event. Returns the inserted event."""
    prev = await db.audit_events.find_one({}, {"_id": 0, "hash_self": 1, "seq": 1}, sort=[("seq", -1)])
    prev_hash = prev.get("hash_self") if prev else None
    seq = (prev.get("seq", 0) + 1) if prev else 1

    evt = AuditEvent(
        seq=seq, actor=actor, action=action,
        target_type=target_type, target_id=target_id,
        before=before, after=after,
        evidence_uris=evidence_uris or [],
        metadata=metadata or {},
        hash_prev=prev_hash,
    ).model_dump()
    evt["hash_self"] = _hash_event(evt, prev_hash)
    await db.audit_events.insert_one(evt)
    evt.pop("_id", None)
    return evt


async def list_events(db, *, target_type: Optional[str] = None,
                      target_id: Optional[str] = None,
                      actor: Optional[str] = None,
                      action_prefix: Optional[str] = None,
                      limit: int = 200) -> List[Dict]:
    q: Dict[str, Any] = {}
    if target_type:
        q["target_type"] = target_type
    if target_id:
        q["target_id"] = target_id
    if actor:
        q["actor"] = actor
    if action_prefix:
        q["action"] = {"$regex": f"^{action_prefix}"}
    rows = await db.audit_events.find(q, {"_id": 0}).sort("seq", -1).limit(limit).to_list(limit)
    return rows


async def verify_chain(db, limit: int = 1000) -> Dict:
    """Walk the chain and verify hash_self == sha256(event + hash_prev). Returns
    {ok, checked, first_break}. Use this in tests + a manual /audit/verify endpoint."""
    rows = await db.audit_events.find({}, {"_id": 0}).sort("seq", 1).limit(limit).to_list(limit)
    prev_hash: Optional[str] = None
    for r in rows:
        expected = _hash_event(r, prev_hash)
        if r.get("hash_self") != expected:
            return {"ok": False, "checked": rows.index(r), "first_break": r.get("id"), "expected": expected, "stored": r.get("hash_self")}
        if r.get("hash_prev") != prev_hash:
            return {"ok": False, "checked": rows.index(r), "first_break": r.get("id"), "reason": "hash_prev mismatch"}
        prev_hash = r.get("hash_self")
    return {"ok": True, "checked": len(rows)}
