"""Iteration 14 backend tests:
- Audit playbook PDFs (4 endpoints)
- Free 90-day broker audit start (lead_magnet field)
- Outreach campaigns (5 templates), render, log, admin log list/patch.
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


# ============================================================
# 1 · AUDIT PLAYBOOK PDFs
# ============================================================
PDF_ENDPOINTS = [
    "/api/audit/data-checklist.pdf",
    "/api/audit/playbook.pdf",
    "/api/audit/data-request-letter.pdf",
    "/api/audit/engagement-agreement.pdf",
]


@pytest.mark.parametrize("path", PDF_ENDPOINTS)
def test_pdf_endpoint_returns_pdf(s, path):
    r = s.get(f"{BASE_URL}{path}", timeout=30)
    assert r.status_code == 200, f"{path} → {r.status_code} :: {r.text[:200]}"
    assert r.headers.get("content-type", "").lower().startswith("application/pdf")
    assert r.content[:4] == b"%PDF", f"Not a valid PDF magic header on {path}"
    assert len(r.content) > 1000


# ============================================================
# 2 · FREE BROKER AUDIT START (lead_magnet)
# ============================================================
def test_audit_start_with_lead_magnet(s):
    payload = {
        "company_name": "TEST_Bay_and_Bay_Brokers",
        "contact_email": "test_dana@example.com",
        "industry": "freight_brokerage",
        "fleet_or_team_size": "50_trucks",
        "lead_magnet": "free_90_day",
    }
    r = s.post(f"{BASE_URL}/api/audit/start", json=payload, timeout=20)
    assert r.status_code in (200, 201), r.text[:300]
    data = r.json()
    assert "id" in data
    assert data.get("industry") == "freight_brokerage"
    # Fetch the audit doc to verify lead_magnet round-trip
    audit_id = data["id"]
    r2 = s.get(f"{BASE_URL}/api/audit/{audit_id}", timeout=15)
    assert r2.status_code == 200, r2.text[:200]
    doc = r2.json()
    assert doc.get("lead_magnet") == "free_90_day"
    assert doc.get("company_name") == payload["company_name"]


# ============================================================
# 3 · OUTREACH CAMPAIGNS LIST
# ============================================================
EXPECTED_CAMPAIGNS = {
    "broker_cold_email",
    "lighthouse_trio",
    "consulting_upsell",
    "linkedin_dm",
    "followup_sequence",
}


def test_outreach_list_campaigns(s):
    r = s.get(f"{BASE_URL}/api/outreach/campaigns", timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "campaigns" in data
    ids = {c["id"] for c in data["campaigns"]}
    assert ids == EXPECTED_CAMPAIGNS, f"got {ids}"
    # Each must have key fields
    for c in data["campaigns"]:
        for key in ("id", "label", "channel", "color", "audience", "subject", "body", "cta", "variables", "attach_pdfs"):
            assert key in c, f"{c['id']} missing {key}"


def test_outreach_broker_has_attach_pdf(s):
    r = s.get(f"{BASE_URL}/api/outreach/campaigns", timeout=15)
    cmap = {c["id"]: c for c in r.json()["campaigns"]}
    assert "data-checklist.pdf" in cmap["broker_cold_email"]["attach_pdfs"]


# ============================================================
# 4 · OUTREACH RENDER (template substitution)
# ============================================================
def test_outreach_render_broker(s):
    payload = {
        "campaign_id": "broker_cold_email",
        "variables": {"first_name": "Dana", "company": "Bay & Bay"},
    }
    r = s.post(f"{BASE_URL}/api/outreach/render", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "Bay & Bay" in data["subject"]
    assert "Dana" in data["body"]
    assert "Bay & Bay" not in data["subject"].replace("Bay & Bay", "")  # sanity
    # Unfilled vars should not appear
    assert "{{company}}" not in data["subject"]
    assert "{{first_name}}" not in data["body"]


def test_outreach_render_passthrough_undeclared(s):
    # consulting_upsell uses {{score}} and {{tier}} — omit them; they should remain
    payload = {
        "campaign_id": "consulting_upsell",
        "variables": {"first_name": "X", "company": "Y"},
    }
    r = s.post(f"{BASE_URL}/api/outreach/render", json=payload, timeout=15)
    assert r.status_code == 200
    body = r.json()["body"]
    assert "{{score}}" in body or "{{tier}}" in body, "Undeclared vars should pass through"


def test_outreach_render_404_for_unknown(s):
    r = s.post(f"{BASE_URL}/api/outreach/render",
               json={"campaign_id": "nope", "variables": {}}, timeout=15)
    assert r.status_code == 404


# ============================================================
# 5 · OUTREACH LOG · CREATE → LIST → PATCH
# ============================================================
def test_outreach_log_create_list_patch(s):
    # CREATE
    payload = {
        "campaign_id": "broker_cold_email",
        "recipient_name": "TEST_Dana",
        "recipient_company": "TEST_BayAndBay",
        "recipient_email": "test_dana_x@example.com",
        "notes": "iteration14 test",
    }
    r = s.post(f"{BASE_URL}/api/outreach/log", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    created = r.json()
    log_id = created["id"]
    assert created["status"] == "sent"
    assert created["recipient_name"] == "TEST_Dana"

    # LIST (admin) — should include this record
    time.sleep(0.3)
    r2 = s.get(f"{BASE_URL}/api/admin/outreach/log?limit=50", timeout=15)
    assert r2.status_code == 200, r2.text
    data = r2.json()
    assert "log" in data and "stats" in data
    ids = {row["id"] for row in data["log"]}
    assert log_id in ids

    # PATCH → mark replied
    r3 = s.patch(f"{BASE_URL}/api/admin/outreach/log/{log_id}",
                 json={"status": "replied", "notes": "they replied"}, timeout=15)
    assert r3.status_code == 200, r3.text
    assert r3.json()["updated"] is True

    # Verify persistence
    r4 = s.get(f"{BASE_URL}/api/admin/outreach/log?limit=50", timeout=15)
    found = [row for row in r4.json()["log"] if row["id"] == log_id]
    assert found, "log row vanished"
    assert found[0]["status"] == "replied"
    assert found[0]["notes"] == "they replied"

    # PATCH unknown → 404
    r5 = s.patch(f"{BASE_URL}/api/admin/outreach/log/nonexistent_id",
                 json={"status": "passed"}, timeout=15)
    assert r5.status_code == 404


def test_outreach_log_unknown_campaign(s):
    r = s.post(f"{BASE_URL}/api/outreach/log",
               json={"campaign_id": "bogus", "recipient_name": "X"}, timeout=15)
    assert r.status_code == 404
