"""JADE OS — AI Agents for Minneapolis operators.

FastAPI backend providing:
- Public lead capture
- Interactive agent demos (chat, BOL extraction, outreach drafting, lead qualification)
- Admin JWT auth + leads dashboard
- Streaming Claude/OpenAI chat via Emergent universal key
"""
from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Literal, Annotated
from pathlib import Path
from datetime import datetime, timezone, timedelta
import os
import uuid
import json
import logging
import asyncio
import bcrypt
import jwt

from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
EMERGENT_LLM_KEY = os.environ["EMERGENT_LLM_KEY"]
JWT_SECRET = os.environ["JWT_SECRET"]
ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

app = FastAPI(title="JADE OS API")
api = APIRouter(prefix="/api")
security = HTTPBearer(auto_error=False)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("jadeos")


# -------------------- Models --------------------
def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Lead(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    company: str
    phone: Optional[str] = None
    vertical: str = "freight_brokerage"
    company_size: Optional[str] = None
    use_case: Optional[str] = None
    monthly_volume: Optional[str] = None
    source: str = "website"
    score: Optional[int] = None
    qualification_summary: Optional[str] = None
    status: str = "new"
    created_at: str = Field(default_factory=_utcnow_iso)


class LeadCreate(BaseModel):
    name: str
    email: EmailStr
    company: str
    phone: Optional[str] = None
    vertical: str = "freight_brokerage"
    company_size: Optional[str] = None
    use_case: Optional[str] = None
    monthly_volume: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    email: str


class AgentRun(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_type: Literal["chat", "extract_bol", "draft_outreach", "qualify_lead"]
    model: str
    provider: str
    input_preview: str
    output_preview: Optional[str] = None
    tokens_in: Optional[int] = None
    success: bool = True
    created_at: str = Field(default_factory=_utcnow_iso)


class ChatRequest(BaseModel):
    session_id: str
    message: str
    provider: Literal["anthropic", "openai"] = "anthropic"
    model: Optional[str] = None


class ExtractBOLRequest(BaseModel):
    text: str
    provider: Literal["anthropic", "openai"] = "anthropic"


class OutreachRequest(BaseModel):
    load_summary: str
    carrier_name: Optional[str] = "Operator"
    tone: str = "direct"
    provider: Literal["anthropic", "openai"] = "anthropic"


class QualifyLeadRequest(BaseModel):
    company: str
    role: str
    use_case: str
    monthly_volume: Optional[str] = None
    budget: Optional[str] = None
    timeline: Optional[str] = None
    provider: Literal["anthropic", "openai"] = "anthropic"


# -------------------- Auth helpers --------------------
def _hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def _verify_pw(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())


def _make_token(email: str) -> str:
    payload = {
        "sub": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


async def require_admin(creds: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    if not creds:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing token")
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    email = payload.get("sub")
    user = await db.admins.find_one({"email": email}, {"_id": 0})
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Admin not found")
    return email


# -------------------- LLM helpers --------------------
SYSTEM_PROMPT_BROKER = (
    "You are JADE — the operator-grade AI agent for freight brokers, 3PLs, and dispatchers in the upper Midwest. "
    "You speak short. Action verbs. Console-style precision. Light operator pet-names ('operator', 'captain') used sparingly. "
    "Tech words allowed: tape, deck, vault, console, drop, lab, rig. Never bubbly. Never apologetic. Never marketing-speak. "
    "You know freight: BOLs, load postings, lane rates, deadhead, RPM, MC numbers, DAT/Truckstop conventions, FTL/LTL, "
    "shipper/consignee, accessorials, detention, layover. You help match loads, draft carrier outreach, "
    "extract structured data, and route tier-1 questions. Stay factual. Cite when uncertain."
)

DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-5-20250929",
    "openai": "gpt-5.2",
}


def _llm(session_id: str, system_prompt: str, provider: str, model: Optional[str] = None) -> LlmChat:
    m = model or DEFAULT_MODELS[provider]
    return LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=session_id,
        system_message=system_prompt,
    ).with_model(provider, m)


async def _log_run(agent_type: str, provider: str, model: str, inp: str, out: str, success: bool = True) -> None:
    run = AgentRun(
        agent_type=agent_type,
        provider=provider,
        model=model,
        input_preview=inp[:300],
        output_preview=(out or "")[:500],
        success=success,
    )
    await db.agent_runs.insert_one(run.model_dump())


# -------------------- Routes: health --------------------
@api.get("/")
async def root():
    return {"service": "JADE OS API", "status": "online", "ts": _utcnow_iso()}


# -------------------- Routes: auth --------------------
@api.post("/auth/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    user = await db.admins.find_one({"email": body.email}, {"_id": 0})
    if not user or not _verify_pw(body.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    return TokenResponse(access_token=_make_token(body.email), email=body.email)


@api.get("/auth/me")
async def me(email: str = Depends(require_admin)):
    return {"email": email}


# -------------------- Routes: leads --------------------
@api.post("/leads", response_model=Lead)
async def create_lead(body: LeadCreate):
    lead = Lead(**body.model_dump())
    await db.leads.insert_one(lead.model_dump())
    return lead


@api.get("/leads", response_model=List[Lead])
async def list_leads(_: str = Depends(require_admin)):
    docs = await db.leads.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return [Lead(**d) for d in docs]


@api.patch("/leads/{lead_id}")
async def update_lead_status(lead_id: str, status_value: str, _: str = Depends(require_admin)):
    res = await db.leads.update_one({"id": lead_id}, {"$set": {"status": status_value}})
    if res.matched_count == 0:
        raise HTTPException(404, "Not found")
    return {"ok": True}


# -------------------- Routes: agent demo --------------------
@api.post("/agent/chat")
async def agent_chat(body: ChatRequest):
    chat = _llm(body.session_id, SYSTEM_PROMPT_BROKER, body.provider, body.model)
    user_msg = UserMessage(text=body.message)
    model_used = body.model or DEFAULT_MODELS[body.provider]

    async def gen():
        full = []
        try:
            async for ev in chat.stream_message(user_msg):
                if isinstance(ev, TextDelta):
                    full.append(ev.content)
                    yield f"data: {json.dumps({'delta': ev.content})}\n\n"
                elif isinstance(ev, StreamDone):
                    break
            yield f"data: {json.dumps({'done': True})}\n\n"
            await _log_run("chat", body.provider, model_used, body.message, "".join(full))
        except Exception as e:
            log.exception("chat stream error")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


EXTRACT_SYSTEM = (
    "You are JADE's data extraction subroutine. Extract a load posting / BOL / shipment text into strict JSON. "
    "Return ONLY a JSON object — no prose, no markdown fences. "
    "Schema: {origin_city, origin_state, dest_city, dest_state, equipment, weight_lbs, pickup_date, "
    "delivery_date, rate_usd, commodity, miles, mc_number, reference_number, contact_name, contact_phone, notes}. "
    "Use null for unknown fields. Numbers as numbers. Dates as ISO YYYY-MM-DD when possible."
)


def _strip_json(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
        if t.lower().startswith("json"):
            t = t[4:]
        t = t.strip("` \n")
    return t


@api.post("/agent/extract-bol")
async def extract_bol(body: ExtractBOLRequest):
    session = str(uuid.uuid4())
    chat = _llm(session, EXTRACT_SYSTEM, body.provider)
    model = DEFAULT_MODELS[body.provider]
    try:
        raw = []
        async for ev in chat.stream_message(UserMessage(text=body.text)):
            if isinstance(ev, TextDelta):
                raw.append(ev.content)
            elif isinstance(ev, StreamDone):
                break
        raw_text = "".join(raw)
        try:
            data = json.loads(_strip_json(raw_text))
        except Exception:
            data = {"raw": raw_text, "parse_error": True}
        await _log_run("extract_bol", body.provider, model, body.text, json.dumps(data)[:500])
        return {"extracted": data}
    except Exception as e:
        log.exception("extract error")
        raise HTTPException(500, str(e))


OUTREACH_SYSTEM = (
    "You are JADE's outreach drafter for freight dispatchers. Write a short, no-fluff carrier outreach email. "
    "5–8 sentences max. Subject line on first line prefixed 'Subject: '. Direct. Includes ask, lane, rate or 'open to rate', "
    "pickup window, MC/contact. No emojis. No 'I hope this finds you well'. Operator-grade."
)


@api.post("/agent/draft-outreach")
async def draft_outreach(body: OutreachRequest):
    session = str(uuid.uuid4())
    chat = _llm(session, OUTREACH_SYSTEM, body.provider)
    model = DEFAULT_MODELS[body.provider]
    prompt = (
        f"Carrier: {body.carrier_name}\nTone: {body.tone}\nLoad summary:\n{body.load_summary}\n"
        "Draft the email now."
    )
    try:
        out = []
        async for ev in chat.stream_message(UserMessage(text=prompt)):
            if isinstance(ev, TextDelta):
                out.append(ev.content)
            elif isinstance(ev, StreamDone):
                break
        text = "".join(out).strip()
        await _log_run("draft_outreach", body.provider, model, body.load_summary, text)
        return {"email": text}
    except Exception as e:
        log.exception("outreach error")
        raise HTTPException(500, str(e))


QUALIFY_SYSTEM = (
    "You are JADE's sales qualification analyst. Score a B2B lead 0-100 for fit with JADE OS "
    "(AI agents for Minneapolis logistics / freight / 3PL / ops automation). "
    "Return ONLY JSON with fields: score (0-100), tier ('hot'|'warm'|'cold'), rationale (<= 60 words), "
    "next_action (1 sentence), red_flags (array of strings), green_flags (array of strings)."
)


@api.post("/agent/qualify-lead")
async def qualify_lead(body: QualifyLeadRequest):
    session = str(uuid.uuid4())
    chat = _llm(session, QUALIFY_SYSTEM, body.provider)
    model = DEFAULT_MODELS[body.provider]
    prompt = (
        f"Company: {body.company}\nRole: {body.role}\nUse case: {body.use_case}\n"
        f"Monthly volume: {body.monthly_volume}\nBudget: {body.budget}\nTimeline: {body.timeline}\n"
        "Score now."
    )
    try:
        raw = []
        async for ev in chat.stream_message(UserMessage(text=prompt)):
            if isinstance(ev, TextDelta):
                raw.append(ev.content)
            elif isinstance(ev, StreamDone):
                break
        raw_text = "".join(raw)
        try:
            data = json.loads(_strip_json(raw_text))
        except Exception:
            data = {"raw": raw_text, "parse_error": True}
        await _log_run("qualify_lead", body.provider, model, prompt, json.dumps(data)[:500])
        return {"result": data}
    except Exception as e:
        log.exception("qualify error")
        raise HTTPException(500, str(e))


# -------------------- Routes: admin stats --------------------
@api.get("/admin/stats")
async def admin_stats(_: str = Depends(require_admin)):
    leads_total = await db.leads.count_documents({})
    leads_new = await db.leads.count_documents({"status": "new"})
    runs_total = await db.agent_runs.count_documents({})
    by_type_cursor = db.agent_runs.aggregate([
        {"$group": {"_id": "$agent_type", "n": {"$sum": 1}}}
    ])
    by_type = {d["_id"]: d["n"] async for d in by_type_cursor}
    recent_leads = await db.leads.find({}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    return {
        "leads_total": leads_total,
        "leads_new": leads_new,
        "runs_total": runs_total,
        "runs_by_type": by_type,
        "recent_leads": recent_leads,
    }


@api.get("/admin/agent-runs", response_model=List[AgentRun])
async def admin_agent_runs(_: str = Depends(require_admin)):
    docs = await db.agent_runs.find({}, {"_id": 0}).sort("created_at", -1).limit(100).to_list(100)
    return [AgentRun(**d) for d in docs]


# -------------------- Startup: seed admin --------------------
@app.on_event("startup")
async def seed_admin():
    existing = await db.admins.find_one({"email": ADMIN_EMAIL})
    if not existing:
        await db.admins.insert_one({
            "email": ADMIN_EMAIL,
            "password_hash": _hash_pw(ADMIN_PASSWORD),
            "created_at": _utcnow_iso(),
        })
        log.info(f"Seeded admin: {ADMIN_EMAIL}")


@app.on_event("shutdown")
async def shutdown_db():
    client.close()


app.include_router(api)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
