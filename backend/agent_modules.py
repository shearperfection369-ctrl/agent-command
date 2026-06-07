"""JADE OS · Agent Modules · Deterministic-first MVPs.

These ship today as honest, source-cited deterministic scoring with a clear
PILOT-PHASE designation. No LLM, no fabrication, no hidden mocks. Each function
returns a `source` field naming the benchmark or rule set that drove the score.

Modules:
  • M1 · Dispatch Optimizer  (score_dispatch)
  • M5 · Driver Retention    (score_retention)
  • M6 · Predictive Maint    (score_maintenance)
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in miles."""
    R = 3958.7613
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# =============================================================================
# M1 · DISPATCH OPTIMIZER (deterministic MVP)
# =============================================================================

class DriverState(BaseModel):
    driver_id: str
    name: Optional[str] = None
    lat: float
    lon: float
    hos_remaining_drive_h: float = Field(..., ge=0, le=11)
    hos_remaining_duty_h: float = Field(..., ge=0, le=14)
    weekly_remaining_h: float = Field(..., ge=0, le=70)
    home_base_miles: float = 0
    avg_cpm_usd: float = 1.65  # cost per mile · driver+truck loaded · ATRI 2024 ~$2.27 total, $1.65 ex-fuel
    preferred_lanes: List[str] = []


class OpenLoad(BaseModel):
    load_id: str
    pickup_lat: float
    pickup_lon: float
    dropoff_lat: float
    dropoff_lon: float
    pickup_window_hours: float = 24  # how soon we need a driver on it
    customer_priority: int = Field(2, ge=1, le=5)  # 1 spot · 5 strategic
    revenue_usd: float
    lane_code: Optional[str] = None  # e.g. "MN-WI"


class DispatchScore(BaseModel):
    driver_id: str
    load_id: str
    score: float
    deadhead_miles: float
    loaded_miles: float
    estimated_drive_h: float
    hos_feasible: bool
    hos_feasibility_note: str
    margin_estimate_usd: float
    reasons: List[str]


def score_dispatch(drivers: List[DriverState], loads: List[OpenLoad],
                    *, avg_speed_mph: float = 50.0,
                    hos_overrun_penalty: float = 1000.0) -> Dict[str, Any]:
    """Score every driver × load pairing and return top-3 per load.

    Scoring (higher = better):
      utility = revenue * customer_priority_weight
              - deadhead_cost (deadhead_miles * cpm)
              - hos_overrun_penalty (if not HOS feasible)
              - preferred_lane_bonus_offset

    No LLM. Reproducible. Source: ATRI 2024 cost-per-mile baseline · FMCSA §395 HOS.
    """
    rows: List[DispatchScore] = []
    for ld in loads:
        loaded_miles = _haversine_miles(ld.pickup_lat, ld.pickup_lon, ld.dropoff_lat, ld.dropoff_lon)
        drive_h_loaded = loaded_miles / avg_speed_mph
        for dr in drivers:
            dh = _haversine_miles(dr.lat, dr.lon, ld.pickup_lat, ld.pickup_lon)
            drive_h_total = (dh + loaded_miles) / avg_speed_mph
            feasible = (drive_h_total <= dr.hos_remaining_drive_h and
                         drive_h_total <= dr.hos_remaining_duty_h and
                         drive_h_total <= dr.weekly_remaining_h)
            note = "feasible" if feasible else (
                f"need {drive_h_total:.1f}h · driver has {min(dr.hos_remaining_drive_h, dr.hos_remaining_duty_h, dr.weekly_remaining_h):.1f}h"
            )
            priority_weight = {1: 1.0, 2: 1.05, 3: 1.12, 4: 1.20, 5: 1.30}[ld.customer_priority]
            deadhead_cost = dh * dr.avg_cpm_usd
            preferred_bonus = 50.0 if (ld.lane_code and ld.lane_code in dr.preferred_lanes) else 0.0
            margin = ld.revenue_usd - ((dh + loaded_miles) * dr.avg_cpm_usd)
            utility = (ld.revenue_usd * priority_weight) - deadhead_cost + preferred_bonus
            if not feasible:
                utility -= hos_overrun_penalty
            reasons = []
            if dh < 50: reasons.append(f"low deadhead · {dh:.0f}mi")
            elif dh > 150: reasons.append(f"high deadhead · {dh:.0f}mi")
            if ld.customer_priority >= 4: reasons.append(f"priority customer · weight x{priority_weight:.2f}")
            if preferred_bonus: reasons.append(f"preferred lane · +${preferred_bonus:.0f}")
            if not feasible: reasons.append(f"HOS NOT FEASIBLE · -${hos_overrun_penalty:.0f}")
            if margin < 200: reasons.append(f"thin margin · ${margin:.0f}")
            rows.append(DispatchScore(driver_id=dr.driver_id, load_id=ld.load_id,
                                       score=round(utility, 2), deadhead_miles=round(dh, 1),
                                       loaded_miles=round(loaded_miles, 1),
                                       estimated_drive_h=round(drive_h_total, 2),
                                       hos_feasible=feasible, hos_feasibility_note=note,
                                       margin_estimate_usd=round(margin, 2),
                                       reasons=reasons))
    rows.sort(key=lambda r: r.score, reverse=True)
    # Top 3 per load
    by_load: Dict[str, List[DispatchScore]] = {}
    for r in rows:
        by_load.setdefault(r.load_id, []).append(r)
    recommendations = {lid: [r.model_dump() for r in lst[:3]] for lid, lst in by_load.items()}
    return {
        "recommendations": recommendations,
        "total_pairings_scored": len(rows),
        "drivers": len(drivers), "loads": len(loads),
        "method": "constraint+utility · deterministic MVP",
        "source": "ATRI 2024 cost-per-mile · FMCSA §395 HOS rules",
        "generated_at": _utcnow_iso(),
        "status": "PILOT_PHASE · deterministic-first; LLM coaching layer follows in Pilot",
    }


# =============================================================================
# M5 · DRIVER RETENTION (deterministic MVP)
# =============================================================================

class DriverRetentionInput(BaseModel):
    driver_id: str
    name: Optional[str] = None
    tenure_months: int = Field(..., ge=0)
    miles_last_30d: int = Field(..., ge=0)
    home_time_days_last_30d: int = Field(..., ge=0, le=30)
    weeks_since_last_pay_raise: int = Field(..., ge=0)
    dispatch_complaints_90d: int = Field(0, ge=0)
    accidents_or_violations_90d: int = Field(0, ge=0)
    pay_per_mile_usd: float = 0.55


class RetentionResult(BaseModel):
    driver_id: str
    retention_risk_score: int   # 0 (very safe) → 100 (high risk)
    band: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    top_factors: List[Dict[str, Any]]
    recommended_actions: List[str]
    source: str
    generated_at: str


def score_retention(inp: DriverRetentionInput) -> RetentionResult:
    """Score a driver's retention risk 0-100 with deterministic weighting.

    Weighting reflects ATA/ATRI retention literature: home-time deficit and pay
    stagnation are the two largest churn drivers in mid-market freight; recent
    accidents/violations + complaint history are accelerants.
    """
    factors: List[Dict[str, Any]] = []
    score = 0

    # 1. Home-time deficit · target ≥ 6 days/30d for OTR · big driver
    target_home = 6
    if inp.home_time_days_last_30d < target_home:
        deficit = target_home - inp.home_time_days_last_30d
        pts = min(35, deficit * 7)
        score += pts
        factors.append({"name": "home_time_deficit",
                        "weight": pts,
                        "detail": f"{inp.home_time_days_last_30d}/{target_home} days home in last 30d"})

    # 2. Pay stagnation · weeks since raise
    if inp.weeks_since_last_pay_raise >= 52:
        pts = min(25, (inp.weeks_since_last_pay_raise // 13) * 5)
        score += pts
        factors.append({"name": "pay_stagnation",
                        "weight": pts,
                        "detail": f"{inp.weeks_since_last_pay_raise} weeks since last raise"})

    # 3. Tenure curve · the 0-6 month and 12-18 month cliffs are highest churn
    if inp.tenure_months <= 6:
        pts = 15
        score += pts
        factors.append({"name": "early_tenure_cliff", "weight": pts,
                        "detail": f"{inp.tenure_months} months tenure · 0-6 month churn band"})
    elif 12 <= inp.tenure_months <= 18:
        pts = 10
        score += pts
        factors.append({"name": "12_18_month_cliff", "weight": pts,
                        "detail": f"{inp.tenure_months} months tenure"})

    # 4. Complaints
    if inp.dispatch_complaints_90d > 0:
        pts = min(15, inp.dispatch_complaints_90d * 5)
        score += pts
        factors.append({"name": "dispatch_complaints", "weight": pts,
                        "detail": f"{inp.dispatch_complaints_90d} complaint(s) in last 90d"})

    # 5. Accidents/violations
    if inp.accidents_or_violations_90d > 0:
        pts = min(20, inp.accidents_or_violations_90d * 10)
        score += pts
        factors.append({"name": "safety_event", "weight": pts,
                        "detail": f"{inp.accidents_or_violations_90d} event(s) in last 90d"})

    # 6. Mileage outliers · under 2,000 mi or over 12,000 mi/month both flag
    if inp.miles_last_30d < 2000:
        pts = 8
        score += pts
        factors.append({"name": "low_miles", "weight": pts,
                        "detail": f"{inp.miles_last_30d} mi last 30d · revenue/effort imbalance"})
    elif inp.miles_last_30d > 12000:
        pts = 10
        score += pts
        factors.append({"name": "burnout_miles", "weight": pts,
                        "detail": f"{inp.miles_last_30d} mi last 30d · burnout risk"})

    score = min(100, score)
    band: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = (
        "LOW" if score < 25 else "MEDIUM" if score < 50 else "HIGH" if score < 75 else "CRITICAL"
    )

    # Sort factors by weight desc for "top reasons"
    factors.sort(key=lambda f: -f["weight"])

    actions: List[str] = []
    factor_names = {f["name"] for f in factors}
    if "home_time_deficit" in factor_names:
        actions.append("Schedule guaranteed home-time window inside next 14 days · communicate in writing")
    if "pay_stagnation" in factor_names:
        actions.append(f"Review pay band; cost-of-living + tenure raise · est. +$0.02-0.05/mi from current ${inp.pay_per_mile_usd:.2f}")
    if "dispatch_complaints" in factor_names:
        actions.append("Driver-manager 1:1 within 7 days · review last 3 dispatches, document resolution")
    if "safety_event" in factor_names:
        actions.append("Safety coaching session + ride-along scheduling · pair with mentor driver")
    if "early_tenure_cliff" in factor_names:
        actions.append("First-90-day onboarding check-in (formal) · introduce driver to operations team")
    if "burnout_miles" in factor_names:
        actions.append("Cap miles for next 30 days to ≤ 10,000 · enforce home-time")
    if not actions:
        actions.append("Hold steady · monthly retention pulse + birthday/anniversary recognition")

    return RetentionResult(
        driver_id=inp.driver_id,
        retention_risk_score=int(score),
        band=band,
        top_factors=factors[:5],
        recommended_actions=actions,
        source="ATA driver shortage analyses + ATRI Operational Costs · deterministic weighting",
        generated_at=_utcnow_iso(),
    )


# =============================================================================
# M6 · PREDICTIVE MAINTENANCE (deterministic MVP)
# =============================================================================

class MaintenanceInput(BaseModel):
    vehicle_id: str
    unit_type: Literal["tractor", "trailer", "straight_truck"] = "tractor"
    miles_since_last_pm_a: int = Field(0, ge=0)
    miles_since_last_pm_b: int = Field(0, ge=0)
    fault_codes_30d: List[str] = []  # SPN codes e.g. "SPN-3361" (DEF), "SPN-94" (fuel pressure)
    inspection_violations_12mo: int = 0
    primary_route: Literal["regional", "longhaul", "local"] = "regional"


class MaintenanceResult(BaseModel):
    vehicle_id: str
    urgency_score: int   # 0-100
    band: Literal["ROUTINE", "WATCH", "SCHEDULE_SOON", "GROUND_NOW"]
    window_days: int     # recommended days to bring in
    recommended_services: List[str]
    fault_severity_breakdown: Dict[str, int]
    source: str
    generated_at: str


# Common high-severity J1939 SPN codes (subset, deterministic mapping)
FAULT_SEVERITY = {
    # Engine + emissions critical
    "SPN-94": ("Engine fuel delivery pressure", 25),
    "SPN-100": ("Engine oil pressure", 35),
    "SPN-110": ("Engine coolant temperature", 25),
    "SPN-3361": ("DEF/SCR system fault", 15),
    "SPN-3251": ("DPF differential pressure", 18),
    # Transmission / driveline
    "SPN-191": ("Transmission output speed", 20),
    "SPN-127": ("Transmission oil pressure", 22),
    # Brakes / ABS
    "SPN-789": ("ABS wheel speed", 18),
    "SPN-1807": ("Brake stroke", 22),
    # Aftertreatment downtime
    "SPN-3216": ("NOx sensor", 12),
}


def score_maintenance(inp: MaintenanceInput) -> MaintenanceResult:
    """Score a vehicle's maintenance urgency 0-100.

    Uses: J1939 fault severity dictionary + PM mileage thresholds + recent
    inspection-violation count. Deterministic; reproducible.
    """
    score = 0
    fault_breakdown: Dict[str, int] = {}
    services: List[str] = []

    # PM-A intervals: 10,000 mi · PM-B intervals: 40,000 mi (mid-market typical)
    if inp.miles_since_last_pm_a >= 12000:
        score += 15
        services.append(f"PM-A overdue · {inp.miles_since_last_pm_a} mi (target 10k)")
    elif inp.miles_since_last_pm_a >= 9000:
        score += 6
        services.append(f"PM-A due soon · {inp.miles_since_last_pm_a} mi")
    if inp.miles_since_last_pm_b >= 45000:
        score += 25
        services.append(f"PM-B overdue · {inp.miles_since_last_pm_b} mi (target 40k)")
    elif inp.miles_since_last_pm_b >= 38000:
        score += 10
        services.append(f"PM-B due soon · {inp.miles_since_last_pm_b} mi")

    # Fault codes
    for code in inp.fault_codes_30d:
        meta = FAULT_SEVERITY.get(code.upper())
        if meta:
            label, pts = meta
            score += pts
            fault_breakdown[code.upper()] = pts
            services.append(f"Investigate {code.upper()} · {label} (+{pts})")

    # Inspection violations · CSA score driver
    if inp.inspection_violations_12mo > 0:
        pts = min(20, inp.inspection_violations_12mo * 5)
        score += pts
        services.append(f"Review last {inp.inspection_violations_12mo} inspection violation(s) · safety + maint cross-check")

    # Long-haul amplifier · faults in long-haul use have more downside
    if inp.primary_route == "longhaul" and fault_breakdown:
        score = int(score * 1.15)

    score = min(100, score)
    band: Literal["ROUTINE", "WATCH", "SCHEDULE_SOON", "GROUND_NOW"] = (
        "ROUTINE" if score < 20 else "WATCH" if score < 45 else "SCHEDULE_SOON" if score < 75 else "GROUND_NOW"
    )
    window_days = (
        30 if band == "ROUTINE" else 14 if band == "WATCH" else 5 if band == "SCHEDULE_SOON" else 0
    )

    if not services:
        services.append("No actionable signals · continue routine inspections per PM schedule")

    return MaintenanceResult(
        vehicle_id=inp.vehicle_id,
        urgency_score=score,
        band=band,
        window_days=window_days,
        recommended_services=services,
        fault_severity_breakdown=fault_breakdown,
        source="J1939 SPN severity table (industry consensus) + PM mileage thresholds",
        generated_at=_utcnow_iso(),
    )


# =============================================================================
# Module ship-status registry — single source of truth for what's real today
# =============================================================================

MODULE_STATUS = {
    "M1": "shipping_pilot_phase",   # deterministic MVP; LLM coaching layer in Pilot
    "M2": "shipping_partial",        # route+stops live (OSRM/OSM); fuel MILP pending
    "M3": "shipping_partial",        # HOS check live; full audit-pack PDF pending
    "M4": "shipping_full",           # rate-floor guard + audit chain LIVE
    "M5": "shipping_pilot_phase",    # deterministic MVP; survival analysis + LLM coaching in Pilot
    "M6": "shipping_pilot_phase",    # deterministic MVP; J1939 live ingest + anomaly detection in Pilot
}

MODULE_STATUS_LABEL = {
    "shipping_full": ("● LIVE", "#ccff00", "Production · audit-cleared"),
    "shipping_partial": ("◐ LIVE · PARTIAL", "#00ffff", "Core endpoint live; advanced features in next iteration"),
    "shipping_pilot_phase": ("◐ PILOT-PHASE", "#ffce4f", "Deterministic MVP ships today; LLM/ingest layer activates in Pilot"),
    "not_built": ("○ ROADMAP", "rgba(255,255,255,0.45)", "Targeted for Phase 4 (Scale)"),
}
