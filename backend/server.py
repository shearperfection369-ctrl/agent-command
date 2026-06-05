"""JADE OS — AI Agents for Minneapolis operators.

FastAPI backend providing:
- Public lead capture
- Interactive agent demos (chat, BOL extraction, outreach drafting, lead qualification)
- Admin JWT auth + leads dashboard
- Streaming Claude/OpenAI chat via Emergent universal key
"""
from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse, JSONResponse, PlainTextResponse, FileResponse
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
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", "")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "https://mpls-automation-hub.preview.emergentagent.com").rstrip("/")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_SENDER = os.environ.get("RESEND_SENDER", "onboarding@resend.dev")
RESEND_WEBHOOK_SECRET = os.environ.get("RESEND_WEBHOOK_SECRET", "")

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
    source: Optional[str] = "website"


# ============================================================
# LIGHTHOUSE CUSTOMER PROGRAM
# ============================================================
# A separate, higher-intent application flow for prospects willing to be a published case study
# in exchange for: 50% off year 1, hands-on white-glove implementation, named engineer, co-marketing.
# JADE auto-scores every application using the qualification agent.
# ============================================================

class LighthouseApplication(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    # Operator
    name: str
    title: str
    email: EmailStr
    phone: Optional[str] = None
    # Company
    company: str
    industry: str = "freight_brokerage"
    company_size: str = "11-50"  # "1-10" | "11-50" | "51-200" | "201-1000" | "1000+"
    website: Optional[str] = None
    # Fit
    primary_pain: str  # one of: support_overflow, doc_overload, lead_chaos, ops_drift, content_grind, other
    pain_detail: str  # free text
    target_outcome: str  # e.g. "cut tier-1 response from 11h → 1h"
    timeline: str = "30_days"  # "14_days" | "30_days" | "60_days" | "90_plus"
    decision_authority: str = "decision_maker"  # "decision_maker" | "influencer" | "researcher"
    budget_band: str = "1500_4500"  # "<1500" | "1500_4500" | "4500_10000" | "10000+"
    # Case study willingness
    case_study_consent: bool = False
    logo_consent: bool = False
    quote_consent: bool = False
    metrics_consent: bool = False
    # Auto-scored by JADE
    score: Optional[int] = None
    tier: Optional[str] = None  # "hot" | "warm" | "cold"
    rationale: Optional[str] = None
    next_action: Optional[str] = None
    green_flags: List[str] = []
    red_flags: List[str] = []
    # Status workflow
    status: str = "new"  # "new" | "screening" | "interview_scheduled" | "selected" | "pilot_live" | "case_published" | "passed"
    notes: Optional[str] = None
    created_at: str = Field(default_factory=_utcnow_iso)


class LighthouseCreate(BaseModel):
    name: str
    title: str
    email: EmailStr
    phone: Optional[str] = None
    company: str
    industry: str = "freight_brokerage"
    company_size: str = "11-50"
    website: Optional[str] = None
    primary_pain: str
    pain_detail: str
    target_outcome: str
    timeline: str = "30_days"
    decision_authority: str = "decision_maker"
    budget_band: str = "1500_4500"
    case_study_consent: bool = False
    logo_consent: bool = False
    quote_consent: bool = False
    metrics_consent: bool = False


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


# ============================================================
# THE MOAT — Proprietary IP layers that lock customers in
# ============================================================
# These layers turn JADE OS from "thin LLM wrapper" into a defensible product:
#   1. Schema Library      — versioned, customer-tuned extraction schemas
#   2. Prompt Library      — versioned, named prompts with A/B variants
#   3. Playbooks           — multi-step workflows chained as code (not single LLM calls)
#   4. Model Router        — automatic per-task model selection (margin defense)
#   5. Run Analytics       — accuracy/latency/cost tracking that compounds over time
#
# Customer corrections feed back into OUR schemas. Their playbooks live in OUR DB.
# Switching providers (Anthropic ↔ OpenAI) is silent — model routing is OUR layer.
# ============================================================

# ---------- Model Router (margin defense) ----------
# Each task profile carries a preferred provider+model + a budget tier.
# When prices shift, we re-tier silently. Customer code never changes.
MODEL_ROUTING = {
    # Cheap/fast tasks — short triage, classification
    "fast": [("anthropic", "claude-haiku-4-5-20251001"), ("openai", "gpt-5-mini")],
    # Default — extraction, drafting, qualification
    "default": [("anthropic", "claude-sonnet-4-5-20250929"), ("openai", "gpt-5.2")],
    # Reasoning-heavy — playbook orchestration, complex extraction
    "smart": [("anthropic", "claude-opus-4-7"), ("openai", "gpt-5.4")],
}


def _route_model(profile: str, provider_override: Optional[str] = None) -> tuple[str, str]:
    """Return (provider, model) for a task profile. Customer can pin a provider."""
    options = MODEL_ROUTING.get(profile, MODEL_ROUTING["default"])
    if provider_override:
        for prov, mdl in options:
            if prov == provider_override:
                return prov, mdl
    return options[0]


# ---------- Schema Library ----------
# Versioned extraction schemas. Customer corrections create new versions.
class SchemaField(BaseModel):
    name: str
    type: Literal["string", "number", "date", "boolean", "array", "object"] = "string"
    required: bool = False
    description: Optional[str] = None
    redact: bool = False  # for PHI/PII fields


class ExtractionSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    slug: str  # e.g. "freight_bol", "healthcare_intake"
    industry: str
    version: int = 1
    name: str
    description: Optional[str] = None
    fields: List[SchemaField] = []
    parent_id: Optional[str] = None  # links to previous version
    org_email: Optional[str] = None  # tenant scope; None = global default
    correction_count: int = 0
    created_at: str = Field(default_factory=_utcnow_iso)


class SchemaCreate(BaseModel):
    slug: str
    industry: str
    name: str
    description: Optional[str] = None
    fields: List[SchemaField] = []
    org_email: Optional[str] = None


class SchemaCorrection(BaseModel):
    schema_id: str
    run_id: Optional[str] = None
    original_output: Dict[str, Any]
    corrected_output: Dict[str, Any]
    notes: Optional[str] = None
    org_email: Optional[str] = None


SCHEMA_SEED = [
    {
        "slug": "freight_bol", "industry": "freight_brokerage", "name": "Freight BOL · v1",
        "description": "Bill of Lading / load posting for freight brokers and 3PLs",
        "fields": [
            {"name": "origin_city", "type": "string", "required": True},
            {"name": "origin_state", "type": "string", "required": True},
            {"name": "dest_city", "type": "string", "required": True},
            {"name": "dest_state", "type": "string", "required": True},
            {"name": "equipment", "type": "string"},
            {"name": "weight_lbs", "type": "number"},
            {"name": "pickup_date", "type": "date"},
            {"name": "delivery_date", "type": "date"},
            {"name": "rate_usd", "type": "number"},
            {"name": "miles", "type": "number"},
            {"name": "mc_number", "type": "string"},
            {"name": "commodity", "type": "string"},
            {"name": "contact_name", "type": "string"},
            {"name": "contact_phone", "type": "string"},
        ],
    },
    {
        "slug": "healthcare_intake", "industry": "healthcare", "name": "Patient Intake · v1",
        "description": "Patient intake form — PHI fields auto-redacted in logs",
        "fields": [
            {"name": "patient_name", "type": "string", "required": True, "redact": True},
            {"name": "dob", "type": "date", "redact": True},
            {"name": "member_id", "type": "string", "redact": True},
            {"name": "insurer", "type": "string"},
            {"name": "visit_date", "type": "date"},
            {"name": "provider", "type": "string"},
            {"name": "diagnosis_codes", "type": "array"},
            {"name": "cpt_codes", "type": "array"},
            {"name": "prior_auth_id", "type": "string"},
            {"name": "prior_auth_status", "type": "string"},
        ],
    },
    {
        "slug": "saas_order_form", "industry": "saas", "name": "SaaS Order Form · v1",
        "description": "B2B SaaS order form / contract summary",
        "fields": [
            {"name": "account_name", "type": "string", "required": True},
            {"name": "plan", "type": "string"},
            {"name": "seats", "type": "number"},
            {"name": "mrr_usd", "type": "number"},
            {"name": "term_months", "type": "number"},
            {"name": "start_date", "type": "date"},
            {"name": "renewal_date", "type": "date"},
            {"name": "owner", "type": "string"},
            {"name": "addons", "type": "array"},
        ],
    },
    {
        "slug": "manufacturing_po", "industry": "manufacturing", "name": "Manufacturing PO · v1",
        "description": "Purchase order for industrial procurement",
        "fields": [
            {"name": "po_number", "type": "string", "required": True},
            {"name": "vendor", "type": "string", "required": True},
            {"name": "buyer", "type": "string"},
            {"name": "items", "type": "array"},
            {"name": "total_usd", "type": "number"},
            {"name": "required_by", "type": "date"},
            {"name": "terms", "type": "string"},
        ],
    },
]


def _schema_prompt(s: dict) -> str:
    """Build a strict JSON schema prompt from a stored ExtractionSchema."""
    lines = [
        f"Extract the input into JSON matching THIS exact schema (version {s.get('version', 1)} · {s['name']}):",
    ]
    for f in s.get("fields", []):
        marker = "*" if f.get("required") else ""
        redact = " (REDACT with '***' in logs but keep structure)" if f.get("redact") else ""
        desc = f" — {f['description']}" if f.get("description") else ""
        lines.append(f"  {f['name']}{marker}: {f['type']}{desc}{redact}")
    lines.append("Return ONLY a JSON object with these exact keys. Unknown fields → null. Numbers as numbers, dates ISO YYYY-MM-DD.")
    return "\n".join(lines)


@api.get("/schemas", response_model=List[ExtractionSchema])
async def schemas_list(industry: Optional[str] = None, org_email: Optional[str] = None):
    q = {}
    if industry: q["industry"] = industry
    if org_email: q["$or"] = [{"org_email": org_email}, {"org_email": None}]
    docs = await db.schemas.find(q, {"_id": 0}).sort([("industry", 1), ("created_at", -1)]).to_list(200)
    return [ExtractionSchema(**d) for d in docs]


@api.get("/schemas/{slug}", response_model=ExtractionSchema)
async def schema_get(slug: str, org_email: Optional[str] = None):
    """Get latest version of a schema. Tenant override wins over global."""
    q = {"slug": slug}
    if org_email:
        tenant = await db.schemas.find_one({"slug": slug, "org_email": org_email}, {"_id": 0}, sort=[("version", -1)])
        if tenant:
            return ExtractionSchema(**tenant)
    doc = await db.schemas.find_one({"slug": slug, "org_email": None}, {"_id": 0}, sort=[("version", -1)])
    if not doc:
        raise HTTPException(404, "Schema not found")
    return ExtractionSchema(**doc)


@api.post("/schemas", response_model=ExtractionSchema)
async def schema_create(body: SchemaCreate, _: str = Depends(require_admin)):
    s = ExtractionSchema(**body.model_dump())
    await db.schemas.insert_one(s.model_dump())
    return s


@api.post("/schemas/{schema_id}/correct")
async def schema_correct(schema_id: str, body: SchemaCorrection, _: str = Depends(require_admin)):
    """Record a customer correction. Increments correction_count.
    The longer customers use JADE, the more our schemas improve from THEIR data."""
    parent = await db.schemas.find_one({"id": schema_id}, {"_id": 0})
    if not parent:
        raise HTTPException(404, "Schema not found")
    await db.schema_corrections.insert_one({
        "id": str(uuid.uuid4()),
        "schema_id": schema_id,
        "run_id": body.run_id,
        "original_output": body.original_output,
        "corrected_output": body.corrected_output,
        "notes": body.notes,
        "org_email": body.org_email,
        "created_at": _utcnow_iso(),
    })
    await db.schemas.update_one({"id": schema_id}, {"$inc": {"correction_count": 1}})
    return {"ok": True, "schema_id": schema_id}


# ---------- Prompt Library ----------
class PromptTemplate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    slug: str
    industry: str = "general"
    name: str
    template: str
    variables: List[str] = []
    variant: str = "A"  # A/B testing
    version: int = 1
    org_email: Optional[str] = None
    created_at: str = Field(default_factory=_utcnow_iso)


class PromptCreate(BaseModel):
    slug: str
    industry: str = "general"
    name: str
    template: str
    variables: List[str] = []
    variant: str = "A"
    org_email: Optional[str] = None


PROMPT_SEED = [
    {
        "slug": "carrier_outreach_v1", "industry": "freight_brokerage", "name": "Freight · Carrier Outreach (operator-blunt)",
        "template": "Write a short carrier outreach email. Subject line starts 'Subject:'. 5–8 sentences. Direct ask. Include lane, equipment, rate, pickup window, MC number. No fluff.\n\nLOAD: {{load_summary}}\nCARRIER: {{recipient}}",
        "variables": ["load_summary", "recipient"],
    },
    {
        "slug": "patient_followup_v1", "industry": "healthcare", "name": "Healthcare · Patient Follow-up (courteous-direct)",
        "template": "Draft a patient follow-up. Warm but efficient. Confirm visit/test details, prior auth status, next steps. 4–6 sentences. No medical advice.\n\nCONTEXT: {{summary}}\nPATIENT: {{recipient}}",
        "variables": ["summary", "recipient"],
    },
    {
        "slug": "renewal_email_v1", "industry": "saas", "name": "SaaS · Renewal Email (consultative)",
        "template": "Write a renewal email to a customer. Reference usage growth, propose terms, soft CTA for a 15-min call. 5–7 sentences.\n\nACCOUNT: {{recipient}}\nDETAILS: {{summary}}",
        "variables": ["recipient", "summary"],
    },
]


@api.get("/prompts", response_model=List[PromptTemplate])
async def prompts_list(industry: Optional[str] = None):
    q = {"industry": industry} if industry else {}
    docs = await db.prompts.find(q, {"_id": 0}).sort("created_at", -1).to_list(200)
    return [PromptTemplate(**d) for d in docs]


@api.post("/prompts", response_model=PromptTemplate)
async def prompt_create(body: PromptCreate, _: str = Depends(require_admin)):
    p = PromptTemplate(**body.model_dump())
    await db.prompts.insert_one(p.model_dump())
    return p


@api.delete("/prompts/{pid}")
async def prompt_delete(pid: str, _: str = Depends(require_admin)):
    await db.prompts.delete_one({"id": pid})
    return {"ok": True}


class PromptRunRequest(BaseModel):
    slug: str
    variables: Dict[str, str]
    industry: str = "general"
    profile: Literal["fast", "default", "smart"] = "default"
    provider: Optional[Literal["anthropic", "openai"]] = None


@api.post("/prompts/run")
async def prompt_run(body: PromptRunRequest):
    """Run a stored prompt by slug. Variables substituted via {{name}} interpolation."""
    p = await db.prompts.find_one({"slug": body.slug}, {"_id": 0}, sort=[("version", -1)])
    if not p:
        raise HTTPException(404, "Prompt not found")
    rendered = p["template"]
    for k, v in body.variables.items():
        rendered = rendered.replace("{{" + k + "}}", str(v))
    provider, model = _route_model(body.profile, body.provider)
    session = str(uuid.uuid4())
    chat = _llm(session, _system_for(body.industry, "execute the prompt template precisely"), provider, model)
    out = []
    async for ev in chat.stream_message(UserMessage(text=rendered)):
        if isinstance(ev, TextDelta):
            out.append(ev.content)
        elif isinstance(ev, StreamDone):
            break
    text = "".join(out)
    await _log_run("chat", provider, model, f"[prompt:{body.slug}] {rendered[:200]}", text)
    return {"output": text, "prompt_slug": body.slug, "provider": provider, "model": model}


# ---------- Playbooks (multi-step workflows) ----------
# The killer feature. This is what Zapier + ChatGPT cannot replicate.
class PlaybookStep(BaseModel):
    kind: Literal["extract", "qualify", "draft_outreach", "support_triage", "chat", "match"]
    label: str
    config: Dict[str, Any] = {}
    # `from` lets a step reference previous step output, e.g. {"summary": "$0.email"}


class Playbook(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    slug: str
    industry: str
    name: str
    description: Optional[str] = None
    steps: List[PlaybookStep] = []
    created_at: str = Field(default_factory=_utcnow_iso)


class PlaybookCreate(BaseModel):
    slug: str
    industry: str
    name: str
    description: Optional[str] = None
    steps: List[PlaybookStep] = []


PLAYBOOK_SEED = [
    {
        "slug": "freight_load_intake",
        "industry": "freight_brokerage",
        "name": "Freight · Load Intake → Carrier Outreach",
        "description": "Paste raw load posting → extract → draft outreach email. End-to-end in one call.",
        "steps": [
            {"kind": "extract", "label": "Parse load posting", "config": {"schema_slug": "freight_bol"}},
            {"kind": "draft_outreach", "label": "Draft carrier outreach", "config": {"prompt_slug": "carrier_outreach_v1"}},
        ],
    },
    {
        "slug": "healthcare_intake_triage",
        "industry": "healthcare",
        "name": "Healthcare · Intake → Triage",
        "description": "Parse intake form → triage urgency → draft confirmation",
        "steps": [
            {"kind": "extract", "label": "Parse intake form", "config": {"schema_slug": "healthcare_intake"}},
            {"kind": "support_triage", "label": "Triage urgency"},
        ],
    },
    {
        "slug": "saas_inbound_lead",
        "industry": "saas",
        "name": "SaaS · Inbound Lead → Qualified",
        "description": "Score inbound lead → draft tailored outreach if hot",
        "steps": [
            {"kind": "qualify", "label": "Qualify the lead"},
            {"kind": "draft_outreach", "label": "Draft outreach (if hot)"},
        ],
    },
]


@api.get("/playbooks/by-owner")
async def playbooks_by_owner(email: EmailStr):
    docs = await db.playbooks.find({"owner_email": email}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return docs


@api.get("/playbooks", response_model=List[Playbook])
async def playbooks_list(industry: Optional[str] = None):
    q = {"industry": industry} if industry else {}
    docs = await db.playbooks.find(q, {"_id": 0}).sort("created_at", -1).to_list(200)
    return [Playbook(**d) for d in docs]


@api.get("/playbooks/{slug}", response_model=Playbook)
async def playbook_get(slug: str):
    doc = await db.playbooks.find_one({"slug": slug}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Playbook not found")
    return Playbook(**doc)


@api.post("/playbooks", response_model=Playbook)
async def playbook_create(body: PlaybookCreate, _: str = Depends(require_admin)):
    p = Playbook(**body.model_dump())
    await db.playbooks.insert_one(p.model_dump())
    return p


class PlaybookRunRequest(BaseModel):
    slug: str
    input: str  # raw text for step 0
    industry: Optional[str] = None
    provider: Literal["anthropic", "openai"] = "anthropic"


@api.post("/playbooks/run")
async def playbook_run(body: PlaybookRunRequest):
    """Execute a multi-step playbook. Returns each step's output + final.
    This is the moat: customers build playbooks once, run forever, and we own the orchestration."""
    pb = await db.playbooks.find_one({"slug": body.slug}, {"_id": 0})
    if not pb:
        raise HTTPException(404, "Playbook not found")
    industry = body.industry or pb["industry"]
    outputs = []
    current_text = body.input
    run_id = str(uuid.uuid4())
    started = datetime.now(timezone.utc)

    for i, step in enumerate(pb["steps"]):
        kind = step["kind"]
        cfg = step.get("config", {})
        step_out: Dict[str, Any] = {"kind": kind, "label": step.get("label")}
        try:
            if kind == "extract":
                slug = cfg.get("schema_slug")
                schema_doc = None
                if slug:
                    schema_doc = await db.schemas.find_one({"slug": slug, "org_email": None}, {"_id": 0}, sort=[("version", -1)])
                sys_msg = (
                    f"You are JADE extraction for {industry}. "
                    + (_schema_prompt(schema_doc) if schema_doc else f"Extract to JSON. Use null for unknown fields.")
                )
                provider, model = _route_model("default", body.provider)
                chat = _llm(f"{run_id}-{i}", sys_msg, provider, model)
                raw = []
                async for ev in chat.stream_message(UserMessage(text=current_text)):
                    if isinstance(ev, TextDelta): raw.append(ev.content)
                    elif isinstance(ev, StreamDone): break
                try:
                    data = json.loads(_strip_json("".join(raw)))
                except Exception:
                    data = {"raw": "".join(raw), "parse_error": True}
                step_out["output"] = data
                step_out["schema_used"] = schema_doc.get("slug") if schema_doc else None
                # Build a brief text summary for next step input
                current_text = json.dumps(data)[:1500]

            elif kind == "draft_outreach":
                prov, model = _route_model("default", body.provider)
                chat = _llm(f"{run_id}-{i}", _system_for(industry, "draft outreach email — subject first, 5-8 sentences, direct"), prov, model)
                prompt = f"Context (from previous step):\n{current_text}\n\nDraft the email."
                raw = []
                async for ev in chat.stream_message(UserMessage(text=prompt)):
                    if isinstance(ev, TextDelta): raw.append(ev.content)
                    elif isinstance(ev, StreamDone): break
                email = "".join(raw).strip()
                step_out["output"] = {"email": email}
                current_text = email[:1500]

            elif kind == "support_triage":
                prov, model = _route_model("fast", body.provider)
                sys_msg = _system_for(industry, "triage a Tier-1 support ticket") + (
                    " Return ONLY JSON with: category, priority(p0-p3), sentiment, summary, suggested_response, escalate, escalate_to, tags."
                )
                chat = _llm(f"{run_id}-{i}", sys_msg, prov, model)
                raw = []
                async for ev in chat.stream_message(UserMessage(text=current_text)):
                    if isinstance(ev, TextDelta): raw.append(ev.content)
                    elif isinstance(ev, StreamDone): break
                try:
                    data = json.loads(_strip_json("".join(raw)))
                except Exception:
                    data = {"raw": "".join(raw), "parse_error": True}
                step_out["output"] = data
                current_text = json.dumps(data)[:1500]

            elif kind == "qualify":
                prov, model = _route_model("default", body.provider)
                sys_msg = "You are JADE lead-qualification. Return ONLY JSON with score (0-100), tier ('hot'|'warm'|'cold'), rationale, next_action, recommended_agent."
                chat = _llm(f"{run_id}-{i}", sys_msg, prov, model)
                raw = []
                async for ev in chat.stream_message(UserMessage(text=current_text)):
                    if isinstance(ev, TextDelta): raw.append(ev.content)
                    elif isinstance(ev, StreamDone): break
                try: data = json.loads(_strip_json("".join(raw)))
                except Exception: data = {"raw": "".join(raw), "parse_error": True}
                step_out["output"] = data
                current_text = json.dumps(data)[:1500]

            else:
                step_out["output"] = {"skipped": True, "reason": f"kind={kind} not implemented"}

            step_out["status"] = "ok"
        except Exception as e:
            log.exception("playbook step failed")
            step_out["status"] = "error"
            step_out["error"] = str(e)
        outputs.append(step_out)

    elapsed_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
    record = {
        "id": run_id,
        "playbook_slug": pb["slug"],
        "industry": industry,
        "input_preview": body.input[:300],
        "steps": outputs,
        "elapsed_ms": elapsed_ms,
        "created_at": _utcnow_iso(),
    }
    await db.playbook_runs.insert_one(record)
    return {"run_id": run_id, "playbook": pb["slug"], "elapsed_ms": elapsed_ms, "steps": outputs}


@api.get("/playbook-runs")
async def playbook_runs_list(_: str = Depends(require_admin)):
    docs = await db.playbook_runs.find({}, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)
    return docs


# ---------- Moat Analytics ----------
@api.get("/moat/stats")
async def moat_stats():
    """Public-ish moat metrics — shown on landing as social proof of accumulating IP."""
    return {
        "schemas": await db.schemas.count_documents({}),
        "prompts": await db.prompts.count_documents({}),
        "playbooks": await db.playbooks.count_documents({}),
        "playbook_runs": await db.playbook_runs.count_documents({}),
        "schema_corrections": await db.schema_corrections.count_documents({}),
        "agent_runs": await db.agent_runs.count_documents({}),
    }


@api.get("/moat/admin")
async def moat_admin(_: str = Depends(require_admin)):
    """Detailed moat dashboard for admin."""
    schemas = await db.schemas.find({}, {"_id": 0}).to_list(50)
    prompts = await db.prompts.find({}, {"_id": 0}).to_list(50)
    playbooks = await db.playbooks.find({}, {"_id": 0}).to_list(50)
    corrections = await db.schema_corrections.count_documents({})
    runs_by_type_cursor = db.agent_runs.aggregate([{"$group": {"_id": "$agent_type", "n": {"$sum": 1}}}])
    by_type = {d["_id"]: d["n"] async for d in runs_by_type_cursor}
    return {
        "schemas": schemas,
        "prompts": prompts,
        "playbooks": playbooks,
        "schema_corrections": corrections,
        "agent_runs_by_type": by_type,
        "model_routing": {k: [f"{p}/{m}" for p, m in v] for k, v in MODEL_ROUTING.items()},
    }


# ---------- end MOAT ----------


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


# -------------------- Routes: Lighthouse Customer Program --------------------
LIGHTHOUSE_QUALIFY_SYS = (
    "You are JADE's lighthouse-customer screener. Score this applicant 0-100 for fit as a JADE OS design partner / case study. "
    "Higher score = better fit. Weight these factors heavily: (a) decision_authority='decision_maker', "
    "(b) case_study_consent=true with logo+quote+metrics consent, (c) timeline <= 30 days, "
    "(d) budget_band >= 1500_4500, (e) primary_pain matches one of our 6 agents cleanly. "
    "Return ONLY JSON with: score (0-100), tier ('hot'|'warm'|'cold'), rationale (<=60 words), "
    "next_action (1 sentence — e.g. 'Book 20-min discovery this week'), "
    "red_flags (array of strings), green_flags (array of strings)."
)


async def _score_lighthouse(app_dict: dict) -> dict:
    """Use JADE itself to score the lighthouse application. Dogfood."""
    session = str(uuid.uuid4())
    chat = _llm(session, LIGHTHOUSE_QUALIFY_SYS, "anthropic")
    prompt = (
        f"Industry: {app_dict.get('industry')}\n"
        f"Company: {app_dict.get('company')} ({app_dict.get('company_size')} employees)\n"
        f"Operator: {app_dict.get('name')} · {app_dict.get('title')}\n"
        f"Authority: {app_dict.get('decision_authority')}\n"
        f"Timeline: {app_dict.get('timeline')}\n"
        f"Budget: {app_dict.get('budget_band')}\n"
        f"Primary pain: {app_dict.get('primary_pain')}\n"
        f"Pain detail: {app_dict.get('pain_detail')}\n"
        f"Target outcome: {app_dict.get('target_outcome')}\n"
        f"Case-study consent: {app_dict.get('case_study_consent')}\n"
        f"Logo consent: {app_dict.get('logo_consent')}\n"
        f"Quote consent: {app_dict.get('quote_consent')}\n"
        f"Metrics consent: {app_dict.get('metrics_consent')}\n"
        "Score now."
    )
    try:
        raw = []
        async for ev in chat.stream_message(UserMessage(text=prompt)):
            if isinstance(ev, TextDelta): raw.append(ev.content)
            elif isinstance(ev, StreamDone): break
        try:
            return json.loads(_strip_json("".join(raw)))
        except Exception:
            return {"score": None, "tier": None, "rationale": "auto-score parse error", "next_action": "Manual review", "red_flags": [], "green_flags": []}
    except Exception:
        return {"score": None, "tier": None, "rationale": "auto-score llm error", "next_action": "Manual review", "red_flags": [], "green_flags": []}


@api.post("/lighthouse/apply", response_model=LighthouseApplication)
async def lighthouse_apply(body: LighthouseCreate):
    """Public endpoint. Captures application and auto-scores it via JADE."""
    app = LighthouseApplication(**body.model_dump())
    # Auto-score with JADE
    qual = await _score_lighthouse(app.model_dump())
    app.score = qual.get("score")
    app.tier = qual.get("tier")
    app.rationale = qual.get("rationale")
    app.next_action = qual.get("next_action")
    app.green_flags = qual.get("green_flags") or []
    app.red_flags = qual.get("red_flags") or []
    # Hot applicants auto-advance to screening; cold get queued
    if app.tier == "hot":
        app.status = "screening"
    await db.lighthouse_applications.insert_one(app.model_dump())
    await _log_run("qualify_lead", "anthropic", DEFAULT_MODELS["anthropic"], f"[lighthouse] {app.company} · {app.industry}", json.dumps(qual)[:500])
    # --- AUTO-FOLLOWUP · web applicants get an immediate welcome email + SMS (if phone known) ---
    snap = app.model_dump()
    if snap.get("email"):
        asyncio.create_task(_send_welcome_email(snap["email"], snap))
    if snap.get("phone"):
        asyncio.create_task(_send_followup_sms(snap["phone"], snap))
    return app


@api.get("/lighthouse/applications", response_model=List[LighthouseApplication])
async def lighthouse_list(_: str = Depends(require_admin)):
    docs = await db.lighthouse_applications.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return [LighthouseApplication(**d) for d in docs]


@api.patch("/lighthouse/applications/{app_id}")
async def lighthouse_update(app_id: str, status_value: Optional[str] = None, notes: Optional[str] = None, _: str = Depends(require_admin)):
    update: Dict[str, Any] = {}
    if status_value: update["status"] = status_value
    if notes is not None: update["notes"] = notes
    if not update:
        raise HTTPException(400, "No update fields")
    res = await db.lighthouse_applications.update_one({"id": app_id}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(404, "Not found")
    return {"ok": True}


@api.get("/lighthouse/stats")
async def lighthouse_stats():
    """Public-ish counter for the landing page."""
    total = await db.lighthouse_applications.count_documents({})
    selected = await db.lighthouse_applications.count_documents({"status": {"$in": ["selected", "pilot_live", "case_published"]}})
    cap = 5  # MAX 5 lighthouse slots
    slots_remaining = max(0, cap - selected)
    return {"total_applications": total, "slots_total": cap, "slots_remaining": slots_remaining, "selected_or_active": selected}


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


# ============================================================
# P2 · TWILIO SMS + VOICE for LIGHTHOUSE applications
# ============================================================
# Inbound SMS to TWILIO_PHONE_NUMBER → parse intent via Claude → save LighthouseApplication → reply SMS
# Inbound Voice → TwiML <Gather> for speech → transcript → Claude extracts fields → save → confirm
# ============================================================

try:
    from twilio.rest import Client as TwilioClient
    from twilio.twiml.voice_response import VoiceResponse, Gather
    from twilio.twiml.messaging_response import MessagingResponse
except Exception:
    TwilioClient = None
    VoiceResponse = None
    Gather = None
    MessagingResponse = None


def _twilio_configured() -> bool:
    return bool(TwilioClient and TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER)


def _twilio_client():
    if not _twilio_configured():
        return None
    return TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


SMS_PARSE_SYS = (
    "Extract a JADE OS lighthouse-program application from a free-form SMS or voice transcript. "
    "Return ONLY JSON with: name, company, title, industry (one of: freight_brokerage, logistics, manufacturing, "
    "healthcare, saas, ecommerce, insurance, legal, real_estate, professional_services, general), "
    "primary_pain (one of: support_overflow, doc_overload, lead_chaos, ops_drift, content_grind, other), "
    "pain_detail, target_outcome, timeline (one of: 14_days, 30_days, 60_days, 90_plus). "
    "Use null when unclear. Be lenient — operators speak loose. "
    "If the message says nothing about lighthouse / case-study / pilot / demo — set name=null to signal not-an-application."
)


async def _parse_inbound_to_app(text: str, sender_id: str) -> dict:
    session = str(uuid.uuid4())
    chat = _llm(session, SMS_PARSE_SYS, "anthropic")
    raw = []
    async for ev in chat.stream_message(UserMessage(text=text)):
        if isinstance(ev, TextDelta): raw.append(ev.content)
        elif isinstance(ev, StreamDone): break
    try:
        parsed = json.loads(_strip_json("".join(raw)))
    except Exception:
        parsed = {}
    return parsed


@api.post("/twilio/sms", response_class=PlainTextResponse)
async def twilio_sms_inbound(request: Request):
    """Inbound SMS webhook. Configure in Twilio console → SMS handler URL."""
    if not MessagingResponse:
        raise HTTPException(500, "Twilio SDK not installed")
    form = await request.form()
    from_number = form.get("From", "")
    body = (form.get("Body", "") or "").strip()
    log.info(f"SMS in from {from_number}: {body[:80]}")

    parsed = await _parse_inbound_to_app(body, from_number)
    reply = MessagingResponse()

    if not parsed or not parsed.get("name"):
        reply.message(
            "JADE OS · Lighthouse program. Text APPLY with: your name, company, role, industry, the pain you want solved. "
            "Or apply at onejades.com/lighthouse — JADE will score it live."
        )
        await db.sms_inbound.insert_one({
            "id": str(uuid.uuid4()), "from_number": from_number, "body": body[:1000],
            "matched": False, "created_at": _utcnow_iso(),
        })
        return PlainTextResponse(content=str(reply), media_type="application/xml")

    # Best-effort: build a LighthouseApplication. Email/phone from Twilio number.
    body_dict = {
        "name": parsed.get("name") or "Unknown",
        "title": parsed.get("title") or "—",
        "email": f"sms+{from_number.lstrip('+')}@jadeos.ai",
        "phone": from_number,
        "company": parsed.get("company") or "Unknown",
        "industry": parsed.get("industry") or "general",
        "company_size": "11-50",
        "primary_pain": parsed.get("primary_pain") or "other",
        "pain_detail": parsed.get("pain_detail") or body[:500],
        "target_outcome": parsed.get("target_outcome") or "—",
        "timeline": parsed.get("timeline") or "30_days",
        "decision_authority": "decision_maker",
        "budget_band": "1500_4500",
        "case_study_consent": True,  # implied by texting in
        "logo_consent": False,
        "quote_consent": False,
        "metrics_consent": False,
    }
    app_doc = LighthouseApplication(**body_dict)
    qual = await _score_lighthouse(app_doc.model_dump())
    app_doc.score = qual.get("score"); app_doc.tier = qual.get("tier")
    app_doc.rationale = qual.get("rationale"); app_doc.next_action = qual.get("next_action")
    app_doc.green_flags = qual.get("green_flags") or []; app_doc.red_flags = qual.get("red_flags") or []
    if app_doc.tier == "hot": app_doc.status = "screening"
    app_doc.notes = f"[SMS · {from_number}] {body[:400]}"
    await db.lighthouse_applications.insert_one(app_doc.model_dump())
    await _log_run("qualify_lead", "anthropic", DEFAULT_MODELS["anthropic"], f"[sms-lighthouse] {body[:200]}", json.dumps(qual)[:500])
    await db.sms_inbound.insert_one({
        "id": str(uuid.uuid4()), "from_number": from_number, "body": body[:1000],
        "matched": True, "application_id": app_doc.id, "created_at": _utcnow_iso(),
    })

    confirm = f"Locked in, operator. JADE scored you {app_doc.score}/100 ({(app_doc.tier or 'pending').upper()}). " + (
        "Hot fit — we'll call within 48h. Demo + pilot link incoming."
        if app_doc.tier == "hot"
        else "We'll review and reach out. Demo + pilot link incoming."
    )
    reply.message(confirm)
    # --- AUTO-FOLLOWUP · second SMS with demo reel link + email if any ---
    snap = app_doc.model_dump()
    asyncio.create_task(_send_followup_sms(from_number, snap))
    if snap.get("email") and not snap["email"].startswith("sms+"):
        asyncio.create_task(_send_welcome_email(snap["email"], snap))
    return PlainTextResponse(content=str(reply), media_type="application/xml")


# ============================================================
# AUTO-FOLLOWUP · after vetting a caller, fire SMS (immediate)
# and welcome email (if Resend configured + email known). Queues
# missing-channel sends in db.auto_followups for the admin to see.
# ============================================================
def _welcome_email_subject(name: str) -> str:
    first = (name or "Operator").split()[0]
    return f"{first} — your JADE OS pilot package (5 min read)"


def _welcome_email_body_plain(app: dict) -> str:
    first = (app.get("name") or "Operator").split()[0]
    demo_url = f"{PUBLIC_BASE_URL}/demo-reel"
    pricing_url = f"{PUBLIC_BASE_URL}/#pricing"
    lighthouse_url = f"{PUBLIC_BASE_URL}/lighthouse"
    video_url = f"{PUBLIC_BASE_URL}/api/promo/video"
    score_line = (
        f"JADE auto-scored your call: {app.get('score', '--')} ({(app.get('tier') or '--').upper()}). "
        + ((app.get('rationale') or "")[:280])
    ).strip()
    return (
        f"Hi {first},\n\n"
        f"Thanks for the call -- JADE is the AI-agent platform built for Minneapolis ops teams "
        f"who are drowning in inbox / docs / tickets / leads work. Three things while it's fresh:\n\n"
        f"1) Watch the 12-second demo reel: {video_url}\n"
        f"   (Or the embedded version with full context: {demo_url})\n\n"
        f"2) Your fit assessment\n"
        f"   {score_line}\n\n"
        f"3) Two next steps -- pick one:\n"
        f"   - Claim a Lighthouse pilot spot ($750 / 1-month, full white-glove setup): {lighthouse_url}\n"
        f"   - Self-serve pricing + book a 15-min walkthrough: {pricing_url}\n\n"
        f"What JADE does today, in plain English:\n"
        f"  * Auto-files chaotic inboxes by topic/priority (the Outlook drag-and-drop nightmare, gone)\n"
        f"  * Extracts BOLs, intake forms, contracts to clean JSON in 8 seconds\n"
        f"  * Triages support tickets with priority + suggested response\n"
        f"  * Scores inbound leads 0-100 with green/red flags\n"
        f"  * Runs multi-step playbooks (chain agents -- extract -> score -> draft email -> send)\n\n"
        f"All operator-grade -- your data stays in your tenant, no model training.\n\n"
        f"Reply to this email or text the number you just called. I read every one personally.\n\n"
        f"-- Oliver Cummins\n"
        f"   Founder, JADE OS · onejades.com\n"
    )


async def _enqueue_followup(channel: str, *, to: str, app: dict, status: str = "queued",
                            payload: Optional[dict] = None, error: Optional[str] = None) -> str:
    fid = str(uuid.uuid4())
    await db.auto_followups.insert_one({
        "id": fid, "channel": channel, "to": to,
        "app_id": app.get("id"), "app_score": app.get("score"), "app_tier": app.get("tier"),
        "status": status, "payload": payload or {}, "error": error,
        "created_at": _utcnow_iso(),
    })
    return fid


async def _send_followup_sms(phone: str, app: dict) -> dict:
    if not phone:
        return {"status": "skipped", "reason": "no phone"}
    first = (app.get("name") or "there").split()[0]
    score = app.get("score") or "--"
    tier = (app.get("tier") or "").upper() or "REVIEW"
    video_url = f"{PUBLIC_BASE_URL}/api/promo/video"
    lighthouse_url = f"{PUBLIC_BASE_URL}/lighthouse"
    msg = (
        f"Hey {first} -- JADE here. Scored your call {score} ({tier}).\n"
        f"12-sec demo: {video_url}\n"
        f"Claim pilot: {lighthouse_url}\n"
        f"Reply MORE for the full pitch, STOP to opt out."
    )
    if not _twilio_configured():
        fid = await _enqueue_followup("sms", to=phone, app=app, status="queued",
                                      payload={"body": msg}, error="twilio not configured")
        return {"status": "queued", "id": fid}
    try:
        client = _twilio_client()
        sent = await asyncio.to_thread(client.messages.create,
                                       body=msg, from_=TWILIO_PHONE_NUMBER, to=phone)
        fid = await _enqueue_followup("sms", to=phone, app=app, status="sent",
                                      payload={"body": msg, "sid": sent.sid})
        return {"status": "sent", "sid": sent.sid, "id": fid}
    except Exception as e:
        log.exception("followup SMS failed")
        fid = await _enqueue_followup("sms", to=phone, app=app, status="failed",
                                      payload={"body": msg}, error=str(e))
        return {"status": "failed", "error": str(e), "id": fid}


async def _send_welcome_email(email: str, app: dict) -> dict:
    if not email or "@" not in email or email.startswith(("voice+", "sms+")):
        return {"status": "skipped", "reason": "no real email"}
    subject = _welcome_email_subject(app.get("name") or "")
    text = _welcome_email_body_plain(app)
    html = _plain_to_html(text)
    payload = {"subject": subject, "text": text, "html": html}
    if not _resend_configured():
        fid = await _enqueue_followup("email", to=email, app=app, status="queued",
                                      payload=payload, error="resend not configured")
        return {"status": "queued", "id": fid}
    try:
        result = await _resend_send({
            "from": RESEND_SENDER, "to": [email], "subject": subject,
            "text": text, "html": html,
            "reply_to": "cummins_oliver@yahoo.com",
            "tags": [
                {"name": "campaign", "value": "welcome_package"},
                {"name": "tier", "value": (app.get("tier") or "review")},
            ],
        })
        await db.email_sends.insert_one({
            "id": str(uuid.uuid4()), "resend_id": result.get("id"),
            "to": email, "from_": RESEND_SENDER, "subject": subject,
            "tags": {"campaign": "welcome_package", "tier": app.get("tier")},
            "status": "sent", "events": [{"type": "sent", "at": _utcnow_iso()}],
            "created_at": _utcnow_iso(),
        })
        fid = await _enqueue_followup("email", to=email, app=app, status="sent",
                                      payload={**payload, "resend_id": result.get("id")})
        return {"status": "sent", "resend_id": result.get("id"), "id": fid}
    except Exception as e:
        log.exception("welcome email failed")
        fid = await _enqueue_followup("email", to=email, app=app, status="failed",
                                      payload=payload, error=str(e))
        return {"status": "failed", "error": str(e), "id": fid}


@api.get("/auto-followups")
async def auto_followups_list(channel: Optional[str] = None, status: Optional[str] = None,
                              limit: int = 100, _: str = Depends(require_admin)):
    q: dict = {}
    if channel: q["channel"] = channel
    if status: q["status"] = status
    docs = await db.auto_followups.find(q, {"_id": 0}).sort("created_at", -1).limit(min(limit, 500)).to_list(min(limit, 500))
    return docs


@api.post("/auto-followups/{fid}/retry")
async def auto_followups_retry(fid: str, _: str = Depends(require_admin)):
    rec = await db.auto_followups.find_one({"id": fid}, {"_id": 0})
    if not rec:
        raise HTTPException(404, "Not found")
    app_doc = {"id": rec.get("app_id"), "name": "", "score": rec.get("app_score"), "tier": rec.get("app_tier")}
    if rec.get("app_id"):
        real = await db.lighthouse_applications.find_one({"id": rec["app_id"]}, {"_id": 0})
        if real: app_doc = real
    if rec["channel"] == "sms":
        return await _send_followup_sms(rec["to"], app_doc)
    return await _send_welcome_email(rec["to"], app_doc)


class TriggerFollowupRequest(BaseModel):
    application_id: str
    email: Optional[EmailStr] = None


@api.post("/auto-followups/trigger")
async def auto_followups_trigger(body: TriggerFollowupRequest, _: str = Depends(require_admin)):
    """Manually fire SMS + email followup for a given lighthouse application id."""
    app_doc = await db.lighthouse_applications.find_one({"id": body.application_id}, {"_id": 0})
    if not app_doc:
        raise HTTPException(404, "application not found")
    sms_result = await _send_followup_sms(app_doc.get("phone") or "", app_doc)
    email_addr = body.email or app_doc.get("email", "")
    email_result = await _send_welcome_email(email_addr, app_doc)
    return {"sms": sms_result, "email": email_result}




@api.post("/twilio/voice", response_class=PlainTextResponse)
async def twilio_voice_inbound(request: Request):
    """Inbound voice call. Greets caller and gathers speech (lighthouse intake)."""
    if not VoiceResponse:
        raise HTTPException(500, "Twilio SDK not installed")
    resp = VoiceResponse()
    resp.say(
        "Welcome to JADE OS, the AI agent platform for Minneapolis operators. "
        "After the tone, tell me your name, company, role, your industry, "
        "and the workflow you want JADE to automate. You have one minute.",
        voice="Polly.Joanna-Neural",
    )
    base = str(request.base_url).rstrip("/")
    gather = Gather(
        input="speech",
        action=f"{base}/api/twilio/voice/process",
        method="POST",
        speech_timeout="auto",
        timeout=8,
        language="en-US",
    )
    resp.append(gather)
    resp.say("Didn't catch that. Visit one jades dot com slash lighthouse, or text us back. Goodbye.",
             voice="Polly.Joanna-Neural")
    return PlainTextResponse(content=str(resp), media_type="application/xml")


@api.post("/twilio/voice/process", response_class=PlainTextResponse)
async def twilio_voice_process(request: Request):
    """Handles the <Gather> callback. Transcript arrives in SpeechResult."""
    if not VoiceResponse:
        raise HTTPException(500, "Twilio SDK not installed")
    form = await request.form()
    transcript = (form.get("SpeechResult", "") or "").strip()
    from_number = form.get("From", "")
    log.info(f"Voice transcript from {from_number}: {transcript[:120]}")

    resp = VoiceResponse()
    if not transcript:
        resp.say("Didn't catch anything. Please visit jadeos dot ai slash lighthouse. Goodbye.", voice="Polly.Matthew-Neural")
        return PlainTextResponse(content=str(resp), media_type="application/xml")

    parsed = await _parse_inbound_to_app(transcript, from_number)
    if not parsed or not parsed.get("name"):
        resp.say(
            "Couldn't parse a complete application. Visit one jades dot com slash lighthouse, or text us. Goodbye.",
            voice="Polly.Matthew-Neural",
        )
        await db.voice_calls.insert_one({
            "id": str(uuid.uuid4()), "from_number": from_number, "transcript": transcript[:2000],
            "matched": False, "created_at": _utcnow_iso(),
        })
        return PlainTextResponse(content=str(resp), media_type="application/xml")

    body_dict = {
        "name": parsed.get("name") or "Unknown",
        "title": parsed.get("title") or "—",
        "email": f"voice+{from_number.lstrip('+')}@jadeos.ai",
        "phone": from_number,
        "company": parsed.get("company") or "Unknown",
        "industry": parsed.get("industry") or "general",
        "company_size": "11-50",
        "primary_pain": parsed.get("primary_pain") or "other",
        "pain_detail": parsed.get("pain_detail") or transcript[:500],
        "target_outcome": parsed.get("target_outcome") or "—",
        "timeline": parsed.get("timeline") or "30_days",
        "decision_authority": "decision_maker",
        "budget_band": "1500_4500",
        "case_study_consent": True,
        "logo_consent": False, "quote_consent": False, "metrics_consent": False,
    }
    app_doc = LighthouseApplication(**body_dict)
    qual = await _score_lighthouse(app_doc.model_dump())
    app_doc.score = qual.get("score"); app_doc.tier = qual.get("tier")
    app_doc.rationale = qual.get("rationale"); app_doc.next_action = qual.get("next_action")
    app_doc.green_flags = qual.get("green_flags") or []; app_doc.red_flags = qual.get("red_flags") or []
    if app_doc.tier == "hot": app_doc.status = "screening"
    app_doc.notes = f"[VOICE · {from_number}] {transcript[:600]}"
    await db.lighthouse_applications.insert_one(app_doc.model_dump())
    await _log_run("qualify_lead", "anthropic", DEFAULT_MODELS["anthropic"], f"[voice-lighthouse] {transcript[:200]}", json.dumps(qual)[:500])
    await db.voice_calls.insert_one({
        "id": str(uuid.uuid4()), "from_number": from_number, "transcript": transcript[:2000],
        "matched": True, "application_id": app_doc.id, "created_at": _utcnow_iso(),
    })

    # --- AUTO-FOLLOWUP · fire SMS immediately, queue/send welcome email ---
    app_snapshot = app_doc.model_dump()
    asyncio.create_task(_send_followup_sms(from_number, app_snapshot))
    asyncio.create_task(_send_welcome_email(app_snapshot.get("email", ""), app_snapshot))

    score_text = "ninety five" if (app_doc.score or 0) >= 90 else "warm" if (app_doc.tier == "warm") else "captured"
    resp.say(
        f"Locked in. JADE scored you {score_text}. " + (
            "Hot fit. Expect a call within forty eight hours. Watch for a text with your demo reel."
            if app_doc.tier == "hot"
            else "We'll review and reach out. Watch for a text with your demo reel. Goodbye."
        ),
        voice="Polly.Joanna-Neural",
    )
    return PlainTextResponse(content=str(resp), media_type="application/xml")


@api.get("/twilio/inbound")
async def twilio_inbound_list(_: str = Depends(require_admin)):
    sms = await db.sms_inbound.find({}, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)
    calls = await db.voice_calls.find({}, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)
    return {
        "sms": sms, "calls": calls,
        "configured": _twilio_configured(),
        "phone": TWILIO_PHONE_NUMBER if _twilio_configured() else None,
    }


# ============================================================
# P2 · Stripe Customer Portal
# ============================================================
class PortalSessionRequest(BaseModel):
    email: EmailStr
    return_url: str


@api.post("/billing/portal-session")
async def billing_portal_session(body: PortalSessionRequest, _: str = Depends(require_admin)):
    """Create a Stripe Customer Portal session so a customer can self-serve subscription mgmt."""
    if not STRIPE_API_KEY:
        raise HTTPException(500, "Stripe not configured")
    import stripe
    stripe.api_key = STRIPE_API_KEY
    # Find or create a Stripe customer by email
    try:
        customers = stripe.Customer.list(email=body.email, limit=1).data
        if customers:
            cust = customers[0]
        else:
            cust = stripe.Customer.create(email=body.email)
        session = stripe.billing_portal.Session.create(
            customer=cust.id,
            return_url=body.return_url,
        )
        return {"url": session.url}
    except Exception as e:
        log.exception("portal session failed")
        raise HTTPException(500, str(e))


# ============================================================
# P2 · Per-customer hard token caps
# ============================================================
class TokenBudgetUpdate(BaseModel):
    email: EmailStr
    monthly_token_budget: int


@api.patch("/orgs/budget")
async def update_org_budget(body: TokenBudgetUpdate, _: str = Depends(require_admin)):
    res = await db.orgs.update_one(
        {"email": body.email},
        {"$set": {"monthly_token_budget": body.monthly_token_budget, "updated_at": _utcnow_iso()}},
    )
    if res.matched_count == 0:
        raise HTTPException(404, "Org not found")
    return {"ok": True}


async def _check_token_budget(email: Optional[str]) -> tuple[bool, dict]:
    """Returns (allowed, info). If email is None — allowed. Otherwise checks usage vs cap."""
    if not email:
        return True, {"unlimited": True}
    org = await db.orgs.find_one({"email": email}, {"_id": 0})
    if not org:
        return True, {"no_org": True}
    cap = org.get("monthly_token_budget", 2_000_000)
    # Estimate usage from this month's agent runs (4 chars/token)
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    cursor = db.agent_runs.aggregate([
        {"$match": {"created_at": {"$gte": month_start}}},
        {"$project": {"n": {"$add": [
            {"$strLenCP": {"$ifNull": ["$input_preview", ""]}},
            {"$strLenCP": {"$ifNull": ["$output_preview", ""]}},
        ]}}},
        {"$group": {"_id": None, "total": {"$sum": "$n"}}},
    ])
    used_chars = 0
    async for d in cursor:
        used_chars = d.get("total", 0)
    used_tokens = used_chars // 4
    return used_tokens < cap, {"used_tokens": used_tokens, "cap": cap}


@api.get("/orgs/budget-check")
async def org_budget_check(email: EmailStr):
    allowed, info = await _check_token_budget(email)
    return {"allowed": allowed, **info}


# ============================================================
# P3 · Public Playbook Builder
# ============================================================
class CustomerPlaybookCreate(BaseModel):
    name: str
    industry: str = "general"
    description: Optional[str] = None
    steps: List[PlaybookStep] = []
    owner_email: EmailStr


@api.post("/playbooks/customer", response_model=Playbook)
async def customer_playbook_create(body: CustomerPlaybookCreate, _: str = Depends(require_admin)):
    """Customers can build their own playbooks. Slug is auto-generated; org-scoped."""
    slug_base = body.name.lower().replace(" ", "_").replace("-", "_")
    slug_base = "".join(c for c in slug_base if c.isalnum() or c == "_")[:40] or "playbook"
    # Ensure uniqueness
    slug = slug_base
    i = 1
    while await db.playbooks.find_one({"slug": slug}):
        i += 1
        slug = f"{slug_base}_{i}"
    pb = Playbook(slug=slug, industry=body.industry, name=body.name, description=body.description, steps=body.steps)
    doc = pb.model_dump()
    doc["owner_email"] = body.owner_email
    await db.playbooks.insert_one(doc)
    return pb


# ============================================================
# P3 · Multi-user org roles
# ============================================================
class OrgMember(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    org_email: EmailStr  # the org's primary contact email
    member_email: EmailStr
    name: Optional[str] = None
    role: Literal["owner", "admin", "member", "viewer"] = "member"
    created_at: str = Field(default_factory=_utcnow_iso)


class OrgMemberCreate(BaseModel):
    org_email: EmailStr
    member_email: EmailStr
    name: Optional[str] = None
    role: Literal["owner", "admin", "member", "viewer"] = "member"


@api.post("/orgs/members", response_model=OrgMember)
async def org_member_add(body: OrgMemberCreate, _: str = Depends(require_admin)):
    m = OrgMember(**body.model_dump())
    await db.org_members.update_one(
        {"org_email": m.org_email, "member_email": m.member_email},
        {"$set": m.model_dump()},
        upsert=True,
    )
    return m


@api.get("/orgs/members", response_model=List[OrgMember])
async def org_members_list(org_email: Optional[EmailStr] = None, _: str = Depends(require_admin)):
    q = {"org_email": org_email} if org_email else {}
    docs = await db.org_members.find(q, {"_id": 0}).sort("created_at", -1).to_list(200)
    return [OrgMember(**d) for d in docs]


@api.delete("/orgs/members/{member_id}")
async def org_member_remove(member_id: str, _: str = Depends(require_admin)):
    res = await db.org_members.delete_one({"id": member_id})
    if res.deleted_count == 0:
        raise HTTPException(404, "Not found")
    return {"ok": True}


# ============================================================
# P3 · Demo Reel Embed
# ============================================================
@api.get("/embed/reel-config")
async def embed_reel_config(industry: Optional[str] = None, scene: Optional[int] = None):
    """Returns config for the embeddable reel. Used by the iframe widget."""
    return {
        "industry": industry,
        "starting_scene": scene or 0,
        "autoplay": True,
        "branded": True,
        "version": 1,
    }


# ============================================================
# ADMIN · SELF-TEST · runs a battery of checks across every major feature
# ============================================================
async def _check(name: str, category: str, fn, *, skip_reason: Optional[str] = None) -> dict:
    """Run a single check and return a structured result. fn is an async callable."""
    if skip_reason:
        return {"name": name, "category": category, "status": "skip",
                "latency_ms": 0, "message": skip_reason, "details": None}
    started = datetime.now(timezone.utc)
    try:
        details = await fn()
        latency = (datetime.now(timezone.utc) - started).total_seconds() * 1000
        return {"name": name, "category": category, "status": "pass",
                "latency_ms": round(latency, 1),
                "message": "OK", "details": details}
    except AssertionError as ae:
        latency = (datetime.now(timezone.utc) - started).total_seconds() * 1000
        return {"name": name, "category": category, "status": "fail",
                "latency_ms": round(latency, 1),
                "message": str(ae) or "assertion failed", "details": None}
    except Exception as e:
        latency = (datetime.now(timezone.utc) - started).total_seconds() * 1000
        return {"name": name, "category": category, "status": "fail",
                "latency_ms": round(latency, 1),
                "message": f"{type(e).__name__}: {e}", "details": None}


@api.get("/admin/self-test")
async def admin_self_test(deep: bool = False, _: str = Depends(require_admin)):
    """Run a battery of health checks across every major feature.

    `deep=true` enables LLM-backed checks (extract/chat) which consume tokens.
    Returns: { results: [...], summary: {pass, fail, skip, total, total_ms} }
    """
    results: List[dict] = []
    overall_started = datetime.now(timezone.utc)

    # --- AUTH ---
    async def _admin_exists():
        doc = await db.admins.find_one({"email": ADMIN_EMAIL})
        assert doc, "admin record missing"
        return {"email": ADMIN_EMAIL}
    results.append(await _check("admin record present", "AUTH", _admin_exists))

    # --- LEADS ---
    async def _leads_list():
        n = await db.leads.count_documents({})
        return {"count": n}
    results.append(await _check("leads collection reachable", "LEADS", _leads_list))

    async def _lead_roundtrip():
        probe_email = f"selftest+{uuid.uuid4().hex[:8]}@jadeos.ai"
        lead = Lead(name="Self Test", email=probe_email, company="JADE QA",
                    vertical="general", use_case="self-test probe")
        await db.leads.insert_one(lead.model_dump())
        found = await db.leads.find_one({"email": probe_email})
        assert found, "lead insert failed"
        await db.leads.delete_one({"email": probe_email})
        return {"inserted_and_purged": probe_email}
    results.append(await _check("lead insert+delete roundtrip", "LEADS", _lead_roundtrip))

    # --- LIGHTHOUSE ---
    async def _lh_stats():
        n = await db.lighthouse_applications.count_documents({})
        return {"applications": n}
    results.append(await _check("lighthouse_applications reachable", "LIGHTHOUSE", _lh_stats))

    # --- MOAT · schemas / prompts / playbooks ---
    async def _schemas():
        rows = await db.schemas.find({}, {"_id": 0}).to_list(100)
        assert len(rows) >= 1, "no seeded schemas — startup may not have run"
        return {"count": len(rows), "slugs": [r["slug"] for r in rows][:5]}
    results.append(await _check("schemas seeded", "MOAT", _schemas))

    async def _prompts():
        rows = await db.prompts.find({}, {"_id": 0}).to_list(100)
        assert len(rows) >= 1, "no seeded prompts"
        return {"count": len(rows), "slugs": [r["slug"] for r in rows][:5]}
    results.append(await _check("prompts seeded", "MOAT", _prompts))

    async def _playbooks():
        rows = await db.playbooks.find({}, {"_id": 0}).to_list(100)
        assert len(rows) >= 1, "no seeded playbooks"
        return {"count": len(rows), "slugs": [r["slug"] for r in rows][:5]}
    results.append(await _check("playbooks seeded", "MOAT", _playbooks))

    async def _moat_stats():
        # Inline call rather than HTTP round-trip
        s = await db.schemas.count_documents({})
        p = await db.prompts.count_documents({})
        b = await db.playbooks.count_documents({})
        return {"schemas": s, "prompts": p, "playbooks": b}
    results.append(await _check("moat stats computable", "MOAT", _moat_stats))

    # --- KNOWLEDGE BASE ---
    async def _kb():
        n = await db.kb_docs.count_documents({})
        return {"docs": n}
    results.append(await _check("knowledge base reachable", "KB", _kb))

    # --- WEBHOOKS ---
    async def _hooks():
        n = await db.webhooks.count_documents({})
        return {"webhooks": n}
    results.append(await _check("webhook registry reachable", "WEBHOOKS", _hooks))

    # --- BILLING / STRIPE ---
    async def _stripe_configured():
        assert STRIPE_API_KEY, "STRIPE_API_KEY missing"
        return {"has_key": True, "mode": "test" if STRIPE_API_KEY.startswith("sk_test_") else "live"}
    results.append(await _check("Stripe key configured", "BILLING", _stripe_configured))

    async def _orgs():
        n = await db.orgs.count_documents({})
        active = await db.orgs.count_documents({"subscription_status": "active"})
        return {"total": n, "active": active}
    results.append(await _check("orgs collection reachable", "BILLING", _orgs))

    # --- TWILIO ---
    async def _twilio_cfg():
        cfg = _twilio_configured()
        assert cfg, "TWILIO env vars missing or twilio SDK not installed"
        return {"phone": TWILIO_PHONE_NUMBER,
                "sid_prefix": TWILIO_ACCOUNT_SID[:6] + "…" if TWILIO_ACCOUNT_SID else None}
    results.append(await _check(
        "Twilio configured", "TWILIO", _twilio_cfg,
        skip_reason=None if _twilio_configured() else "Twilio creds not set in env (SMS/Voice webhooks unreachable until configured)",
    ))

    async def _twilio_sdk():
        assert MessagingResponse is not None, "twilio.twiml.messaging_response not importable"
        assert VoiceResponse is not None, "twilio.twiml.voice_response not importable"
        # TwiML construction smoke test (does not hit network)
        m = MessagingResponse()
        m.message("ping")
        v = VoiceResponse()
        v.say("ping")
        return {"twiml_smoke": "ok"}
    results.append(await _check("Twilio TwiML SDK importable", "TWILIO", _twilio_sdk))

    # --- LLM CONNECTIVITY ---
    async def _llm_key():
        assert EMERGENT_LLM_KEY, "EMERGENT_LLM_KEY missing"
        return {"has_key": True, "providers": list(DEFAULT_MODELS.keys())}
    results.append(await _check("Emergent LLM key present", "LLM", _llm_key))

    # --- DEEP TESTS · use LLM tokens, only when requested ---
    async def _llm_chat_deep():
        session = str(uuid.uuid4())
        chat = _llm(session, "You are a test bot. Respond with the single word PONG.", "anthropic")
        chunks = []
        async for ev in chat.stream_message(UserMessage(text="ping")):
            if isinstance(ev, TextDelta):
                chunks.append(ev.content)
            elif isinstance(ev, StreamDone):
                break
        text = "".join(chunks).strip()
        assert text, "empty LLM response"
        return {"reply_preview": text[:120], "provider": "anthropic"}
    results.append(await _check(
        "Claude chat round-trip", "LLM", _llm_chat_deep,
        skip_reason=None if deep else "deep=false (pass ?deep=true to enable LLM calls — costs tokens)",
    ))

    async def _llm_extract_deep():
        session = str(uuid.uuid4())
        sys_prompt = ("Extract JSON {company, freight} from input. Return ONLY JSON.")
        chat = _llm(session, sys_prompt, "anthropic")
        chunks = []
        async for ev in chat.stream_message(UserMessage(text="ACME Corp shipped 12 pallets of dry freight from MSP to DFW.")):
            if isinstance(ev, TextDelta):
                chunks.append(ev.content)
            elif isinstance(ev, StreamDone):
                break
        raw = _strip_json("".join(chunks))
        data = json.loads(raw)
        assert "company" in data, "extracted JSON missing 'company'"
        return {"extracted": data}
    results.append(await _check(
        "Claude extract+JSON parse", "LLM", _llm_extract_deep,
        skip_reason=None if deep else "deep=false",
    ))

    # --- AGENT RUNS · ledger ---
    async def _agent_runs():
        n = await db.agent_runs.count_documents({})
        return {"runs_logged": n}
    results.append(await _check("agent_runs ledger reachable", "AGENT", _agent_runs))

    # --- CASE STUDIES ---
    async def _case_studies():
        rows = await db.case_studies.find({}, {"_id": 0, "slug": 1, "title": 1}).to_list(20)
        assert len(rows) >= 1, "no seeded case studies"
        return {"count": len(rows), "slugs": [r["slug"] for r in rows][:5]}
    results.append(await _check("case studies seeded", "CONTENT", _case_studies))

    # --- PDF EXTRACTION DEP ---
    async def _pdf_dep():
        assert PdfReader is not None, "pypdf not installed (pip install pypdf)"
        return {"pypdf": "ok"}
    results.append(await _check("PDF extractor (pypdf) importable", "AGENT", _pdf_dep))

    # --- MONGO PING ---
    async def _mongo_ping():
        pong = await client.admin.command("ping")
        assert pong.get("ok") == 1, "mongo ping failed"
        return {"ping": "ok", "db": DB_NAME}
    results.append(await _check("MongoDB ping", "INFRA", _mongo_ping))

    # --- SUMMARY ---
    summary = {
        "pass": sum(1 for r in results if r["status"] == "pass"),
        "fail": sum(1 for r in results if r["status"] == "fail"),
        "skip": sum(1 for r in results if r["status"] == "skip"),
        "total": len(results),
        "total_ms": round((datetime.now(timezone.utc) - overall_started).total_seconds() * 1000, 1),
        "deep": deep,
        "ran_at": _utcnow_iso(),
    }
    return {"results": results, "summary": summary}


# ============================================================
# PROSPECTS · AI-generated Minneapolis-area leads per industry +
# tailored solicitation email packages (mailto: handoff)
# ============================================================
INDUSTRY_PROSPECT_HINTS = {
    "freight_brokerage": "Minneapolis-St. Paul freight brokers, 3PLs, dispatch shops — focus on Eagan, Bloomington, NE Minneapolis warehouse corridors. Realistic carrier names; 11-200 person ops; pain = load matching, BOL paperwork, after-hours dispatch.",
    "logistics": "Twin Cities last-mile / regional fleet ops — Roseville, Brooklyn Park, Maple Grove. Pain = route planning, driver comms, customer ETAs.",
    "manufacturing": "Minnesota precision manufacturers, medical-device suppliers, food processors — Plymouth, Eden Prairie, Coon Rapids. Pain = work-order intake, supplier follow-up, QA documentation.",
    "healthcare": "Twin Cities specialty clinics, dental groups, behavioral health, urgent care — Edina, St. Louis Park, Woodbury. Pain = patient intake, prior auth, after-hours triage. NEVER invent regulated data.",
    "saas": "Minneapolis B2B SaaS startups (10-100 FTE) — North Loop, Northeast. Pain = lead qualification, support overflow, onboarding sequences.",
    "ecommerce": "MN DTC / Shopify-Plus brands and Mall-of-America-adjacent retailers. Pain = order support, RMA workflow, abandoned-cart sequences.",
    "insurance": "Independent agencies / commercial brokers — St. Paul, Wayzata. Pain = COI requests, claim FNOL intake, renewal follow-up.",
    "legal": "Boutique firms — IP, family, immigration, employment. Twin Cities suburbs. Pain = intake screening, conflict checks, document review.",
    "real_estate": "Commercial property managers & multifamily ops — downtown Mpls, Uptown, St. Paul. Pain = tenant work-orders, lease admin, vendor coordination.",
    "professional_services": "MSP-area agencies / consultancies (marketing, fractional CFO, IT-MSP). Pain = lead intake, proposal generation, SOW drafting.",
    "general": "Minneapolis-St. Paul SMBs (11-200 FTE) across mixed sectors. Pain = the operator drowning in ops work.",
}


PROSPECT_GEN_SYS = (
    "You generate realistic prospective B2B sales leads for JADE OS — an AI-agent platform for ops-heavy SMBs. "
    "Each prospect MUST be plausible (real-sounding company name in the Minneapolis-St. Paul metro, realistic role title, "
    "plausible email at a company domain, a specific operational pain). Do NOT use real famous brands. "
    "Generate diverse roles (Director of Operations, COO, Dispatch Manager, Practice Admin, RevOps Lead, etc.). "
    "Return ONLY JSON: {\"prospects\": [{\"company\": str, \"name\": str, \"title\": str, \"email\": str, \"city\": str, "
    "\"company_size\": str (e.g. '25-50'), \"pain_point\": str (1 sentence, specific), \"hook\": str (1-sentence opening "
    "line JADE could use), \"jade_fit_score\": int 0-100, \"recommended_agent\": str (one of: "
    "qualify_lead/extract/support_triage/draft_outreach/playbook)}]} "
    "Score reflects how strong a JADE OS fit they are."
)


class ProspectRequest(BaseModel):
    industry: str = "general"
    count: int = 8


@api.post("/prospects/generate")
async def prospects_generate(body: ProspectRequest, _: str = Depends(require_admin)):
    """LLM-generate a list of realistic Minneapolis-area B2B prospects for a given industry.

    These are AI-synthesized — useful for outreach planning, role-play, and seeding the leads pipe.
    They are NOT pulled from a real lead database (no Apollo/ZoomInfo wired). Saved to db.prospects.
    """
    count = max(1, min(int(body.count or 8), 12))
    hint = INDUSTRY_PROSPECT_HINTS.get(body.industry, INDUSTRY_PROSPECT_HINTS["general"])
    session = str(uuid.uuid4())
    chat = _llm(session, PROSPECT_GEN_SYS, "anthropic")
    user_msg = (
        f"Industry: {body.industry}\n"
        f"Region hint: {hint}\n"
        f"Generate exactly {count} prospects. Vary city, size, and role. "
        f"Make pain_points concrete (not generic). Score range 55-95 — no obviously bad fits. "
        f"Emails should be at lowercase @company-derived domains."
    )
    raw = []
    async for ev in chat.stream_message(UserMessage(text=user_msg)):
        if isinstance(ev, TextDelta):
            raw.append(ev.content)
        elif isinstance(ev, StreamDone):
            break
    try:
        data = json.loads(_strip_json("".join(raw)))
        prospects = data.get("prospects", [])
    except Exception as e:
        log.exception("prospect parse failed")
        raise HTTPException(500, f"LLM JSON parse failed: {e}")

    # Stamp + persist
    batch_id = str(uuid.uuid4())
    now = _utcnow_iso()
    docs = []
    for p in prospects:
        docs.append({
            "id": str(uuid.uuid4()),
            "batch_id": batch_id,
            "industry": body.industry,
            "company": p.get("company", "Unknown"),
            "name": p.get("name", "Unknown"),
            "title": p.get("title", "—"),
            "email": (p.get("email") or "").lower(),
            "city": p.get("city", "Minneapolis"),
            "company_size": p.get("company_size", "11-50"),
            "pain_point": p.get("pain_point", ""),
            "hook": p.get("hook", ""),
            "jade_fit_score": int(p.get("jade_fit_score", 70)),
            "recommended_agent": p.get("recommended_agent", "qualify_lead"),
            "created_at": now,
            "contacted": False,
        })
    if docs:
        await db.prospects.insert_many(docs)
    await _log_run("qualify_lead", "anthropic", DEFAULT_MODELS["anthropic"],
                   f"[prospects · {body.industry}]", f"generated {len(docs)} prospects")
    # Return without _id (insert_many mutates docs to add _id)
    for d in docs:
        d.pop("_id", None)
    return {"batch_id": batch_id, "industry": body.industry, "count": len(docs), "prospects": docs}


@api.get("/prospects")
async def prospects_list(industry: Optional[str] = None, _: str = Depends(require_admin)):
    q = {"industry": industry} if industry else {}
    docs = await db.prospects.find(q, {"_id": 0}).sort("created_at", -1).limit(200).to_list(200)
    return docs


@api.delete("/prospects/{pid}")
async def prospects_delete(pid: str, _: str = Depends(require_admin)):
    res = await db.prospects.delete_one({"id": pid})
    if res.deleted_count == 0:
        raise HTTPException(404, "Not found")
    return {"ok": True}


@api.patch("/prospects/{pid}/contacted")
async def prospects_mark_contacted(pid: str, _: str = Depends(require_admin)):
    res = await db.prospects.update_one({"id": pid}, {"$set": {"contacted": True, "contacted_at": _utcnow_iso()}})
    if res.matched_count == 0:
        raise HTTPException(404, "Not found")
    return {"ok": True}


OUTREACH_EMAIL_SYS = (
    "You are JADE's outbound copywriter. Voice: short, operator-grade, no marketing fluff, no exclamation marks. "
    "Write a cold-outreach email package from Oliver Cummins (founder of JADE OS — onejades.com) to a Minneapolis-area "
    "operator. Include a specific reference to their pain point. Email body 90-140 words, opens with the hook, "
    "includes one concrete claim (e.g. 'cuts intake time ~60%'), and ends with a 15-min call CTA. "
    "ALSO include a 'package' — 3 bullet talking points and a one-paragraph PS. "
    "Return ONLY JSON: {\"subject\": str, \"body\": str, \"talking_points\": [str, str, str], \"ps\": str}"
)


class OutreachEmailRequest(BaseModel):
    prospect_id: str


@api.post("/prospects/{pid}/email-draft")
async def prospect_email_draft(pid: str, _: str = Depends(require_admin)):
    """Generate a tailored solicitation email package for a saved prospect."""
    p = await db.prospects.find_one({"id": pid}, {"_id": 0})
    if not p:
        raise HTTPException(404, "Prospect not found")
    session = str(uuid.uuid4())
    chat = _llm(session, OUTREACH_EMAIL_SYS, "anthropic")
    user_msg = (
        f"Prospect: {p['name']} · {p['title']} at {p['company']} ({p['city']}, {p['company_size']} FTE)\n"
        f"Industry: {p['industry']}\n"
        f"Pain point: {p['pain_point']}\n"
        f"Suggested hook: {p.get('hook') or '—'}\n"
        f"Recommended JADE agent: {p.get('recommended_agent') or 'qualify_lead'}\n\n"
        f"Write the package."
    )
    raw = []
    async for ev in chat.stream_message(UserMessage(text=user_msg)):
        if isinstance(ev, TextDelta):
            raw.append(ev.content)
        elif isinstance(ev, StreamDone):
            break
    try:
        pkg = json.loads(_strip_json("".join(raw)))
    except Exception as e:
        raise HTTPException(500, f"LLM JSON parse failed: {e}")
    await _log_run("draft_outreach", "anthropic", DEFAULT_MODELS["anthropic"],
                   f"[prospect-email · {p['company']}]", pkg.get("subject", "")[:200])
    pkg["to"] = p["email"]
    pkg["prospect_id"] = pid
    return pkg


# ============================================================
# PROMO REEL · Sora 2 generated promotional video, served publicly
# v2 (sora-2-pro, longer, real ops use-case scenes) preferred when present.
# ============================================================
PROMO_VIDEO_PATH = Path("/app/static/jadeos_promo.mp4")
PROMO_META_PATH = Path("/app/static/jadeos_promo.json")
PROMO_V2_PATH = Path("/app/static/jadeos_promo_v2.mp4")
PROMO_V2_META = Path("/app/static/jadeos_promo_v2.json")
PROMO_V3_PATH = Path("/app/static/jadeos_promo_v3.mp4")
PROMO_V3_META = Path("/app/static/jadeos_promo_v3.json")


def _active_promo():
    if PROMO_V3_PATH.exists() and PROMO_V3_META.exists():
        return PROMO_V3_PATH, PROMO_V3_META
    if PROMO_V2_PATH.exists() and PROMO_V2_META.exists():
        return PROMO_V2_PATH, PROMO_V2_META
    return PROMO_VIDEO_PATH, PROMO_META_PATH


@api.get("/promo/video")
async def promo_video(v: Optional[int] = None):
    """Stream the JADE OS promotional reel. `?v=1`, `?v=2`, or `?v=3` pins a version; omit for newest."""
    if v == 1:
        path = PROMO_VIDEO_PATH
    elif v == 2:
        path = PROMO_V2_PATH
    elif v == 3:
        path = PROMO_V3_PATH
    else:
        path, _ = _active_promo()
    if not path.exists():
        raise HTTPException(404, "promo video not yet generated")
    return FileResponse(
        str(path),
        media_type="video/mp4",
        filename=path.name,
        headers={"Cache-Control": "public, max-age=3600"},
    )


@api.get("/promo/meta")
async def promo_meta(v: Optional[int] = None):
    """Metadata sidecar. Same version-pinning semantics as /promo/video."""
    if v == 1:
        meta_path, vid_path = PROMO_META_PATH, PROMO_VIDEO_PATH
    elif v == 2:
        meta_path, vid_path = PROMO_V2_META, PROMO_V2_PATH
    elif v == 3:
        meta_path, vid_path = PROMO_V3_META, PROMO_V3_PATH
    else:
        vid_path, meta_path = _active_promo()
    if not meta_path.exists():
        return {"available": False, "versions_available": {
            "v1": PROMO_VIDEO_PATH.exists(),
            "v2": PROMO_V2_PATH.exists(),
            "v3": PROMO_V3_PATH.exists(),
        }}
    try:
        data = json.loads(meta_path.read_text())
    except Exception:
        data = {}
    data["available"] = vid_path.exists()
    data["versions_available"] = {
        "v1": PROMO_VIDEO_PATH.exists(),
        "v2": PROMO_V2_PATH.exists(),
        "v3": PROMO_V3_PATH.exists(),
    }
    return data


# ============================================================
# RESEND · transactional email send + delivery tracking
# Closes the gap from `mailto:` handoff to first-class outbound channel.
# ============================================================
try:
    import resend as _resend
except Exception:
    _resend = None


def _resend_configured() -> bool:
    return bool(_resend and RESEND_API_KEY)


class ResendSendRequest(BaseModel):
    to: EmailStr
    subject: str
    html: Optional[str] = None
    text: Optional[str] = None
    reply_to: Optional[EmailStr] = None
    sender: Optional[str] = None  # override default sender
    tags: Optional[Dict[str, str]] = None  # e.g. {"campaign": "prospect_outreach"}


async def _resend_send(payload: dict) -> dict:
    """Call Resend in a thread to keep the event loop free."""
    if not _resend_configured():
        raise HTTPException(503, "Resend not configured — set RESEND_API_KEY in /app/backend/.env")
    _resend.api_key = RESEND_API_KEY
    return await asyncio.to_thread(_resend.Emails.send, payload)


@api.post("/resend/send")
async def resend_send_email(body: ResendSendRequest, _: str = Depends(require_admin)):
    """Send a transactional email via Resend. Persists a sends record for delivery tracking."""
    if not body.html and not body.text:
        raise HTTPException(400, "Provide html and/or text body")
    params = {
        "from": body.sender or RESEND_SENDER,
        "to": [str(body.to)],
        "subject": body.subject,
    }
    if body.html: params["html"] = body.html
    if body.text: params["text"] = body.text
    if body.reply_to: params["reply_to"] = str(body.reply_to)
    if body.tags:
        params["tags"] = [{"name": k, "value": v} for k, v in body.tags.items()]

    try:
        result = await _resend_send(params)
    except HTTPException:
        raise
    except Exception as e:
        log.exception("resend send failed")
        raise HTTPException(500, f"Resend send failed: {e}")

    record = {
        "id": str(uuid.uuid4()),
        "resend_id": result.get("id"),
        "to": str(body.to),
        "from_": params["from"],
        "subject": body.subject,
        "tags": body.tags or {},
        "status": "sent",
        "events": [{"type": "sent", "at": _utcnow_iso()}],
        "created_at": _utcnow_iso(),
    }
    await db.email_sends.insert_one(record)
    record.pop("_id", None)
    return record


class ProspectSendRequest(BaseModel):
    """Send a prospect's pre-drafted email via Resend (instead of mailto:).

    Frontend posts the pkg from /prospects/{id}/email-draft directly here.
    """
    prospect_id: str
    subject: str
    body: str  # plain-text body — server converts to HTML on the wire
    sender: Optional[str] = None


def _plain_to_html(text: str) -> str:
    """Light wrap — preserves newlines, no external CSS, email-safe."""
    safe = (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    paragraphs = safe.split("\n\n")
    html_parts = [
        f'<p style="margin:0 0 16px;font:14px/1.55 Inter,Helvetica,Arial,sans-serif;color:#1a1a1a">{p.replace(chr(10), "<br>")}</p>'
        for p in paragraphs if p.strip()
    ]
    return (
        '<table cellpadding="0" cellspacing="0" border="0" width="100%" '
        'style="background:#ffffff;padding:24px 0">'
        '<tr><td align="center"><table cellpadding="0" cellspacing="0" border="0" width="560" '
        'style="max-width:560px"><tr><td>'
        + "".join(html_parts)
        + '<p style="margin:24px 0 0;padding-top:16px;border-top:1px solid #e5e5e5;'
          'font:11px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;color:#888">'
          'Sent via <b style="color:#7aaf00">JADE&nbsp;OS</b> · onejades.com</p>'
        + '</td></tr></table></td></tr></table>'
    )


@api.post("/prospects/{pid}/send-via-resend")
async def prospect_send_via_resend(pid: str, body: ProspectSendRequest, _: str = Depends(require_admin)):
    """Send the drafted solicitation email directly via Resend (one click, no mailto handoff)."""
    p = await db.prospects.find_one({"id": pid}, {"_id": 0})
    if not p:
        raise HTTPException(404, "Prospect not found")
    html = _plain_to_html(body.body)
    params = {
        "from": body.sender or RESEND_SENDER,
        "to": [p["email"]],
        "subject": body.subject,
        "text": body.body,
        "html": html,
        "tags": [
            {"name": "campaign", "value": "prospect_outreach"},
            {"name": "industry", "value": p.get("industry", "general")},
            {"name": "prospect_id", "value": pid},
        ],
        "reply_to": "cummins_oliver@yahoo.com",
    }
    try:
        result = await _resend_send(params)
    except HTTPException:
        raise
    except Exception as e:
        log.exception("prospect resend failed")
        raise HTTPException(500, f"Resend send failed: {e}")

    send_id = str(uuid.uuid4())
    await db.email_sends.insert_one({
        "id": send_id,
        "resend_id": result.get("id"),
        "to": p["email"],
        "from_": params["from"],
        "subject": body.subject,
        "tags": {"campaign": "prospect_outreach", "industry": p.get("industry"), "prospect_id": pid},
        "status": "sent",
        "events": [{"type": "sent", "at": _utcnow_iso()}],
        "created_at": _utcnow_iso(),
    })
    await db.prospects.update_one({"id": pid}, {"$set": {
        "contacted": True, "contacted_at": _utcnow_iso(),
        "last_send_id": send_id, "last_resend_id": result.get("id"),
    }})
    return {"ok": True, "send_id": send_id, "resend_id": result.get("id")}


@api.get("/resend/status")
async def resend_status(_: str = Depends(require_admin)):
    """Quick health check for the Resend integration."""
    return {
        "configured": _resend_configured(),
        "sender": RESEND_SENDER if _resend_configured() else None,
        "sdk_installed": _resend is not None,
        "has_key": bool(RESEND_API_KEY),
        "has_webhook_secret": bool(RESEND_WEBHOOK_SECRET),
    }


@api.get("/resend/sends")
async def resend_sends_list(limit: int = 100, _: str = Depends(require_admin)):
    """List recent email sends with their latest status + event timeline."""
    docs = await db.email_sends.find({}, {"_id": 0}).sort("created_at", -1).limit(min(limit, 500)).to_list(min(limit, 500))
    return docs


@api.post("/webhooks/resend")
async def resend_webhook(request: Request):
    """Inbound Resend webhook — updates the send record with delivery/open/click/bounce events.

    Signature verification (svix) is wired but optional: if RESEND_WEBHOOK_SECRET is set
    AND the svix-id/svix-timestamp/svix-signature headers are present, we verify.
    Otherwise we accept (suitable for early dev / Resend's testing mode).
    """
    raw = await request.body()
    headers = dict(request.headers)

    if RESEND_WEBHOOK_SECRET and headers.get("svix-signature"):
        try:
            from svix.webhooks import Webhook  # ships transitively with resend
            wh = Webhook(RESEND_WEBHOOK_SECRET)
            wh.verify(raw, headers)
        except Exception as e:
            log.warning(f"resend webhook signature invalid: {e}")
            raise HTTPException(400, "invalid signature")

    try:
        evt = json.loads(raw.decode("utf-8"))
    except Exception:
        raise HTTPException(400, "invalid JSON")

    # Resend event schema: {type: "email.delivered", data: {email_id, to, ...}, created_at}
    event_type = (evt.get("type") or "").lower()       # email.sent / .delivered / .opened / .clicked / .bounced / .complained / .delivery_delayed
    data = evt.get("data") or {}
    resend_id = data.get("email_id") or data.get("id")
    status = event_type.split(".")[-1] if event_type else "unknown"

    if resend_id:
        await db.email_sends.update_one(
            {"resend_id": resend_id},
            {
                "$set": {"status": status, "last_event_at": _utcnow_iso()},
                "$push": {"events": {"type": event_type, "at": _utcnow_iso(), "data": data}},
            },
        )
    # Always store raw inbound for audit
    await db.resend_inbound.insert_one({
        "id": str(uuid.uuid4()),
        "event_type": event_type,
        "resend_id": resend_id,
        "raw": evt,
        "created_at": _utcnow_iso(),
    })
    return {"ok": True}


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
    # Seed schemas (MOAT)
    for s in SCHEMA_SEED:
        await db.schemas.update_one(
            {"slug": s["slug"], "org_email": None, "version": 1},
            {"$setOnInsert": {**s, "id": str(uuid.uuid4()), "version": 1, "org_email": None, "correction_count": 0, "created_at": _utcnow_iso()}},
            upsert=True,
        )
    # Seed prompts (MOAT)
    for p in PROMPT_SEED:
        await db.prompts.update_one(
            {"slug": p["slug"]},
            {"$setOnInsert": {**p, "id": str(uuid.uuid4()), "variant": "A", "version": 1, "org_email": None, "created_at": _utcnow_iso()}},
            upsert=True,
        )
    # Seed playbooks (MOAT — the killer feature)
    for pb in PLAYBOOK_SEED:
        await db.playbooks.update_one(
            {"slug": pb["slug"]},
            {"$setOnInsert": {**pb, "id": str(uuid.uuid4()), "created_at": _utcnow_iso()}},
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
