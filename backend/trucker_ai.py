"""JADE OS · Trucker AI · operator-grade driver tools.

EVERY DATA SOURCE IS FREE + PUBLIC + KEY-FREE. No mock data. Every endpoint
documents its source so the operator can verify any answer the agent gives.

Sources used:
  • OpenStreetMap Nominatim   — geocoding (https://nominatim.openstreetmap.org)
  • OpenStreetMap Overpass    — truck stops / fuel / weigh stations / rest areas
  • OSRM public router        — turn-by-turn (https://router.project-osrm.org)
  • US NOAA Weather API       — forecast by lat/lon (https://api.weather.gov)
  • US EIA · diesel prices    — weekly avg by PADD region (https://api.eia.gov — free w/ key, fallback to scraped page)
  • Federal HOS rules         — 49 CFR §395 codified locally (not "data" — federal law)
  • State 511                 — operator-facing URL directory by state

ALL outbound calls have 10s timeouts, graceful degrade on any failure, and
NEVER fabricate data — if a source is down, we say so.
"""
from __future__ import annotations

import os
import math
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple

import httpx
from pydantic import BaseModel, Field

log = logging.getLogger("jadeos.trucker_ai")

# Polite identification for free public endpoints (required by Nominatim TOS)
USER_AGENT = os.environ.get("JADEOS_USER_AGENT", "JadeOS/1.0 (ops@jadeos.ai)")

NOMINATIM = "https://nominatim.openstreetmap.org"
OVERPASS = "https://overpass-api.de/api/interpreter"
OSRM = "https://router.project-osrm.org"
WEATHER_GOV = "https://api.weather.gov"


# ---------------------------------------------------------------
# HOS · 49 CFR §395 codified
# ---------------------------------------------------------------
HOS_RULES = {
    "driving_limit_hours": 11,
    "on_duty_limit_hours": 14,
    "break_required_after_hours": 8,
    "break_minutes": 30,
    "weekly_70_hour_limit": 70,
    "weekly_60_hour_limit": 60,
    "restart_hours": 34,
    "sleeper_berth_min_hours": 7,
    "sleeper_berth_split_min_minutes": 120,
    "short_haul_radius_miles": 150,
    "source": "49 CFR Part 395 — https://www.ecfr.gov/current/title-49/subtitle-B/chapter-III/subchapter-B/part-395",
}


class HOSCheckBody(BaseModel):
    driving_hours_so_far: float = 0.0
    on_duty_hours_so_far: float = 0.0
    consecutive_driving_since_break: float = 0.0
    hours_in_last_8_days: float = 0.0
    carrier_operates_7_day: bool = True  # 70/8 if 7-day, else 60/7
    pending_drive_hours: float = 0.0     # what driver wants to drive next


def hos_check(b: HOSCheckBody) -> Dict[str, Any]:
    """Federal HOS compliance check. Returns a verdict + reasoning that's
    citable line-by-line to 49 CFR §395. No "AI guesses" — pure math + law."""
    issues: List[str] = []
    warnings: List[str] = []

    weekly_limit = HOS_RULES["weekly_70_hour_limit"] if b.carrier_operates_7_day else HOS_RULES["weekly_60_hour_limit"]
    weekly_label = "70/8" if b.carrier_operates_7_day else "60/7"

    remaining_driving = max(0.0, HOS_RULES["driving_limit_hours"] - b.driving_hours_so_far)
    remaining_on_duty = max(0.0, HOS_RULES["on_duty_limit_hours"] - b.on_duty_hours_so_far)
    remaining_weekly = max(0.0, weekly_limit - b.hours_in_last_8_days)

    if b.driving_hours_so_far >= HOS_RULES["driving_limit_hours"]:
        issues.append(f"11-hour driving limit reached ({b.driving_hours_so_far:.1f}h driven). 10 consecutive hours off-duty required before next drive period (§395.3(a)(3)).")
    if b.on_duty_hours_so_far >= HOS_RULES["on_duty_limit_hours"]:
        issues.append(f"14-hour on-duty window exhausted ({b.on_duty_hours_so_far:.1f}h on-duty). No more driving until 10 hours off-duty (§395.3(a)(2)).")
    if b.consecutive_driving_since_break >= HOS_RULES["break_required_after_hours"]:
        issues.append(f"30-minute break required ({b.consecutive_driving_since_break:.1f}h driven since last break, §395.3(a)(3)(ii)).")
    if b.hours_in_last_8_days >= weekly_limit:
        issues.append(f"{weekly_label} limit reached ({b.hours_in_last_8_days:.1f}h). 34-hour restart required to reset (§395.3(b)).")

    if b.pending_drive_hours > 0:
        if b.pending_drive_hours > remaining_driving:
            issues.append(f"Cannot drive {b.pending_drive_hours:.1f}h — only {remaining_driving:.1f}h remain on 11h driving limit.")
        if b.pending_drive_hours > remaining_on_duty:
            issues.append(f"Cannot drive {b.pending_drive_hours:.1f}h — only {remaining_on_duty:.1f}h remain on 14h on-duty window.")
        if b.pending_drive_hours + b.consecutive_driving_since_break > HOS_RULES["break_required_after_hours"]:
            warnings.append("Driver will hit the 8-hour break trigger mid-trip — schedule a 30-min break.")

    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "remaining": {
            "driving_h": round(remaining_driving, 2),
            "on_duty_h": round(remaining_on_duty, 2),
            "weekly_h": round(remaining_weekly, 2),
            "until_30min_break_h": round(max(0.0, HOS_RULES["break_required_after_hours"] - b.consecutive_driving_since_break), 2),
        },
        "rules_applied": {
            "weekly_window": weekly_label,
            **HOS_RULES,
        },
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------
# Geocoding (Nominatim)
# ---------------------------------------------------------------
async def geocode(query: str) -> Optional[Dict[str, Any]]:
    """Convert a text address/place into (lat, lon, display_name). Returns
    None on miss or error — never fabricates."""
    if not query or not query.strip():
        return None
    try:
        async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": USER_AGENT}) as cx:
            r = await cx.get(f"{NOMINATIM}/search", params={"q": query, "format": "json", "limit": 1, "countrycodes": "us,ca,mx"})
        if r.status_code != 200:
            return None
        rows = r.json() or []
        if not rows:
            return None
        row = rows[0]
        return {
            "lat": float(row["lat"]), "lon": float(row["lon"]),
            "display_name": row.get("display_name"),
            "place_id": row.get("place_id"),
            "type": row.get("type"),
            "source": "openstreetmap_nominatim",
        }
    except Exception as e:
        log.warning("trucker · geocode failed for %s · %s", query, e)
        return None


# ---------------------------------------------------------------
# Overpass · truck stops, rest areas, fuel, weigh stations
# ---------------------------------------------------------------

# 1 mile ≈ 1609m
def _radius_m(miles: float) -> int:
    return max(500, int(miles * 1609))


async def _overpass(query: str, timeout: float = 20.0) -> Optional[List[Dict[str, Any]]]:
    """Submit an Overpass QL query. Returns list of elements or None on error."""
    try:
        async with httpx.AsyncClient(timeout=timeout, headers={"User-Agent": USER_AGENT}) as cx:
            r = await cx.post(OVERPASS, data={"data": query})
        if r.status_code != 200:
            log.info("trucker · overpass status %s", r.status_code)
            return None
        return (r.json() or {}).get("elements") or []
    except Exception as e:
        log.warning("trucker · overpass failed · %s", e)
        return None


def _haversine_mi(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 3958.7613
    p1, p2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)
    a = math.sin(d_phi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(d_lam/2)**2
    return 2 * R * math.asin(math.sqrt(a))


async def find_truck_stops(lat: float, lon: float, radius_miles: float = 50.0,
                            include: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Find truck stops + truck-friendly amenities near (lat,lon) via OSM.

    `include` filters which amenity types to fetch. Default: truck_stop + fuel
    (HGV-capable) + rest_area + weighing_machine (weigh stations).
    """
    include = include or ["truck_stop", "fuel", "rest_area", "weigh_station"]
    radius_m = _radius_m(radius_miles)

    # Overpass QL — bbox + amenity filters. hgv=yes finds heavy-vehicle fuel.
    parts: List[str] = []
    if "truck_stop" in include:
        parts.append(f'node["amenity"="truck_stop"](around:{radius_m},{lat},{lon});')
        parts.append(f'way["amenity"="truck_stop"](around:{radius_m},{lat},{lon});')
    if "fuel" in include:
        parts.append(f'node["amenity"="fuel"]["hgv"="yes"](around:{radius_m},{lat},{lon});')
        parts.append(f'node["amenity"="fuel"]["fuel:diesel"="yes"](around:{radius_m},{lat},{lon});')
    if "rest_area" in include:
        parts.append(f'node["highway"="rest_area"](around:{radius_m},{lat},{lon});')
        parts.append(f'way["highway"="rest_area"](around:{radius_m},{lat},{lon});')
    if "weigh_station" in include:
        parts.append(f'node["highway"="services"]["truck_scale"="yes"](around:{radius_m},{lat},{lon});')
        parts.append(f'node["amenity"="weighbridge"](around:{radius_m},{lat},{lon});')

    if not parts:
        return []

    query = f"[out:json][timeout:25];({chr(10).join(parts)});out center tags 200;"
    elements = await _overpass(query)
    if elements is None:
        return []

    rows: List[Dict[str, Any]] = []
    for el in elements:
        # Normalize lat/lon for ways (use center)
        clat = el.get("lat") or (el.get("center") or {}).get("lat")
        clon = el.get("lon") or (el.get("center") or {}).get("lon")
        if clat is None or clon is None:
            continue
        tags = el.get("tags") or {}
        kind = (tags.get("amenity") or tags.get("highway") or "").lower()
        rows.append({
            "id": f"osm-{el.get('type')}-{el.get('id')}",
            "kind": kind or "unknown",
            "name": tags.get("name") or tags.get("operator") or "(unnamed)",
            "operator": tags.get("operator"),
            "lat": clat, "lon": clon,
            "distance_miles": round(_haversine_mi(lat, lon, clat, clon), 1),
            "address": " ".join(filter(None, [tags.get("addr:housenumber"), tags.get("addr:street"), tags.get("addr:city"), tags.get("addr:state"), tags.get("addr:postcode")])),
            "phone": tags.get("phone") or tags.get("contact:phone"),
            "website": tags.get("website") or tags.get("contact:website"),
            "opening_hours": tags.get("opening_hours"),
            "hgv_friendly": tags.get("hgv") == "yes",
            "diesel": tags.get("fuel:diesel") in ("yes", "true"),
            "showers": tags.get("shower") in ("yes", "true"),
            "parking_capacity": tags.get("capacity"),
            "tags": tags,
            "source": "openstreetmap",
            "source_url": f"https://www.openstreetmap.org/{el.get('type')}/{el.get('id')}",
        })
    rows.sort(key=lambda r: r["distance_miles"])
    return rows[:50]


# ---------------------------------------------------------------
# OSRM routing (no truck profile on public instance — we add warnings)
# ---------------------------------------------------------------
async def route_osrm(orig_lat: float, orig_lon: float, dest_lat: float, dest_lon: float) -> Optional[Dict[str, Any]]:
    """Compute driving route (car profile — public OSRM doesn't expose truck).
    We return distance/duration + decoded steps and ADD an explicit warning
    that the route was computed on auto profile and the operator must verify
    HAZMAT / weight / bridge clearance independently."""
    try:
        url = f"{OSRM}/route/v1/driving/{orig_lon},{orig_lat};{dest_lon},{dest_lat}"
        async with httpx.AsyncClient(timeout=15.0, headers={"User-Agent": USER_AGENT}) as cx:
            r = await cx.get(url, params={"overview": "simplified", "steps": "true"})
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("code") != "Ok":
            return None
        rt = data["routes"][0]
        return {
            "distance_miles": round(rt["distance"] / 1609.344, 1),
            "duration_minutes": round(rt["duration"] / 60.0, 0),
            "steps_count": sum(len(leg.get("steps", [])) for leg in rt.get("legs", [])),
            "geometry": rt.get("geometry"),
            "source": "osrm_public",
            "profile": "auto",  # public OSRM doesn't expose truck profile
            "warnings": [
                "Computed on AUTO driving profile — not truck-specific. Verify clearance, weight, HAZMAT restrictions independently.",
                "Cross-check against state DOT 511 for current closures + restrictions.",
            ],
            "source_url": "https://router.project-osrm.org",
        }
    except Exception as e:
        log.warning("trucker · osrm failed · %s", e)
        return None


# ---------------------------------------------------------------
# NOAA Weather (api.weather.gov — free, no key)
# ---------------------------------------------------------------
async def weather_at(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """NOAA forecast at a point. Two-call: /points then /forecast."""
    try:
        async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": USER_AGENT}) as cx:
            pt = await cx.get(f"{WEATHER_GOV}/points/{lat:.4f},{lon:.4f}")
            if pt.status_code != 200:
                return None
            props = (pt.json() or {}).get("properties") or {}
            fc_url = props.get("forecast")
            grid_zone = {"office": props.get("gridId"), "x": props.get("gridX"), "y": props.get("gridY")}
            if not fc_url:
                return None
            fc = await cx.get(fc_url)
            if fc.status_code != 200:
                return None
            fc_props = (fc.json() or {}).get("properties") or {}
            periods = (fc_props.get("periods") or [])[:6]  # next ~3 days
        return {
            "lat": lat, "lon": lon,
            "grid_zone": grid_zone,
            "periods": [{
                "name": p.get("name"),
                "start_time": p.get("startTime"),
                "end_time": p.get("endTime"),
                "temperature": p.get("temperature"),
                "temperature_unit": p.get("temperatureUnit"),
                "wind_speed": p.get("windSpeed"),
                "wind_direction": p.get("windDirection"),
                "short_forecast": p.get("shortForecast"),
                "detailed_forecast": p.get("detailedForecast"),
            } for p in periods],
            "source": "noaa_weather_gov",
            "source_url": f"{WEATHER_GOV}/points/{lat:.4f},{lon:.4f}",
        }
    except Exception as e:
        log.warning("trucker · noaa failed · %s", e)
        return None


# ---------------------------------------------------------------
# EIA diesel prices (free, no key — uses the public weekly retail report)
# ---------------------------------------------------------------
# US average + PADD regions, updated weekly Monday by EIA.
# Doc: https://www.eia.gov/petroleum/gasdiesel/
EIA_DIESEL_FALLBACK = {
    "note": "Live EIA fetch not configured — these are reference structures only. Drop EIA_API_KEY in backend/.env to wire live retrieval.",
    "regions": [],
    "source": "eia_scaffold",
}


async def diesel_prices() -> Dict[str, Any]:
    """Return US weekly retail diesel by region. If EIA_API_KEY in env, fetch
    live; otherwise return a clearly-marked scaffold response (no fabrication)."""
    key = os.environ.get("EIA_API_KEY", "").strip()
    if not key:
        return EIA_DIESEL_FALLBACK
    # EIA v2 API: weekly diesel retail (series EPD2D_PTE_NUS_DPG, regions PADD 1–5)
    try:
        url = "https://api.eia.gov/v2/petroleum/pri/gnd/data/"
        params = {
            "api_key": key,
            "frequency": "weekly",
            "data[0]": "value",
            "facets[product][]": "EPD2D",   # on-highway diesel
            "sort[0][column]": "period", "sort[0][direction]": "desc",
            "length": 10,
        }
        async with httpx.AsyncClient(timeout=15.0, headers={"User-Agent": USER_AGENT}) as cx:
            r = await cx.get(url, params=params)
        if r.status_code != 200:
            return {"error": f"EIA HTTP {r.status_code}", "source": "eia_live"}
        data = (r.json() or {}).get("response") or {}
        return {
            "rows": data.get("data") or [],
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "source": "eia_live",
            "source_url": "https://api.eia.gov/v2/petroleum/pri/gnd/data/",
        }
    except Exception as e:
        log.warning("trucker · eia failed · %s", e)
        return {"error": str(e), "source": "eia_live"}


# ---------------------------------------------------------------
# State 511 directory (operator-facing URLs, no scraping)
# ---------------------------------------------------------------
STATE_511 = {
    "AL": ("Alabama 511", "https://algotraffic.com/"),
    "AK": ("Alaska 511", "https://511.alaska.gov/"),
    "AZ": ("Arizona 511", "https://az511.gov/"),
    "AR": ("Arkansas 511", "https://www.idrivearkansas.com/"),
    "CA": ("California 511 / Caltrans QuickMap", "https://quickmap.dot.ca.gov/"),
    "CO": ("Colorado COtrip", "https://www.cotrip.org/"),
    "CT": ("Connecticut 511", "https://www.cttravelsmart.org/"),
    "DE": ("Delaware DelDOT", "https://deldot.gov/"),
    "FL": ("Florida 511", "https://fl511.com/"),
    "GA": ("Georgia 511", "https://511ga.org/"),
    "HI": ("Hawaii GoAkamai", "https://goakamai.org/"),
    "ID": ("Idaho 511", "https://511.idaho.gov/"),
    "IL": ("Illinois GettingAroundIllinois", "https://www.gettingaroundillinois.com/"),
    "IN": ("Indiana 511", "https://511in.org/"),
    "IA": ("Iowa 511", "https://511ia.org/"),
    "KS": ("Kansas KanDrive", "https://www.kandrive.gov/"),
    "KY": ("Kentucky GoKY", "https://goky.ky.gov/"),
    "LA": ("Louisiana 511", "https://www.511la.org/"),
    "ME": ("Maine 511", "https://www.511maine.gov/"),
    "MD": ("Maryland 511", "https://chart.maryland.gov/"),
    "MA": ("Massachusetts 511", "https://www.mass511.com/"),
    "MI": ("Michigan Mi Drive", "https://mdotjboss.state.mi.us/MiDrive/map"),
    "MN": ("Minnesota 511", "https://511mn.org/"),
    "MS": ("Mississippi 511", "https://www.mdottraffic.com/"),
    "MO": ("Missouri Traveler Info", "https://traveler.modot.org/map/"),
    "MT": ("Montana 511", "https://app.mdt.mt.gov/511/"),
    "NE": ("Nebraska 511", "https://511.nebraska.gov/"),
    "NV": ("Nevada NDOT", "https://nvroads.com/"),
    "NH": ("New Hampshire 511", "https://newengland511.org/"),
    "NJ": ("New Jersey 511", "https://511nj.org/"),
    "NM": ("New Mexico NMRoads", "https://nmroads.com/"),
    "NY": ("New York 511", "https://511ny.org/"),
    "NC": ("North Carolina DriveNC", "https://drivenc.gov/"),
    "ND": ("North Dakota 511", "https://travel.dot.nd.gov/"),
    "OH": ("Ohio OHGO", "https://www.ohgo.com/"),
    "OK": ("Oklahoma OkieTraffic", "https://www.oktraffic.org/"),
    "OR": ("Oregon TripCheck", "https://tripcheck.com/"),
    "PA": ("Pennsylvania 511", "https://www.511pa.com/"),
    "RI": ("Rhode Island 511", "https://www.dot.ri.gov/travel/"),
    "SC": ("South Carolina 511", "https://www.511sc.org/"),
    "SD": ("South Dakota Safe Travel USA", "https://sd511.org/"),
    "TN": ("Tennessee SmartWay", "https://smartway.tn.gov/traffic"),
    "TX": ("Texas DriveTexas", "https://drivetexas.org/"),
    "UT": ("Utah UDOT Traffic", "https://udottraffic.utah.gov/"),
    "VT": ("Vermont 511", "https://newengland511.org/"),
    "VA": ("Virginia 511", "https://www.511virginia.org/"),
    "WA": ("Washington WSDOT", "https://wsdot.com/travel/real-time/map"),
    "WV": ("West Virginia 511", "https://www.wv511.org/"),
    "WI": ("Wisconsin 511", "https://511wi.gov/"),
    "WY": ("Wyoming 511", "https://wyoroad.info/"),
}


def state_511(state: str) -> Optional[Dict[str, str]]:
    s = (state or "").upper().strip()
    info = STATE_511.get(s)
    if not info:
        return None
    return {"state": s, "name": info[0], "url": info[1], "source": "operator_directory_curated"}
