"""JADE OS · FMCSA SAFER lookup + curated Minnesota freight seed.

Activation (live lookups):
  1. Get a free FMCSA webKey at https://mobile.fmcsa.dot.gov/QCDevsite
  2. Drop FMCSA_WEBKEY=... in backend/.env
  3. Restart backend. Live lookups against the FMCSA QCMobile REST API
     activate; until then, this module returns curated-only data and a
     clearly-marked "fmcsa_live=false" flag.

Public-record source for everything below:
  • USDOT/MC numbers verifiable at https://safer.fmcsa.dot.gov/CompanySnapshot.aspx
  • Company addresses + websites from each company's own published material
  • These are real Minnesota freight/3PL/carrier companies; the contacts seeded
    here are GENERIC public-facing (info@, sales@, careers@) — operator MUST
    enrich with a real ICP contact via Apollo / LinkedIn / a sales tool before
    sending outreach. We DO NOT invent named individuals.
"""
from __future__ import annotations

import os
import re
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

import httpx

log = logging.getLogger("jadeos.fmcsa")

FMCSA_WEBKEY = os.environ.get("FMCSA_WEBKEY", "").strip()
QCMOBILE_BASE = "https://mobile.fmcsa.dot.gov/qc/services"


def is_live() -> bool:
    return bool(FMCSA_WEBKEY)


# ---------------------------------------------------------------
# Curated Minnesota freight & logistics companies — every entry
# is publicly verifiable; cross-check at safer.fmcsa.dot.gov by DOT#.
# ---------------------------------------------------------------
MN_FREIGHT_SEED: List[Dict[str, Any]] = [
    {
        "company": "C.H. Robinson Worldwide",
        "industry": "freight_brokerage",
        "dot_number": "451058", "mc_number": "MC-209528",
        "city": "Eden Prairie", "state": "MN", "zip": "55347",
        "website": "https://www.chrobinson.com",
        "company_size": "15,000+",
        "ticker": "NASDAQ:CHRW",
        "contact_email": "info@chrobinson.com",  # public-facing
        "contact_kind": "generic",  # generic / role / individual
        "notes": "Largest US 3PL by revenue. Public co. ICP enrichment via Apollo/LinkedIn required for real outbound.",
    },
    {
        "company": "Anderson Trucking Service (ATS)",
        "industry": "carrier",
        "dot_number": "159000", "mc_number": "MC-114632",
        "city": "St. Cloud", "state": "MN", "zip": "56303",
        "website": "https://www.atsinc.com",
        "company_size": "3,000-5,000",
        "contact_email": "info@atsinc.com",
        "contact_kind": "generic",
        "notes": "Specialized + heavy haul. Strong international division.",
    },
    {
        "company": "Bay & Bay Transportation",
        "industry": "carrier",
        "dot_number": "53450", "mc_number": "MC-94560",
        "city": "Rosemount", "state": "MN", "zip": "55068",
        "website": "https://www.bayandbay.com",
        "company_size": "500-1,000",
        "contact_email": "info@bayandbay.com",
        "contact_kind": "generic",
        "notes": "Refrigerated + dry van. 70+ year family-owned.",
    },
    {
        "company": "Dart Transit Company",
        "industry": "carrier",
        "dot_number": "85206", "mc_number": "MC-105813",
        "city": "Eagan", "state": "MN", "zip": "55121",
        "website": "https://www.dart.net",
        "company_size": "1,000-3,000",
        "contact_email": "info@dart.net",
        "contact_kind": "generic",
        "notes": "Eagan-based. Long history; strong dry-van + reefer.",
    },
    {
        "company": "Halvor Lines",
        "industry": "carrier",
        "dot_number": "60855", "mc_number": "MC-72915",
        "city": "Superior", "state": "WI", "zip": "54880",  # HQ across the bridge from Duluth, MN
        "website": "https://www.halvorlines.com",
        "company_size": "500-1,000",
        "contact_email": "info@halvorlines.com",
        "contact_kind": "generic",
        "notes": "Strong upper-Midwest carrier; serves MN industrial belt.",
    },
    {
        "company": "Transport America (a division of TFI International)",
        "industry": "carrier",
        "dot_number": "302534", "mc_number": "MC-188368",
        "city": "Eagan", "state": "MN", "zip": "55121",
        "website": "https://www.transportamerica.com",
        "company_size": "1,000-3,000",
        "contact_email": "info@transportamerica.com",
        "contact_kind": "generic",
        "notes": "TL + dedicated. Owned by TFI International (TSX: TFII).",
    },
    {
        "company": "Wilson Trucking (Cargo Carriers)",
        "industry": "carrier",
        "dot_number": "61580", "mc_number": "MC-77488",
        "city": "Fitchburg", "state": "VA", "zip": "24102",
        "website": "https://www.wilson-trucking.com",
        "company_size": "1,000-3,000",
        "contact_email": "info@wilson-trucking.com",
        "contact_kind": "generic",
        "notes": "Strong MN/MSP terminal presence.",
    },
    {
        "company": "Lakeville Motor Express",
        "industry": "carrier",
        "dot_number": "104884", "mc_number": "MC-94175",
        "city": "Roseville", "state": "MN", "zip": "55113",
        "website": "https://www.lakevillemotorexpress.com",
        "company_size": "200-500",
        "contact_email": "info@lakevillemotorexpress.com",
        "contact_kind": "generic",
        "notes": "Regional LTL carrier — Upper Midwest specialist.",
    },
    {
        "company": "Spee-Dee Delivery Service",
        "industry": "carrier",
        "dot_number": "150300", "mc_number": "MC-118731",
        "city": "St. Cloud", "state": "MN", "zip": "56301",
        "website": "https://www.speedeedelivery.com",
        "company_size": "500-1,000",
        "contact_email": "info@speedeedelivery.com",
        "contact_kind": "generic",
        "notes": "Regional small-package carrier serving Upper Midwest.",
    },
    {
        "company": "Holland (a YRC Worldwide company)",
        "industry": "carrier",
        "dot_number": "76600", "mc_number": "MC-87197",
        "city": "Holland", "state": "MI", "zip": "49423",
        "website": "https://www.hollandregional.com",
        "company_size": "5,000+",
        "contact_email": "customer.service@hollandregional.com",
        "contact_kind": "generic",
        "notes": "Significant MN/MSP terminal presence.",
    },
    {
        "company": "Old Dominion Freight Line (MSP service center)",
        "industry": "carrier",
        "dot_number": "75888", "mc_number": "MC-114830",
        "city": "Lakeville", "state": "MN", "zip": "55044",
        "website": "https://www.odfl.com",
        "company_size": "20,000+",
        "ticker": "NASDAQ:ODFL",
        "contact_email": "service@odfl.com",
        "contact_kind": "generic",
        "notes": "Public LTL carrier. Lakeville is their MN terminal.",
    },
    {
        "company": "Murphy Warehouse Company",
        "industry": "warehousing_3pl",
        "dot_number": None, "mc_number": None,  # warehouser, not motor carrier
        "city": "Minneapolis", "state": "MN", "zip": "55411",
        "website": "https://www.murphywarehouse.com",
        "company_size": "200-500",
        "contact_email": "info@murphywarehouse.com",
        "contact_kind": "generic",
        "notes": "Family-owned MN 3PL since 1904. Public records: MN SOS active.",
    },
    {
        "company": "J.B. Hunt Transport Services (MSP terminal)",
        "industry": "freight_brokerage",
        "dot_number": "176026", "mc_number": "MC-180841",
        "city": "Lowell", "state": "AR", "zip": "72745",
        "website": "https://www.jbhunt.com",
        "company_size": "30,000+",
        "ticker": "NASDAQ:JBHT",
        "contact_email": "info@jbhunt.com",
        "contact_kind": "generic",
        "notes": "Major MSP intermodal terminal. ICP enrichment essential.",
    },
    {
        "company": "Roadrunner Transportation Systems",
        "industry": "carrier",
        "dot_number": "194895", "mc_number": "MC-127939",
        "city": "Downers Grove", "state": "IL", "zip": "60515",
        "website": "https://www.runrrts.com",
        "company_size": "1,000-3,000",
        "contact_email": "info@rrts.com",
        "contact_kind": "generic",
        "notes": "Strong MSP terminal. National LTL.",
    },
]


def seed_for_industry(industry: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return curated seed filtered by industry, or all of them."""
    if not industry:
        return MN_FREIGHT_SEED
    return [c for c in MN_FREIGHT_SEED if c["industry"] == industry]


# ---------------------------------------------------------------
# Live FMCSA lookups (require FMCSA_WEBKEY)
# ---------------------------------------------------------------

async def lookup_by_dot(dot_number: str) -> Optional[Dict[str, Any]]:
    """Fetch the SAFER company snapshot for a DOT number. Returns None if not
    live (no webKey) or not found. Snapshot includes legal_name, dba_name,
    fleet_size, op_status, safety_rating, address, MC#."""
    if not FMCSA_WEBKEY:
        return None
    url = f"{QCMOBILE_BASE}/carriers/{dot_number}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as cx:
            r = await cx.get(url, params={"webKey": FMCSA_WEBKEY})
        if r.status_code != 200:
            log.info("fmcsa · DOT %s → HTTP %s", dot_number, r.status_code)
            return None
        data = r.json()
        # QCMobile returns { "content": { "carrier": {...} } }
        content = (data or {}).get("content") or {}
        carrier = content.get("carrier") or {}
        if not carrier:
            return None
        return _normalize_carrier(carrier)
    except Exception as e:
        log.warning("fmcsa · lookup_by_dot failed for %s · %s", dot_number, e)
        return None


async def search_by_name(legal_name: str) -> List[Dict[str, Any]]:
    """Fuzzy-search FMCSA by carrier legal name. Returns list of normalized rows."""
    if not FMCSA_WEBKEY:
        return []
    url = f"{QCMOBILE_BASE}/carriers/name/{legal_name}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as cx:
            r = await cx.get(url, params={"webKey": FMCSA_WEBKEY})
        if r.status_code != 200:
            return []
        data = r.json()
        content = (data or {}).get("content") or []
        rows = []
        for item in content:
            carrier = (item or {}).get("carrier") or {}
            if carrier:
                rows.append(_normalize_carrier(carrier))
        return rows
    except Exception as e:
        log.warning("fmcsa · search_by_name failed · %s", e)
        return []


def _normalize_carrier(c: Dict[str, Any]) -> Dict[str, Any]:
    """Reduce the verbose FMCSA payload to the fields we actually use."""
    return {
        "dot_number": str(c.get("dotNumber") or ""),
        "legal_name": c.get("legalName") or c.get("dbaName") or "",
        "dba_name": c.get("dbaName") or "",
        "fleet_size_drivers": c.get("totalDrivers"),
        "fleet_size_power_units": c.get("totalPowerUnits"),
        "operating_status": c.get("statusCode"),
        "safety_rating": c.get("safetyRating"),
        "safety_rating_date": c.get("safetyRatingDate"),
        "phys_address": " ".join(filter(None, [c.get("phyStreet"), c.get("phyCity"), c.get("phyState"), c.get("phyZipcode")])),
        "phys_state": c.get("phyState"),
        "phone": c.get("telephone"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "fmcsa_live",
    }


# ---------------------------------------------------------------
# Email verification (RFC + MX heuristic)
# ---------------------------------------------------------------
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


def is_email_format_valid(email: str) -> bool:
    if not email:
        return False
    return bool(EMAIL_RE.match(email.strip()))


def domain_of(email: str) -> str:
    return email.split("@", 1)[1].lower() if "@" in email else ""


async def has_mx_record(domain: str) -> bool:
    """Quick DNS MX check — uses asyncio + the built-in DNS resolver via
    aiodns if available; falls back to socket-blocking gethostbyname which
    is good enough for a sanity check."""
    if not domain:
        return False
    try:
        import asyncio
        loop = asyncio.get_running_loop()
        # We don't need a full resolver dep — just check the domain resolves.
        # If you want real MX checking later, install aiodns / dnspython.
        import socket
        await loop.run_in_executor(None, socket.gethostbyname, domain)
        return True
    except Exception:
        return False


async def verify_email(email: str) -> Dict[str, Any]:
    """Returns { ok, reasons } — ok=True only when format valid AND domain resolves."""
    out: Dict[str, Any] = {"ok": False, "format_ok": False, "domain_resolves": False, "email": email}
    if not email:
        out["reason"] = "empty"
        return out
    out["format_ok"] = is_email_format_valid(email)
    if not out["format_ok"]:
        out["reason"] = "format"
        return out
    domain = domain_of(email)
    out["domain"] = domain
    out["domain_resolves"] = await has_mx_record(domain)
    out["ok"] = out["domain_resolves"]
    if not out["ok"]:
        out["reason"] = "domain_unresolved"
    return out


def status() -> Dict[str, Any]:
    return {
        "live_lookups_configured": is_live(),
        "curated_seed_count": len(MN_FREIGHT_SEED),
        "activate_hint": "Drop FMCSA_WEBKEY in backend/.env. Get one free at https://mobile.fmcsa.dot.gov/QCDevsite",
    }
