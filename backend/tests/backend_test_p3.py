"""JADE OS P3 backend pytest suite — MOAT + Lighthouse Customer Program.

Covers:
- MOAT: /api/moat/stats, /api/moat/admin
- Schemas: list, filter by industry, get, 404, create (admin), correct (admin)
- Prompts: list, create+delete (admin), run
- Playbooks: list, get, create (admin), run (LLM-heavy), playbook-runs list
- Lighthouse: apply (hot+cold), list (admin), patch status, stats, agent-run logging
"""
import json
import os
import time
from pathlib import Path

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
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
PLAYBOOK_TIMEOUT = 180


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
    return tok


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ============================================================
# MOAT — stats & admin
# ============================================================
class TestMoat:
    def test_moat_stats_public(self, session):
        r = session.get(f"{API}/moat/stats", timeout=10)
        assert r.status_code == 200
        d = r.json()
        for k in ("schemas", "prompts", "playbooks", "playbook_runs", "schema_corrections", "agent_runs"):
            assert k in d, f"missing key {k}"
            assert isinstance(d[k], int), f"{k} must be int"
            assert d[k] >= 0
        # seeded
        assert d["schemas"] > 0
        assert d["prompts"] > 0
        assert d["playbooks"] > 0

    def test_moat_admin_requires_auth(self, session):
        r = session.get(f"{API}/moat/admin", timeout=10)
        assert r.status_code in (401, 403)

    def test_moat_admin_authed(self, session, admin_headers):
        r = session.get(f"{API}/moat/admin", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        d = r.json()
        for k in ("schemas", "prompts", "playbooks", "schema_corrections", "agent_runs_by_type", "model_routing"):
            assert k in d, f"missing key {k}"
        assert isinstance(d["schemas"], list)
        assert isinstance(d["prompts"], list)
        assert isinstance(d["playbooks"], list)
        assert isinstance(d["schema_corrections"], int)
        assert isinstance(d["agent_runs_by_type"], dict)
        assert isinstance(d["model_routing"], dict)
        # model_routing should have fast/default/smart keys
        for prof in ("fast", "default", "smart"):
            assert prof in d["model_routing"]


# ============================================================
# SCHEMA LIBRARY
# ============================================================
class TestSchemas:
    def test_schemas_list(self, session):
        r = session.get(f"{API}/schemas", timeout=10)
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list)
        slugs = {s["slug"] for s in items}
        for expected in ("freight_bol", "healthcare_intake", "saas_order_form", "manufacturing_po"):
            assert expected in slugs, f"missing seeded schema {expected}"

    def test_schemas_list_industry_filter(self, session):
        r = session.get(f"{API}/schemas", params={"industry": "healthcare"}, timeout=10)
        assert r.status_code == 200
        items = r.json()
        assert len(items) >= 1
        for s in items:
            assert s["industry"] == "healthcare"

    def test_schema_get_freight_bol(self, session):
        r = session.get(f"{API}/schemas/freight_bol", timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert d["slug"] == "freight_bol"
        assert isinstance(d["fields"], list)
        assert len(d["fields"]) == 14
        field_names = {f["name"] for f in d["fields"]}
        assert "origin_city" in field_names
        assert "dest_city" in field_names
        # Required check
        required_names = {f["name"] for f in d["fields"] if f.get("required")}
        assert "origin_city" in required_names
        assert "dest_city" in required_names

    def test_schema_get_404(self, session):
        r = session.get(f"{API}/schemas/nonexistent_xyz_abc", timeout=10)
        assert r.status_code == 404

    def test_schema_create_requires_admin(self, session):
        body = {
            "slug": "TEST_p3_schema",
            "industry": "general",
            "name": "TEST P3 Schema",
            "fields": [{"name": "foo", "type": "string", "required": True}],
        }
        r = session.post(f"{API}/schemas", json=body, timeout=10)
        assert r.status_code in (401, 403)

    def test_schema_create_admin_and_correct(self, session, admin_headers):
        body = {
            "slug": "TEST_p3_schema",
            "industry": "general",
            "name": "TEST P3 Schema",
            "fields": [
                {"name": "foo", "type": "string", "required": True},
                {"name": "bar", "type": "number"},
            ],
        }
        r = session.post(f"{API}/schemas", json=body, headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["slug"] == "TEST_p3_schema"
        assert d["correction_count"] == 0
        schema_id = d["id"]

        # Record correction
        corr_body = {
            "schema_id": schema_id,
            "original_output": {"foo": "x"},
            "corrected_output": {"foo": "x", "bar": 5},
            "notes": "TEST_p3 correction",
        }
        r2 = session.post(f"{API}/schemas/{schema_id}/correct", json=corr_body, headers=admin_headers, timeout=15)
        assert r2.status_code == 200, r2.text
        assert r2.json()["ok"] is True

        # Verify correction_count incremented via list (re-fetch via /schemas)
        rlist = session.get(f"{API}/schemas", timeout=10)
        assert rlist.status_code == 200
        match = [s for s in rlist.json() if s["id"] == schema_id]
        assert len(match) == 1
        assert match[0]["correction_count"] >= 1

    def test_schema_correct_404(self, session, admin_headers):
        r = session.post(
            f"{API}/schemas/nonexistent-id/correct",
            json={"schema_id": "nonexistent-id", "original_output": {}, "corrected_output": {}},
            headers=admin_headers, timeout=10,
        )
        assert r.status_code == 404


# ============================================================
# PROMPT LIBRARY
# ============================================================
class TestPrompts:
    def test_prompts_list(self, session):
        r = session.get(f"{API}/prompts", timeout=10)
        assert r.status_code == 200
        items = r.json()
        slugs = {p["slug"] for p in items}
        for expected in ("carrier_outreach_v1", "patient_followup_v1", "renewal_email_v1"):
            assert expected in slugs, f"missing seeded prompt {expected}"

    def test_prompt_create_requires_admin(self, session):
        body = {"slug": "TEST_p3_prompt", "name": "TEST", "template": "Say {{x}}", "variables": ["x"]}
        r = session.post(f"{API}/prompts", json=body, timeout=10)
        assert r.status_code in (401, 403)

    def test_prompt_create_and_delete(self, session, admin_headers):
        body = {"slug": "TEST_p3_prompt", "name": "TEST P3", "template": "Say {{x}}", "variables": ["x"]}
        r = session.post(f"{API}/prompts", json=body, headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        pid = r.json()["id"]
        # Delete
        rdel = session.delete(f"{API}/prompts/{pid}", headers=admin_headers, timeout=10)
        assert rdel.status_code == 200
        assert rdel.json().get("ok") is True

    def test_prompt_run_carrier_outreach(self, session):
        body = {
            "slug": "carrier_outreach_v1",
            "variables": {"load_summary": "53 reefer Eagan→Joliet", "recipient": "Bay & Bay"},
            "industry": "freight_brokerage",
            "profile": "default",
        }
        r = session.post(f"{API}/prompts/run", json=body, timeout=LLM_TIMEOUT)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["prompt_slug"] == "carrier_outreach_v1"
        assert isinstance(d["output"], str)
        assert len(d["output"].strip()) > 30
        assert d["provider"] in ("anthropic", "openai")
        assert isinstance(d["model"], str) and len(d["model"]) > 0


# ============================================================
# PLAYBOOKS
# ============================================================
class TestPlaybooks:
    def test_playbooks_list(self, session):
        r = session.get(f"{API}/playbooks", timeout=10)
        assert r.status_code == 200
        items = r.json()
        slugs = {p["slug"] for p in items}
        for expected in ("freight_load_intake", "healthcare_intake_triage", "saas_inbound_lead"):
            assert expected in slugs, f"missing seeded playbook {expected}"

    def test_playbook_get_freight(self, session):
        r = session.get(f"{API}/playbooks/freight_load_intake", timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert d["slug"] == "freight_load_intake"
        assert isinstance(d["steps"], list)
        assert len(d["steps"]) == 2

    def test_playbook_get_404(self, session):
        r = session.get(f"{API}/playbooks/nonexistent_playbook", timeout=10)
        assert r.status_code == 404

    def test_playbook_create_requires_admin(self, session):
        body = {
            "slug": "TEST_p3_pb", "industry": "general", "name": "TEST P3 PB",
            "steps": [{"kind": "chat", "label": "say hi", "config": {}}],
        }
        r = session.post(f"{API}/playbooks", json=body, timeout=10)
        assert r.status_code in (401, 403)

    def test_playbook_create_admin(self, session, admin_headers):
        body = {
            "slug": "TEST_p3_pb", "industry": "general", "name": "TEST P3 PB",
            "steps": [{"kind": "chat", "label": "say hi", "config": {}}],
        }
        r = session.post(f"{API}/playbooks", json=body, headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json()["slug"] == "TEST_p3_pb"

    def test_playbook_run_freight_load_intake(self, session):
        load_text = (
            "Need a 53' reefer carrier. Pickup Tue 10/15 in Eagan, MN, deliver Wed 10/16 to Joliet, IL. "
            "Approx 39,500 lbs frozen produce. Rate $2,150 all-in. Approx 400 miles. "
            "Contact: Mike Adams, 612-555-9087, MC-987654."
        )
        body = {
            "slug": "freight_load_intake",
            "input": load_text,
            "industry": "freight_brokerage",
            "provider": "anthropic",
        }
        r = session.post(f"{API}/playbooks/run", json=body, timeout=PLAYBOOK_TIMEOUT)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "run_id" in d
        assert d["playbook"] == "freight_load_intake"
        assert isinstance(d["elapsed_ms"], int) and d["elapsed_ms"] > 0
        assert isinstance(d["steps"], list) and len(d["steps"]) == 2
        for step in d["steps"]:
            assert step.get("status") == "ok", f"step failed: {step}"
            assert step.get("output") is not None

    def test_playbook_runs_list_requires_admin(self, session):
        r = session.get(f"{API}/playbook-runs", timeout=10)
        assert r.status_code in (401, 403)

    def test_playbook_runs_list_admin(self, session, admin_headers):
        r = session.get(f"{API}/playbook-runs", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list)
        # The freight_load_intake run from previous test should be present
        slugs = [i.get("playbook_slug") for i in items]
        assert "freight_load_intake" in slugs


# ============================================================
# LIGHTHOUSE CUSTOMER PROGRAM
# ============================================================
class TestLighthouse:
    HOT_APP_ID = None
    COLD_APP_ID = None

    def test_lighthouse_apply_hot(self, session):
        body = {
            "name": "Sarah Johnson",
            "title": "VP Operations",
            "email": "TEST_sarah_p3@example.com",
            "company": "TEST_Apex Freight Brokerage",
            "industry": "freight_brokerage",
            "company_size": "51-200",
            "primary_pain": "doc_overload",
            "pain_detail": "Ops team spends 6+ hrs/day parsing BOLs, rate cons, and emails into our TMS. We close 80 loads/day and the manual entry is killing our margins.",
            "target_outcome": "Cut BOL/load intake time from 6h/day to <30 min, freeing 2 FTEs for higher-value carrier relations.",
            "timeline": "14_days",
            "decision_authority": "decision_maker",
            "budget_band": "4500_10000",
            "case_study_consent": True,
            "logo_consent": True,
            "quote_consent": True,
            "metrics_consent": True,
        }
        r = session.post(f"{API}/lighthouse/apply", json=body, timeout=LLM_TIMEOUT)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "id" in d
        TestLighthouse.HOT_APP_ID = d["id"]
        # Auto-scored fields should be populated (even if None on LLM error, but verify present)
        for k in ("score", "tier", "rationale", "next_action", "green_flags", "red_flags", "status"):
            assert k in d, f"missing field {k}"
        # Score should be int 0-100 if present
        if d["score"] is not None:
            assert isinstance(d["score"], int)
            assert 0 <= d["score"] <= 100
        if d["tier"] is not None:
            assert d["tier"] in ("hot", "warm", "cold"), f"unexpected tier {d['tier']}"
        assert isinstance(d["green_flags"], list)
        assert isinstance(d["red_flags"], list)
        # If tier is hot, status should be screening; else new
        if d["tier"] == "hot":
            assert d["status"] == "screening"
        else:
            assert d["status"] == "new"

    def test_lighthouse_apply_cold(self, session):
        body = {
            "name": "Random Researcher",
            "title": "Grad Student",
            "email": "TEST_cold_p3@example.com",
            "company": "TEST_University Project",
            "industry": "general",
            "company_size": "1-10",
            "primary_pain": "other",
            "pain_detail": "Researching AI tools for a class project.",
            "target_outcome": "Write a paper.",
            "timeline": "90_plus",
            "decision_authority": "researcher",
            "budget_band": "<1500",
            "case_study_consent": False,
            "logo_consent": False,
            "quote_consent": False,
            "metrics_consent": False,
        }
        r = session.post(f"{API}/lighthouse/apply", json=body, timeout=LLM_TIMEOUT)
        assert r.status_code == 200, r.text
        d = r.json()
        TestLighthouse.COLD_APP_ID = d["id"]
        # score computed
        assert "score" in d
        # tier likely cold
        if d["tier"] is not None:
            assert d["tier"] in ("hot", "warm", "cold")
        # Per spec: cold/warm get status='new'
        if d["tier"] != "hot":
            assert d["status"] == "new"

    def test_lighthouse_list_requires_admin(self, session):
        r = session.get(f"{API}/lighthouse/applications", timeout=10)
        assert r.status_code in (401, 403)

    def test_lighthouse_list_admin(self, session, admin_headers):
        r = session.get(f"{API}/lighthouse/applications", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list)
        assert len(items) >= 2
        # Sorted newest first — check created_at descending
        if len(items) >= 2:
            assert items[0]["created_at"] >= items[1]["created_at"]
        # Should contain our two test apps
        ids = {i["id"] for i in items}
        if TestLighthouse.HOT_APP_ID:
            assert TestLighthouse.HOT_APP_ID in ids
        if TestLighthouse.COLD_APP_ID:
            assert TestLighthouse.COLD_APP_ID in ids

    def test_lighthouse_patch_status_admin(self, session, admin_headers):
        if not TestLighthouse.HOT_APP_ID:
            pytest.skip("no app to patch")
        r = session.patch(
            f"{API}/lighthouse/applications/{TestLighthouse.HOT_APP_ID}",
            params={"status_value": "selected"},
            headers=admin_headers, timeout=10,
        )
        assert r.status_code == 200
        assert r.json().get("ok") is True
        # Verify via list
        rlist = session.get(f"{API}/lighthouse/applications", headers=admin_headers, timeout=10)
        match = [i for i in rlist.json() if i["id"] == TestLighthouse.HOT_APP_ID]
        assert len(match) == 1
        assert match[0]["status"] == "selected"

    def test_lighthouse_patch_404(self, session, admin_headers):
        r = session.patch(
            f"{API}/lighthouse/applications/nonexistent-xyz",
            params={"status_value": "selected"},
            headers=admin_headers, timeout=10,
        )
        assert r.status_code == 404

    def test_lighthouse_stats(self, session):
        r = session.get(f"{API}/lighthouse/stats", timeout=10)
        assert r.status_code == 200
        d = r.json()
        for k in ("total_applications", "slots_total", "slots_remaining", "selected_or_active"):
            assert k in d
            assert isinstance(d[k], int)
        assert d["slots_total"] == 5
        assert d["total_applications"] >= 2
        # After patching one to selected, selected_or_active >=1
        assert d["selected_or_active"] >= 1
        assert d["slots_remaining"] == max(0, d["slots_total"] - d["selected_or_active"])

    def test_lighthouse_logged_as_agent_run(self, session, admin_headers):
        # Verify _log_run was called with [lighthouse] prefix for qualify_lead
        r = session.get(f"{API}/admin/agent-runs", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        runs = r.json()
        assert isinstance(runs, list)
        qual_runs = [r for r in runs if r.get("agent_type") == "qualify_lead"
                     and "[lighthouse]" in (r.get("input_preview") or "")]
        assert len(qual_runs) >= 1, "expected qualify_lead run with [lighthouse] prefix"
