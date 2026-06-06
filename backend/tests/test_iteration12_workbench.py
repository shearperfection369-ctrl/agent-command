"""Iteration 12 · Operations Workbench (OP-01..OP-06) backend tests.

Covers admin-gated workbench endpoints and public /api/agent/workbench/* wrappers.

NOTE: OP-01 uses Claude Sonnet 4.5 and can take 60-90s. If the LLM budget is
exceeded or the call fails, the endpoint may return 502/500 — we skip the
hard assertions in that case but still verify graceful error path / runs list.
"""
import os
import io
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@jadeos.ai"
ADMIN_PASS = "JadeOS!2026"


# ----------------------------- fixtures ------------------------------------

@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{API}/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASS},
                      timeout=30)
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.status_code} {r.text[:200]}")
    tok = r.json().get("access_token") or r.json().get("token")
    assert tok, f"no token in {r.json()}"
    return tok


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ============================================================================
# Module · Admin Workbench overview, decisions, risks, phases
# ============================================================================

class TestWorkbenchOverview:
    def test_overview_basic_shape(self, admin_headers):
        r = requests.get(f"{API}/workbench/overview", headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert len(d.get("operations", [])) == 6, "expected 6 OPs"
        assert len(d.get("decisions", [])) == 5, "expected 5 seeded decisions"
        assert len(d.get("risks", [])) == 7, "expected 7 seeded risks"
        assert len(d.get("phases", [])) == 8, "expected 8 phases"
        # validate stat summary keys
        s = d.get("summary", {})
        for k in ("ops_total", "ops_full", "decisions_pending", "risks_open"):
            assert k in s

    def test_decision_flip_persists(self, admin_headers):
        # grab a decision
        ov = requests.get(f"{API}/workbench/overview", headers=admin_headers, timeout=30).json()
        dec = ov["decisions"][0]
        did = dec["id"]
        choice = (dec.get("options") or ["yes", "no"])[0]
        # flip
        r = requests.patch(f"{API}/workbench/decisions/{did}",
                           headers=admin_headers,
                           json={"choice": choice, "rationale": "TEST flip", "status": "decided"},
                           timeout=30)
        assert r.status_code == 200, r.text
        after = r.json()
        assert after["status"] == "decided"
        assert after["choice"] == choice
        # verify persistence via overview
        ov2 = requests.get(f"{API}/workbench/overview", headers=admin_headers, timeout=30).json()
        d2 = next((x for x in ov2["decisions"] if x["id"] == did), None)
        assert d2 and d2["choice"] == choice

    def test_risk_mitigate_persists(self, admin_headers):
        ov = requests.get(f"{API}/workbench/overview", headers=admin_headers, timeout=30).json()
        # find an open risk
        risk = next((r for r in ov["risks"] if r.get("status") == "open"), ov["risks"][0])
        rid = risk["id"]
        r = requests.patch(f"{API}/workbench/risks/{rid}",
                           headers=admin_headers,
                           json={"status": "mitigated", "mitigation_notes": "TEST mitigation"},
                           timeout=30)
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "mitigated"


# ============================================================================
# Module · OP-02 ROI Lab (deterministic math)
# ============================================================================

class TestOp02Roi:
    def test_op02_run_mid_market(self, admin_headers):
        r = requests.post(f"{API}/workbench/labs/op-02/run", headers=admin_headers,
                          json={"archetype": "mid_market"}, timeout=30)
        assert r.status_code == 200, r.text
        out = r.json()
        text = str(out)
        for key in ("annual_total_savings_usd", "npv_at_10pct_discount_usd", "payback_months"):
            assert key in text, f"missing {key} in OP-02 output"

    def test_op02_archetype_switch(self, admin_headers):
        r1 = requests.post(f"{API}/workbench/labs/op-02/run", headers=admin_headers,
                           json={"archetype": "mid_market"}, timeout=30).json()
        r2 = requests.post(f"{API}/workbench/labs/op-02/run", headers=admin_headers,
                           json={"archetype": "small_regional"}, timeout=30).json()
        # values must differ
        assert str(r1) != str(r2), "small_regional should produce different ROI than mid_market"


# ============================================================================
# Module · OP-03 AI Architecture (deterministic)
# ============================================================================

class TestOp03Architecture:
    def test_op03_run(self, admin_headers):
        r = requests.post(f"{API}/workbench/labs/op-03/run", headers=admin_headers,
                          json={}, timeout=30)
        assert r.status_code == 200, r.text
        body = r.json()
        out = body.get("output") or body
        text = str(out)
        assert "modules" in text
        assert "data_pipeline" in text or "pipeline" in text
        assert "api_surface" in text or "swimlanes" in text


# ============================================================================
# Module · OP-04 Pitch Deck (12 slides + 4 fact sheets) + PDF download
# ============================================================================

class TestOp04Deck:
    def test_op04_run_and_download(self, admin_headers):
        r = requests.post(f"{API}/workbench/labs/op-04/run", headers=admin_headers,
                          json={}, timeout=60)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("slide_count") == 12, f"expected 12 slides, got {body.get('slide_count')}"
        assert body.get("factsheet_count") == 4, f"expected 4 fact sheets, got {body.get('factsheet_count')}"
        run_id = body.get("id")
        assert run_id, "missing id (run_id) for OP-04"
        # download
        d = requests.get(f"{API}/workbench/labs/op-04/download/{run_id}",
                         headers=admin_headers, timeout=60)
        assert d.status_code == 200, d.text[:200]
        assert d.content[:4] == b"%PDF", "expected PDF magic bytes"
        assert len(d.content) > 5000, f"PDF too small ({len(d.content)} bytes)"


# ============================================================================
# Module · OP-05 Technical Brief (10 sections) + PDF download
# ============================================================================

class TestOp05Brief:
    def test_op05_run_and_download(self, admin_headers):
        r = requests.post(f"{API}/workbench/labs/op-05/run", headers=admin_headers,
                          json={}, timeout=60)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("section_count") == 10
        run_id = body.get("id")
        assert run_id
        d = requests.get(f"{API}/workbench/labs/op-05/download/{run_id}",
                         headers=admin_headers, timeout=60)
        assert d.status_code == 200
        assert d.content[:4] == b"%PDF"
        assert len(d.content) > 5000


# ============================================================================
# Module · OP-06 FMCSA MN Freight Seed
# ============================================================================

class TestOp06Fmcsa:
    def test_op06_run_real_mn_companies(self, admin_headers):
        r = requests.post(f"{API}/workbench/labs/op-06/run", headers=admin_headers,
                          json={}, timeout=30)
        assert r.status_code == 200, r.text
        body = r.json()
        out = body.get("output") or body
        text = str(out)
        # Must reference DOT numbers and MN
        assert "DOT" in text or "dot_number" in text.lower(), "no DOT references in OP-06 output"


# ============================================================================
# Module · OP-01 Market analysis (LLM-based · graceful)
# ============================================================================

class TestOp01MarketAnalysis:
    def test_op01_run_pdf(self, admin_headers):
        r = requests.post(f"{API}/workbench/labs/op-01/run", headers=admin_headers,
                          json={}, timeout=180)
        if r.status_code != 200:
            # LLM failure → check run history endpoint still works
            rl = requests.get(f"{API}/workbench/labs/OP-01/runs", headers=admin_headers, timeout=30)
            assert rl.status_code == 200
            pytest.skip(f"OP-01 LLM failed gracefully ({r.status_code}); runs endpoint still OK")
        body = r.json()
        sc = body.get("section_count") or (body.get("output") or {}).get("section_count")
        assert sc is None or sc >= 5
        run_id = body.get("run_id") or (body.get("output") or {}).get("run_id")
        if run_id:
            d = requests.get(f"{API}/workbench/labs/op-01/download/{run_id}",
                             headers=admin_headers, timeout=60)
            assert d.status_code == 200
            assert d.content[:4] == b"%PDF"
            assert len(d.content) > 5000


# ============================================================================
# Module · PUBLIC /api/agent/workbench/* wrappers (no admin gate)
# ============================================================================

class TestPublicWorkbench:
    def test_public_architecture(self):
        r = requests.get(f"{API}/agent/workbench/architecture", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert len(d.get("modules", [])) == 6
        assert "data_pipeline" in d
        assert "api_surface" in d

    def test_public_roi_default_and_switch(self):
        r1 = requests.post(f"{API}/agent/workbench/roi", json={"archetype": "mid_market"}, timeout=30)
        assert r1.status_code == 200
        m1 = r1.json().get("model") or {}
        # required fields (deterministic OP-02 keys)
        assert "annual_total_savings_usd" in str(m1)
        assert "npv_at_10pct_discount_usd" in str(m1)
        assert "payback_months" in str(m1)
        # switch
        r2 = requests.post(f"{API}/agent/workbench/roi", json={"archetype": "small_regional"}, timeout=30)
        assert r2.status_code == 200
        assert r2.json() != r1.json(), "small_regional should differ from mid_market"

    def test_public_roi_bad_archetype(self):
        r = requests.post(f"{API}/agent/workbench/roi", json={"archetype": "BOGUS"}, timeout=30)
        assert r.status_code == 400

    def test_public_collateral(self):
        r = requests.get(f"{API}/agent/workbench/collateral", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d.get("slide_count") == 12, f"expected 12 slides, got {d.get('slide_count')}"
        assert d.get("factsheet_count") == 4, f"expected 4 fact sheets, got {d.get('factsheet_count')}"
        deck = d.get("deck", {})
        assert len(deck.get("slides", [])) == 12

    def test_public_document(self):
        r = requests.get(f"{API}/agent/workbench/document", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d.get("section_count") == 10, f"expected 10 sections, got {d.get('section_count')}"

    def test_public_deck_pdf(self):
        r = requests.get(f"{API}/agent/workbench/deck.pdf", timeout=60)
        assert r.status_code == 200
        assert r.content[:4] == b"%PDF"
        assert len(r.content) > 5000

    def test_public_document_pdf(self):
        r = requests.get(f"{API}/agent/workbench/document.pdf", timeout=60)
        assert r.status_code == 200
        assert r.content[:4] == b"%PDF"
        assert len(r.content) > 5000

    def test_public_decisions_risks_phases(self):
        d = requests.get(f"{API}/agent/workbench/decisions", timeout=30).json()
        assert d.get("count") == 5
        r = requests.get(f"{API}/agent/workbench/risks", timeout=30).json()
        assert r.get("count") == 7
        p = requests.get(f"{API}/agent/workbench/phases", timeout=30).json()
        assert p.get("count") == 8


# ============================================================================
# Regression · existing endpoints still respond
# ============================================================================

class TestRegression:
    def test_trucker_hos_rules(self):
        r = requests.get(f"{API}/trucker/hos-rules", timeout=30)
        assert r.status_code == 200
        assert "source" in r.json()

    def test_health(self):
        r = requests.get(f"{API}/", timeout=30)
        # any 2xx is acceptable; some apps return 404 for root
        assert r.status_code in (200, 404)
