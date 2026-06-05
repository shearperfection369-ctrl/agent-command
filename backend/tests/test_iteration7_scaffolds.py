"""
Iteration 7 — JADE OS scaffolds testing.

Covers:
  • GET  /api/admin/integrations-scaffold  (sentry/rag/client_auth/resend status + activate_hints)
  • POST /api/rag/ingest, /api/rag/query, GET /api/rag/tenant/{id}, DELETE /api/rag/tenant/{id}/{doc}
  • POST /api/client/auth/request-magic-link, /api/client/auth/verify
  • GET  /api/client/me  (and cross-aud token rejection)
"""
import os
import re
import time
import uuid
import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") if "REACT_APP_BACKEND_URL" in os.environ else None
if not BASE_URL:
    # fall back to frontend/.env at test-collection time
    import pathlib
    env = pathlib.Path("/app/frontend/.env").read_text()
    m = re.search(r"REACT_APP_BACKEND_URL=(\S+)", env)
    BASE_URL = m.group(1).rstrip("/")

ADMIN_EMAIL = "admin@jadeos.ai"
ADMIN_PASSWORD = "JadeOS!2026"


@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"admin login failed: {r.status_code} {r.text[:200]}")
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ----------------------------- Integrations scaffold -----------------------------
class TestIntegrationsScaffold:
    def test_requires_admin(self):
        r = requests.get(f"{BASE_URL}/api/admin/integrations-scaffold", timeout=15)
        assert r.status_code in (401, 403)

    def test_scaffold_contract(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/integrations-scaffold",
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        # all four scaffold blocks present
        for k in ("sentry", "rag", "client_auth", "resend"):
            assert k in d, f"missing scaffold block: {k}"
            assert "activate_hint" in d[k], f"missing activate_hint in {k}"
            assert isinstance(d[k]["activate_hint"], str) and len(d[k]["activate_hint"]) > 0
        # sanity on individual blocks
        assert "configured" in d["sentry"]
        assert "provider" in d["rag"]
        assert "magic_link_ttl_min" in d["client_auth"]
        assert "sender" in d["resend"]
        assert "scaffold_principle" in d


# ----------------------------- RAG per-tenant ------------------------------------
class TestRagTenantIsolation:
    TENANT_A = "TEST_acme-freight"
    TENANT_B = "TEST_other"

    def test_ingest_requires_admin(self):
        r = requests.post(f"{BASE_URL}/api/rag/ingest",
                          json={"tenant_id": "x", "title": "y", "content": "z"}, timeout=15)
        assert r.status_code in (401, 403)

    def test_full_flow(self, admin_headers):
        # Ingest into tenant A
        body = {"tenant_id": self.TENANT_A, "title": "TEST_carrier",
                "content": "reefer carrier MN to TX with chassis"}
        r = requests.post(f"{BASE_URL}/api/rag/ingest", json=body,
                          headers=admin_headers, timeout=20)
        assert r.status_code == 200, r.text
        doc = r.json()
        assert doc["tenant_id"] == self.TENANT_A
        assert doc["title"] == "TEST_carrier"
        assert "id" in doc
        doc_id = doc["id"]

        # Query tenant A -- should hit
        r = requests.post(f"{BASE_URL}/api/rag/query",
                          json={"tenant_id": self.TENANT_A,
                                "question": "reefer MN TX", "k": 5}, timeout=20)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["tenant_id"] == self.TENANT_A
        assert isinstance(d["hits"], list)
        assert len(d["hits"]) >= 1, f"tenant A query should return at least 1 hit: {d}"
        assert any(h["id"] == doc_id for h in d["hits"]), "ingested doc not retrievable"

        # Query tenant B -- should return 0 hits (isolation)
        r = requests.post(f"{BASE_URL}/api/rag/query",
                          json={"tenant_id": self.TENANT_B,
                                "question": "reefer MN TX", "k": 5}, timeout=20)
        assert r.status_code == 200, r.text
        assert len(r.json()["hits"]) == 0, "tenant B should be isolated from A"

        # List tenant A docs
        r = requests.get(f"{BASE_URL}/api/rag/tenant/{self.TENANT_A}",
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200
        listing = r.json()
        assert listing["tenant_id"] == self.TENANT_A
        assert any(x["id"] == doc_id for x in listing["docs"])

        # Delete the doc
        r = requests.delete(f"{BASE_URL}/api/rag/tenant/{self.TENANT_A}/{doc_id}",
                            headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json().get("ok") is True

        # Verify deletion -- query returns 0 hits
        r = requests.post(f"{BASE_URL}/api/rag/query",
                          json={"tenant_id": self.TENANT_A,
                                "question": "reefer MN TX", "k": 5}, timeout=15)
        assert r.status_code == 200
        assert len(r.json()["hits"]) == 0, "doc should be removed after delete"

        # Verify list is empty now
        r = requests.get(f"{BASE_URL}/api/rag/tenant/{self.TENANT_A}",
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200
        assert not any(x["id"] == doc_id for x in r.json()["docs"])


# ----------------------------- Client magic-link auth ----------------------------
class TestClientMagicLink:
    EMAIL = f"TEST_design+{uuid.uuid4().hex[:6]}@partner.com"
    COMPANY = "Partner Inc TEST"

    def test_request_magic_link_returns_link_preview_mode(self):
        r = requests.post(f"{BASE_URL}/api/client/auth/request-magic-link",
                          json={"email": self.EMAIL, "company": self.COMPANY},
                          timeout=20)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("ok") is True
        assert "expires" in d
        # Either email was sent (Resend wired) or magic_url is present
        assert d.get("email_sent") is True or d.get("magic_url"), "must return magic_url in preview"
        if d.get("magic_url"):
            assert "/client/verify?token=" in d["magic_url"]
            type(self).MAGIC_URL = d["magic_url"]
            type(self).TOKEN = d["magic_url"].split("token=", 1)[1]

    def test_verify_returns_session_jwt_and_me_works(self, admin_token):
        if not hasattr(self, "TOKEN"):
            pytest.skip("magic link not minted (Resend wired?)")
        # verify
        r = requests.post(f"{BASE_URL}/api/client/auth/verify",
                          json={"token": self.TOKEN}, timeout=15)
        assert r.status_code == 200, r.text
        v = r.json()
        assert "token" in v
        assert v["user"]["email"] == self.EMAIL.lower()
        client_jwt = v["token"]

        # /api/client/me works with this client JWT
        r = requests.get(f"{BASE_URL}/api/client/me",
                         headers={"Authorization": f"Bearer {client_jwt}"}, timeout=15)
        assert r.status_code == 200, r.text
        me = r.json()
        assert me["user"]["email"] == self.EMAIL.lower()
        assert "org" in me
        assert "runs" in me and isinstance(me["runs"], list)

        # Cross-aud rejection: client JWT must NOT be accepted on admin route
        r = requests.get(f"{BASE_URL}/api/leads",
                         headers={"Authorization": f"Bearer {client_jwt}"}, timeout=15)
        assert r.status_code in (401, 403), (
            f"client JWT should NOT pass admin auth; got {r.status_code}: {r.text[:200]}"
        )

        # And reverse: admin JWT must NOT be accepted on /client/me
        r = requests.get(f"{BASE_URL}/api/client/me",
                         headers={"Authorization": f"Bearer {admin_token}"}, timeout=15)
        assert r.status_code in (401, 403), (
            f"admin JWT should NOT pass client auth; got {r.status_code}: {r.text[:200]}"
        )

    def test_verify_with_bad_token_400(self):
        r = requests.post(f"{BASE_URL}/api/client/auth/verify",
                          json={"token": "not-a-real-token"}, timeout=15)
        assert r.status_code == 400

    def test_client_me_requires_token(self):
        r = requests.get(f"{BASE_URL}/api/client/me", timeout=15)
        assert r.status_code in (401, 403)
