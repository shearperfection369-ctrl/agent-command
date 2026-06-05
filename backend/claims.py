"""JADE OS · Claims module.

Three claim kinds in scope:
  • cargo            — damaged/lost freight, claim against carrier insurance
  • detention        — driver/truck waiting time beyond free hours → bill shipper/consignee
  • overage_shortage — BOL pallet/piece count mismatch on delivery

Filing autonomy is mixed-mode (operator-chosen):
  • Claims under CLAIMS_AUTO_FILE_LIMIT_USD (default $500) auto-file when drafted.
  • Higher-value claims queue with status="ready_for_review" — operator clicks FILE.

On filing, the claim payload is delivered to every active webhook with
kind="claims" (reuses the existing /api/webhooks infra). Until a webhook is
configured the claim is logged + held; nothing breaks.
"""
from __future__ import annotations

import os
import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field, ConfigDict

log = logging.getLogger("jadeos.claims")

ClaimKind = Literal["cargo", "detention", "overage_shortage"]
ClaimStatus = Literal["draft", "ready_for_review", "filed", "acknowledged", "resolved", "denied", "withdrawn"]

AUTO_FILE_LIMIT_USD = float(os.environ.get("CLAIMS_AUTO_FILE_LIMIT_USD", "500"))


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------- Models ----------

class ClaimPartyInfo(BaseModel):
    """Carrier / shipper / consignee info on the claim."""
    model_config = ConfigDict(extra="ignore")
    role: Literal["carrier", "shipper", "consignee", "broker"]
    name: Optional[str] = None
    mc_number: Optional[str] = None
    dot_number: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class Claim(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    claim_number: str  # human-readable, auto-generated if not provided
    kind: ClaimKind
    status: ClaimStatus = "draft"
    # Linked memory thread (optional but recommended)
    memory_thread_id: Optional[str] = None
    # Load / shipment context
    load_id: Optional[str] = None
    bol_number: Optional[str] = None
    pickup_date: Optional[str] = None
    delivery_date: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    parties: List[ClaimPartyInfo] = Field(default_factory=list)
    # Financials
    claim_amount_usd: float = 0.0
    auto_filed: bool = False
    # Body / evidence
    title: str
    summary: str
    facts: List[str] = Field(default_factory=list)
    evidence_uris: List[str] = Field(default_factory=list)  # photo / pdf / email refs
    requested_remedy: Optional[str] = None
    # Outcome
    delivery_attempts: int = 0
    delivery_log: List[Dict[str, Any]] = Field(default_factory=list)
    resolution_notes: Optional[str] = None
    # Audit
    created_by: str = "agent"  # "agent" | operator email
    created_at: str = Field(default_factory=_utcnow_iso)
    updated_at: str = Field(default_factory=_utcnow_iso)
    filed_at: Optional[str] = None


class ClaimDraftRequest(BaseModel):
    kind: ClaimKind
    # The agent can draft from either a memory_thread_id or freeform context_text
    memory_thread_id: Optional[str] = None
    context_text: Optional[str] = None
    # Optional structured hints
    load_id: Optional[str] = None
    bol_number: Optional[str] = None
    claim_amount_usd: Optional[float] = None
    parties: Optional[List[ClaimPartyInfo]] = None
    provider: Literal["anthropic", "openai"] = "anthropic"


class ClaimUpdate(BaseModel):
    status: Optional[ClaimStatus] = None
    resolution_notes: Optional[str] = None
    claim_amount_usd: Optional[float] = None
    requested_remedy: Optional[str] = None


# ---------- Claim number generator ----------

def make_claim_number(kind: str) -> str:
    """JCL-{KIND}-{YYYYMM}-{short_uuid}. Human-readable, sortable."""
    now = datetime.now(timezone.utc)
    code = {"cargo": "CGO", "detention": "DET", "overage_shortage": "OSD"}.get(kind, "CLM")
    return f"JCL-{code}-{now:%Y%m}-{uuid.uuid4().hex[:6].upper()}"


# ---------- LLM drafting ----------

DRAFT_PROMPTS: Dict[str, str] = {
    "cargo": """You draft cargo damage / loss claims for a freight broker.

Read the context (transcript, memory facts, freeform notes) and output JSON with:
  title           — one-line claim summary (e.g., "Cargo damage · 3 pallets crushed · BOL 8842")
  summary         — 2-4 sentence neutral factual summary of what happened
  facts           — array of 5-10 verifiable fact bullets (dates, names, locations, MC#, dollar amounts, POD/BOL refs)
  requested_remedy — exact dollar amount + reason (e.g., "$3,240 — full replacement value per invoice INV-552")
  claim_amount_usd — number only (best estimate from context, 0 if unknown)
  parties          — array of { role, name, mc_number, email } objects you can identify
  load_id          — best guess from context
  bol_number       — best guess from context
Output ONLY the JSON. No markdown fences.""",
    "detention": """You draft detention / accessorial billing claims for a freight broker.

Output JSON with:
  title           — e.g., "Detention · 4.5h beyond free time · LD-2026-481"
  summary         — what happened, when driver arrived, when they were released
  facts           — bullets with timestamps, location, free-time policy, total detained hours, rate-per-hour
  requested_remedy — exact dollar amount + math (hours × rate)
  claim_amount_usd — number only
  parties          — { role, name, mc_number, email }
  load_id          — best guess
  bol_number       — best guess
Output ONLY the JSON. No markdown fences.""",
    "overage_shortage": """You draft overage / shortage / damage claims (OS&D) for a freight broker.

Output JSON with:
  title           — e.g., "Shortage · 2 pallets · BOL 8842"
  summary         — BOL count vs delivered count, where the discrepancy was found, who signed
  facts           — bullets with BOL piece count, actual delivered count, signing party, time of receipt, photos taken
  requested_remedy — dollar amount per missing/damaged unit × count
  claim_amount_usd — number only
  parties          — { role, name, mc_number, email }
  load_id          — best guess
  bol_number       — best guess
Output ONLY the JSON. No markdown fences.""",
}


async def draft_claim(
    db,
    *,
    kind: str,
    memory_thread_id: Optional[str] = None,
    context_text: Optional[str] = None,
    provider: str = "anthropic",
    llm_chat_factory,
    memory_recall_fn,  # callable async (db, thread_id) -> str
    extra_hints: Optional[Dict[str, Any]] = None,
) -> Dict:
    """Run an LLM pass over the context and return a parsed claim draft."""
    context_parts: List[str] = []
    if memory_thread_id:
        recall = await memory_recall_fn(db, memory_thread_id)
        if recall:
            context_parts.append(recall)
    if context_text:
        context_parts.append(f"OPERATOR NOTES:\n{context_text}")
    if extra_hints:
        context_parts.append(f"STRUCTURED HINTS:\n{json.dumps(extra_hints, indent=2)}")

    if not context_parts:
        raise ValueError("draft_claim requires at least memory_thread_id, context_text, or extra_hints")

    full_context = "\n\n".join(context_parts)
    sys_prompt = DRAFT_PROMPTS[kind]

    from emergentintegrations.llm.chat import UserMessage, TextDelta, StreamDone

    session_id = f"claim-draft-{uuid.uuid4().hex[:8]}"
    chat = llm_chat_factory(session_id, sys_prompt, provider)
    out: List[str] = []
    user_msg = UserMessage(text=full_context)
    async for ev in chat.stream_message(user_msg):
        if isinstance(ev, TextDelta):
            out.append(ev.content)
        elif isinstance(ev, StreamDone):
            break
    raw = "".join(out).strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        log.warning("claims · draft failed to parse json · using raw text")
        parsed = {"title": f"{kind.upper()} CLAIM · auto-draft (parse failed)",
                  "summary": raw[:500], "facts": [], "claim_amount_usd": 0}

    # Normalize
    claim_amount = float(parsed.get("claim_amount_usd") or 0)
    parties_in = parsed.get("parties") or []
    parties: List[Dict] = []
    for p in parties_in:
        if isinstance(p, dict) and p.get("role") in ("carrier", "shipper", "consignee", "broker"):
            parties.append({
                "role": p["role"],
                "name": p.get("name"),
                "mc_number": p.get("mc_number"),
                "dot_number": p.get("dot_number"),
                "email": p.get("email"),
                "phone": p.get("phone"),
            })

    return {
        "kind": kind,
        "title": str(parsed.get("title") or f"{kind.upper()} CLAIM"),
        "summary": str(parsed.get("summary") or ""),
        "facts": [str(f) for f in (parsed.get("facts") or [])][:25],
        "requested_remedy": parsed.get("requested_remedy"),
        "claim_amount_usd": claim_amount,
        "parties": parties,
        "load_id": parsed.get("load_id") or (extra_hints or {}).get("load_id"),
        "bol_number": parsed.get("bol_number") or (extra_hints or {}).get("bol_number"),
        "memory_thread_id": memory_thread_id,
    }


# ---------- Auto-file decision ----------

def should_auto_file(claim_amount_usd: float) -> bool:
    """Auto-file low-dollar claims to keep operators focused on judgment calls."""
    return claim_amount_usd > 0 and claim_amount_usd <= AUTO_FILE_LIMIT_USD


# ---------- Delivery payload ----------

def to_webhook_payload(claim: Dict) -> Dict:
    """Compact, carrier-ready payload that we ship to every active claims webhook."""
    return {
        "claim_number": claim.get("claim_number"),
        "kind": claim.get("kind"),
        "status": claim.get("status"),
        "title": claim.get("title"),
        "summary": claim.get("summary"),
        "load_id": claim.get("load_id"),
        "bol_number": claim.get("bol_number"),
        "claim_amount_usd": claim.get("claim_amount_usd"),
        "requested_remedy": claim.get("requested_remedy"),
        "facts": claim.get("facts", []),
        "parties": claim.get("parties", []),
        "filed_at": claim.get("filed_at"),
        "auto_filed": claim.get("auto_filed", False),
        "claim_url": None,  # set by caller if portal URL available
    }
