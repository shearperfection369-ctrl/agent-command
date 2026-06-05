"""Iteration 6 — COMPLIANCE · ROUTE backend tests + iteration-5 regression."""
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") or os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")
if not BASE_URL:
    # fallback to frontend .env
    with open("/app/frontend/.env") as f:
        for ln in f:
            if ln.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = ln.split("=", 1)[1].strip().rstrip("/")
                break

ADMIN_EMAIL = "admin@jadeos.ai"
ADMIN_PASSWORD = "JadeOS!2026"


@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    if r.status_code != 200:
        pytest.skip(f"Cannot login admin: {r.status_code} {r.text[:200]}")
    j = r.json()
    return j.get("access_token") or j.get("token")


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ============================================================
# /api/admin/compliance (full)
# ============================================================
class TestAdminCompliance:
    def test_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/admin/compliance", timeout=10)
        assert r.status_code in (401, 403), f"Expected 401/403 unauth, got {r.status_code}"

    def test_full_payload_shape(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/compliance", headers=admin_headers, timeout=10)
        assert r.status_code == 200
        d = r.json()
        # summary counts
        s = d["summary"]
        assert s["total_industries"] == 14
        assert s["go_now"] == 8
        assert s["go_with_tos"] == 3
        assert s["blocked"] == 3
        # 14 industries
        assert isinstance(d["industries"], list)
        assert len(d["industries"]) == 14
        # industries_by_status
        ibs = d["industries_by_status"]
        assert len(ibs["go_now"]) == 8
        assert len(ibs["go_with_tos"]) == 3
        assert len(ibs["blocked"]) == 3
        # universal requirements + roadmap + principles
        assert len(d["universal_requirements"]) == 6
        assert len(d["roadmap"]) == 4
        assert len(d["headline_principles"]) == 5

    def test_each_industry_has_required_fields(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/compliance", headers=admin_headers, timeout=10)
        assert r.status_code == 200
        required = {"id", "label", "status", "color", "headline", "summary", "ready_to_sell"}
        for ind in r.json()["industries"]:
            missing = required - set(ind.keys())
            assert not missing, f"industry {ind.get('id')} missing {missing}"
            assert ind["status"] in ("go_now", "go_with_tos", "blocked")

    def test_specific_industry_statuses(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/compliance", headers=admin_headers, timeout=10)
        by_id = {i["id"]: i for i in r.json()["industries"]}
        # Required GO NOW
        for iid in ["freight_brokerage", "logistics", "manufacturing", "ecommerce",
                    "real_estate", "professional_services", "saas", "general"]:
            assert by_id[iid]["status"] == "go_now", f"{iid} not go_now"
            assert by_id[iid]["ready_to_sell"] is True
        # Blocked
        for iid in ["healthcare", "saas_enterprise", "finance"]:
            assert by_id[iid]["status"] == "blocked", f"{iid} not blocked"
            assert by_id[iid]["ready_to_sell"] is False
        # go_with_tos
        for iid in ["legal", "insurance", "hr"]:
            assert by_id[iid]["status"] == "go_with_tos", f"{iid} not go_with_tos"

    def test_universal_requirements_ids(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/compliance", headers=admin_headers, timeout=10)
        ids = {x["id"] for x in r.json()["universal_requirements"]}
        assert ids == {"privacy_policy", "terms_of_service", "dpa", "ai_disclosure", "soc2", "eo_insurance"}
        for req in r.json()["universal_requirements"]:
            assert "cost_est" in req
            assert "effort_weeks" in req

    def test_roadmap_phases(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/compliance", headers=admin_headers, timeout=10)
        months = [p["month"] for p in r.json()["roadmap"]]
        assert months == ["1-2", "3-4", "6", "8+"]
        for p in r.json()["roadmap"]:
            assert "actions" in p and len(p["actions"]) > 0
            assert "unlocks" in p and len(p["unlocks"]) > 0


# ============================================================
# /api/compliance/public (no auth, slimmed)
# ============================================================
class TestPublicCompliance:
    def test_no_auth_required(self):
        r = requests.get(f"{BASE_URL}/api/compliance/public", timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert "ready_now" in d and "coming_soon" in d
        assert len(d["ready_now"]) == 11  # go_now(8) + go_with_tos(3)
        assert len(d["coming_soon"]) == 3  # blocked

    def test_does_not_leak_costs_or_gates(self):
        r = requests.get(f"{BASE_URL}/api/compliance/public", timeout=10)
        d = r.json()
        for item in d["ready_now"] + d["coming_soon"]:
            assert set(item.keys()) == {"id", "label", "headline"}, f"Leak: {item.keys()}"
            # ensure no cost_est / gates / tos_must_have / summary
            for forbidden in ("cost_est", "gates", "tos_must_have", "summary",
                              "unlock_path", "estimated_market_size_msp"):
                assert forbidden not in item


# ============================================================
# Regression — iteration 5 still healthy
# ============================================================
class TestRegression:
    def test_llm_health_public(self):
        r = requests.get(f"{BASE_URL}/api/llm-health", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "status" in d

    def test_admin_system_health(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/system-health", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "overall" in d and "services" in d

    def test_launch_campaign_21_posts(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/launch/campaign", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert len(d["all_posts"]) == 21
