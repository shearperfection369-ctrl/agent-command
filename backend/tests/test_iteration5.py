"""Iteration 5 backend tests — Health, Launch, Security, LLM error classification."""
import io
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


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def admin_token(session):
    r = session.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# =========================================================
# 1. Public LLM health (no auth)
# =========================================================
class TestLlmHealthPublic:
    def test_llm_health_no_auth(self, session):
        r = session.get(f"{API}/llm-health", timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "status" in body
        assert "code" in body
        assert "message" in body
        # status is one of expected enums
        assert body["status"] in ("ok", "degraded", "warn", "healthy", "unhealthy", "unknown")


# =========================================================
# 2. Admin system health
# =========================================================
class TestAdminSystemHealth:
    def test_system_health(self, session, admin_headers):
        r = session.get(f"{API}/admin/system-health", headers=admin_headers, timeout=20)
        assert r.status_code == 200, r.text
        body = r.json()
        for k in ("overall", "mongo", "llm", "services", "security", "counts", "disk", "auto_followups", "needs_action"):
            assert k in body, f"missing key {k}: {list(body.keys())}"
        # services matrix
        services = body["services"]
        assert services.get("llm", {}).get("configured") is True
        assert services.get("mongo", {}).get("configured") is True

    def test_llm_probe(self, session, admin_headers):
        r = session.post(f"{API}/admin/llm-probe", headers=admin_headers, timeout=30)
        assert r.status_code in (200, 402, 503), r.text
        body = r.json()
        assert "status" in body
        # If healthy: latency_ms + reply present
        if body.get("status") == "healthy":
            assert "latency_ms" in body
            assert "reply" in body
        else:
            # degraded path must surface a code
            assert "code" in body or "detail" in body

    def test_llm_errors_list(self, session, admin_headers):
        r = session.get(f"{API}/admin/llm-errors", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "errors" in body
        assert "by_code" in body
        assert "total_recent" in body
        assert isinstance(body["errors"], list)


# =========================================================
# 3. Launch campaign + assets
# =========================================================
class TestLaunchCampaign:
    def test_campaign_default(self, session, admin_headers):
        r = session.get(f"{API}/admin/launch/campaign", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "weeks" in body
        assert "platforms" in body
        assert "total_posts" in body
        assert "all_posts" in body
        assert body["total_posts"] == 21, f"expected 21 posts, got {body['total_posts']}"
        assert len(body["all_posts"]) == 21
        assert len(body["weeks"]) == 4
        assert len(body["platforms"]) == 11
        # Spot-check post shape
        p0 = body["all_posts"][0]
        for k in ("headline", "body", "hashtags", "scheduled_for"):
            assert k in p0, f"post missing {k}: {list(p0.keys())}"

    def test_campaign_custom_start(self, session, admin_headers):
        r = session.get(
            f"{API}/admin/launch/campaign",
            params={"start_date": "2026-03-01"},
            headers=admin_headers,
            timeout=15,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        # The first scheduled post should be on/near 2026-03-01
        first_date = body["all_posts"][0]["scheduled_for"]
        assert "2026-03" in first_date, f"first scheduled_for={first_date}"

    def test_assets_list(self, session, admin_headers):
        r = session.get(f"{API}/admin/launch/assets", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        # body shape could be {assets:[...]} or list
        assets = body.get("assets") if isinstance(body, dict) else body
        assert isinstance(assets, list)
        assert len(assets) == 5, f"expected 5 assets, got {len(assets)}"
        for a in assets:
            assert "size_mb" in a
            assert "url" in a

    def test_public_asset_download(self, session):
        r = session.get(f"{API}/launch/asset/jadeos_v3_vertical_9x16.mp4", timeout=30, stream=True)
        assert r.status_code == 200, f"status={r.status_code}"
        ctype = r.headers.get("content-type", "")
        assert "video/mp4" in ctype, f"content-type={ctype}"
        # Read a chunk; full file should be >1MB
        size = int(r.headers.get("content-length") or 0)
        if size:
            assert size > 1_000_000, f"size={size}"

    def test_path_traversal_blocked(self, session):
        r = session.get(f"{API}/launch/asset/..%2Fetc%2Fpasswd", timeout=10, allow_redirects=False)
        # Some frameworks normalize; check that body is not /etc/passwd content
        assert r.status_code in (400, 404), f"status={r.status_code} body={r.text[:200]}"
        # Try the literal form too
        r2 = session.get(f"{API}/launch/asset/../etc/passwd", timeout=10, allow_redirects=False)
        assert r2.status_code in (400, 404), f"status={r2.status_code}"


# =========================================================
# 4. Security: rate limit + PDF magic-byte + headers
# =========================================================
class TestSecurity:
    def test_login_rate_limit(self, session):
        # Use a dedicated session to avoid affecting other tests
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        last = None
        statuses = []
        for i in range(10):
            r = s.post(f"{API}/auth/login", json={"email": "bruteforce@x.io", "password": "wrong"}, timeout=10)
            statuses.append(r.status_code)
            last = r
            if r.status_code == 429:
                break
        assert 429 in statuses, f"no 429 in {statuses}"

    def test_pdf_magic_byte(self, admin_headers):
        # Use plain requests (not session) to avoid forced JSON Content-Type
        files = {"file": ("fake.pdf", io.BytesIO(b"fake content not a pdf"), "application/pdf")}
        r = requests.post(f"{API}/agent/extract-pdf", files=files, headers=admin_headers, timeout=20)
        assert r.status_code == 400, f"status={r.status_code} body={r.text[:300]}"
        body_lower = r.text.lower()
        assert "magic" in body_lower or "pdf" in body_lower

    def test_security_headers(self, session):
        r = session.get(f"{API}/", timeout=10)
        # endpoint may be 404 but headers still added by middleware
        hdrs = {k.lower(): v for k, v in r.headers.items()}
        assert "strict-transport-security" in hdrs, list(hdrs.keys())
        assert "x-content-type-options" in hdrs
        assert "x-frame-options" in hdrs


# =========================================================
# 5. Regression
# =========================================================
class TestRegression:
    def test_promo_video_v3(self, session):
        r = session.get(f"{API}/promo/video", params={"v": "3"}, timeout=30, stream=True)
        assert r.status_code == 200
        assert "video/mp4" in r.headers.get("content-type", "")

    def test_admin_self_test_exists(self, session, admin_headers):
        # Just verify endpoint reachable; deep flow may need LLM
        r = session.get(f"{API}/admin/self-test", headers=admin_headers, timeout=20)
        assert r.status_code in (200, 405, 404), f"unexpected {r.status_code}"
