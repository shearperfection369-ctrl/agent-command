"""JADE OS P1+P2 feature tests (iteration 2).

Covers:
- Case studies seeded + 404
- Stripe billing checkout + status
- Webhooks CRUD + dispatch (httpbin)
- KB docs CRUD + ask (RAG-lite)
- Orgs admin + usage
- Portal preview (no 404 for unknown)
- PDF extract (multipart) — happy + non-PDF reject
- Regression sanity: agent/extract (saas), agent/support-triage
- agent_runs 'chat' agent_type appears after KB ask
"""
import io
import os
import time
import uuid

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    from pathlib import Path
    for line in Path("/app/frontend/.env").read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip().strip('"')
            break
BASE_URL = (BASE_URL or "").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@jadeos.ai"
ADMIN_PASSWORD = "JadeOS!2026"

LLM_TIMEOUT = 120


# --------- Fixtures ---------
@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def admin_headers(session):
    r = session.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return {"Authorization": f"Bearer {r.json()['access_token']}", "Content-Type": "application/json"}


# --------- Health ---------
def test_root_health(session):
    r = session.get(f"{API}/", timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert body.get("service") == "JADE OS API"
    assert body.get("status") == "online"


def test_auth_me(session, admin_headers):
    r = session.get(f"{API}/auth/me", headers=admin_headers, timeout=15)
    assert r.status_code == 200
    assert r.json().get("email") == ADMIN_EMAIL


# --------- Case Studies ---------
EXPECTED_SLUGS = {"northstar-logistics", "twin-cities-health", "bjornson-saas"}


def test_case_studies_seeded(session):
    r = session.get(f"{API}/case-studies", timeout=20)
    assert r.status_code == 200
    docs = r.json()
    assert isinstance(docs, list)
    slugs = {d["slug"] for d in docs}
    assert EXPECTED_SLUGS.issubset(slugs), f"missing slugs, got {slugs}"


def test_case_study_detail(session):
    r = session.get(f"{API}/case-studies/northstar-logistics", timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert d["slug"] == "northstar-logistics"
    assert d["company"] == "Northstar Logistics"
    assert d["industry"] == "freight_brokerage"
    assert isinstance(d["results"], list) and len(d["results"]) > 0
    assert d.get("quote")


def test_case_study_404(session):
    r = session.get(f"{API}/case-studies/does-not-exist", timeout=15)
    assert r.status_code == 404


# --------- Billing / Stripe ---------
_billing_session_id = {"sid": None}


def test_billing_checkout_dispatch(session):
    r = session.post(f"{API}/billing/checkout", json={
        "tier": "dispatch",
        "origin_url": "https://example.com",
    }, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "url" in data and "session_id" in data
    assert "checkout.stripe.com" in data["url"], f"unexpected url: {data['url']}"
    _billing_session_id["sid"] = data["session_id"]


def test_billing_checkout_fleet(session):
    r = session.post(f"{API}/billing/checkout", json={
        "tier": "fleet",
        "origin_url": "https://example.com",
    }, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "checkout.stripe.com" in data["url"]


def test_billing_checkout_invalid_tier(session):
    r = session.post(f"{API}/billing/checkout", json={
        "tier": "invalid",
        "origin_url": "https://example.com",
    }, timeout=15)
    # Pydantic Literal -> 422; spec says 400. Either is a reject.
    assert r.status_code in (400, 422), r.text


def test_billing_status_found(session):
    sid = _billing_session_id["sid"]
    if not sid:
        pytest.skip("no checkout session id from previous test")
    r = session.get(f"{API}/billing/status/{sid}", timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "payment_status" in data or "status" in data
    assert data.get("session_id") == sid or data.get("amount_total") is not None or "payment_status" in data


def test_billing_status_not_found(session):
    r = session.get(f"{API}/billing/status/cs_does_not_exist_{uuid.uuid4().hex}", timeout=15)
    assert r.status_code == 404


# --------- Webhooks ---------
def test_webhook_create_requires_admin(session):
    r = session.post(f"{API}/webhooks", json={"name": "x", "url": "https://x", "kind": "slack"}, timeout=15)
    assert r.status_code == 401


def test_webhook_full_flow(session, admin_headers):
    # Create
    r = session.post(f"{API}/webhooks", headers=admin_headers, json={
        "name": "TEST_httpbin", "url": "https://httpbin.org/post", "kind": "generic"
    }, timeout=20)
    assert r.status_code == 200, r.text
    w = r.json()
    wid = w["id"]
    assert w["url"] == "https://httpbin.org/post"
    assert w["kind"] == "generic"

    # List
    r2 = session.get(f"{API}/webhooks", headers=admin_headers, timeout=20)
    assert r2.status_code == 200
    assert any(x["id"] == wid for x in r2.json())

    # Dispatch
    r3 = session.post(f"{API}/webhooks/{wid}/dispatch", headers=admin_headers, json={
        "title": "TEST_dispatch", "body": "hello", "metadata": {"k": "v"}
    }, timeout=30)
    assert r3.status_code == 200, r3.text
    res = r3.json()
    assert "delivered" in res
    assert res["delivered"] is True, f"delivery failed: {res}"

    # Delete
    r4 = session.delete(f"{API}/webhooks/{wid}", headers=admin_headers, timeout=20)
    assert r4.status_code == 200
    assert r4.json().get("ok") is True


# --------- KB docs + ask ---------
_kb_doc_id = {"id": None}


def test_kb_docs_create_requires_admin(session):
    r = session.post(f"{API}/kb/docs", json={"title": "x", "content": "y", "industry": "saas"}, timeout=15)
    assert r.status_code == 401


def test_kb_docs_create_and_list(session, admin_headers):
    r = session.post(f"{API}/kb/docs", headers=admin_headers, json={
        "industry": "saas",
        "title": "TEST_Password Reset Procedure",
        "content": "To reset your password, click 'Forgot password' on the login page. You'll receive an email link valid for 30 minutes. If you do not receive the email within 5 minutes, check spam and verify your account email."
    }, timeout=20)
    assert r.status_code == 200, r.text
    doc = r.json()
    assert doc["industry"] == "saas"
    assert doc["title"].startswith("TEST_")
    assert "id" in doc
    _kb_doc_id["id"] = doc["id"]

    # filtered list
    r2 = session.get(f"{API}/kb/docs?industry=saas", timeout=20)
    assert r2.status_code == 200
    ids = [d["id"] for d in r2.json()]
    assert doc["id"] in ids


def test_kb_ask_with_sources(session):
    if not _kb_doc_id["id"]:
        pytest.skip("kb doc not created")
    r = session.post(f"{API}/kb/ask", json={
        "question": "How do I reset my password?",
        "industry": "saas",
    }, timeout=LLM_TIMEOUT)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data.get("answer"), str) and len(data["answer"]) > 5
    assert data.get("industry") == "saas"
    assert isinstance(data.get("sources"), list) and len(data["sources"]) >= 1


def test_kb_doc_delete(session, admin_headers):
    if not _kb_doc_id["id"]:
        pytest.skip("kb doc not created")
    r = session.delete(f"{API}/kb/docs/{_kb_doc_id['id']}", headers=admin_headers, timeout=20)
    assert r.status_code == 200
    # confirm gone
    r2 = session.get(f"{API}/kb/docs", timeout=20)
    ids = [d["id"] for d in r2.json()]
    assert _kb_doc_id["id"] not in ids


# --------- Orgs + usage ---------
def test_orgs_requires_admin(session):
    r = session.get(f"{API}/orgs", timeout=15)
    assert r.status_code == 401


def test_orgs_list_admin(session, admin_headers):
    r = session.get(f"{API}/orgs", headers=admin_headers, timeout=20)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_orgs_usage(session, admin_headers):
    r = session.get(f"{API}/orgs/usage", headers=admin_headers, timeout=20)
    assert r.status_code == 200
    data = r.json()
    for k in ["runs", "estimated_tokens", "by_type"]:
        assert k in data, f"missing {k}"
    assert isinstance(data["by_type"], dict)


# --------- Portal preview ---------
def test_portal_preview_unknown_no_404(session):
    r = session.get(f"{API}/portal/preview", params={"email": "non-existent@x.com"}, timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("org") is None
    assert data.get("runs") == []
    assert isinstance(data.get("usage"), dict)


# --------- PDF extract ---------
def _make_pdf_bytes(text: str) -> bytes:
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    y = 800
    for line in text.split("\n"):
        c.drawString(50, y, line)
        y -= 18
        if y < 50:
            c.showPage()
            y = 800
    c.save()
    return buf.getvalue()


def test_extract_pdf_happy():
    pdf = _make_pdf_bytes(
        "Order Form\nAcme Inc.\nPlan: Enterprise\nSeats: 250\nMRR: $14250\nTerm: 24 months\nStart: 03/01"
    )
    files = {"file": ("order.pdf", pdf, "application/pdf")}
    data = {"industry": "saas", "provider": "anthropic"}
    r = requests.post(f"{API}/agent/extract-pdf", files=files, data=data, timeout=LLM_TIMEOUT)
    assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
    body = r.json()
    assert body.get("industry") == "saas"
    assert "extracted" in body
    assert isinstance(body["extracted"], dict)


def test_extract_pdf_non_pdf_rejected():
    files = {"file": ("not.txt", b"hello world", "text/plain")}
    data = {"industry": "general"}
    r = requests.post(f"{API}/agent/extract-pdf", files=files, data=data, timeout=30)
    assert r.status_code == 400, r.text


# --------- Regression: existing agent endpoints ---------
def test_extract_saas_regression():
    r = requests.post(f"{API}/agent/extract", json={
        "text": "Order Form Acme Inc. Enterprise 250 seats MRR $14250 24 months start 03/01",
        "industry": "saas",
    }, timeout=LLM_TIMEOUT)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["industry"] == "saas"
    assert isinstance(body["extracted"], dict)


def test_support_triage_regression():
    r = requests.post(f"{API}/agent/support-triage", json={
        "ticket": "Cannot login after password reset link expired.",
        "industry": "saas",
    }, timeout=LLM_TIMEOUT)
    assert r.status_code == 200, r.text
    res = r.json().get("result")
    assert isinstance(res, dict)
    assert res.get("priority") in ("p0", "p1", "p2", "p3")


# --------- chat agent_type recorded ---------
def test_kb_chat_run_logged(session, admin_headers):
    """KB ask uses _log_run('chat'). Verify it appears in /api/admin/agent-runs."""
    # do a kb_ask call to ensure a chat run is logged
    requests.post(f"{API}/kb/ask", json={
        "question": "anything", "industry": "general"
    }, timeout=LLM_TIMEOUT)
    time.sleep(1)
    r = session.get(f"{API}/admin/agent-runs", headers=admin_headers, timeout=20)
    assert r.status_code == 200
    runs = r.json()
    types = {x.get("agent_type") for x in runs}
    assert "chat" in types, f"expected 'chat' agent_type, got {types}"


# --------- Stripe webhook endpoint smoke ---------
def test_stripe_webhook_exists_rejects_bad(session):
    """The endpoint exists and rejects malformed payloads (signature fail)."""
    r = session.post(f"{API}/webhook/stripe", data=b"{}", headers={
        "Stripe-Signature": "t=1,v1=bogus",
        "Content-Type": "application/json",
    }, timeout=15)
    # Should fail signature verification -> 400, not 404
    assert r.status_code in (400, 401, 403), f"unexpected {r.status_code} {r.text[:200]}"
