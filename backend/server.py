"""JADE OS — AI Agents for Minneapolis operators.

FastAPI backend providing:
- Public lead capture
- Interactive agent demos (chat, BOL extraction, outreach drafting, lead qualification)
- Admin JWT auth + leads dashboard
- Streaming Claude/OpenAI chat via Emergent universal key
"""
from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Literal, Annotated, Dict, Any
from pathlib import Path
from datetime import datetime, timezone, timedelta
import os
import uuid
import json
import logging
import asyncio
import io
import bcrypt
import jwt

from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone
from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, CheckoutSessionRequest, CheckoutSessionResponse, CheckoutStatusResponse,
)
try:
    from pypdf import PdfReader  # PDF text extraction
except Exception:
    PdfReader = None  # graceful

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
EMERGENT_LLM_KEY = os.environ["EMERGENT_LLM_KEY"]
JWT_SECRET = os.environ["JWT_SECRET"]
ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")

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


# -------------------- PDF Extraction --------------------
@api.post("/agent/extract-pdf")
async def extract_pdf(
    file: UploadFile = File(...),
    industry: str = Form("general"),
    provider: str = Form("anthropic"),
):
    if PdfReader is None:
        raise HTTPException(500, "pypdf not installed")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files supported")
    raw = await file.read()
    if len(raw) > 8 * 1024 * 1024:
        raise HTTPException(413, "File too large (8MB max)")
    try:
        reader = PdfReader(io.BytesIO(raw))
        pages = [p.extract_text() or "" for p in reader.pages[:20]]
        text = "\n\n".join(pages).strip()
        if not text:
            return {"extracted": {"parse_error": True, "raw": "PDF contained no extractable text"}, "industry": industry}
    except Exception as e:
        raise HTTPException(400, f"PDF parse failed: {e}")

    body = ExtractRequest(text=text[:30000], industry=industry, provider=provider)
    return await agent_extract(body)


# -------------------- Knowledge Base (RAG-lite) --------------------
class KbDoc(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    industry: str = "general"
    title: str
    content: str
    created_at: str = Field(default_factory=_utcnow_iso)


class KbCreate(BaseModel):
    industry: str = "general"
    title: str
    content: str


@api.post("/kb/docs", response_model=KbDoc)
async def kb_create(body: KbCreate, _: str = Depends(require_admin)):
    doc = KbDoc(**body.model_dump())
    await db.kb_docs.insert_one(doc.model_dump())
    return doc


@api.get("/kb/docs", response_model=List[KbDoc])
async def kb_list(industry: Optional[str] = None):
    q = {"industry": industry} if industry else {}
    docs = await db.kb_docs.find(q, {"_id": 0}).sort("created_at", -1).to_list(200)
    return [KbDoc(**d) for d in docs]


@api.delete("/kb/docs/{doc_id}")
async def kb_delete(doc_id: str, _: str = Depends(require_admin)):
    res = await db.kb_docs.delete_one({"id": doc_id})
    if res.deleted_count == 0:
        raise HTTPException(404, "Not found")
    return {"ok": True}


class KbAskRequest(BaseModel):
    question: str
    industry: str = "general"
    provider: Literal["anthropic", "openai"] = "anthropic"


@api.post("/kb/ask")
async def kb_ask(body: KbAskRequest):
    """Lite RAG: pull top docs by industry, concatenate, ask LLM with citations."""
    docs = await db.kb_docs.find({"industry": body.industry}, {"_id": 0}).limit(8).to_list(8)
    if not docs:
        docs = await db.kb_docs.find({}, {"_id": 0}).limit(8).to_list(8)
    context = "\n\n".join([f"[{i+1}] {d['title']}\n{d['content']}" for i, d in enumerate(docs)])
    sys_msg = _system_for(body.industry, "answer the operator's question using ONLY the provided knowledge base. Cite sources as [N].")
    sys_msg += f"\n\nKNOWLEDGE BASE:\n{context}" if context else "\n\nNo knowledge base configured."

    session = str(uuid.uuid4())
    chat = _llm(session, sys_msg, body.provider)
    out = []
    async for ev in chat.stream_message(UserMessage(text=body.question)):
        if isinstance(ev, TextDelta):
            out.append(ev.content)
        elif isinstance(ev, StreamDone):
            break
    answer = "".join(out)
    sources = [{"n": i + 1, "title": d["title"], "id": d["id"]} for i, d in enumerate(docs)]
    await _log_run("chat", body.provider, DEFAULT_MODELS[body.provider], f"[kb:{body.industry}] {body.question[:200]}", answer)
    return {"answer": answer, "sources": sources, "industry": body.industry}


# -------------------- Slack/CRM Webhook delivery --------------------
class WebhookConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    url: str
    kind: Literal["slack", "crm", "generic"] = "slack"
    active: bool = True
    created_at: str = Field(default_factory=_utcnow_iso)


class WebhookConfigCreate(BaseModel):
    name: str
    url: str
    kind: Literal["slack", "crm", "generic"] = "slack"


@api.post("/webhooks", response_model=WebhookConfig)
async def webhook_create(body: WebhookConfigCreate, _: str = Depends(require_admin)):
    w = WebhookConfig(**body.model_dump())
    await db.webhooks.insert_one(w.model_dump())
    return w


@api.get("/webhooks", response_model=List[WebhookConfig])
async def webhook_list(_: str = Depends(require_admin)):
    docs = await db.webhooks.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return [WebhookConfig(**d) for d in docs]


@api.delete("/webhooks/{wid}")
async def webhook_delete(wid: str, _: str = Depends(require_admin)):
    await db.webhooks.delete_one({"id": wid})
    return {"ok": True}


class WebhookDispatch(BaseModel):
    title: str
    body: str
    metadata: Optional[Dict[str, Any]] = None


@api.post("/webhooks/{wid}/dispatch")
async def webhook_dispatch(wid: str, payload: WebhookDispatch, _: str = Depends(require_admin)):
    import httpx
    w = await db.webhooks.find_one({"id": wid}, {"_id": 0})
    if not w:
        raise HTTPException(404, "Not found")
    if w.get("kind") == "slack":
        body = {"text": f"*{payload.title}*\n{payload.body}"}
    else:
        body = {"title": payload.title, "body": payload.body, "metadata": payload.metadata or {}}
    delivered = False
    err = None
    try:
        async with httpx.AsyncClient(timeout=8.0) as cx:
            r = await cx.post(w["url"], json=body)
            delivered = 200 <= r.status_code < 300
            if not delivered:
                err = f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        err = str(e)
    await db.webhook_deliveries.insert_one({
        "id": str(uuid.uuid4()),
        "webhook_id": wid,
        "title": payload.title,
        "body_preview": payload.body[:300],
        "delivered": delivered,
        "error": err,
        "created_at": _utcnow_iso(),
    })
    return {"delivered": delivered, "error": err}


# -------------------- Stripe Subscription Checkout --------------------
TIER_PRICING = {
    "dispatch": {"name": "DISPATCH", "amount": 1500.00, "currency": "usd"},
    "fleet":    {"name": "FLEET",    "amount": 4500.00, "currency": "usd"},
    # 'vault' is contact-sales, no checkout
}


class CheckoutCreate(BaseModel):
    tier: Literal["dispatch", "fleet"]
    origin_url: str
    email: Optional[EmailStr] = None
    company: Optional[str] = None


@api.post("/billing/checkout")
async def billing_checkout(body: CheckoutCreate, http_request: Request):
    if not STRIPE_API_KEY:
        raise HTTPException(500, "Stripe not configured")
    pkg = TIER_PRICING.get(body.tier)
    if not pkg:
        raise HTTPException(400, "Invalid tier")

    webhook_url = f"{str(http_request.base_url).rstrip('/')}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)

    success_url = f"{body.origin_url.rstrip('/')}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{body.origin_url.rstrip('/')}/?billing=cancelled"

    metadata = {
        "tier": body.tier,
        "email": body.email or "",
        "company": body.company or "",
    }
    req = CheckoutSessionRequest(
        amount=pkg["amount"],
        currency=pkg["currency"],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata,
    )
    session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(req)
    await db.payment_transactions.insert_one({
        "id": str(uuid.uuid4()),
        "session_id": session.session_id,
        "tier": body.tier,
        "amount": pkg["amount"],
        "currency": pkg["currency"],
        "email": body.email or None,
        "company": body.company or None,
        "metadata": metadata,
        "payment_status": "pending",
        "status": "open",
        "created_at": _utcnow_iso(),
    })
    return {"url": session.url, "session_id": session.session_id}


@api.get("/billing/status/{session_id}")
async def billing_status(session_id: str, http_request: Request):
    if not STRIPE_API_KEY:
        raise HTTPException(500, "Stripe not configured")
    existing = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    if not existing:
        raise HTTPException(404, "Session not found")
    # If already finalized, just return it
    if existing.get("payment_status") in ("paid", "expired", "failed"):
        return existing

    webhook_url = f"{str(http_request.base_url).rstrip('/')}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    s: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
    update = {
        "payment_status": s.payment_status,
        "status": s.status,
        "amount_total": s.amount_total,
        "currency": s.currency,
        "updated_at": _utcnow_iso(),
    }
    await db.payment_transactions.update_one({"session_id": session_id}, {"$set": update})
    # If paid, create or update org
    if s.payment_status == "paid":
        tier = existing.get("tier")
        email = existing.get("email")
        company = existing.get("company")
        if email and company:
            await db.orgs.update_one(
                {"email": email},
                {"$set": {
                    "email": email,
                    "company": company,
                    "tier": tier,
                    "subscription_status": "active",
                    "session_id": session_id,
                    "updated_at": _utcnow_iso(),
                }, "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": _utcnow_iso()}},
                upsert=True,
            )
    merged = {**existing, **update}
    return merged


@api.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    if not STRIPE_API_KEY:
        return JSONResponse({"ok": False}, status_code=500)
    body = await request.body()
    sig = request.headers.get("Stripe-Signature") or ""
    host_url = str(request.base_url).rstrip("/")
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=f"{host_url}/api/webhook/stripe")
    try:
        ev = await stripe_checkout.handle_webhook(body, sig)
    except Exception as e:
        log.exception("stripe webhook decode failed")
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    if ev and getattr(ev, "session_id", None):
        await db.payment_transactions.update_one(
            {"session_id": ev.session_id},
            {"$set": {
                "payment_status": ev.payment_status or "unknown",
                "status": "complete" if ev.payment_status == "paid" else ev.payment_status,
                "webhook_event": ev.event_type,
                "updated_at": _utcnow_iso(),
            }},
        )
    return {"ok": True}


# -------------------- Orgs (multi-tenant skeleton) --------------------
class Org(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company: str
    email: EmailStr
    tier: Optional[str] = None
    subscription_status: str = "trial"
    monthly_token_budget: int = 2_000_000  # tokens
    created_at: str = Field(default_factory=_utcnow_iso)


@api.get("/orgs", response_model=List[Org])
async def list_orgs(_: str = Depends(require_admin)):
    docs = await db.orgs.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return [Org(**d) for d in docs]


@api.get("/orgs/usage")
async def orgs_usage(_: str = Depends(require_admin)):
    """Estimated token usage per org based on agent runs (rough: 4 chars/token)."""
    pipeline = [
        {"$project": {
            "session_id": 1,
            "n_chars": {"$add": [
                {"$strLenCP": {"$ifNull": ["$input_preview", ""]}},
                {"$strLenCP": {"$ifNull": ["$output_preview", ""]}},
            ]},
            "agent_type": 1,
            "created_at": 1,
        }},
    ]
    runs = await db.agent_runs.aggregate(pipeline).to_list(2000)
    total_chars = sum(r.get("n_chars", 0) for r in runs)
    return {
        "runs": len(runs),
        "estimated_tokens": int(total_chars / 4),
        "by_type": _by_field(runs, "agent_type"),
    }


def _by_field(rows, key):
    out = {}
    for r in rows:
        k = r.get(key) or "unknown"
        out[k] = out.get(k, 0) + 1
    return out


# -------------------- Case Studies (public) --------------------
class CaseStudy(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    slug: str
    company: str
    industry: str
    headline: str
    problem: str
    solution: str
    results: List[str] = []
    quote: Optional[str] = None
    quote_attribution: Optional[str] = None
    created_at: str = Field(default_factory=_utcnow_iso)


@api.get("/case-studies", response_model=List[CaseStudy])
async def case_studies_list():
    docs = await db.case_studies.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return [CaseStudy(**d) for d in docs]


@api.get("/case-studies/{slug}", response_model=CaseStudy)
async def case_study_get(slug: str):
    doc = await db.case_studies.find_one({"slug": slug}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Not found")
    return CaseStudy(**doc)


CASE_STUDY_SEED = [
    {
        "slug": "northstar-logistics",
        "company": "Northstar Logistics",
        "industry": "freight_brokerage",
        "headline": "4.2 hours/day reclaimed per dispatcher",
        "problem": "Northstar's 9 dispatchers spent 2–4 hours each day on carrier outreach and BOL data entry. Margins were under 3%. They were turning down loads because they couldn't keep up with the email volume.",
        "solution": "JADE OS shipped two agents in week one: Freight Co-Pilot (carrier outreach drafting + load-to-carrier matching) and Data Extraction (BOL → structured JSON). Slack-delivered with human-in-the-loop approval before any send.",
        "results": [
            "4.2 hours reclaimed per dispatcher, per day",
            "Same-day carrier response up 18%",
            "Zero BOL rekey errors in Q2",
            "1 dispatcher reallocated to lane analysis (margin work)",
        ],
        "quote": "I stopped hiring dispatchers and started hiring lane analysts. JADE is my new headcount.",
        "quote_attribution": "Dana Bjornson, VP Operations · Northstar Logistics",
    },
    {
        "slug": "twin-cities-health",
        "company": "Twin Cities Health Network",
        "industry": "healthcare",
        "headline": "96% intake-form extraction accuracy. Zero PHI breaches.",
        "problem": "TCH was manually keying patient intake forms from 12 clinic locations into their EMR. Average 9 minutes per form, 450 forms/day. Backlog of 1,800 forms by Friday every week.",
        "solution": "JADE Document Extraction tuned for healthcare schema (ICD-10/CPT aware, PHI auto-redacted in logs). Human-in-the-loop approval on every record before EMR write. BAA signed before pilot.",
        "results": [
            "Intake processing time: 9 min → 47 seconds per form",
            "96% field-level extraction accuracy (3-month measured)",
            "Friday backlog eliminated within 21 days",
            "Zero PHI events in audit · BAA-grade logs",
        ],
        "quote": "We deflected a $180k EMR-integrator quote by shipping JADE in 6 weeks instead.",
        "quote_attribution": "Karen Holst, Director Admin Ops · Twin Cities Health",
    },
    {
        "slug": "bjornson-saas",
        "company": "Bjornson SaaS",
        "industry": "saas",
        "headline": "47% Tier-1 ticket deflection. CSAT up 18 points.",
        "problem": "Bjornson's 6-person support team was drowning. 3,200 tickets/month, 60% of them password resets, FAQ, or onboarding questions a doc could answer. Tier-1 response time slipped to 11 hours.",
        "solution": "JADE Support Triage + KB-aware chat agent. Tier-1 tickets auto-classified, sentiment-flagged, drafted response queued for one-click approve. Knowledge base ingested from existing help docs.",
        "results": [
            "47% Tier-1 ticket deflection without human touch",
            "First-response time: 11h → 38s",
            "CSAT up 18 points (62 → 80) in 60 days",
            "Support team reallocated 2 FTE to customer-success outbound",
        ],
        "quote": "Our team finally has time to do the work humans should be doing.",
        "quote_attribution": "S. Cho, Head of Support · Bjornson SaaS",
    },
]


# -------------------- Org Portal preview (read-only) --------------------
@api.get("/portal/preview")
async def portal_preview(email: EmailStr):
    """Public read-only portal preview — given an email, returns subscription status + recent runs.
    For demo use; production should be JWT-scoped per org."""
    org = await db.orgs.find_one({"email": email}, {"_id": 0})
    if not org:
        return {"org": None, "runs": [], "usage": {"runs": 0, "estimated_tokens": 0}}
    runs = await db.agent_runs.find({}, {"_id": 0}).sort("created_at", -1).limit(10).to_list(10)
    total = await db.agent_runs.count_documents({})
    return {
        "org": org,
        "runs": runs,
        "usage": {"runs": total, "estimated_tokens": min(org.get("monthly_token_budget", 0), total * 800)},
    }


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
    # Seed case studies
    for cs in CASE_STUDY_SEED:
        await db.case_studies.update_one(
            {"slug": cs["slug"]},
            {"$setOnInsert": {**cs, "id": str(uuid.uuid4()), "created_at": _utcnow_iso()}},
            upsert=True,
        )


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
