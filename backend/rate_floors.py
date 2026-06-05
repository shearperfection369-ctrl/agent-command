"""JADE OS · Rate Floor + Quote Validation.

The "don't let the agent quote $800 on a $1200 load" system.

Three layered floor sources (recommendation per user · option (d)):
  1. MANUAL    — operator-entered floor per (origin, dest, equipment). Wins ties.
  2. FORMULA   — floor = carrier_pay × (1 + required_margin_pct) + fuel_surcharge
                 Reads `default_required_margin_pct` from settings (default 0.12).
  3. HISTORICAL — median of recent successful actuals on the same lane/equipment.

Severity bands (per user — defaults):
  LOW       0–5%  below floor
  MEDIUM    5–10% below floor
  HIGH      10%+  below floor
  CRITICAL  at or below carrier cost basis (literal money-loser)

Decision matrix (tiered — option (c)):
  CLEAR    → AUTO_OK
  LOW      → AUTO_OK with `flagged_for_log` (no human gate, but logged)
  MEDIUM   → QUEUE_REVIEW (operator must approve before the quote can be sent)
  HIGH     → QUEUE_REVIEW (escalated · SLA tighter)
  CRITICAL → HARD_BLOCK   (quote CANNOT be sent until manual override + reason)
"""
from __future__ import annotations

import os
import uuid
import logging
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field, ConfigDict

log = logging.getLogger("jadeos.rate_floors")

FloorSource = Literal["manual", "formula", "historical"]
Severity = Literal["CLEAR", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
Decision = Literal["AUTO_OK", "QUEUE_REVIEW", "HARD_BLOCK"]

DEFAULT_MARGIN_PCT = float(os.environ.get("RATE_DEFAULT_MARGIN_PCT", "0.12"))
HISTORICAL_LOOKBACK_DAYS = int(os.environ.get("RATE_HISTORICAL_LOOKBACK_DAYS", "90"))
MIN_HISTORICAL_SAMPLES = int(os.environ.get("RATE_MIN_HISTORICAL_SAMPLES", "3"))

SEVERITY_BANDS = {
    "LOW_PCT": float(os.environ.get("RATE_BAND_LOW_PCT", "0.05")),       # 0–5%
    "MEDIUM_PCT": float(os.environ.get("RATE_BAND_MEDIUM_PCT", "0.10")), # 5–10%
    # HIGH = > MEDIUM_PCT (10%+) below floor
    # CRITICAL = at/below cost basis (special, see below)
}


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------- Models ----------

class RateFloor(BaseModel):
    """Manual or formula-anchored rate floor for a lane + equipment combo."""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lane_key: str  # normalized e.g. "MN-TX-V53" (state-state-equip) or "MSP-DFW-R53"
    origin: Optional[str] = None
    destination: Optional[str] = None
    equipment: str = "V53"  # V53 (53' van), R53 (reefer), FB48, etc.
    floor_rate_usd: float  # absolute minimum total broker quote
    cost_basis_usd: Optional[float] = None  # what we pay carrier · used for CRITICAL band
    required_margin_pct: float = DEFAULT_MARGIN_PCT
    source: FloorSource = "manual"
    rationale: Optional[str] = None  # why this floor exists
    valid_from: str = Field(default_factory=_utcnow_iso)
    valid_until: Optional[str] = None  # None = open-ended
    created_by: str = "operator"
    created_at: str = Field(default_factory=_utcnow_iso)
    updated_at: str = Field(default_factory=_utcnow_iso)


class RateFloorCreate(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    equipment: str = "V53"
    lane_key: Optional[str] = None
    floor_rate_usd: float
    cost_basis_usd: Optional[float] = None
    required_margin_pct: Optional[float] = None
    source: FloorSource = "manual"
    rationale: Optional[str] = None
    valid_until: Optional[str] = None


class RateActual(BaseModel):
    """A historical actual — the rate we successfully quoted on a real lane."""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lane_key: str
    equipment: str
    quoted_rate_usd: float
    carrier_pay_usd: float
    fuel_surcharge_usd: float = 0.0
    margin_pct: Optional[float] = None
    load_id: Optional[str] = None
    bol_number: Optional[str] = None
    closed_at: str = Field(default_factory=_utcnow_iso)


class QuoteValidationRequest(BaseModel):
    """Submit a proposed quote for risk-engine validation."""
    proposed_rate_usd: float
    carrier_pay_usd: Optional[float] = None  # what we'd pay carrier
    fuel_surcharge_usd: float = 0.0
    origin: Optional[str] = None
    destination: Optional[str] = None
    equipment: str = "V53"
    lane_key: Optional[str] = None
    load_id: Optional[str] = None
    bol_number: Optional[str] = None
    memory_thread_id: Optional[str] = None
    agent_rationale: Optional[str] = None  # why agent picked this number
    customer: Optional[str] = None


# ---------- Lane key normalization ----------

def normalize_lane_key(*, origin: Optional[str], destination: Optional[str],
                       equipment: str = "V53", explicit: Optional[str] = None) -> str:
    """Normalize a lane key. Order of precedence:
       1. explicit caller-supplied key
       2. derived from origin / destination / equipment
    """
    if explicit:
        return explicit.strip().upper()
    o = (origin or "").strip().upper().replace(" ", "")
    d = (destination or "").strip().upper().replace(" ", "")
    eq = (equipment or "V53").strip().upper().replace(" ", "")
    return f"{o or '???'}|{d or '???'}|{eq}"


# ---------- Floor lookup ----------

async def _lookup_manual_floor(db, lane_key: str, equipment: str) -> Optional[Dict]:
    """Find the newest active manual floor for the lane/equipment."""
    now = _utcnow_iso()
    cur = db.rate_floors.find({
        "lane_key": lane_key, "equipment": equipment, "source": "manual",
        "$or": [{"valid_until": None}, {"valid_until": {"$gt": now}}],
    }, {"_id": 0}).sort("created_at", -1).limit(1)
    rows = await cur.to_list(1)
    return rows[0] if rows else None


def _compute_formula_floor(*, carrier_pay_usd: Optional[float],
                           fuel_surcharge_usd: float,
                           required_margin_pct: float) -> Optional[Dict]:
    """floor = carrier_pay × (1 + margin) + fuel_surcharge. Returns None if no carrier_pay."""
    if carrier_pay_usd is None or carrier_pay_usd <= 0:
        return None
    floor = (carrier_pay_usd * (1.0 + required_margin_pct)) + fuel_surcharge_usd
    return {
        "floor_rate_usd": round(floor, 2),
        "cost_basis_usd": round(carrier_pay_usd + fuel_surcharge_usd, 2),
        "required_margin_pct": required_margin_pct,
        "source": "formula",
        "rationale": f"carrier_pay ${carrier_pay_usd:.2f} × (1 + {required_margin_pct:.0%}) + fuel ${fuel_surcharge_usd:.2f}",
    }


async def _lookup_historical_floor(db, lane_key: str, equipment: str) -> Optional[Dict]:
    """Median of last N successful actuals on the lane (within lookback window).
    The floor floor is the 25th percentile minus a small buffer."""
    since = (datetime.now(timezone.utc) - timedelta(days=HISTORICAL_LOOKBACK_DAYS)).isoformat()
    actuals = await db.rate_actuals.find(
        {"lane_key": lane_key, "equipment": equipment, "closed_at": {"$gte": since}},
        {"_id": 0},
    ).sort("closed_at", -1).limit(50).to_list(50)
    if len(actuals) < MIN_HISTORICAL_SAMPLES:
        return None
    rates = sorted(float(a["quoted_rate_usd"]) for a in actuals)
    # Use the 25th percentile as a conservative floor reference
    idx = max(0, int(len(rates) * 0.25) - 1)
    p25 = rates[idx]
    median = statistics.median(rates)
    return {
        "floor_rate_usd": round(p25, 2),
        "cost_basis_usd": None,
        "required_margin_pct": None,
        "source": "historical",
        "rationale": f"P25 of {len(actuals)} actuals on {lane_key} · median ${median:.2f} · last {HISTORICAL_LOOKBACK_DAYS}d",
        "sample_size": len(actuals),
        "median_rate_usd": round(median, 2),
    }


async def compute_effective_floor(db, *, lane_key: str, equipment: str,
                                   carrier_pay_usd: Optional[float] = None,
                                   fuel_surcharge_usd: float = 0.0,
                                   required_margin_pct: Optional[float] = None) -> Dict:
    """Layer all three sources. Returns the WINNING floor + all candidates for audit.

    Layering rule: take the HIGHEST floor across sources (= most protective).
    The "winning" source ID is recorded so the audit trail is reproducible.
    """
    margin_pct = required_margin_pct if required_margin_pct is not None else DEFAULT_MARGIN_PCT
    candidates: List[Dict] = []

    manual = await _lookup_manual_floor(db, lane_key, equipment)
    if manual:
        candidates.append({
            "source": "manual",
            "floor_rate_usd": float(manual["floor_rate_usd"]),
            "cost_basis_usd": manual.get("cost_basis_usd"),
            "required_margin_pct": manual.get("required_margin_pct", margin_pct),
            "rationale": manual.get("rationale") or f"manual floor set {manual.get('created_at', '?')[:10]}",
            "ref_id": manual["id"],
        })

    formula = _compute_formula_floor(
        carrier_pay_usd=carrier_pay_usd, fuel_surcharge_usd=fuel_surcharge_usd,
        required_margin_pct=margin_pct,
    )
    if formula:
        candidates.append(formula)

    hist = await _lookup_historical_floor(db, lane_key, equipment)
    if hist:
        candidates.append(hist)

    if not candidates:
        return {
            "winner": None,
            "candidates": [],
            "note": "no floor available · agent must request a manual rate-check before quoting",
        }

    winner = max(candidates, key=lambda c: c["floor_rate_usd"])
    return {"winner": winner, "candidates": candidates}


# ---------- Severity + decision ----------

def severity_for(*, proposed_rate_usd: float, floor: Dict) -> Dict:
    """Return severity band + breach details."""
    floor_rate = float(floor.get("floor_rate_usd") or 0)
    cost_basis = floor.get("cost_basis_usd")
    if floor_rate <= 0:
        return {
            "severity": "CLEAR",
            "breach_amount_usd": 0.0,
            "breach_pct": 0.0,
            "below_cost_basis": False,
            "note": "no protective floor available",
        }

    breach_amount = floor_rate - proposed_rate_usd  # positive = below floor
    breach_pct = breach_amount / floor_rate if floor_rate > 0 else 0.0

    below_cost = bool(cost_basis is not None and proposed_rate_usd <= float(cost_basis))

    if below_cost:
        sev: Severity = "CRITICAL"
    elif breach_amount <= 0:
        sev = "CLEAR"
    elif breach_pct <= SEVERITY_BANDS["LOW_PCT"]:
        sev = "LOW"
    elif breach_pct <= SEVERITY_BANDS["MEDIUM_PCT"]:
        sev = "MEDIUM"
    else:
        sev = "HIGH"

    return {
        "severity": sev,
        "breach_amount_usd": round(max(0.0, breach_amount), 2),
        "breach_pct": round(max(0.0, breach_pct) * 100, 2),
        "below_cost_basis": below_cost,
        "floor_rate_usd": floor_rate,
        "cost_basis_usd": cost_basis,
    }


def decision_for(severity: str) -> Decision:
    """User-locked tiered mapping (option c)."""
    if severity in ("CLEAR", "LOW"):
        return "AUTO_OK"
    if severity in ("MEDIUM", "HIGH"):
        return "QUEUE_REVIEW"
    return "HARD_BLOCK"  # CRITICAL


def alert_severity_for(decision: str, severity: str) -> str:
    """Pager-level for the alerts channel. CRITICAL pages immediately."""
    if severity == "CRITICAL" or decision == "HARD_BLOCK":
        return "page"
    if severity == "HIGH":
        return "high"
    if severity == "MEDIUM":
        return "medium"
    return "info"


# ---------- Quote review record ----------

class QuoteReview(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    proposed_rate_usd: float
    floor_rate_usd: Optional[float] = None
    cost_basis_usd: Optional[float] = None
    breach_amount_usd: float = 0.0
    breach_pct: float = 0.0
    severity: Severity
    decision: Decision
    floor_source: Optional[str] = None
    floor_rationale: Optional[str] = None
    floor_candidates: List[Dict] = Field(default_factory=list)
    lane_key: str
    origin: Optional[str] = None
    destination: Optional[str] = None
    equipment: str = "V53"
    carrier_pay_usd: Optional[float] = None
    fuel_surcharge_usd: float = 0.0
    load_id: Optional[str] = None
    bol_number: Optional[str] = None
    customer: Optional[str] = None
    memory_thread_id: Optional[str] = None
    agent_rationale: Optional[str] = None
    status: Literal["pending", "approved", "rejected", "overridden", "expired", "auto_ok"] = "pending"
    reviewer: Optional[str] = None
    reviewer_notes: Optional[str] = None
    reviewed_at: Optional[str] = None
    sla_due_at: Optional[str] = None
    created_at: str = Field(default_factory=_utcnow_iso)


def sla_due_at(severity: str) -> str:
    """SLA: HIGH→1h, MEDIUM→4h, CRITICAL→immediate (blocks anyway), else 24h."""
    hours = {"CRITICAL": 1, "HIGH": 1, "MEDIUM": 4}.get(severity, 24)
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()
