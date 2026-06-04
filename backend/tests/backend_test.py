"""JADE OS backend pytest suite.

Covers:
- Health /api/
- Auth: login + me
- Leads: create (public), list (admin), patch
- Agents: chat (SSE), extract (healthcare/saas/manufacturing), extract-bol alias,
  draft-outreach (healthcare/freight), qualify-lead, support-triage
- Admin: stats, agent-runs
"""
import json
import os
import re
import time

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    # Fallback - read from frontend .env
    from pathlib import Path
    env_p = Path("/app/frontend/.env").read_text()
    for line in env_p.splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip().strip('"')
            break

BASE_URL = (BASE_URL or "").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@jadeos.ai"
ADMIN_PASSWORD = "JadeOS!2026"

LLM_TIMEOUT = 90


# --------- Fixtures ---------
@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def admin_token(session):
    r = session.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    tok = r.json()["access_token"]
    assert isinstance(tok, str) and len(tok) > 20
    return tok


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# --------- Health ---------
def test_root_health(session):
    r = session.get(f"{API}/", timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert body.get("service") == "JADE OS API"
    assert body.get("status") == "online"
    assert "ts" in body


# --------- Auth ---------
def test_login_invalid(session):
    r = session.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong"}, timeout=15)
    assert r.status_code == 401


def test_me_without_token(session):
    r = session.get(f"{API}/auth/me", timeout=15)
    assert r.status_code == 401


def test_me_with_token(session, admin_headers):
    r = session.get(f"{API}/auth/me", headers=admin_headers, timeout=15)
    assert r.status_code == 200
    assert r.json().get("email") == ADMIN_EMAIL


# --------- Leads ---------
VERTICALS = [
    "freight_brokerage", "healthcare", "saas", "manufacturing", "ecommerce",
    "insurance", "legal", "real_estate", "professional_services", "logistics", "general"
]


@pytest.mark.parametrize("vertical", VERTICALS)
def test_create_lead_public(session, vertical):
    payload = {
        "name": "TEST_Operator",
        "email": f"test_{vertical}@example.com",
        "company": f"TEST_{vertical}_co",
        "vertical": vertical,
        "use_case": "auto-test",
    }
    r = session.post(f"{API}/leads", json=payload, timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["vertical"] == vertical
    assert data["status"] == "new"
    assert data["email"] == payload["email"]
    assert "id" in data and len(data["id"]) > 10


def test_list_leads_requires_auth(session):
    r = session.get(f"{API}/leads", timeout=15)
    assert r.status_code == 401


def test_list_leads_sorted(session, admin_headers):
    r = session.get(f"{API}/leads", headers=admin_headers, timeout=20)
    assert r.status_code == 200
    leads = r.json()
    assert isinstance(leads, list) and len(leads) >= 1
    # newest first - created_at ISO sortable lex
    timestamps = [l["created_at"] for l in leads]
    assert timestamps == sorted(timestamps, reverse=True)


def test_patch_lead_status(session, admin_headers):
    # create new
    r = session.post(f"{API}/leads", json={
        "name": "TEST_patch", "email": "test_patch@example.com",
        "company": "TEST_PatchCo", "vertical": "general"
    }, timeout=15)
    lead_id = r.json()["id"]
    # patch
    r2 = session.patch(f"{API}/leads/{lead_id}?status_value=contacted", headers=admin_headers, timeout=15)
    assert r2.status_code == 200
    assert r2.json().get("ok") is True
    # verify
    r3 = session.get(f"{API}/leads", headers=admin_headers, timeout=20)
    found = [l for l in r3.json() if l["id"] == lead_id]
    assert found and found[0]["status"] == "contacted"


# --------- Agent: chat (SSE) ---------
def _consume_sse(url, payload):
    deltas, done, error = [], False, None
    with requests.post(url, json=payload, stream=True, timeout=LLM_TIMEOUT) as resp:
        assert resp.status_code == 200, resp.text
        for raw in resp.iter_lines(decode_unicode=True):
            if not raw or not raw.startswith("data:"):
                continue
            chunk = raw[len("data:"):].strip()
            try:
                evt = json.loads(chunk)
            except Exception:
                continue
            if "delta" in evt:
                deltas.append(evt["delta"])
            elif evt.get("done"):
                done = True
                break
            elif "error" in evt:
                error = evt["error"]
                break
    return "".join(deltas), done, error


def test_agent_chat_healthcare_sse():
    text, done, err = _consume_sse(f"{API}/agent/chat", {
        "session_id": "test-hc-1",
        "message": "I have a patient intake backlog problem. What should I prioritize?",
        "industry": "healthcare",
    })
    assert err is None, f"stream error: {err}"
    assert done, "did not receive 'done' event"
    assert len(text) > 20
    # Lenient: should not be freight-centric
    lower = text.lower()
    assert "bol" not in lower and "lane" not in lower and "freight broker" not in lower


# --------- Agent: extract ---------
HEALTHCARE_INTAKE = (
    "Patient Intake — Name J. Sample DOB 1971-04-22 Insurer BlueCross MN Member 8842XXXX "
    "Visit 02/12 Dr. Patel Allina Clinic chest pain"
)
SAAS_ORDER = "Order Form Acme Inc. Enterprise 250 seats MRR $14250 24 months start 03/01"
MFG_PO = "PO #44218 Vendor Acme Steel Items 250x Bar Stock $4.20/ea Total $19550 Required 03/04"
BOL_FREIGHT = ("Bill of Lading Origin Minneapolis MN Dest Chicago IL Equipment Dry Van 53ft "
               "Weight 38000 lbs Pickup 02/12 Delivery 02/13 Rate $1850 MC#123456 Ref BOL-9981")


def _post_json(url, payload):
    r = requests.post(url, json=payload, timeout=LLM_TIMEOUT)
    assert r.status_code == 200, f"{url} -> {r.status_code} {r.text[:300]}"
    return r.json()


def test_extract_healthcare():
    data = _post_json(f"{API}/agent/extract", {"text": HEALTHCARE_INTAKE, "industry": "healthcare"})
    assert data["industry"] == "healthcare"
    ext = data["extracted"]
    assert isinstance(ext, dict)
    # lenient: at least one healthcare-relevant field present
    flat = json.dumps(ext).lower()
    keys = ["patient", "insurer", "member", "dob", "provider", "diagnosis"]
    assert any(k in flat for k in keys), f"no healthcare fields: {flat[:300]}"


def test_extract_saas():
    data = _post_json(f"{API}/agent/extract", {"text": SAAS_ORDER, "industry": "saas"})
    ext = data["extracted"]
    assert isinstance(ext, dict)
    flat = json.dumps(ext).lower()
    keys = ["plan", "seats", "mrr", "term", "account"]
    assert any(k in flat for k in keys), f"no saas fields: {flat[:300]}"


def test_extract_manufacturing():
    data = _post_json(f"{API}/agent/extract", {"text": MFG_PO, "industry": "manufacturing"})
    ext = data["extracted"]
    assert isinstance(ext, dict)
    flat = json.dumps(ext).lower()
    keys = ["po", "vendor", "item", "quant", "total"]
    assert any(k in flat for k in keys), f"no manufacturing fields: {flat[:300]}"


def test_extract_bol_backcompat():
    data = _post_json(f"{API}/agent/extract-bol", {"text": BOL_FREIGHT, "industry": "freight_brokerage"})
    ext = data["extracted"]
    assert isinstance(ext, dict)
    flat = json.dumps(ext).lower()
    keys = ["origin", "dest", "equipment", "weight", "rate", "mc", "reference"]
    assert any(k in flat for k in keys), f"no freight fields: {flat[:300]}"


# --------- Agent: draft-outreach ---------
def test_outreach_healthcare_tone():
    data = _post_json(f"{API}/agent/draft-outreach", {
        "summary": "Hospital system has long patient intake backlog and missed prior auths.",
        "recipient": "Director of Patient Access",
        "industry": "healthcare",
    })
    email = data["email"]
    assert isinstance(email, str) and email.lower().startswith("subject:")
    low = email.lower()
    assert "bol" not in low and "freight broker" not in low and "lane" not in low


def test_outreach_freight_tone():
    data = _post_json(f"{API}/agent/draft-outreach", {
        "summary": "Brokerage runs 60 reefer loads/wk MSP->Chicago, manual lane research.",
        "recipient": "Ops Manager",
        "industry": "freight_brokerage",
    })
    email = data["email"]
    assert isinstance(email, str) and email.lower().startswith("subject:")


# --------- Agent: qualify-lead ---------
def test_qualify_lead():
    data = _post_json(f"{API}/agent/qualify-lead", {
        "company": "Acme Brokerage",
        "role": "VP Ops",
        "use_case": "Automate carrier vetting and rate quoting",
        "monthly_volume": "1200 loads",
        "budget": "$5k-$15k/mo",
        "timeline": "Q1",
        "industry": "freight_brokerage",
    })
    res = data["result"]
    assert isinstance(res, dict)
    for k in ["score", "tier", "rationale", "next_action", "green_flags", "red_flags", "recommended_agent"]:
        assert k in res, f"missing key {k} in {list(res.keys())}"
    assert isinstance(res["score"], (int, float))
    assert res["tier"] in ("hot", "warm", "cold")
    assert res["recommended_agent"] in (
        "support", "sales_qual", "data_extraction", "ops_automation", "content_generation"
    )


# --------- Agent: support-triage ---------
def test_support_triage_ecommerce():
    data = _post_json(f"{API}/agent/support-triage", {
        "ticket": "I returned my package 14 days ago — UPS shows delivered to your warehouse but no refund. Order #88421.",
        "industry": "ecommerce",
    })
    res = data["result"]
    assert isinstance(res, dict)
    for k in ["category", "priority", "sentiment", "summary", "suggested_response", "escalate", "tags"]:
        assert k in res, f"missing key {k}"
    assert res["priority"] in ("p0", "p1", "p2", "p3")
    assert isinstance(res["escalate"], bool)
    assert isinstance(res["tags"], list)


def test_support_triage_legal():
    data = _post_json(f"{API}/agent/support-triage", {
        "ticket": "New client wants to file a wrongful termination claim against former employer, statute may be tight.",
        "industry": "legal",
    })
    res = data["result"]
    assert isinstance(res, dict)
    assert res.get("priority") in ("p0", "p1", "p2", "p3")
    assert "summary" in res


# --------- Admin: stats + runs ---------
def test_admin_stats(admin_headers):
    r = requests.get(f"{API}/admin/stats", headers=admin_headers, timeout=20)
    assert r.status_code == 200
    body = r.json()
    for k in ["leads_total", "leads_new", "runs_total", "runs_by_type", "recent_leads"]:
        assert k in body
    assert isinstance(body["runs_by_type"], dict)
    assert isinstance(body["recent_leads"], list)


def test_admin_agent_runs(admin_headers):
    r = requests.get(f"{API}/admin/agent-runs", headers=admin_headers, timeout=20)
    assert r.status_code == 200
    runs = r.json()
    assert isinstance(runs, list)
    types = {run.get("agent_type") for run in runs}
    # After running prior tests, we should see at least these
    assert "extract" in types, f"extract not seen in {types}"
    assert "support_triage" in types, f"support_triage not seen in {types}"
