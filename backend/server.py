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
    agent_type: Literal["chat", "extract", "extract_bol", "draft_outreach", "qualify_lead", "support_triage"]
    model: str
    provider: str
    input_preview: str
    output_preview: Optional[str] = None
    tokens_in: Optional[int] = None
    success: bool = True
    created_at: str = Field(default_factory=_utcnow_iso)


Industry = Literal[
    "freight_brokerage", "logistics", "manufacturing", "healthcare",
    "saas", "ecommerce", "insurance", "legal", "real_estate", "professional_services", "general"
]


class ChatRequest(BaseModel):
    session_id: str
    message: str
    industry: Industry = "general"
    provider: Literal["anthropic", "openai"] = "anthropic"
    model: Optional[str] = None


class ExtractRequest(BaseModel):
    text: str
    industry: Industry = "general"
    document_type: Optional[str] = None  # e.g. "bol", "invoice", "intake_form"
    provider: Literal["anthropic", "openai"] = "anthropic"


class OutreachRequest(BaseModel):
    summary: str
    recipient: Optional[str] = "Operator"
    tone: str = "direct"
    industry: Industry = "general"
    provider: Literal["anthropic", "openai"] = "anthropic"


class QualifyLeadRequest(BaseModel):
    company: str
    role: str
    use_case: str
    monthly_volume: Optional[str] = None
    budget: Optional[str] = None
    timeline: Optional[str] = None
    industry: Industry = "general"
    provider: Literal["anthropic", "openai"] = "anthropic"


class SupportTicketRequest(BaseModel):
    ticket: str
    industry: Industry = "general"
    company_context: Optional[str] = None
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
INDUSTRY_LEXICON = {
    "freight_brokerage": "freight broker / 3PL ops. Vocabulary: BOL, MC#, lane, RPM, deadhead, FTL/LTL, accessorials, detention, DAT/Truckstop, drop-and-hook.",
    "logistics": "carrier / fleet / warehouse ops. Vocabulary: route, dwell, dock, SKU, OS&D, yard, ELD, HOS.",
    "manufacturing": "production / supply chain. Vocabulary: BOM, MRP, takt time, OEE, work order, lot, defect class, scrap rate.",
    "healthcare": "healthcare admin / clinical ops. Vocabulary: ICD-10, CPT, prior auth, EOB, intake, referral, HIPAA, payer.",
    "saas": "B2B SaaS. Vocabulary: MRR, ARR, churn, NRR, NPS, PQL, ICP, expansion, seat-based pricing.",
    "ecommerce": "DTC / marketplace ops. Vocabulary: SKU, AOV, CAC, LTV, RMA, fulfillment, abandoned cart, conversion.",
    "insurance": "insurance ops. Vocabulary: claim, adjuster, policy, premium, COI, subrogation, FNOL, underwriting.",
    "legal": "legal ops / law firm. Vocabulary: intake, conflict check, billable, retainer, discovery, matter, redline.",
    "real_estate": "commercial / property management. Vocabulary: lease, tenant, CAM, NOI, work order, vacancy, NNN.",
    "professional_services": "agencies / consultancies. Vocabulary: scope, SOW, deliverable, retainer, utilization, billable.",
    "general": "general B2B operator language. Stay industry-neutral but pragmatic.",
}


def _system_for(industry: str, role_hint: str) -> str:
    lex = INDUSTRY_LEXICON.get(industry, INDUSTRY_LEXICON["general"])
    return (
        f"You are JADE — the operator-grade AI agent. Voice: short. Action verbs. Console-style precision. "
        f"Light operator pet-names ('operator', 'captain') used sparingly. Never bubbly. Never apologetic. Never marketing-speak. "
        f"You serve a {industry.replace('_', ' ')} operator. Context lexicon: {lex} "
        f"Role for this turn: {role_hint}. Be factual, cite uncertainty, and never invent regulated data (medical/legal/financial)."
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


def _strip_json(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
        if t.lower().startswith("json"):
            t = t[4:]
        t = t.strip("` \n")
    return t


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
    sys_msg = _system_for(body.industry, "be a knowledgeable Tier-1 / ops co-pilot — answer questions, route issues, escalate when needed")
    chat = _llm(body.session_id, sys_msg, body.provider, body.model)
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
            await _log_run("chat", body.provider, model_used, f"[{body.industry}] {body.message}", "".join(full))
        except Exception as e:
            log.exception("chat stream error")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _extract_schema_hint(industry: str, doc_type: Optional[str]) -> str:
    base = (
        "Schemas vary by document. Common fields when present: parties (from, to), dates, identifiers, "
        "monetary_amounts, line_items[], totals, addresses, contacts, status, notes. "
        "Detect the document_type from content if unclear and include it in the output."
    )
    hints = {
        "freight_brokerage": "If freight: origin_city/state, dest_city/state, equipment, weight_lbs, pickup_date, delivery_date, rate_usd, commodity, miles, mc_number, reference_number, contact_name, contact_phone.",
        "logistics": "If shipment/manifest: tracking_id, carrier, origin, destination, weight, pieces, status, eta.",
        "manufacturing": "If PO/work order: po_number, vendor, items[], quantities, lead_times, due_date, total.",
        "healthcare": "If intake / EOB: patient_name (redact when possible), dob, insurer, member_id (mask), policy, claim_id, dos, provider, diagnosis_codes, cpt_codes, amount, notes. NEVER invent PHI.",
        "saas": "If contract/order form: account, plan, seats, mrr_usd, term_months, start_date, renewal_date, owner.",
        "ecommerce": "If order/return: order_id, customer, items[], sku, qty, price, ship_to, return_reason.",
        "insurance": "If claim/policy: claim_number, policy_number, insured, dol, loss_type, adjuster, reserve, status.",
        "legal": "If intake/matter: matter_id, client, conflict_check, jurisdiction, opposing_party, counsel, dates.",
        "real_estate": "If lease/work order: property, unit, tenant, term, monthly_rent, cam, request_type, priority.",
        "professional_services": "If SOW/proposal: client, scope, deliverables[], fee_usd, term, owner, milestones.",
    }
    extra = hints.get(industry, "")
    if doc_type:
        extra += f" Caller hinted document_type='{doc_type}'."
    return f"{base} {extra}"


@api.post("/agent/extract")
async def agent_extract(body: ExtractRequest):
    sys_msg = (
        f"You are JADE's data extraction subroutine for {body.industry.replace('_', ' ')}. "
        f"Extract the input text/document into strict JSON. Return ONLY a JSON object — no prose, no markdown fences. "
        f"{_extract_schema_hint(body.industry, body.document_type)} "
        f"Use null for unknown fields. Numbers as numbers. Dates as ISO YYYY-MM-DD when possible. "
        f"For PII in regulated industries (healthcare, legal, insurance), redact sensitive identifiers with '***' but keep structure."
    )
    session = str(uuid.uuid4())
    chat = _llm(session, sys_msg, body.provider)
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
        await _log_run("extract", body.provider, model, f"[{body.industry}] {body.text[:200]}", json.dumps(data)[:500])
        return {"extracted": data, "industry": body.industry}
    except Exception as e:
        log.exception("extract error")
        raise HTTPException(500, str(e))


# Backwards-compatible alias for the BOL endpoint
@api.post("/agent/extract-bol")
async def agent_extract_bol(body: ExtractRequest):
    body.industry = body.industry or "freight_brokerage"
    return await agent_extract(body)


@api.post("/agent/draft-outreach")
async def draft_outreach(body: OutreachRequest):
    sys_msg = _system_for(body.industry, "draft a short, no-fluff outreach email") + (
        " Write 5–8 sentences. Subject line on first line prefixed 'Subject: '. Direct ask. "
        " Match the tone to the industry — operator-direct for ops verticals, courteous-direct for healthcare/legal. "
        " No emojis. No 'I hope this finds you well'."
    )
    session = str(uuid.uuid4())
    chat = _llm(session, sys_msg, body.provider)
    model = DEFAULT_MODELS[body.provider]
    prompt = (
        f"Recipient: {body.recipient}\nTone: {body.tone}\nIndustry: {body.industry}\nContext:\n{body.summary}\n"
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
        await _log_run("draft_outreach", body.provider, model, f"[{body.industry}] {body.summary[:200]}", text)
        return {"email": text, "industry": body.industry}
    except Exception as e:
        log.exception("outreach error")
        raise HTTPException(500, str(e))


@api.post("/agent/qualify-lead")
async def qualify_lead(body: QualifyLeadRequest):
    sys_msg = (
        f"You are JADE's sales qualification analyst for {body.industry.replace('_', ' ')} prospects. "
        "Score 0-100 for fit with JADE OS (universal AI agents for support, sales-qual, data extraction, ops automation, content). "
        "Return ONLY JSON with: score (0-100), tier ('hot'|'warm'|'cold'), rationale (<= 60 words), "
        "next_action (1 sentence), red_flags (array of strings), green_flags (array of strings), "
        "recommended_agent (one of: support, sales_qual, data_extraction, ops_automation, content_generation)."
    )
    session = str(uuid.uuid4())
    chat = _llm(session, sys_msg, body.provider)
    model = DEFAULT_MODELS[body.provider]
    prompt = (
        f"Industry: {body.industry}\nCompany: {body.company}\nRole: {body.role}\nUse case: {body.use_case}\n"
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
        await _log_run("qualify_lead", body.provider, model, f"[{body.industry}] {prompt[:200]}", json.dumps(data)[:500])
        return {"result": data, "industry": body.industry}
    except Exception as e:
        log.exception("qualify error")
        raise HTTPException(500, str(e))


@api.post("/agent/support-triage")
async def support_triage(body: SupportTicketRequest):
    sys_msg = _system_for(body.industry, "triage a Tier-1 support ticket") + (
        " Return ONLY JSON with: category (string), priority ('p0'|'p1'|'p2'|'p3'), "
        " sentiment ('angry'|'frustrated'|'neutral'|'positive'), summary (<= 30 words), "
        " suggested_response (3-6 sentences, in the brand voice), "
        " escalate (boolean), escalate_to (string or null), tags (array of strings)."
    )
    session = str(uuid.uuid4())
    chat = _llm(session, sys_msg, body.provider)
    model = DEFAULT_MODELS[body.provider]
    prompt = (
        f"Industry: {body.industry}\n"
        f"Company context: {body.company_context or 'n/a'}\n"
        f"Inbound ticket:\n{body.ticket}\n"
        "Triage now."
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
        await _log_run("support_triage", body.provider, model, f"[{body.industry}] {body.ticket[:200]}", json.dumps(data)[:500])
        return {"result": data, "industry": body.industry}
    except Exception as e:
        log.exception("support error")
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
