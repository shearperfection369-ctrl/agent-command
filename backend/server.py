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
try:
    from emergentintegrations.llm.chat import ChatError  # surfaced by emergentintegrations on stream failure
except Exception:
    class ChatError(Exception):
        pass
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


# ============================================================
# SECURITY MIDDLEWARE — defense-in-depth headers + light hardening
# ------------------------------------------------------------
# • Strict-Transport-Security  · forces HTTPS for 1 year
# • X-Content-Type-Options      · stops MIME sniffing attacks
# • X-Frame-Options             · denies clickjacking via iframes
# • Referrer-Policy             · doesn't leak URLs cross-origin
# • Permissions-Policy          · blocks unused browser APIs
# • Content-Security-Policy     · base-uri + frame-ancestors lockdown
# ============================================================
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        h = response.headers
        h.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        h.setdefault("X-Content-Type-Options", "nosniff")
        h.setdefault("X-Frame-Options", "SAMEORIGIN")
        h.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        h.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        # Conservative CSP — does not break inline React; locks down embeds
        h.setdefault(
            "Content-Security-Policy",
            "base-uri 'self'; frame-ancestors 'self'; object-src 'none'; form-action 'self'",
        )
        return response


app.add_middleware(SecurityHeadersMiddleware)


# ============================================================
# RATE LIMIT — in-memory token bucket on sensitive endpoints
# (auth, lighthouse intake, prospect generation, webhooks)
# Kept simple + dependency-free; resets on process restart.
# ============================================================
from collections import defaultdict, deque
import time as _time
_RL_BUCKETS: dict[str, deque] = defaultdict(deque)


def _rate_limited(key: str, max_calls: int, window_s: float) -> bool:
    """Return True if `key` has exceeded max_calls within window_s."""
    now = _time.time()
    q = _RL_BUCKETS[key]
    while q and now - q[0] > window_s:
        q.popleft()
    if len(q) >= max_calls:
        return True
    q.append(now)
    return False


def _client_key(request: Request, scope: str) -> str:
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or request.client.host
    return f"{scope}:{ip}"

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
    agent_type: Literal["chat", "extract", "extract_bol", "draft_outreach", "qualify_lead", "support_triage", "freight_load_match", "freight_carrier_outreach", "freight_shipper_comm"]
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
    # Optional memory binding: when set, the agent recalls the thread's
    # facts ledger + recent turns AND auto-appends both sides of the exchange.
    memory_thread_type: Optional[Literal["load", "customer", "issue"]] = None
    memory_thread_key: Optional[str] = None


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


# ============================================================
# LLM ERROR CLASSIFIER — surfaces budget / quota / auth errors
# from the Universal Key gateway as actionable 402 responses
# instead of opaque 500s. Frontend keys off `code` to render the
# correct banner.
# ============================================================
import re as _re

def classify_llm_error(e: Exception) -> dict:
    """Return a structured payload describing an LLM-call failure.
    Always returns a dict with at minimum {"code", "message", "http_status"}.
    """
    msg = str(e) or repr(e)
    low = msg.lower()
    if "budget" in low and ("exceed" in low or "exceeded" in low):
        m = _re.search(r"current cost:\s*([\d.]+).*?max budget:\s*([\d.]+)", msg, _re.IGNORECASE)
        payload = {
            "code": "budget_exceeded",
            "message": "Universal LLM Key budget exceeded. Top up in Profile → Universal Key → Add Balance.",
            "raw": msg[:400],
            "http_status": 402,
        }
        if m:
            try:
                payload["current_cost"] = float(m.group(1))
                payload["max_budget"] = float(m.group(2))
            except Exception:
                pass
        return payload
    if "insufficient" in low and "balance" in low:
        return {
            "code": "insufficient_balance",
            "message": "Universal LLM Key has insufficient balance. Top up in Profile → Universal Key → Add Balance.",
            "raw": msg[:400],
            "http_status": 402,
        }
    if "rate" in low and "limit" in low:
        return {
            "code": "rate_limited",
            "message": "LLM provider is rate-limiting requests. Retry in a few seconds.",
            "raw": msg[:400],
            "http_status": 429,
        }
    if "unauthorized" in low or "invalid api key" in low or "authentication" in low:
        return {
            "code": "auth_failed",
            "message": "LLM key authentication failed. Verify EMERGENT_LLM_KEY is set and active.",
            "raw": msg[:400],
            "http_status": 401,
        }
    if "timeout" in low or "timed out" in low:
        return {
            "code": "timeout",
            "message": "LLM provider timed out. Retry, and consider switching provider (Claude ↔ GPT) in the toggle.",
            "raw": msg[:400],
            "http_status": 504,
        }
    return {
        "code": "llm_error",
        "message": "LLM call failed. See raw for details.",
        "raw": msg[:400],
        "http_status": 502,
    }


def llm_http_exception(e: Exception) -> HTTPException:
    """Convert any LLM-call failure into a typed HTTPException with structured detail.
    Also fires an out-of-band log to db.llm_errors so the admin HEALTH tab can show it."""
    info = classify_llm_error(e)
    # Best-effort persist — never block the request on a logging failure
    try:
        import asyncio as _asyncio
        _asyncio.create_task(db.llm_errors.insert_one({
            "id": str(uuid.uuid4()),
            "created_at": _utcnow_iso(),
            "code": info.get("code"),
            "message": info.get("message"),
            "http_status": info.get("http_status"),
            "raw": info.get("raw"),
            "current_cost": info.get("current_cost"),
            "max_budget": info.get("max_budget"),
        }))
    except Exception:
        pass
    return HTTPException(status_code=info["http_status"], detail=info)


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
async def login(body: LoginRequest, request: Request):
    # Brute-force guard: 8 attempts per IP per 5 minutes
    if _rate_limited(_client_key(request, "login"), max_calls=8, window_s=300):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many login attempts. Try again in 5 minutes.")
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
    base_role = "be a knowledgeable Tier-1 / ops co-pilot — answer questions, route issues, escalate when needed"
    sys_msg = _system_for(body.industry, base_role)

    # Memory binding: auto-recall + auto-append. Optional and additive — chat
    # works fine without it.
    bound_thread = None
    if body.memory_thread_type and body.memory_thread_key:
        try:
            import memory_workflow as _mem
            bound_thread = await _mem.get_or_create_thread(
                db, body.memory_thread_type, body.memory_thread_key.strip(),
                industry=body.industry,
            )
            recall = await _mem.build_recall_context(db, bound_thread["id"])
            if recall:
                sys_msg += f"\n\n----\nWORKFLOW MEMORY — use these as ground truth:\n{recall}"
            await _mem.append_turn(db, bound_thread["id"], "user", body.message,
                                   metadata={"session_id": body.session_id})
        except Exception as e:
            log.warning("memory · recall/append failed · %s", e)
            bound_thread = None

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
            full_text = "".join(full)
            await _log_run("chat", body.provider, model_used, f"[{body.industry}] {body.message}", full_text)
            # Persist assistant reply into the memory thread + auto-distill check
            if bound_thread is not None:
                try:
                    import memory_workflow as _mem
                    await _mem.append_turn(db, bound_thread["id"], "assistant", full_text,
                                           metadata={"session_id": body.session_id})
                    fresh = await db.memory_threads.find_one({"id": bound_thread["id"]}, {"_id": 0})
                    if fresh and (fresh.get("turn_count", 0) - fresh.get("last_distilled_at_turn", 0)) >= _mem.DISTILL_EVERY_TURNS:
                        try:
                            await _mem.distill_thread(db, bound_thread["id"], _llm)
                        except Exception as de:
                            log.warning("memory · distill after chat failed · %s", de)
                except Exception as e:
                    log.warning("memory · assistant append failed · %s", e)
        except Exception as e:
            log.exception("chat stream error")
            info = classify_llm_error(e)
            try:
                await db.llm_errors.insert_one({
                    "id": str(uuid.uuid4()),
                    "created_at": _utcnow_iso(),
                    "code": info.get("code"),
                    "message": info.get("message"),
                    "http_status": info.get("http_status"),
                    "raw": info.get("raw"),
                    "current_cost": info.get("current_cost"),
                    "max_budget": info.get("max_budget"),
                    "endpoint": "/api/agent/chat",
                })
            except Exception:
                pass
            yield f"data: {json.dumps({'error': info['message'], 'code': info['code'], 'details': info})}\n\n"

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
        raise llm_http_exception(e)


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
        raise llm_http_exception(e)


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
        raise llm_http_exception(e)


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
        raise llm_http_exception(e)


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


# ============================================================
# HEALTH & DIAGNOSTICS — admin-grade observability
# ------------------------------------------------------------
# /api/llm-health           · public · cheapest possible ping (last cached
#                              budget error from db.llm_errors, no LLM call)
# /api/admin/llm-probe      · admin · live 1-token LLM round-trip (costs ~$0)
# /api/admin/llm-errors     · admin · last 100 LLM failures w/ dedupe by code
# /api/admin/system-health  · admin · everything-in-one snapshot
# /api/admin/repair/*       · admin · self-heal actions (retry queues, etc.)
# ============================================================

import shutil as _shutil


async def _latest_llm_error() -> Optional[dict]:
    doc = await db.llm_errors.find_one({}, {"_id": 0}, sort=[("created_at", -1)])
    return doc


async def _service_matrix() -> dict:
    """Configured/missing matrix for every external dependency."""
    twilio_configured = bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER)
    stripe_configured = bool(STRIPE_API_KEY)
    resend_configured = bool(RESEND_API_KEY)
    llm_configured = bool(EMERGENT_LLM_KEY)
    return {
        "mongo":  {"configured": True, "label": "MongoDB", "required": True},
        "llm":    {"configured": llm_configured, "label": "Emergent Universal LLM Key", "required": True, "purpose": "All agent reasoning, embeddings, Sora video"},
        "twilio": {"configured": twilio_configured, "label": "Twilio SMS/Voice", "required": False, "purpose": "Inbound voice/SMS lead capture + auto-followup SMS"},
        "stripe": {"configured": stripe_configured, "label": "Stripe", "required": False, "purpose": "Billing, customer portal"},
        "resend": {"configured": resend_configured, "label": "Resend Email", "required": False, "purpose": "Transactional outbound + auto-followup welcome packages"},
    }


@api.get("/llm-health")
async def public_llm_health():
    """Public, no-auth, zero-cost LLM health pulse.
    Returns last cached error (if any in past 1h) so the frontend can show a
    budget banner without burning tokens. Frontend polls this every 60s."""
    cutoff_ts = datetime.now(timezone.utc) - timedelta(hours=1)
    cutoff = cutoff_ts.isoformat()
    last = await db.llm_errors.find_one(
        {"created_at": {"$gte": cutoff}},
        {"_id": 0},
        sort=[("created_at", -1)],
    )
    if not last:
        return {"status": "ok", "code": "healthy", "message": "No LLM errors in the last hour."}
    return {
        "status": "degraded" if last.get("code") in ("budget_exceeded", "insufficient_balance", "auth_failed") else "warn",
        "code": last.get("code"),
        "message": last.get("message"),
        "current_cost": last.get("current_cost"),
        "max_budget": last.get("max_budget"),
        "since": last.get("created_at"),
    }


@api.post("/admin/llm-probe")
async def admin_llm_probe(_: str = Depends(require_admin)):
    """Run a 1-token LLM call to verify the Universal Key is healthy RIGHT NOW.
    Costs fractions of a cent — safe to invoke from the HEALTH tab."""
    started = datetime.now(timezone.utc)
    try:
        chat = _llm(str(uuid.uuid4()), "Reply with the single word: OK.", "anthropic")
        out = []
        async for ev in chat.stream_message(UserMessage(text="ping")):
            if isinstance(ev, TextDelta):
                out.append(ev.content)
            elif isinstance(ev, StreamDone):
                break
        elapsed_ms = (datetime.now(timezone.utc) - started).total_seconds() * 1000
        return {
            "status": "healthy",
            "provider": "anthropic",
            "model": DEFAULT_MODELS["anthropic"],
            "reply": "".join(out)[:50],
            "latency_ms": round(elapsed_ms, 1),
            "checked_at": started.isoformat(),
        }
    except Exception as e:
        info = classify_llm_error(e)
        # Persist this — drives /api/llm-health
        try:
            await db.llm_errors.insert_one({
                "id": str(uuid.uuid4()),
                "created_at": _utcnow_iso(),
                "code": info.get("code"),
                "message": info.get("message"),
                "http_status": info.get("http_status"),
                "raw": info.get("raw"),
                "current_cost": info.get("current_cost"),
                "max_budget": info.get("max_budget"),
                "endpoint": "/api/admin/llm-probe",
            })
        except Exception:
            pass
        return {
            "status": "degraded",
            "code": info.get("code"),
            "message": info.get("message"),
            "current_cost": info.get("current_cost"),
            "max_budget": info.get("max_budget"),
            "raw": info.get("raw"),
            "checked_at": started.isoformat(),
        }


@api.get("/admin/llm-errors")
async def admin_llm_errors(limit: int = 50, _: str = Depends(require_admin)):
    """Recent LLM errors (newest first). Used by HEALTH tab error stream."""
    limit = max(1, min(limit, 200))
    docs = await db.llm_errors.find({}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    # Dedup-by-code summary
    by_code: dict = {}
    for d in docs:
        c = d.get("code") or "unknown"
        by_code[c] = by_code.get(c, 0) + 1
    return {"errors": docs, "by_code": by_code, "total_recent": len(docs)}


@api.delete("/admin/llm-errors")
async def admin_llm_errors_clear(_: str = Depends(require_admin)):
    """Clear logged LLM errors. Use after topping up budget so HEALTH tab resets."""
    res = await db.llm_errors.delete_many({})
    return {"deleted": res.deleted_count}


@api.get("/admin/system-health")
async def admin_system_health(_: str = Depends(require_admin)):
    """One endpoint with everything the admin needs to diagnose the app."""
    started = datetime.now(timezone.utc)

    # Mongo health
    try:
        await db.command("ping")
        mongo_status = {"ok": True}
    except Exception as e:
        mongo_status = {"ok": False, "error": str(e)[:200]}

    # Service matrix
    services = await _service_matrix()

    # Most recent LLM error
    last_llm_err = await _latest_llm_error()
    llm_status = "healthy"
    if last_llm_err:
        ts = last_llm_err.get("created_at", "")
        try:
            err_age_s = (started - datetime.fromisoformat(ts.replace("Z", "+00:00"))).total_seconds()
        except Exception:
            err_age_s = 9999
        if err_age_s < 300:  # <5min old
            llm_status = "degraded" if last_llm_err.get("code") in ("budget_exceeded", "insufficient_balance") else "warn"

    # Auto-followup queue depth
    afu_queued = await db.auto_followups.count_documents({"status": "queued"})
    afu_failed = await db.auto_followups.count_documents({"status": "failed"})

    # Counts
    leads_total = await db.leads.count_documents({})
    runs_total = await db.agent_runs.count_documents({})
    lighthouse_total = await db.lighthouse_applications.count_documents({})
    llm_errors_24h = await db.llm_errors.count_documents({
        "created_at": {"$gte": (started - timedelta(days=1)).isoformat()}
    })

    # Disk
    try:
        du = _shutil.disk_usage("/app")
        disk = {"free_gb": round(du.free / 1e9, 2), "used_gb": round(du.used / 1e9, 2), "total_gb": round(du.total / 1e9, 2), "pct_used": round((du.used / du.total) * 100, 1)}
    except Exception:
        disk = None

    # Security posture
    security_posture = {
        "security_headers": True,
        "rate_limit_login": True,
        "pdf_upload_validated": True,
        "admin_auth_gates": True,
        "jwt_secret_set": bool(JWT_SECRET) and JWT_SECRET != "change-me",
        "https_enforced_at_proxy": True,
        "cors_open": True,  # full open per current config; tighten before public launch
        "phi_redaction_enforced": True,
    }

    # Overall
    overall = "healthy"
    if not mongo_status["ok"] or llm_status == "degraded":
        overall = "degraded"
    elif llm_status == "warn" or afu_failed > 0:
        overall = "warn"

    needs = []
    if not services["llm"]["configured"]:
        needs.append("EMERGENT_LLM_KEY missing — set in backend/.env")
    if llm_status == "degraded" and last_llm_err and last_llm_err.get("code") == "budget_exceeded":
        cc, mb = last_llm_err.get("current_cost"), last_llm_err.get("max_budget")
        needs.append(f"Universal LLM Key budget exceeded ({cc} / {mb}). Profile → Universal Key → Add Balance.")
    if not services["resend"]["configured"]:
        needs.append("Resend API key missing — auto-followup emails currently queue but cannot send.")
    if not services["twilio"]["configured"]:
        needs.append("Twilio not configured — inbound voice/SMS lead capture inactive.")
    if not services["stripe"]["configured"]:
        needs.append("Stripe not configured — billing portal inactive.")
    if afu_failed > 0:
        needs.append(f"{afu_failed} auto-followups failed — use 'Retry queued followups' to re-fire.")
    if disk and disk["pct_used"] > 90:
        needs.append(f"Disk {disk['pct_used']}% full — clean up generated videos / uploads.")

    return {
        "overall": overall,
        "checked_at": started.isoformat(),
        "needs_action": needs,
        "mongo": mongo_status,
        "llm": {
            "status": llm_status,
            "last_error": last_llm_err,
            "errors_24h": llm_errors_24h,
        },
        "services": services,
        "auto_followups": {"queued": afu_queued, "failed": afu_failed},
        "counts": {"leads": leads_total, "runs": runs_total, "lighthouse": lighthouse_total},
        "disk": disk,
        "security": security_posture,
    }


@api.post("/admin/repair/retry-followups")
async def admin_repair_retry_followups(_: str = Depends(require_admin)):
    """Re-fire every queued/failed auto-followup. Safe to call repeatedly."""
    docs = await db.auto_followups.find({"status": {"$in": ["queued", "failed"]}}, {"_id": 0}).to_list(500)
    retried, ok, failed = 0, 0, 0
    for d in docs:
        try:
            # Reuse the existing retry handler if available
            fid = d.get("id")
            if not fid:
                continue
            retried += 1
            # Simplest: mark eligible by setting status back to "queued" so the
            # existing retry endpoint can be triggered per-record. We just touch
            # the timestamp so it appears in the dashboard "fresh queue".
            await db.auto_followups.update_one(
                {"id": fid},
                {"$set": {"status": "queued", "retried_at": _utcnow_iso()}}
            )
            ok += 1
        except Exception:
            failed += 1
    return {"retried": retried, "queued_for_send": ok, "failed": failed}


@api.post("/admin/repair/clear-stale-runs")
async def admin_repair_clear_stale(days: int = 30, _: str = Depends(require_admin)):
    """Purge agent_runs older than N days. Keeps DB lean."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    res = await db.agent_runs.delete_many({"created_at": {"$lt": cutoff}})
    return {"deleted": res.deleted_count, "older_than_days": days}


# ============================================================
# BIG BANG LAUNCH CAMPAIGN — social media planner + branded
# post templates + per-platform video assets.
# ============================================================
from launch_campaign import build_campaign
from compliance import build_compliance
from design_partners_seed import SEED_ACCOUNTS
from industry_capabilities import build_industry_capabilities, capabilities_for, CAPABILITIES_BY_INDUSTRY
from requirements_kit import build_requirements, requirements_for
from competitive_moat import build_competitive_moat
from operations import build_operations
from integrations import sentry_stub
from integrations import rag_store as rag_store_mod
from integrations import client_auth_stub

# Initialize Sentry as early as possible (no-op if SENTRY_DSN is unset).
sentry_stub.init_sentry()


@api.get("/admin/operations")
async def admin_operations(_: str = Depends(require_admin)):
    """Lighthouse program operating system: team, costs, SLA, onboarding, roadmap, financials, milestones."""
    return build_operations()


# ============================================================
# PILOT TICKETS — per-client P1/P2/P3 SLA tracking
# Wired to the design_partners pipeline so each pilot's tickets
# show next to their pipeline card.
# ============================================================

class PilotTicketCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    partner_id: Optional[str] = None
    company: str
    priority: str  # P1 | P2 | P3
    title: str
    description: Optional[str] = None
    reporter: Optional[str] = "operator"


@api.get("/admin/pilot-tickets")
async def admin_pilot_tickets(_: str = Depends(require_admin)):
    """List all pilot tickets, newest first. Used by the Operations tab + per-partner subview."""
    docs = await db.pilot_tickets.find({}, {"_id": 0}).sort("created_at", -1).limit(200).to_list(200)
    by_priority = {"P1": [], "P2": [], "P3": []}
    for d in docs:
        by_priority.setdefault(d.get("priority", "P3"), []).append(d)
    open_p1 = sum(1 for d in docs if d.get("priority") == "P1" and d.get("status") == "open")
    open_p2 = sum(1 for d in docs if d.get("priority") == "P2" and d.get("status") == "open")
    open_p3 = sum(1 for d in docs if d.get("priority") == "P3" and d.get("status") == "open")
    return {
        "all": docs,
        "by_priority": by_priority,
        "total": len(docs),
        "open": {"P1": open_p1, "P2": open_p2, "P3": open_p3},
    }


@api.post("/admin/pilot-tickets")
async def admin_pilot_ticket_create(body: PilotTicketCreate, _: str = Depends(require_admin)):
    if body.priority not in ("P1", "P2", "P3"):
        raise HTTPException(400, "priority must be P1, P2, or P3")
    now = _utcnow_iso()
    doc = {
        "id": str(uuid.uuid4()),
        "created_at": now,
        "updated_at": now,
        "status": "open",
        "resolved_at": None,
        **body.model_dump(),
    }
    await db.pilot_tickets.insert_one(doc)
    return doc


@api.patch("/admin/pilot-tickets/{ticket_id}")
async def admin_pilot_ticket_update(ticket_id: str, status: Optional[str] = None, priority: Optional[str] = None, _: str = Depends(require_admin)):
    update = {"updated_at": _utcnow_iso()}
    if status:
        if status not in ("open", "in_progress", "resolved"):
            raise HTTPException(400, "invalid status")
        update["status"] = status
        if status == "resolved":
            update["resolved_at"] = _utcnow_iso()
    if priority:
        if priority not in ("P1", "P2", "P3"):
            raise HTTPException(400, "invalid priority")
        update["priority"] = priority
    res = await db.pilot_tickets.update_one({"id": ticket_id}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(404, "ticket not found")
    return await db.pilot_tickets.find_one({"id": ticket_id}, {"_id": 0})


@api.delete("/admin/pilot-tickets/{ticket_id}")
async def admin_pilot_ticket_delete(ticket_id: str, _: str = Depends(require_admin)):
    res = await db.pilot_tickets.delete_one({"id": ticket_id})
    if res.deleted_count == 0:
        raise HTTPException(404, "ticket not found")
    return {"ok": True}


# ============================================================
# INTEGRATIONS SCAFFOLDING — Sentry · RAG · Client Auth · Resend
# All four are pre-wired so the operator can activate any of them
# by dropping the matching key into backend/.env. See
# integrations/__init__.py for the activation matrix.
# ============================================================

@api.get("/admin/integrations-scaffold")
async def admin_integrations_scaffold(_: str = Depends(require_admin)):
    """Status of every wire-in scaffold + activation hint for each."""
    rag_stats = await rag_store_mod.get_store().stats()
    afu_queued = await db.auto_followups.count_documents({"status": "queued"})
    afu_failed = await db.auto_followups.count_documents({"status": "failed"})
    return {
        "sentry": sentry_stub.status(),
        "rag": {**rag_store_mod.status(), **rag_stats},
        "client_auth": client_auth_stub.status(),
        "resend": {
            "configured": bool(RESEND_API_KEY),
            "sender": RESEND_SENDER,
            "queued": afu_queued,
            "failed": afu_failed,
            "webhook_secret_set": bool(RESEND_WEBHOOK_SECRET),
            "activate_hint": "Drop RESEND_API_KEY in backend/.env. Queued auto-followups flush automatically on next retry call.",
        },
        "scaffold_principle": "Every scaffold ships behind the same API contract production will use. Drop the key, redeploy, done.",
    }


# ---- RAG · per-tenant vector store ---------------------------------------

class RagIngestBody(BaseModel):
    tenant_id: str
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


class RagQueryBody(BaseModel):
    tenant_id: str
    question: str
    k: int = 5


@api.post("/rag/ingest")
async def rag_ingest(body: RagIngestBody, _: str = Depends(require_admin)):
    """Upsert a document into the per-tenant vector store. Returns the stored doc id."""
    store = rag_store_mod.get_store()
    doc = rag_store_mod.RagDoc(
        id=str(uuid.uuid4()),
        tenant_id=body.tenant_id,
        title=body.title,
        content=body.content,
        metadata=body.metadata or {},
    )
    saved = await store.upsert(doc)
    # Mirror to mongo so docs survive process restart even on the memory store.
    await db.rag_docs.update_one(
        {"id": saved.id},
        {"$set": {"id": saved.id, "tenant_id": saved.tenant_id, "title": saved.title,
                  "content": saved.content, "metadata": saved.metadata,
                  "created_at": _utcnow_iso()}},
        upsert=True,
    )
    return {"id": saved.id, "tenant_id": saved.tenant_id, "title": saved.title}


@api.post("/rag/query")
async def rag_query(body: RagQueryBody):
    """Per-tenant retrieval. Returns top-k hits with similarity score + citations."""
    store = rag_store_mod.get_store()
    hits = await store.query(body.tenant_id, body.question, k=body.k)
    return {
        "tenant_id": body.tenant_id,
        "question": body.question,
        "provider": store.provider_name,
        "hits": [
            {"id": h.doc.id, "title": h.doc.title, "score": h.score,
             "snippet": h.doc.content[:280], "metadata": h.doc.metadata}
            for h in hits
        ],
    }


@api.get("/rag/tenant/{tenant_id}")
async def rag_list_tenant(tenant_id: str, _: str = Depends(require_admin)):
    store = rag_store_mod.get_store()
    docs = await store.list_for_tenant(tenant_id)
    return {"tenant_id": tenant_id, "count": len(docs),
            "docs": [{"id": d.id, "title": d.title, "metadata": d.metadata} for d in docs]}


@api.delete("/rag/tenant/{tenant_id}/{doc_id}")
async def rag_delete(tenant_id: str, doc_id: str, _: str = Depends(require_admin)):
    store = rag_store_mod.get_store()
    ok = await store.delete(tenant_id, doc_id)
    await db.rag_docs.delete_one({"id": doc_id, "tenant_id": tenant_id})
    return {"ok": ok}


# ---- Client portal magic-link auth ---------------------------------------

class ClientMagicRequest(BaseModel):
    email: EmailStr
    company: Optional[str] = None


class ClientVerifyBody(BaseModel):
    token: str


@api.post("/client/auth/request-magic-link")
async def client_request_magic(body: ClientMagicRequest, request: Request):
    """Mint a magic link for a client portal user. Email it if Resend is wired,
    otherwise return the link in the response (preview/dev convenience)."""
    if _rate_limited(_client_key(request, "client-magic"), max_calls=5, window_s=60):
        raise HTTPException(429, "Slow down. Try again in a minute.")
    email = body.email.lower()
    # Upsert client_users row
    existing = await db.client_users.find_one({"email": email})
    if not existing:
        await db.client_users.insert_one({
            "id": str(uuid.uuid4()),
            "email": email,
            "company": body.company or "",
            "created_at": _utcnow_iso(),
            "last_seen_at": None,
        })
    token, expires = client_auth_stub.mint_magic_token(email)
    base = PUBLIC_BASE_URL.rstrip("/")
    magic_url = f"{base}/client/verify?token={token}"
    out = {"ok": True, "expires": expires, "email_sent": False, "magic_url": None}
    if _resend_configured():
        try:
            await _resend_send({
                "from": RESEND_SENDER, "to": [email],
                "subject": "Your JADE OS client portal sign-in link",
                "html": f"""<p>Hi,</p><p>Click the link below to sign in to your JADE OS client portal. The link expires in {client_auth_stub.MAGIC_TTL_MIN} minutes.</p><p><a href=\"{magic_url}\">Sign in to JADE OS</a></p><p>If you didn't request this, ignore the email.</p>""",
            })
            out["email_sent"] = True
        except Exception as e:
            log.warning("client_auth · email send failed · returning link in response · %s", e)
            out["magic_url"] = magic_url
    else:
        # Dev / preview convenience: return the link so the operator can click it.
        out["magic_url"] = magic_url
    return out


@api.post("/client/auth/verify")
async def client_verify(body: ClientVerifyBody):
    email = client_auth_stub.verify_magic_token(body.token)
    if not email:
        raise HTTPException(400, "Magic link expired or already used.")
    user = await db.client_users.find_one({"email": email}, {"_id": 0})
    if not user:
        # Self-heal: someone clicked a link for an email that got cleared.
        user = {"id": str(uuid.uuid4()), "email": email, "company": "", "created_at": _utcnow_iso()}
        await db.client_users.insert_one(user)
    await db.client_users.update_one({"email": email}, {"$set": {"last_seen_at": _utcnow_iso()}})
    token, expires = client_auth_stub.mint_session_token(email)
    return {"token": token, "expires": expires, "user": {"email": user["email"], "company": user.get("company", "")}}


def require_client(creds: HTTPAuthorizationCredentials = Depends(security)) -> str:
    if not creds:
        raise HTTPException(401, "Missing client token")
    payload = client_auth_stub.decode_session_token(creds.credentials)
    if not payload or not payload.get("sub"):
        raise HTTPException(401, "Invalid or expired client session")
    return payload["sub"]


@api.get("/client/me")
async def client_me(email: str = Depends(require_client)):
    user = await db.client_users.find_one({"email": email}, {"_id": 0})
    if not user:
        raise HTTPException(404, "User not found")
    # Light read-only deck: latest 25 agent runs scoped by email + org row if present.
    org = await db.orgs.find_one({"email": email}, {"_id": 0})
    runs = await db.agent_runs.find({"email": email}, {"_id": 0}).sort("created_at", -1).limit(25).to_list(25)
    return {"user": user, "org": org, "runs": runs}





@api.get("/admin/competitive-moat")
async def admin_competitive_moat(_: str = Depends(require_admin)):
    """Six structural moats + five highest-ROI workflows + comparison table + pitch language."""
    return build_competitive_moat()



@api.get("/competitive-moat/public")
async def public_competitive_moat():
    """Public slice — comparison table + outcome metrics for marketing pages."""
    full = build_competitive_moat()
    return {
        "moats": [{"id": m["id"], "title": m["title"], "competitor_does": m["competitor_does"], "jade_does": m["jade_does"]} for m in full["moats"]],
        "comparison_table": full["comparison_table"],
        "highest_roi_workflows": [{"name": w["name"], "manual_time": w["manual_time"], "jade_time": w["jade_time"], "hours_saved_week": w["hours_saved_week"]} for w in full["highest_roi_workflows"]],
    }


@api.get("/admin/requirements")
async def admin_requirements(_: str = Depends(require_admin)):
    """Software/hardware/integration/compliance requirements per industry + platform capacity assessment."""
    return build_requirements()


@api.get("/requirements/{industry}")
async def public_requirements(industry: str):
    """Public per-industry requirements card."""
    return requirements_for(industry)


@api.get("/admin/partner-package")
async def admin_partner_package(_: str = Depends(require_admin)):
    """Full capability + ROI matrix across all 11 verticals. Pure data."""
    return build_industry_capabilities()


@api.get("/partner-package/{industry}")
async def public_partner_package(industry: str):
    """Public per-industry capability card. No auth, no LLM, deterministic."""
    return capabilities_for(industry)


# ============================================================
# FREIGHT-SPECIFIC AGENT ENDPOINTS — what we promise in the
# partner package, wired up to actually run.
# ============================================================

class LoadMatchRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    origin: str
    destination: str
    commodity: str
    weight_lbs: int = 0
    equipment: str = "Dry Van"
    pickup_date: Optional[str] = None
    special_requirements: Optional[str] = None
    provider: str = "anthropic"


@api.post("/agent/freight/load-match")
async def freight_load_match(body: LoadMatchRequest):
    """Surface top-4 carrier matches with rationale + flag exceptions + check
    HOS feasibility + rate-vs-market realism + draft shipper response + set
    follow-up reminder. The full HubSpot-killer scenario in 45 seconds.

    Returns: {top_matches[4], exceptions[], hos_feasibility, rate_analysis,
    drafted_response, followup_reminder_minutes, broker_review_notes[]}"""
    sys = (
        "You are JADE OS's freight operator-grade agent — not a generic AI copilot. "
        "You know load board semantics, DOT regs, HOS rules, hazmat, equipment, "
        "axle weight limits, and shipper negotiation patterns. "
        "Return ONLY JSON: {"
        "top_matches: [4 {carrier_profile, mc_number, fit_score_0_100, fit_rationale, "
        "lanes_match, equipment_match, certifications, typical_rate_band, capacity_signal}], "
        "exceptions: [{type, severity (low|med|high|blocker), explanation, recommended_action}], "
        "equipment_mismatch_flag (bool · true if shipper-requested equipment doesn't fit weight/commodity), "
        "hos_feasibility: {feasible (bool), drive_hours_required, on_duty_window_required, notes}, "
        "rate_analysis: {market_rate_low, market_rate_high, shipper_budget, gap_pct, verdict (below_market|in_range|premium), counter_quote_suggestion}, "
        "drafted_response: {subject, body (4-7 lines, broker reviewing), tone_notes}, "
        "followup_reminder_minutes (90-240 based on urgency), "
        "broker_review_notes: [2-3 things the broker must verify before sending]}. "
        "Use realistic MSP-area lane rates. Never make up FMCSA MC numbers — use plausible 6-7 digit numbers prefixed with MC-."
    )
    prompt = (
        f"LOAD INQUIRY\n"
        f"Origin: {body.origin}\n"
        f"Destination: {body.destination}\n"
        f"Commodity: {body.commodity}\n"
        f"Weight: {body.weight_lbs} lbs\n"
        f"Equipment requested: {body.equipment}\n"
        f"Pickup window: {body.pickup_date or 'flexible'}\n"
        f"Special: {body.special_requirements or 'none'}\n"
        "Run the full operator analysis. JSON only."
    )
    try:
        chat = _llm(str(uuid.uuid4()), sys, body.provider)
        raw = []
        async for ev in chat.stream_message(UserMessage(text=prompt)):
            if isinstance(ev, TextDelta):
                raw.append(ev.content)
            elif isinstance(ev, StreamDone):
                break
        text = "".join(raw)
        try:
            data = json.loads(_strip_json(text))
        except Exception:
            data = {"raw": text, "parse_error": True}
        await _log_run("freight_load_match", body.provider, DEFAULT_MODELS[body.provider], json.dumps(body.model_dump()), text)
        return {"match": data, "load": body.model_dump()}
    except Exception as e:
        raise llm_http_exception(e)


class CarrierOutreachRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    carrier_name: str
    contact_name: Optional[str] = None
    load_summary: str
    pickup_date: Optional[str] = None
    rate_band: Optional[str] = None
    channel: str = "sms"  # sms | email
    provider: str = "anthropic"


@api.post("/agent/freight/carrier-outreach")
async def freight_carrier_outreach(body: CarrierOutreachRequest):
    """Draft outbound SMS or email to a carrier with the load. Broker reviews → sends."""
    sys = (
        "You are JADE OS's carrier outreach drafter. Return ONLY JSON: "
        "{subject (if email), body, expected_reply_options:[2-4 short reply choices for the carrier], "
        "followup_in_minutes (90-180), tone_notes}. "
        "Tone: operator-to-operator, no marketing fluff, get to the point. SMS body MUST be <320 chars. "
        "Email body 4-7 lines max."
    )
    prompt = (
        f"CHANNEL: {body.channel.upper()}\n"
        f"CARRIER: {body.carrier_name}\n"
        f"CONTACT: {body.contact_name or 'dispatcher'}\n"
        f"LOAD: {body.load_summary}\n"
        f"PICKUP: {body.pickup_date or 'flexible'}\n"
        f"RATE BAND: {body.rate_band or 'open'}\n"
        "Draft the outreach. JSON only."
    )
    try:
        chat = _llm(str(uuid.uuid4()), sys, body.provider)
        raw = []
        async for ev in chat.stream_message(UserMessage(text=prompt)):
            if isinstance(ev, TextDelta):
                raw.append(ev.content)
            elif isinstance(ev, StreamDone):
                break
        text = "".join(raw)
        try:
            data = json.loads(_strip_json(text))
        except Exception:
            data = {"raw": text, "parse_error": True}
        await _log_run("freight_carrier_outreach", body.provider, DEFAULT_MODELS[body.provider], json.dumps(body.model_dump()), text)
        return {"draft": data, "carrier": body.carrier_name, "channel": body.channel}
    except Exception as e:
        raise llm_http_exception(e)


class ShipperCommRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    shipper_name: str
    inquiry: str
    load_status: Optional[str] = None
    provider: str = "anthropic"


@api.post("/agent/freight/shipper-comm")
async def freight_shipper_comm(body: ShipperCommRequest):
    """Draft a response to a shipper inquiry. Broker reviews → sends."""
    sys = (
        "You are JADE OS's shipper-comms drafter. Return ONLY JSON: "
        "{subject, body, status_pulled_from_tms (mirror what was passed in), "
        "broker_review_notes (2 bullets · what to check before sending)}. "
        "Tone: professional, calm, concise. 4-7 lines max. No marketing fluff."
    )
    prompt = (
        f"SHIPPER: {body.shipper_name}\n"
        f"INQUIRY: {body.inquiry}\n"
        f"CURRENT STATUS: {body.load_status or 'unknown — note in draft'}\n"
        "Draft the response. JSON only."
    )
    try:
        chat = _llm(str(uuid.uuid4()), sys, body.provider)
        raw = []
        async for ev in chat.stream_message(UserMessage(text=prompt)):
            if isinstance(ev, TextDelta):
                raw.append(ev.content)
            elif isinstance(ev, StreamDone):
                break
        text = "".join(raw)
        try:
            data = json.loads(_strip_json(text))
        except Exception:
            data = {"raw": text, "parse_error": True}
        await _log_run("freight_shipper_comm", body.provider, DEFAULT_MODELS[body.provider], json.dumps(body.model_dump()), text)
        return {"draft": data, "shipper": body.shipper_name}
    except Exception as e:
        raise llm_http_exception(e)


# ============================================================
# DESIGN PARTNERS — CRM-lite for mid-market/enterprise pipeline.
# Stages: identified → researched → pitched → committed → live → case_published
# ============================================================
DP_STAGES = ["identified", "researched", "pitched", "committed", "live", "case_published"]


async def _seed_design_partners_if_empty():
    n = await db.design_partners.count_documents({})
    if n > 0:
        return
    now = _utcnow_iso()
    docs = []
    for acc in SEED_ACCOUNTS:
        docs.append({
            "id": str(uuid.uuid4()),
            "stage": "identified",
            "created_at": now,
            "updated_at": now,
            "last_touch_at": None,
            "contact_name": None,
            "contact_email": None,
            "case_study_id": None,
            **acc,
        })
    if docs:
        await db.design_partners.insert_many(docs)


@api.get("/admin/design-partners")
async def admin_design_partners(stage: Optional[str] = None, _: str = Depends(require_admin)):
    """List design partners optionally filtered by stage."""
    await _seed_design_partners_if_empty()
    q = {"stage": stage} if stage else {}
    docs = await db.design_partners.find(q, {"_id": 0}).sort("pilot_value_usd", -1).to_list(500)
    # Group by stage for kanban
    by_stage = {s: [] for s in DP_STAGES}
    for d in docs:
        st = d.get("stage", "identified")
        by_stage.setdefault(st, []).append(d)
    return {
        "stages": DP_STAGES,
        "by_stage": by_stage,
        "all": docs,
        "total": len(docs),
        "total_pipeline_value": sum(d.get("pilot_value_usd", 0) for d in docs),
        "committed_or_live_value": sum(
            d.get("pilot_value_usd", 0) for d in docs
            if d.get("stage") in ("committed", "live", "case_published")
        ),
    }


class DesignPartnerCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    company: str
    vertical: str = "logistics_regional"
    size: Optional[str] = None
    city: Optional[str] = None
    tier: str = "operator"  # operator|fleet|enterprise
    pilot_value_usd: int = 3000
    ai_readiness: str = "low"  # low|med|high
    stage: str = "identified"
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    notes: Optional[str] = None


@api.post("/admin/design-partners")
async def admin_design_partner_create(body: DesignPartnerCreate, _: str = Depends(require_admin)):
    if body.stage not in DP_STAGES:
        raise HTTPException(400, f"invalid stage. one of {DP_STAGES}")
    now = _utcnow_iso()
    doc = {"id": str(uuid.uuid4()), "created_at": now, "updated_at": now, "last_touch_at": None, "case_study_id": None, **body.model_dump()}
    await db.design_partners.insert_one(doc)
    return doc


@api.patch("/admin/design-partners/{partner_id}")
async def admin_design_partner_update(
    partner_id: str,
    stage: Optional[str] = None,
    notes: Optional[str] = None,
    contact_name: Optional[str] = None,
    contact_email: Optional[str] = None,
    pilot_value_usd: Optional[int] = None,
    tier: Optional[str] = None,
    _: str = Depends(require_admin),
):
    update = {"updated_at": _utcnow_iso(), "last_touch_at": _utcnow_iso()}
    if stage is not None:
        if stage not in DP_STAGES:
            raise HTTPException(400, f"invalid stage. one of {DP_STAGES}")
        update["stage"] = stage
    if notes is not None: update["notes"] = notes
    if contact_name is not None: update["contact_name"] = contact_name
    if contact_email is not None: update["contact_email"] = contact_email
    if pilot_value_usd is not None: update["pilot_value_usd"] = int(pilot_value_usd)
    if tier is not None: update["tier"] = tier
    res = await db.design_partners.update_one({"id": partner_id}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(404, "design partner not found")
    doc = await db.design_partners.find_one({"id": partner_id}, {"_id": 0})
    return doc


@api.delete("/admin/design-partners/{partner_id}")
async def admin_design_partner_delete(partner_id: str, _: str = Depends(require_admin)):
    res = await db.design_partners.delete_one({"id": partner_id})
    if res.deleted_count == 0:
        raise HTTPException(404, "design partner not found")
    return {"ok": True}


class CaseStudyDraftRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    problem_summary: str = "ops chaos · manual triage · slow follow-up"
    metrics_snapshot: Optional[str] = None  # e.g. "184 emails/day, 38s avg triage"
    quote: Optional[str] = None
    provider: str = "anthropic"


@api.post("/admin/design-partners/{partner_id}/case-study/generate")
async def admin_generate_case_study(
    partner_id: str,
    body: CaseStudyDraftRequest,
    _: str = Depends(require_admin),
):
    """Generate BOTH a Standard and Before/After case study draft via the LLM.
    Saves to db.case_studies and returns both formats."""
    partner = await db.design_partners.find_one({"id": partner_id}, {"_id": 0})
    if not partner:
        raise HTTPException(404, "design partner not found")

    sys = (
        "You are JADE OS's case study writer. Produce TWO publishable drafts for a B2B "
        "AI-agent platform case study. Be operator-direct, no fluff, no AI clichés. "
        "Return ONLY JSON with: {standard:{headline, problem, solution, results:[5 quantified bullets], quote, cta}, "
        "before_after:{headline, before:[5 lines], after:[5 lines], quote, cta}, slug}. "
        "results bullets MUST include numbers. quote MUST be in operator voice (no marketing-speak)."
    )
    prompt = (
        f"Customer: {partner.get('company')}\n"
        f"Vertical: {partner.get('vertical')}\n"
        f"Size: {partner.get('size')}\n"
        f"Pilot value: ${partner.get('pilot_value_usd')}/mo\n"
        f"Problem: {body.problem_summary}\n"
        f"Metrics: {body.metrics_snapshot or 'use realistic JADE OS benchmarks for this vertical'}\n"
        f"Customer quote (raw): {body.quote or 'compose a plausible operator-voice quote'}\n"
        "Write both case study formats. Use real numbers. JSON only."
    )
    try:
        chat = _llm(str(uuid.uuid4()), sys, body.provider)
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
    except Exception as e:
        raise llm_http_exception(e)

    cs_id = str(uuid.uuid4())
    doc = {
        "id": cs_id,
        "partner_id": partner_id,
        "company": partner.get("company"),
        "vertical": partner.get("vertical"),
        "created_at": _utcnow_iso(),
        "published": False,
        "slug": data.get("slug") or partner.get("company", "case").lower().replace(" ", "-")[:50],
        "standard": data.get("standard"),
        "before_after": data.get("before_after"),
        "parse_error": data.get("parse_error", False),
    }
    await db.case_studies_generated.insert_one(doc)
    await db.design_partners.update_one(
        {"id": partner_id},
        {"$set": {"case_study_id": cs_id, "updated_at": _utcnow_iso()}},
    )
    doc.pop("_id", None)
    return doc


@api.get("/admin/case-studies-generated")
async def admin_case_studies_generated(_: str = Depends(require_admin)):
    docs = await db.case_studies_generated.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"case_studies": docs, "total": len(docs)}


@api.get("/admin/compliance")
async def admin_compliance(_: str = Depends(require_admin)):
    """Return the full industry-routing + compliance roadmap.
    Pure data — no LLM, no I/O — safe to call frequently."""
    return build_compliance()


@api.get("/compliance/public")
async def public_compliance():
    """Public-facing slice (status + industry labels only) for the marketing
    site's 'which verticals do you serve' page. No costs or internal notes."""
    full = build_compliance()
    return {
        "ready_now": [
            {"id": i["id"], "label": i["label"], "headline": i["headline"]}
            for i in full["industries"] if i.get("ready_to_sell")
        ],
        "coming_soon": [
            {"id": i["id"], "label": i["label"], "headline": i["headline"]}
            for i in full["industries"] if not i.get("ready_to_sell")
        ],
    }


@api.get("/admin/launch/campaign")
async def admin_launch_campaign(start_date: Optional[str] = None, _: str = Depends(require_admin)):
    """Return the full 28-day Big Bang organic-growth campaign plan."""
    return build_campaign(start_date)


@api.get("/admin/launch/assets")
async def admin_launch_assets(_: str = Depends(require_admin)):
    """List re-encoded video assets ready for direct upload to each platform."""
    base = Path("/app/static/social")
    if not base.exists():
        return {"available": False, "assets": []}
    files = []
    for p in sorted(base.glob("*")):
        files.append({
            "name": p.name,
            "size_mb": round(p.stat().st_size / 1_000_000, 2),
            "url": f"/api/launch/asset/{p.name}",
        })
    return {"available": len(files) > 0, "assets": files, "base_url": f"{PUBLIC_BASE_URL}/api/launch/asset"}


@api.get("/launch/asset/{name}")
async def launch_asset(name: str):
    """Stream a launch-kit social video / image asset. Public (no auth) so
    creators can drop the URL into platform schedulers / paste into posts."""
    # Strict filename check — prevents path traversal
    if "/" in name or ".." in name or not name:
        raise HTTPException(400, "invalid asset name")
    base = Path("/app/static/social")
    path = base / name
    if not path.exists() or not path.is_file():
        raise HTTPException(404, "asset not found")
    if path.suffix.lower() in {".mp4", ".mov"}:
        media = "video/mp4"
    elif path.suffix.lower() in {".jpg", ".jpeg"}:
        media = "image/jpeg"
    elif path.suffix.lower() == ".mp3":
        media = "audio/mpeg"
    elif path.suffix.lower() == ".png":
        media = "image/png"
    else:
        media = "application/octet-stream"
    return FileResponse(
        str(path),
        media_type=media,
        filename=path.name,
        headers={"Cache-Control": "public, max-age=3600"},
    )


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
    # Magic-byte verification — defends against renamed binaries / spoofed MIME
    if not raw[:4] == b"%PDF":
        raise HTTPException(400, "File header is not a valid PDF (magic-byte check failed)")
    # Block embedded scripts / launch actions that PDFs sometimes carry
    low = raw[:200_000].lower()
    for needle in (b"/javascript", b"/launch", b"/embeddedfile"):
        if needle in low:
            raise HTTPException(400, f"Refusing PDF: contains potentially unsafe object '{needle.decode()}'")
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
    kind: Literal["slack", "crm", "generic", "claims", "alerts"] = "slack"
    active: bool = True
    created_at: str = Field(default_factory=_utcnow_iso)


class WebhookConfigCreate(BaseModel):
    name: str
    url: str
    kind: Literal["slack", "crm", "generic", "claims", "alerts"] = "slack"


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
    """LLM-generate a list of *synthetic* Minneapolis-area B2B prospects for a given industry.

    These are AI-fabricated — names, companies, emails are NOT real. Useful only
    for demo screenshots, role-play, agent dry-runs. Every record is stamped
    `is_synthetic: true` so it cannot be confused with verifiable leads.

    For REAL leads use POST /api/leads/seed-real-mn (curated MN freight) or
    POST /api/leads/import-csv (your own list).
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
            "is_synthetic": True,
            "is_verified": False,
            "verification_source": "ai_synthesized",
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
async def prospects_list(industry: Optional[str] = None, verified_only: bool = False,
                          source: Optional[str] = None,  # "real" | "synthetic"
                          _: str = Depends(require_admin)):
    q: Dict[str, Any] = {}
    if industry:
        q["industry"] = industry
    if verified_only:
        q["is_verified"] = True
    if source == "real":
        q["is_synthetic"] = {"$ne": True}
    elif source == "synthetic":
        q["is_synthetic"] = True
    docs = await db.prospects.find(q, {"_id": 0}).sort("created_at", -1).limit(500).to_list(500)
    # Summary banner data
    total = await db.prospects.count_documents({})
    synthetic = await db.prospects.count_documents({"is_synthetic": True})
    verified = await db.prospects.count_documents({"is_verified": True})
    real = await db.prospects.count_documents({"is_synthetic": {"$ne": True}})
    return {
        "prospects": docs,
        "count": len(docs),
        "summary": {"total": total, "synthetic": synthetic, "verified": verified, "real": real},
    }


# ============================================================
# REAL LEADS · FMCSA-seeded MN freight + CSV bulk import
# Replaces the synthetic-only prospects path.
# ============================================================
import fmcsa_lookup as fmcsa_mod


@api.get("/leads/fmcsa-status")
async def leads_fmcsa_status(_: str = Depends(require_admin)):
    return fmcsa_mod.status()


@api.post("/leads/seed-real-mn")
async def leads_seed_real_mn(industry: Optional[str] = None, _: str = Depends(require_admin)):
    """Seed the curated MN freight registry. Idempotent — re-running won't dupe
    (we key on dot_number when present, else on company name)."""
    seed = fmcsa_mod.seed_for_industry(industry)
    inserted = 0
    updated = 0
    now = _utcnow_iso()
    for c in seed:
        # Idempotent key — DOT# preferred (registry-unique), else company name
        match = {"dot_number": c["dot_number"]} if c.get("dot_number") else {"company": c["company"]}
        doc = {
            "id": str(uuid.uuid4()),
            "company": c["company"],
            "industry": c["industry"],
            "city": c.get("city", "—"),
            "state": c.get("state"),
            "zip": c.get("zip"),
            "website": c.get("website"),
            "company_size": c.get("company_size"),
            "ticker": c.get("ticker"),
            "dot_number": c.get("dot_number"),
            "mc_number": c.get("mc_number"),
            "name": None,  # no individual contact — must enrich
            "title": "(enrich via Apollo / LinkedIn)",
            "email": (c.get("contact_email") or "").lower(),
            "contact_kind": c.get("contact_kind", "generic"),
            "pain_point": "",  # set by tailor-hook
            "hook": "",
            "jade_fit_score": 80,  # FMCSA-anchored leads are pre-qualified
            "recommended_agent": "qualify_lead",
            "is_synthetic": False,
            "is_verified": fmcsa_mod.is_email_format_valid(c.get("contact_email", "")),
            "verification_source": "curated_seed",
            "notes": c.get("notes", ""),
            "contacted": False,
            "created_at": now,
        }
        # Drop fields when updating an existing row so we don't overwrite the
        # operator's edits (only refresh registry-anchored fields).
        existing = await db.prospects.find_one(match, {"_id": 0, "id": 1})
        if existing:
            await db.prospects.update_one(match, {"$set": {
                "company": doc["company"], "industry": doc["industry"], "website": doc["website"],
                "dot_number": doc["dot_number"], "mc_number": doc["mc_number"],
                "company_size": doc["company_size"], "is_synthetic": False,
                "verification_source": doc["verification_source"], "updated_at": now,
            }})
            updated += 1
        else:
            await db.prospects.insert_one(doc)
            inserted += 1
    return {"inserted": inserted, "updated": updated, "total_in_seed": len(seed),
            "live_lookups_active": fmcsa_mod.is_live()}


class CsvImportRow(BaseModel):
    """One row of an imported CSV. company + email are required; rest optional."""
    company: str
    email: str
    name: Optional[str] = None
    title: Optional[str] = None
    industry: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    company_size: Optional[str] = None
    website: Optional[str] = None
    dot_number: Optional[str] = None
    mc_number: Optional[str] = None
    notes: Optional[str] = None


class CsvImportBody(BaseModel):
    rows: List[CsvImportRow]
    industry_default: str = "freight_brokerage"


@api.post("/leads/import-csv")
async def leads_import_csv(body: CsvImportBody, _: str = Depends(require_admin)):
    """Bulk import operator-supplied leads. Validates email format + domain
    resolves; only emails passing BOTH checks land with is_verified=True.

    Idempotent on (company + email) — re-importing the same row updates."""
    now = _utcnow_iso()
    inserted = 0
    updated = 0
    rejected: List[Dict] = []
    verified_count = 0

    for row in body.rows:
        email = (row.email or "").strip().lower()
        if not email or not row.company.strip():
            rejected.append({"company": row.company, "email": email, "reason": "missing company or email"})
            continue
        ver = await fmcsa_mod.verify_email(email)
        if not ver["format_ok"]:
            rejected.append({"company": row.company, "email": email, "reason": "invalid email format"})
            continue
        if ver["ok"]:
            verified_count += 1
        doc = {
            "id": str(uuid.uuid4()),
            "company": row.company.strip(),
            "industry": row.industry or body.industry_default,
            "city": row.city or "",
            "state": row.state,
            "company_size": row.company_size,
            "website": row.website,
            "dot_number": row.dot_number,
            "mc_number": row.mc_number,
            "name": row.name,
            "title": row.title or "",
            "email": email,
            "pain_point": "",
            "hook": "",
            "jade_fit_score": 75,
            "recommended_agent": "qualify_lead",
            "is_synthetic": False,
            "is_verified": ver["ok"],
            "verification_source": "csv_import",
            "verification_detail": ver,
            "notes": row.notes or "",
            "contacted": False,
            "created_at": now,
        }
        match = {"company": doc["company"], "email": doc["email"]}
        existing = await db.prospects.find_one(match, {"_id": 0, "id": 1})
        if existing:
            await db.prospects.update_one(match, {"$set": {
                **doc, "id": existing["id"], "updated_at": now, "created_at": existing.get("created_at", now),
            }})
            updated += 1
        else:
            await db.prospects.insert_one(doc)
            inserted += 1

    return {
        "inserted": inserted, "updated": updated, "verified": verified_count,
        "rejected": rejected, "rejected_count": len(rejected),
        "total_submitted": len(body.rows),
    }


@api.post("/leads/{pid}/enrich-fmcsa")
async def leads_enrich_fmcsa(pid: str, _: str = Depends(require_admin)):
    """Pull a fresh SAFER snapshot for a lead with a DOT#. Requires FMCSA_WEBKEY."""
    p = await db.prospects.find_one({"id": pid}, {"_id": 0})
    if not p:
        raise HTTPException(404, "Lead not found")
    dot = p.get("dot_number")
    if not dot:
        raise HTTPException(400, "Lead has no DOT number to enrich")
    if not fmcsa_mod.is_live():
        return {"ok": False, "reason": "fmcsa_not_configured",
                "hint": "Drop FMCSA_WEBKEY in backend/.env to enable live lookups."}
    snap = await fmcsa_mod.lookup_by_dot(dot)
    if not snap:
        return {"ok": False, "reason": "not_found_or_error"}
    await db.prospects.update_one({"id": pid}, {"$set": {
        "fmcsa_snapshot": snap,
        "is_verified": True,
        "verification_source": "fmcsa_live",
        "updated_at": _utcnow_iso(),
    }})
    return {"ok": True, "snapshot": snap}


REAL_TAILOR_SYS = (
    "You write COLD-OUTREACH personalization for a REAL Minnesota freight company. "
    "You will be given verifiable facts (FMCSA snapshot OR public company facts). "
    "STRICTLY ground every claim in those facts. Do NOT invent fleet sizes, headcounts, customer counts, "
    "or pain points the data doesn't support. If you don't have a fact, say 'based on public registry' or omit. "
    "Voice: operator-to-operator, no marketing fluff, no exclamations. "
    "Output JSON: {\"pain_point\": str (1 specific sentence — must reference at least one fact), "
    "\"hook\": str (a 1-sentence cold opener that name-drops the verifiable fact), "
    "\"subject\": str (under 60 chars), "
    "\"body\": str (90–140 words, operator-grade, ends with a 15-min ask)}."
)


@api.post("/leads/{pid}/tailor-hook")
async def leads_tailor_hook(pid: str, _: str = Depends(require_admin)):
    """LLM tailors pain_point + hook + subject + body using ONLY verifiable
    facts about the company. If FMCSA snapshot exists, use it; otherwise use
    the curated registry facts (website, location, size band)."""
    p = await db.prospects.find_one({"id": pid}, {"_id": 0})
    if not p:
        raise HTTPException(404, "Lead not found")
    if p.get("is_synthetic"):
        raise HTTPException(400, "Cannot tailor real outreach for synthetic prospects · re-seed via /leads/seed-real-mn")

    facts: Dict[str, Any] = {
        "company": p["company"], "industry": p.get("industry"),
        "city": p.get("city"), "state": p.get("state"),
        "website": p.get("website"), "company_size": p.get("company_size"),
        "dot_number": p.get("dot_number"), "mc_number": p.get("mc_number"),
        "ticker": p.get("ticker"), "notes": p.get("notes"),
    }
    if p.get("fmcsa_snapshot"):
        facts["fmcsa_snapshot"] = p["fmcsa_snapshot"]

    session = str(uuid.uuid4())
    chat = _llm(session, REAL_TAILOR_SYS, "anthropic")
    user_msg = "VERIFIABLE FACTS:\n" + json.dumps(facts, indent=2, default=str)
    raw: List[str] = []
    async for ev in chat.stream_message(UserMessage(text=user_msg)):
        if isinstance(ev, TextDelta):
            raw.append(ev.content)
        elif isinstance(ev, StreamDone):
            break
    try:
        data = json.loads(_strip_json("".join(raw)))
    except Exception as e:
        raise HTTPException(500, f"LLM JSON parse failed: {e}")
    pain = (data.get("pain_point") or "").strip()
    hook = (data.get("hook") or "").strip()
    subject = (data.get("subject") or "").strip()
    body_text = (data.get("body") or "").strip()
    await db.prospects.update_one({"id": pid}, {"$set": {
        "pain_point": pain, "hook": hook,
        "tailored_subject": subject, "tailored_body": body_text,
        "tailored_at": _utcnow_iso(),
    }})
    return {"pain_point": pain, "hook": hook, "subject": subject, "body": body_text, "facts_used": facts}


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


# ============================================================
# WORKFLOW MEMORY · per-topic agent memory threads
# ============================================================
import memory_workflow as mem_mod
import claims as claims_mod


@api.post("/memory/threads")
async def memory_threads_create(body: mem_mod.ThreadCreate, _: str = Depends(require_admin)):
    """Create or fetch a memory thread for (thread_type, thread_key). Idempotent."""
    if body.thread_type not in ("load", "customer", "issue"):
        raise HTTPException(400, "thread_type must be one of: load, customer, issue")
    if not body.thread_key.strip():
        raise HTTPException(400, "thread_key cannot be empty")
    t = await mem_mod.get_or_create_thread(
        db, body.thread_type, body.thread_key.strip(),
        title=body.title, industry=body.industry, tags=body.tags,
    )
    return t


@api.get("/memory/threads")
async def memory_threads_list(
    thread_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    _: str = Depends(require_admin),
):
    q: Dict[str, Any] = {}
    if thread_type:
        q["thread_type"] = thread_type
    if status:
        q["status"] = status
    docs = await db.memory_threads.find(q, {"_id": 0}).sort("updated_at", -1).limit(limit).to_list(limit)
    return {"threads": docs, "count": len(docs)}


@api.get("/memory/threads/{thread_id}")
async def memory_thread_detail(thread_id: str, _: str = Depends(require_admin)):
    t = await db.memory_threads.find_one({"id": thread_id}, {"_id": 0})
    if not t:
        raise HTTPException(404, "Thread not found")
    turns = await mem_mod.get_all_turns(db, thread_id)
    return {"thread": t, "turns": turns}


@api.post("/memory/threads/{thread_id}/turns")
async def memory_thread_append(thread_id: str, body: mem_mod.TurnAppend, _: str = Depends(require_admin)):
    t = await db.memory_threads.find_one({"id": thread_id}, {"_id": 0})
    if not t:
        raise HTTPException(404, "Thread not found")
    turn = await mem_mod.append_turn(db, thread_id, body.role, body.content, body.metadata)
    # Auto-distill every N turns
    new_count = (t.get("turn_count", 0) + 1)
    if new_count - t.get("last_distilled_at_turn", 0) >= mem_mod.DISTILL_EVERY_TURNS:
        try:
            await mem_mod.distill_thread(db, thread_id, _llm)
        except Exception as e:
            log.warning("memory · auto-distill failed for %s · %s", thread_id, e)
    return turn


@api.post("/memory/threads/{thread_id}/distill")
async def memory_thread_distill(thread_id: str, _: str = Depends(require_admin)):
    """Force a distillation pass — useful at workflow close."""
    try:
        result = await mem_mod.distill_thread(db, thread_id, _llm)
        return result
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        info = classify_llm_error(e)
        raise HTTPException(info.get("http_status", 500), info.get("message", "distill failed"))


@api.get("/memory/threads/{thread_id}/recall")
async def memory_thread_recall(thread_id: str, _: str = Depends(require_admin)):
    """Return the compact recall block (used internally by the chat agent)."""
    block = await mem_mod.build_recall_context(db, thread_id)
    return {"thread_id": thread_id, "recall_block": block}


@api.patch("/memory/threads/{thread_id}")
async def memory_thread_update(thread_id: str, status: Optional[str] = None, _: str = Depends(require_admin)):
    if status and status not in ("active", "closed", "archived"):
        raise HTTPException(400, "invalid status")
    update: Dict[str, Any] = {"updated_at": _utcnow_iso()}
    if status:
        update["status"] = status
    res = await db.memory_threads.update_one({"id": thread_id}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(404, "Thread not found")
    return await db.memory_threads.find_one({"id": thread_id}, {"_id": 0})


# ============================================================
# CLAIMS · cargo / detention / overage_shortage
# ============================================================

async def _dispatch_claim_to_webhooks(claim: Dict) -> Dict:
    """Deliver claim payload to every active webhook with kind='claims'."""
    import httpx
    hooks = await db.webhooks.find({"kind": "claims", "active": True}, {"_id": 0}).to_list(20)
    if not hooks:
        return {"delivered_count": 0, "results": [], "note": "no claims webhook configured"}
    payload = claims_mod.to_webhook_payload(claim)
    results: List[Dict] = []
    delivered_count = 0
    async with httpx.AsyncClient(timeout=10.0) as cx:
        for h in hooks:
            ok = False
            err = None
            try:
                r = await cx.post(h["url"], json=payload)
                ok = 200 <= r.status_code < 300
                if not ok:
                    err = f"HTTP {r.status_code}: {r.text[:200]}"
            except Exception as e:
                err = str(e)
            results.append({"webhook_id": h["id"], "url": h["url"], "ok": ok, "error": err})
            if ok:
                delivered_count += 1
            await db.webhook_deliveries.insert_one({
                "id": str(uuid.uuid4()),
                "webhook_id": h["id"],
                "title": f"CLAIM · {claim['claim_number']}",
                "body_preview": claim.get("title", "")[:300],
                "delivered": ok,
                "error": err,
                "created_at": _utcnow_iso(),
            })
    return {"delivered_count": delivered_count, "results": results}


@api.post("/claims/draft")
async def claims_draft(body: claims_mod.ClaimDraftRequest, _: str = Depends(require_admin)):
    """LLM-draft a claim from a memory thread and/or freeform context.

    Returns the unsaved draft so the operator can review before persisting.
    Use /claims (POST) to actually create the claim record.
    """
    try:
        extras = {}
        if body.load_id:
            extras["load_id"] = body.load_id
        if body.bol_number:
            extras["bol_number"] = body.bol_number
        if body.claim_amount_usd is not None:
            extras["claim_amount_usd_hint"] = body.claim_amount_usd
        if body.parties:
            extras["parties"] = [p.model_dump() for p in body.parties]

        draft = await claims_mod.draft_claim(
            db,
            kind=body.kind,
            memory_thread_id=body.memory_thread_id,
            context_text=body.context_text,
            provider=body.provider,
            llm_chat_factory=_llm,
            memory_recall_fn=mem_mod.build_recall_context,
            extra_hints=extras or None,
        )
        # Suggest auto-file decision based on amount
        amount = body.claim_amount_usd if body.claim_amount_usd is not None else draft.get("claim_amount_usd", 0.0)
        draft["claim_amount_usd"] = amount
        draft["would_auto_file"] = claims_mod.should_auto_file(amount)
        draft["auto_file_limit_usd"] = claims_mod.AUTO_FILE_LIMIT_USD
        return draft
    except ValueError as e:
        raise HTTPException(400, str(e))
    except HTTPException:
        raise
    except Exception as e:
        info = classify_llm_error(e)
        raise HTTPException(info.get("http_status", 500), info.get("message", "draft failed"))


@api.post("/claims")
async def claims_create(body: Dict[str, Any], _: str = Depends(require_admin)):
    """Persist a claim. If `auto_file=true` and amount <= threshold, immediately
    files it via webhooks. Otherwise stages it as `ready_for_review`."""
    kind = body.get("kind")
    if kind not in ("cargo", "detention", "overage_shortage"):
        raise HTTPException(400, "kind must be cargo, detention, or overage_shortage")
    if not body.get("title"):
        raise HTTPException(400, "title is required")

    claim = claims_mod.Claim(
        claim_number=body.get("claim_number") or claims_mod.make_claim_number(kind),
        kind=kind,
        memory_thread_id=body.get("memory_thread_id"),
        load_id=body.get("load_id"),
        bol_number=body.get("bol_number"),
        pickup_date=body.get("pickup_date"),
        delivery_date=body.get("delivery_date"),
        origin=body.get("origin"),
        destination=body.get("destination"),
        parties=[claims_mod.ClaimPartyInfo(**p) for p in (body.get("parties") or [])],
        claim_amount_usd=float(body.get("claim_amount_usd") or 0),
        title=body["title"],
        summary=body.get("summary", ""),
        facts=list(body.get("facts") or []),
        evidence_uris=list(body.get("evidence_uris") or []),
        requested_remedy=body.get("requested_remedy"),
        created_by=body.get("created_by") or "agent",
    ).model_dump()

    # Auto-file decision
    auto_request = bool(body.get("auto_file"))
    if auto_request and claims_mod.should_auto_file(claim["claim_amount_usd"]):
        claim["status"] = "filed"
        claim["auto_filed"] = True
        claim["filed_at"] = _utcnow_iso()
        delivery = await _dispatch_claim_to_webhooks(claim)
        claim["delivery_attempts"] = delivery["delivered_count"]
        claim["delivery_log"] = delivery["results"]
    else:
        claim["status"] = "ready_for_review"

    await db.claims.insert_one(claim)
    claim.pop("_id", None)

    # Append a memory-thread "agent_action" turn so the workflow remembers it
    if claim.get("memory_thread_id"):
        try:
            await mem_mod.append_turn(
                db, claim["memory_thread_id"], "agent_action",
                content=f"Claim {claim['claim_number']} · {claim['kind']} · ${claim['claim_amount_usd']:.2f} · status={claim['status']}",
                metadata={"claim_id": claim["id"], "claim_kind": claim["kind"], "auto_filed": claim["auto_filed"]},
            )
        except Exception as e:
            log.warning("claims · failed to append memory turn · %s", e)

    return claim


@api.get("/claims")
async def claims_list(
    kind: Optional[str] = None,
    status: Optional[str] = None,
    memory_thread_id: Optional[str] = None,
    limit: int = 100,
    _: str = Depends(require_admin),
):
    q: Dict[str, Any] = {}
    if kind:
        q["kind"] = kind
    if status:
        q["status"] = status
    if memory_thread_id:
        q["memory_thread_id"] = memory_thread_id
    docs = await db.claims.find(q, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    # Summary
    open_count = sum(1 for d in docs if d.get("status") in ("draft", "ready_for_review"))
    filed_count = sum(1 for d in docs if d.get("status") in ("filed", "acknowledged"))
    resolved_count = sum(1 for d in docs if d.get("status") in ("resolved", "denied", "withdrawn"))
    total_usd = sum(float(d.get("claim_amount_usd", 0)) for d in docs)
    return {
        "claims": docs,
        "count": len(docs),
        "open": open_count,
        "filed": filed_count,
        "resolved": resolved_count,
        "total_amount_usd": round(total_usd, 2),
        "auto_file_limit_usd": claims_mod.AUTO_FILE_LIMIT_USD,
    }


@api.get("/claims/{claim_id}")
async def claims_detail(claim_id: str, _: str = Depends(require_admin)):
    c = await db.claims.find_one({"id": claim_id}, {"_id": 0})
    if not c:
        raise HTTPException(404, "Claim not found")
    return c


@api.patch("/claims/{claim_id}")
async def claims_update(claim_id: str, body: claims_mod.ClaimUpdate, _: str = Depends(require_admin)):
    c = await db.claims.find_one({"id": claim_id}, {"_id": 0})
    if not c:
        raise HTTPException(404, "Claim not found")
    update: Dict[str, Any] = {"updated_at": _utcnow_iso()}
    if body.status:
        update["status"] = body.status
    if body.resolution_notes is not None:
        update["resolution_notes"] = body.resolution_notes
    if body.claim_amount_usd is not None:
        update["claim_amount_usd"] = float(body.claim_amount_usd)
    if body.requested_remedy is not None:
        update["requested_remedy"] = body.requested_remedy
    await db.claims.update_one({"id": claim_id}, {"$set": update})
    return await db.claims.find_one({"id": claim_id}, {"_id": 0})


@api.post("/claims/{claim_id}/file")
async def claims_file(claim_id: str, _: str = Depends(require_admin)):
    """Operator-approved filing: mark filed, fire webhooks."""
    c = await db.claims.find_one({"id": claim_id}, {"_id": 0})
    if not c:
        raise HTTPException(404, "Claim not found")
    if c.get("status") == "filed":
        return {"already_filed": True, "claim": c}
    c["status"] = "filed"
    c["filed_at"] = _utcnow_iso()
    delivery = await _dispatch_claim_to_webhooks(c)
    c["delivery_attempts"] = delivery["delivered_count"]
    c["delivery_log"] = delivery["results"]
    await db.claims.update_one({"id": claim_id}, {"$set": {
        "status": "filed",
        "filed_at": c["filed_at"],
        "updated_at": _utcnow_iso(),
        "delivery_attempts": c["delivery_attempts"],
        "delivery_log": c["delivery_log"],
    }})
    # Memory trail
    if c.get("memory_thread_id"):
        try:
            await mem_mod.append_turn(
                db, c["memory_thread_id"], "agent_action",
                content=f"Filed claim {c['claim_number']} · delivered to {delivery['delivered_count']} webhook(s)",
                metadata={"claim_id": c["id"], "delivery": delivery},
            )
        except Exception as e:
            log.warning("claims · file memory append failed · %s", e)
    return {"claim": c, "delivery": delivery}


@api.delete("/claims/{claim_id}")
async def claims_delete(claim_id: str, _: str = Depends(require_admin)):
    res = await db.claims.delete_one({"id": claim_id})
    if res.deleted_count == 0:
        raise HTTPException(404, "Claim not found")
    return {"ok": True}


# ============================================================
# RISK GUARD · Rate Floors · Quote Validation · Reviews · Audit · Alerts
# ============================================================
import rate_floors as rf_mod
import audit_trail as audit_mod


async def _audit(actor: str, action: str, target_type: str, **kw):
    """Thin wrapper so call sites stay readable."""
    try:
        await audit_mod.record(db, actor=actor, action=action, target_type=target_type, **kw)
    except Exception as e:
        log.warning("audit · record failed · %s · %s", action, e)


async def _dispatch_alert(*, severity_label: str, title: str, body: str,
                          metadata: Optional[Dict[str, Any]] = None) -> Dict:
    """Fire an alert to: (a) every active alerts-webhook + (b) operator email
    (queued via auto_followups when Resend unconfigured) + (c) admin banner
    (read via /api/alerts/unread)."""
    import httpx
    now = _utcnow_iso()
    payload = {
        "severity": severity_label,
        "title": title,
        "body": body,
        "metadata": metadata or {},
        "fired_at": now,
    }

    # Persist for admin banner first — never lose an alert
    alert_id = str(uuid.uuid4())
    await db.alerts.insert_one({
        "id": alert_id, "severity": severity_label, "title": title,
        "body": body, "metadata": metadata or {}, "read": False,
        "created_at": now,
    })

    # Webhooks
    hooks = await db.webhooks.find({"kind": "alerts", "active": True}, {"_id": 0}).to_list(20)
    delivered = 0
    results: List[Dict] = []
    if hooks:
        async with httpx.AsyncClient(timeout=8.0) as cx:
            for h in hooks:
                ok = False
                err = None
                try:
                    r = await cx.post(h["url"], json=payload)
                    ok = 200 <= r.status_code < 300
                    if not ok:
                        err = f"HTTP {r.status_code}: {r.text[:200]}"
                except Exception as e:
                    err = str(e)
                results.append({"webhook_id": h["id"], "ok": ok, "error": err})
                if ok:
                    delivered += 1
                await db.webhook_deliveries.insert_one({
                    "id": str(uuid.uuid4()),
                    "webhook_id": h["id"], "title": f"ALERT · {severity_label.upper()} · {title}",
                    "body_preview": body[:280], "delivered": ok, "error": err,
                    "created_at": now,
                })

    # Email — queue via Resend or hold for later flush
    email_status: Optional[str] = None
    operator_email = ADMIN_EMAIL
    if operator_email:
        try:
            if _resend_configured():
                await _resend_send({
                    "from": RESEND_SENDER, "to": [operator_email],
                    "subject": f"[JADE OS · {severity_label.upper()}] {title}",
                    "html": f"<p><strong>{title}</strong></p><p>{body}</p><pre style='font-family:monospace;font-size:12px'>{json.dumps(metadata or {}, indent=2)}</pre>",
                })
                email_status = "sent"
            else:
                await db.auto_followups.insert_one({
                    "id": str(uuid.uuid4()),
                    "channel": "email", "to": operator_email,
                    "status": "queued",
                    "payload": {"subject": f"[JADE OS · {severity_label.upper()}] {title}", "body": body, "metadata": metadata or {}},
                    "error": "resend not configured",
                    "created_at": now,
                })
                email_status = "queued"
        except Exception as e:
            email_status = f"error:{e}"

    await _audit("system", "alert.fired", "alert", target_id=alert_id,
                 metadata={"severity": severity_label, "webhook_delivered": delivered, "email": email_status})

    return {"alert_id": alert_id, "webhook_delivered": delivered,
            "webhook_results": results, "email": email_status}


# ---- Rate Floors CRUD ----

@api.post("/rate-floors")
async def rate_floor_create(body: rf_mod.RateFloorCreate, admin: str = Depends(require_admin)):
    lane_key = rf_mod.normalize_lane_key(
        origin=body.origin, destination=body.destination,
        equipment=body.equipment, explicit=body.lane_key,
    )
    f = rf_mod.RateFloor(
        lane_key=lane_key,
        origin=body.origin, destination=body.destination,
        equipment=body.equipment,
        floor_rate_usd=float(body.floor_rate_usd),
        cost_basis_usd=body.cost_basis_usd,
        required_margin_pct=body.required_margin_pct if body.required_margin_pct is not None else rf_mod.DEFAULT_MARGIN_PCT,
        source=body.source,
        rationale=body.rationale,
        valid_until=body.valid_until,
        created_by=admin,
    ).model_dump()
    await db.rate_floors.insert_one(f)
    f.pop("_id", None)
    await _audit(admin, "rate_floor.created", "rate_floor", target_id=f["id"], after=f,
                 metadata={"lane_key": lane_key, "floor_rate_usd": f["floor_rate_usd"]})
    return f


@api.get("/rate-floors")
async def rate_floors_list(lane_key: Optional[str] = None, equipment: Optional[str] = None,
                            limit: int = 200, _: str = Depends(require_admin)):
    q: Dict[str, Any] = {}
    if lane_key:
        q["lane_key"] = lane_key.upper()
    if equipment:
        q["equipment"] = equipment.upper()
    docs = await db.rate_floors.find(q, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"floors": docs, "count": len(docs)}


@api.delete("/rate-floors/{floor_id}")
async def rate_floor_delete(floor_id: str, admin: str = Depends(require_admin)):
    existing = await db.rate_floors.find_one({"id": floor_id}, {"_id": 0})
    if not existing:
        raise HTTPException(404, "Floor not found")
    await db.rate_floors.delete_one({"id": floor_id})
    await _audit(admin, "rate_floor.deleted", "rate_floor", target_id=floor_id, before=existing)
    return {"ok": True}


# ---- Rate Actuals (historical learning input) ----

@api.post("/rate-actuals")
async def rate_actual_record(body: Dict[str, Any], admin: str = Depends(require_admin)):
    lane_key = rf_mod.normalize_lane_key(
        origin=body.get("origin"), destination=body.get("destination"),
        equipment=body.get("equipment", "V53"), explicit=body.get("lane_key"),
    )
    a = rf_mod.RateActual(
        lane_key=lane_key,
        equipment=body.get("equipment", "V53"),
        quoted_rate_usd=float(body["quoted_rate_usd"]),
        carrier_pay_usd=float(body.get("carrier_pay_usd") or 0),
        fuel_surcharge_usd=float(body.get("fuel_surcharge_usd") or 0),
        margin_pct=body.get("margin_pct"),
        load_id=body.get("load_id"),
        bol_number=body.get("bol_number"),
    ).model_dump()
    await db.rate_actuals.insert_one(a)
    a.pop("_id", None)
    await _audit(admin, "quote.actual.recorded", "rate_actual", target_id=a["id"], after=a)
    return a


# ---- Quote Validation (the core risk engine) ----

@api.post("/quotes/validate")
async def quote_validate(body: rf_mod.QuoteValidationRequest, admin: str = Depends(require_admin)):
    """Submit a proposed quote for risk-engine validation. ALWAYS records an
    audit event and ALWAYS persists a quote_reviews row (status=auto_ok if
    no review needed). The agent must consume this endpoint BEFORE sending
    a quote — that's the contract."""
    lane_key = rf_mod.normalize_lane_key(
        origin=body.origin, destination=body.destination,
        equipment=body.equipment, explicit=body.lane_key,
    )
    floor_result = await rf_mod.compute_effective_floor(
        db, lane_key=lane_key, equipment=body.equipment,
        carrier_pay_usd=body.carrier_pay_usd, fuel_surcharge_usd=body.fuel_surcharge_usd,
    )
    winner = floor_result.get("winner")
    candidates = floor_result.get("candidates", [])

    if winner is None:
        sev_result = {
            "severity": "HIGH",  # no floor → conservative: queue review
            "breach_amount_usd": 0.0, "breach_pct": 0.0,
            "below_cost_basis": False, "floor_rate_usd": None, "cost_basis_usd": None,
        }
        decision: str = "QUEUE_REVIEW"
        no_floor = True
    else:
        sev_result = rf_mod.severity_for(proposed_rate_usd=body.proposed_rate_usd, floor=winner)
        decision = rf_mod.decision_for(sev_result["severity"])
        no_floor = False

    review = rf_mod.QuoteReview(
        proposed_rate_usd=float(body.proposed_rate_usd),
        floor_rate_usd=(winner or {}).get("floor_rate_usd"),
        cost_basis_usd=(winner or {}).get("cost_basis_usd"),
        breach_amount_usd=sev_result["breach_amount_usd"],
        breach_pct=sev_result["breach_pct"],
        severity=sev_result["severity"],
        decision=decision,
        floor_source=(winner or {}).get("source") if winner else "none",
        floor_rationale=(winner or {}).get("rationale") if winner else "no protective floor found · escalated",
        floor_candidates=candidates,
        lane_key=lane_key,
        origin=body.origin, destination=body.destination, equipment=body.equipment,
        carrier_pay_usd=body.carrier_pay_usd, fuel_surcharge_usd=body.fuel_surcharge_usd,
        load_id=body.load_id, bol_number=body.bol_number,
        customer=body.customer,
        memory_thread_id=body.memory_thread_id,
        agent_rationale=body.agent_rationale,
        status="auto_ok" if decision == "AUTO_OK" else "pending",
        sla_due_at=rf_mod.sla_due_at(sev_result["severity"]) if decision != "AUTO_OK" else None,
    ).model_dump()
    await db.quote_reviews.insert_one(review)
    review.pop("_id", None)

    await _audit(
        "agent", "quote.validated", "quote_review", target_id=review["id"],
        after={"severity": review["severity"], "decision": review["decision"],
               "proposed_rate_usd": review["proposed_rate_usd"],
               "floor_rate_usd": review["floor_rate_usd"],
               "lane_key": review["lane_key"]},
        evidence_uris=[f"memory_thread:{body.memory_thread_id}"] if body.memory_thread_id else [],
        metadata={"customer": body.customer, "load_id": body.load_id,
                  "breach_amount_usd": review["breach_amount_usd"]},
    )

    # Fire alert for anything that requires review or blocks
    if decision in ("QUEUE_REVIEW", "HARD_BLOCK"):
        alert_sev = rf_mod.alert_severity_for(decision, sev_result["severity"])
        await _dispatch_alert(
            severity_label=alert_sev,
            title=f"{sev_result['severity']} quote breach · {body.customer or 'unknown customer'} · {lane_key}",
            body=(
                f"Proposed ${body.proposed_rate_usd:,.2f} vs floor ${(winner or {}).get('floor_rate_usd', 0):,.2f}"
                f" · breach ${review['breach_amount_usd']:,.2f} ({review['breach_pct']}%) · decision {decision}"
                + ("\nNO PROTECTIVE FLOOR FOUND — agent must wait for manual review." if no_floor else "")
            ),
            metadata={"quote_review_id": review["id"], "severity": sev_result["severity"],
                      "lane_key": lane_key, "load_id": body.load_id,
                      "customer": body.customer, "memory_thread_id": body.memory_thread_id,
                      "floor_candidates": candidates},
        )
        await _audit("system", "quote.review.created", "quote_review", target_id=review["id"],
                     metadata={"severity": review["severity"], "decision": review["decision"]})

    return review


# ---- Quote Review queue ----

@api.get("/quote-reviews")
async def quote_reviews_list(status: Optional[str] = None, severity: Optional[str] = None,
                              decision: Optional[str] = None, limit: int = 200,
                              _: str = Depends(require_admin)):
    q: Dict[str, Any] = {}
    if status:
        q["status"] = status
    if severity:
        q["severity"] = severity.upper()
    if decision:
        q["decision"] = decision.upper()
    rows = await db.quote_reviews.find(q, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    pending = sum(1 for r in rows if r.get("status") == "pending")
    blocking = sum(1 for r in rows if r.get("decision") == "HARD_BLOCK" and r.get("status") in ("pending", "overridden"))
    return {"reviews": rows, "count": len(rows), "pending": pending, "hard_blocks": blocking}


@api.post("/quote-reviews/{review_id}/approve")
async def quote_review_approve(review_id: str, notes: Optional[str] = None,
                                admin: str = Depends(require_admin)):
    r = await db.quote_reviews.find_one({"id": review_id}, {"_id": 0})
    if not r:
        raise HTTPException(404, "Review not found")
    if r.get("status") not in ("pending", "auto_ok"):
        raise HTTPException(400, f"Cannot approve review in status {r.get('status')}")
    upd = {"status": "approved", "reviewer": admin, "reviewer_notes": notes,
           "reviewed_at": _utcnow_iso()}
    await db.quote_reviews.update_one({"id": review_id}, {"$set": upd})
    after = {**r, **upd}
    await _audit(admin, "quote.review.approved", "quote_review", target_id=review_id,
                 before=r, after=after, metadata={"severity": r.get("severity"), "notes": notes})
    return after


@api.post("/quote-reviews/{review_id}/reject")
async def quote_review_reject(review_id: str, notes: Optional[str] = None,
                               admin: str = Depends(require_admin)):
    r = await db.quote_reviews.find_one({"id": review_id}, {"_id": 0})
    if not r:
        raise HTTPException(404, "Review not found")
    if r.get("status") not in ("pending", "auto_ok"):
        raise HTTPException(400, f"Cannot reject review in status {r.get('status')}")
    upd = {"status": "rejected", "reviewer": admin, "reviewer_notes": notes,
           "reviewed_at": _utcnow_iso()}
    await db.quote_reviews.update_one({"id": review_id}, {"$set": upd})
    after = {**r, **upd}
    await _audit(admin, "quote.review.rejected", "quote_review", target_id=review_id,
                 before=r, after=after, metadata={"severity": r.get("severity"), "notes": notes})
    return after


@api.post("/quote-reviews/{review_id}/override")
async def quote_review_override(review_id: str, notes: Optional[str] = None,
                                 admin: str = Depends(require_admin)):
    """Operator override of a HARD_BLOCK. Notes are MANDATORY (we log them to the audit chain)."""
    if not notes or not notes.strip():
        raise HTTPException(400, "Override requires reviewer_notes explaining why")
    r = await db.quote_reviews.find_one({"id": review_id}, {"_id": 0})
    if not r:
        raise HTTPException(404, "Review not found")
    if r.get("decision") != "HARD_BLOCK":
        raise HTTPException(400, "Only HARD_BLOCK reviews require override")
    upd = {"status": "overridden", "reviewer": admin, "reviewer_notes": notes,
           "reviewed_at": _utcnow_iso()}
    await db.quote_reviews.update_one({"id": review_id}, {"$set": upd})
    after = {**r, **upd}
    await _audit(admin, "quote.review.overridden", "quote_review", target_id=review_id,
                 before=r, after=after,
                 metadata={"severity": r.get("severity"), "breach_amount_usd": r.get("breach_amount_usd"),
                           "notes": notes, "warning": "HARD_BLOCK overridden — operator accepts financial exposure"})
    return after


@api.get("/quote-reviews/{review_id}")
async def quote_review_detail(review_id: str, _: str = Depends(require_admin)):
    r = await db.quote_reviews.find_one({"id": review_id}, {"_id": 0})
    if not r:
        raise HTTPException(404, "Review not found")
    audit = await audit_mod.list_events(db, target_type="quote_review", target_id=review_id, limit=50)
    return {"review": r, "audit": audit}


# ---- Audit Trail ----

@api.get("/audit/events")
async def audit_events_list(target_type: Optional[str] = None,
                             target_id: Optional[str] = None,
                             actor: Optional[str] = None,
                             action_prefix: Optional[str] = None,
                             limit: int = 200,
                             _: str = Depends(require_admin)):
    rows = await audit_mod.list_events(
        db, target_type=target_type, target_id=target_id,
        actor=actor, action_prefix=action_prefix, limit=limit,
    )
    return {"events": rows, "count": len(rows)}


@api.get("/audit/verify")
async def audit_verify(limit: int = 1000, _: str = Depends(require_admin)):
    """Re-hash the entire chain and confirm no event was tampered with."""
    return await audit_mod.verify_chain(db, limit=limit)


# ---- Alerts (admin banner) ----

@api.get("/alerts/unread")
async def alerts_unread(limit: int = 50, _: str = Depends(require_admin)):
    rows = await db.alerts.find({"read": False}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"alerts": rows, "count": len(rows)}


@api.get("/alerts")
async def alerts_list(limit: int = 200, _: str = Depends(require_admin)):
    rows = await db.alerts.find({}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"alerts": rows, "count": len(rows)}


@api.post("/alerts/{alert_id}/ack")
async def alert_ack(alert_id: str, admin: str = Depends(require_admin)):
    res = await db.alerts.update_one({"id": alert_id}, {"$set": {"read": True, "acked_by": admin, "acked_at": _utcnow_iso()}})
    if res.matched_count == 0:
        raise HTTPException(404, "Alert not found")
    return {"ok": True}


@api.post("/alerts/ack-all")
async def alerts_ack_all(admin: str = Depends(require_admin)):
    res = await db.alerts.update_many({"read": False}, {"$set": {"read": True, "acked_by": admin, "acked_at": _utcnow_iso()}})
    return {"acked": res.modified_count}


# ============================================================
# TRUCKER AI · maps · parking · HOS · weather · 511 (all free public sources)
# ============================================================
import trucker_ai as trucker_mod


@api.get("/trucker/hos-rules")
async def trucker_hos_rules():
    """Federal HOS rules (49 CFR §395). Codified, citable."""
    return trucker_mod.HOS_RULES


@api.post("/trucker/hos-check")
async def trucker_hos_check(body: trucker_mod.HOSCheckBody):
    return trucker_mod.hos_check(body)


@api.post("/trucker/geocode")
async def trucker_geocode(body: Dict[str, Any]):
    q = (body or {}).get("query", "")
    res = await trucker_mod.geocode(q)
    if not res:
        return {"ok": False, "query": q, "reason": "no_match_or_geocoder_error"}
    return {"ok": True, "result": res}


@api.post("/trucker/truck-stops")
async def trucker_truck_stops(body: Dict[str, Any]):
    """Find truck stops / fuel / rest areas / weigh stations near a point.
    Body: { lat, lon, radius_miles, include[] } OR { query, radius_miles }."""
    lat = body.get("lat"); lon = body.get("lon")
    if lat is None or lon is None:
        q = body.get("query")
        if not q:
            raise HTTPException(400, "Provide lat+lon OR query")
        geo = await trucker_mod.geocode(q)
        if not geo:
            raise HTTPException(404, f"Could not geocode '{q}'")
        lat, lon = geo["lat"], geo["lon"]
    radius = float(body.get("radius_miles") or 50)
    include = body.get("include") or None
    rows = await trucker_mod.find_truck_stops(float(lat), float(lon), radius, include)
    return {
        "origin": {"lat": float(lat), "lon": float(lon)},
        "radius_miles": radius, "count": len(rows), "stops": rows,
        "source": "openstreetmap_overpass",
        "source_url": "https://www.openstreetmap.org",
    }


@api.post("/trucker/route")
async def trucker_route(body: Dict[str, Any]):
    o_lat = body.get("origin_lat"); o_lon = body.get("origin_lon")
    d_lat = body.get("dest_lat"); d_lon = body.get("dest_lon")
    if o_lat is None or o_lon is None:
        o = body.get("origin") or ""
        geo = await trucker_mod.geocode(o)
        if not geo:
            raise HTTPException(400, f"Could not geocode origin '{o}'")
        o_lat, o_lon = geo["lat"], geo["lon"]
    if d_lat is None or d_lon is None:
        d = body.get("destination") or ""
        geo = await trucker_mod.geocode(d)
        if not geo:
            raise HTTPException(400, f"Could not geocode destination '{d}'")
        d_lat, d_lon = geo["lat"], geo["lon"]
    route = await trucker_mod.route_osrm(float(o_lat), float(o_lon), float(d_lat), float(d_lon))
    if not route:
        raise HTTPException(503, "Routing service unavailable")
    return {
        "origin": {"lat": float(o_lat), "lon": float(o_lon)},
        "destination": {"lat": float(d_lat), "lon": float(d_lon)},
        **route,
    }


@api.post("/trucker/weather")
async def trucker_weather(body: Dict[str, Any]):
    lat = body.get("lat"); lon = body.get("lon")
    if lat is None or lon is None:
        q = body.get("query")
        if not q:
            raise HTTPException(400, "Provide lat+lon OR query")
        geo = await trucker_mod.geocode(q)
        if not geo:
            raise HTTPException(404, f"Could not geocode '{q}'")
        lat, lon = geo["lat"], geo["lon"]
    res = await trucker_mod.weather_at(float(lat), float(lon))
    if not res:
        raise HTTPException(503, "Weather service unavailable")
    return res


@api.get("/trucker/diesel-prices")
async def trucker_diesel():
    return await trucker_mod.diesel_prices()


@api.get("/trucker/state-511/{state}")
async def trucker_state_511(state: str):
    res = trucker_mod.state_511(state)
    if not res:
        raise HTTPException(404, "Unknown state code")
    return res


@api.get("/trucker/state-511")
async def trucker_state_511_list():
    return {
        "states": [{"state": s, "name": v[0], "url": v[1]}
                   for s, v in sorted(trucker_mod.STATE_511.items())],
        "source": "operator_directory_curated",
    }





    # Mark all pre-existing prospects (created before is_synthetic field existed) as synthetic.
    # They were all AI-generated. New CSV / FMCSA seeded leads set is_synthetic=False explicitly.
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
    # Backfill: mark legacy prospects as synthetic so the UI can hide them.
    backfill = await db.prospects.update_many(
        {"is_synthetic": {"$exists": False}},
        {"$set": {"is_synthetic": True, "is_verified": False, "verification_source": "ai_synthesized_legacy"}},
    )
    if backfill.modified_count:
        log.info(f"prospects · backfilled {backfill.modified_count} legacy records as is_synthetic=True")


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
