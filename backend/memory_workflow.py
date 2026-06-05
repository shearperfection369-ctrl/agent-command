"""JADE OS · Workflow Memory.

Per-topic persistent agent memory. Threads are uniquely keyed on
(thread_type, thread_key), e.g.:
  ("load",     "LD-2026-00481")
  ("customer", "Acme Freight Inc")
  ("issue",    "claim_2026-018")

Each thread holds:
  • Raw transcript (every agent + operator turn)
  • Distilled facts ledger (LLM-summarized: what happened / what we decided /
    open questions / risks / next actions)

Distillation runs after every Nth turn (configurable) and is also exposed via
an explicit endpoint so the operator can force it on close.

Recall is two-tier:
  • Last K raw turns for short-term continuity
  • Full distilled facts ledger for long-term memory (cheap to inject into
    system prompt)

The chat endpoint can opt into auto-binding to a memory thread by passing
`memory_thread_type` + `memory_thread_key` on ChatRequest. When bound,
inbound user messages + outbound assistant text auto-append to the thread.
"""
from __future__ import annotations

import os
import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field, ConfigDict

log = logging.getLogger("jadeos.memory")

ThreadType = Literal["load", "customer", "issue"]

DISTILL_EVERY_TURNS = int(os.environ.get("MEMORY_DISTILL_EVERY_TURNS", "6"))
RECALL_RECENT_TURNS = int(os.environ.get("MEMORY_RECALL_RECENT_TURNS", "8"))


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------- Models ----------

class MemoryTurn(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    thread_id: str
    role: Literal["user", "assistant", "system", "operator", "agent_action"]
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=_utcnow_iso)


class MemoryFact(BaseModel):
    """Distilled fact bullet — produced by the distillation LLM call."""
    model_config = ConfigDict(extra="ignore")
    category: Literal["happened", "decided", "open_question", "risk", "next_action"]
    text: str


class MemoryThread(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    thread_type: ThreadType
    thread_key: str  # load_id, customer name, issue/claim id
    title: Optional[str] = None
    industry: str = "freight_brokerage"
    tags: List[str] = Field(default_factory=list)
    facts: List[MemoryFact] = Field(default_factory=list)
    turn_count: int = 0
    last_distilled_at_turn: int = 0
    status: Literal["active", "closed", "archived"] = "active"
    created_at: str = Field(default_factory=_utcnow_iso)
    updated_at: str = Field(default_factory=_utcnow_iso)


class ThreadCreate(BaseModel):
    thread_type: ThreadType
    thread_key: str
    title: Optional[str] = None
    industry: str = "freight_brokerage"
    tags: List[str] = Field(default_factory=list)


class TurnAppend(BaseModel):
    role: Literal["user", "assistant", "system", "operator", "agent_action"]
    content: str
    metadata: Optional[Dict[str, Any]] = None


# ---------- Storage helpers ----------

async def get_or_create_thread(db, thread_type: str, thread_key: str,
                               *, title: Optional[str] = None,
                               industry: str = "freight_brokerage",
                               tags: Optional[List[str]] = None) -> Dict:
    """Upsert by (thread_type, thread_key). Returns the thread dict."""
    existing = await db.memory_threads.find_one(
        {"thread_type": thread_type, "thread_key": thread_key}, {"_id": 0}
    )
    if existing:
        return existing
    t = MemoryThread(
        thread_type=thread_type,
        thread_key=thread_key,
        title=title or f"{thread_type.upper()} · {thread_key}",
        industry=industry,
        tags=tags or [],
    )
    await db.memory_threads.insert_one(t.model_dump())
    return t.model_dump()


async def append_turn(db, thread_id: str, role: str, content: str,
                      metadata: Optional[Dict] = None) -> Dict:
    turn = MemoryTurn(thread_id=thread_id, role=role, content=content,
                      metadata=metadata or {})
    await db.memory_turns.insert_one(turn.model_dump())
    await db.memory_threads.update_one(
        {"id": thread_id},
        {"$set": {"updated_at": _utcnow_iso()}, "$inc": {"turn_count": 1}},
    )
    return turn.model_dump()


async def get_recent_turns(db, thread_id: str, k: int = RECALL_RECENT_TURNS) -> List[Dict]:
    cursor = db.memory_turns.find({"thread_id": thread_id}, {"_id": 0}).sort("created_at", -1).limit(k)
    rows = await cursor.to_list(k)
    rows.reverse()  # chronological
    return rows


async def get_all_turns(db, thread_id: str) -> List[Dict]:
    return await db.memory_turns.find({"thread_id": thread_id}, {"_id": 0}).sort("created_at", 1).to_list(1000)


# ---------- Distillation ----------

DISTILL_PROMPT = """You distill freight-broker workflow conversations into a structured fact ledger.

Read the turns below and produce a JSON object with five arrays:
  happened       — verifiable events that occurred (driver assigned, BOL signed, claim opened, photos received)
  decided        — decisions the team made (offered $X, accepted/rejected, escalated)
  open_questions — questions outstanding (still need POD? carrier MC status?)
  risks          — risks worth flagging (driver HOS gap, payment overdue, missing docs)
  next_actions   — concrete next steps (chase POD by EOD, file claim, notify shipper)

Be specific: include load IDs, MC numbers, dollar amounts, dates, names when present.
Keep each bullet to one sentence under 28 words.
Output ONLY the JSON object. No prose.
"""


async def distill_thread(db, thread_id: str, llm_chat_factory) -> Dict:
    """Run an LLM pass over the full transcript, replace the facts ledger.

    `llm_chat_factory(session_id, system, provider)` is injected so this module
    stays decoupled from server.py's _llm helper.
    """
    thread = await db.memory_threads.find_one({"id": thread_id}, {"_id": 0})
    if not thread:
        raise ValueError(f"thread {thread_id} not found")
    turns = await get_all_turns(db, thread_id)
    if len(turns) == 0:
        return {"facts": [], "thread_id": thread_id, "turn_count": 0}

    transcript = "\n".join(
        f"[{t['role'].upper()} · {t['created_at']}] {t['content']}"
        for t in turns[-80:]  # cap context cost
    )

    from emergentintegrations.llm.chat import UserMessage, TextDelta, StreamDone

    session_id = f"distill-{thread_id}-{int(datetime.now(timezone.utc).timestamp())}"
    chat = llm_chat_factory(session_id, DISTILL_PROMPT, "anthropic")
    out: List[str] = []
    user_msg = UserMessage(text=f"THREAD · {thread['title']} · {thread_type_label(thread['thread_type'])} · {thread['thread_key']}\n\nTURNS:\n{transcript}")
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
        log.warning("memory · distill failed to parse json · falling back to raw bullets")
        parsed = {"happened": [raw[:280]], "decided": [], "open_questions": [], "risks": [], "next_actions": []}

    facts: List[Dict] = []
    cat_map = {
        "happened": "happened",
        "decided": "decided",
        "open_questions": "open_question",
        "open_question": "open_question",
        "risks": "risk",
        "risk": "risk",
        "next_actions": "next_action",
        "next_action": "next_action",
    }
    for raw_cat, norm_cat in cat_map.items():
        for line in parsed.get(raw_cat, []) or []:
            facts.append({"category": norm_cat, "text": str(line)[:300]})

    # Dedupe by (category, text)
    seen = set()
    fixed: List[Dict] = []
    for f in facts:
        key = (f["category"], f["text"])
        if key in seen:
            continue
        seen.add(key)
        fixed.append(f)

    await db.memory_threads.update_one(
        {"id": thread_id},
        {"$set": {
            "facts": fixed,
            "last_distilled_at_turn": thread.get("turn_count", 0),
            "updated_at": _utcnow_iso(),
        }},
    )
    log.info("memory · distilled thread %s · %d facts", thread_id, len(fixed))
    return {"facts": fixed, "thread_id": thread_id, "turn_count": thread.get("turn_count", 0)}


def thread_type_label(t: str) -> str:
    return {"load": "LOAD / SHIPMENT", "customer": "CUSTOMER / SHIPPER", "issue": "ISSUE / CLAIM"}.get(t, t)


# ---------- Recall ----------

async def build_recall_context(db, thread_id: str) -> str:
    """Produce a compact recall block to inject into an agent system prompt.

    Format:
      MEMORY · THREAD <title>
      [ HAPPENED ]
        - …
      [ DECIDED ]
        - …
      [ OPEN QUESTIONS ]
        - …
      RECENT TURNS:
        [USER] …
        [ASSISTANT] …
    """
    thread = await db.memory_threads.find_one({"id": thread_id}, {"_id": 0})
    if not thread:
        return ""
    facts = thread.get("facts", [])
    by_cat: Dict[str, List[str]] = {}
    for f in facts:
        by_cat.setdefault(f["category"], []).append(f["text"])
    lines = [f"MEMORY · {thread.get('title', '')} ({thread_type_label(thread['thread_type'])} · {thread['thread_key']})"]
    for cat, label in [
        ("happened", "HAPPENED"),
        ("decided", "DECIDED"),
        ("open_question", "OPEN QUESTIONS"),
        ("risk", "RISKS"),
        ("next_action", "NEXT ACTIONS"),
    ]:
        items = by_cat.get(cat, [])
        if items:
            lines.append(f"[ {label} ]")
            for it in items[:8]:
                lines.append(f"  · {it}")

    recent = await get_recent_turns(db, thread_id, k=RECALL_RECENT_TURNS)
    if recent:
        lines.append("RECENT TURNS:")
        for t in recent:
            preview = t["content"][:220].replace("\n", " ")
            lines.append(f"  [{t['role'].upper()}] {preview}")
    return "\n".join(lines)
