"""Iteration 10 · REAL MN freight leads + CSV import + tailor-hook tests.

Covers:
- /api/leads/fmcsa-status (scaffold mode, FMCSA_WEBKEY empty)
- /api/leads/seed-real-mn idempotency
- /api/prospects new response shape (summary + source/verified filters)
- /api/leads/import-csv (verify, reject malformed)
- /api/leads/{id}/enrich-fmcsa graceful degrade (no 500)
- /api/leads/{id}/tailor-hook on real lead (facts-grounded)
- /api/leads/{id}/tailor-hook on synthetic lead → 400
- Legacy backfill: is_synthetic=true on pre-existing prospects
- /api/prospects/generate stamps is_synthetic=true
"""
import os
import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@jadeos.ai")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "JadeOS!2026")


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def token(session):
    r = session.post(f"{BASE_URL}/api/auth/login",
                     json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    tok = r.json().get("token") or r.json().get("access_token")
    assert tok, f"no token in login response: {r.json()}"
    return tok


@pytest.fixture(scope="module")
def auth(session, token):
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session


# ---------- FMCSA status ----------
class TestFmcsaStatus:
    def test_status_scaffold(self, auth):
        r = auth.get(f"{BASE_URL}/api/leads/fmcsa-status")
        assert r.status_code == 200
        data = r.json()
        assert data["live_lookups_configured"] is False
        assert data["curated_seed_count"] == 14
        assert "activate_hint" in data
        assert "FMCSA_WEBKEY" in data["activate_hint"]


# ---------- Seed Real MN ----------
class TestSeedRealMn:
    def test_seed_idempotent(self, auth):
        r1 = auth.post(f"{BASE_URL}/api/leads/seed-real-mn")
        assert r1.status_code == 200
        d1 = r1.json()
        # First call OR repeat — total inserted+updated must equal seed size (14)
        assert d1["inserted"] + d1["updated"] == d1["total_in_seed"] == 14
        assert d1["live_lookups_active"] is False

        # Second call: must be all updates, zero inserts
        r2 = auth.post(f"{BASE_URL}/api/leads/seed-real-mn")
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2["inserted"] == 0
        assert d2["updated"] == 14

    def test_seeded_rows_real(self, auth):
        r = auth.get(f"{BASE_URL}/api/prospects?source=real")
        assert r.status_code == 200
        rows = r.json()["prospects"]
        assert len(rows) >= 14
        # Find CH Robinson row
        chr_row = next((p for p in rows if "Robinson" in p["company"]), None)
        assert chr_row is not None, "C.H. Robinson not present in real prospects"
        assert chr_row["is_synthetic"] is False
        assert chr_row["is_verified"] is True
        assert chr_row["verification_source"] == "curated_seed"
        assert chr_row["dot_number"] == "451058"
        assert chr_row["mc_number"] == "MC-209528"


# ---------- Prospects list shape ----------
class TestProspectsShape:
    def test_summary_fields(self, auth):
        r = auth.get(f"{BASE_URL}/api/prospects")
        assert r.status_code == 200
        body = r.json()
        assert "prospects" in body
        assert "count" in body
        assert "summary" in body
        s = body["summary"]
        for k in ("total", "synthetic", "verified", "real"):
            assert k in s, f"summary missing {k}"
            assert isinstance(s[k], int)
        assert s["total"] == s["synthetic"] + s["real"]

    def test_filter_source_real(self, auth):
        r = auth.get(f"{BASE_URL}/api/prospects?source=real")
        assert r.status_code == 200
        for p in r.json()["prospects"]:
            assert p.get("is_synthetic") is not True, f"Row {p['company']} should be real"

    def test_filter_source_synthetic(self, auth):
        r = auth.get(f"{BASE_URL}/api/prospects?source=synthetic")
        assert r.status_code == 200
        for p in r.json()["prospects"]:
            assert p["is_synthetic"] is True, f"Row {p['company']} should be synthetic"

    def test_filter_verified_only(self, auth):
        r = auth.get(f"{BASE_URL}/api/prospects?verified_only=true")
        assert r.status_code == 200
        for p in r.json()["prospects"]:
            assert p.get("is_verified") is True


# ---------- CSV Import ----------
class TestCsvImport:
    def test_import_with_mixed_rows(self, auth):
        payload = {
            "rows": [
                {"company": "TEST_Acme Brokerage", "email": "ops@example.com",
                 "name": "Jane Smith", "city": "Plymouth", "state": "MN"},
                {"company": "TEST_Bad", "email": "not-an-email"},
                {"company": "", "email": "a@b.com"},
            ],
            "industry_default": "freight_brokerage",
        }
        r = auth.post(f"{BASE_URL}/api/leads/import-csv", json=payload)
        assert r.status_code == 200, r.text
        d = r.json()
        # 1 valid row inserted/updated
        assert d["inserted"] + d["updated"] == 1
        # example.com resolves so 1 verified
        assert d["verified"] == 1
        # 2 rejected
        assert d["rejected_count"] == 2
        reasons = [x["reason"] for x in d["rejected"]]
        assert "invalid email format" in reasons
        assert "missing company or email" in reasons

    def test_import_idempotent(self, auth):
        payload = {
            "rows": [{"company": "TEST_Acme Brokerage", "email": "ops@example.com"}],
            "industry_default": "freight_brokerage",
        }
        r = auth.post(f"{BASE_URL}/api/leads/import-csv", json=payload)
        assert r.status_code == 200
        d = r.json()
        assert d["inserted"] == 0  # already exists from previous test
        assert d["updated"] == 1


# ---------- Enrich FMCSA (graceful degrade) ----------
class TestEnrichFmcsa:
    def test_enrich_without_key(self, auth):
        # find a row with dot_number
        rows = auth.get(f"{BASE_URL}/api/prospects?source=real").json()["prospects"]
        with_dot = next((p for p in rows if p.get("dot_number")), None)
        assert with_dot, "no real lead with dot_number"
        r = auth.post(f"{BASE_URL}/api/leads/{with_dot['id']}/enrich-fmcsa")
        # MUST NOT 500
        assert r.status_code == 200, f"enrich-fmcsa should not 500: {r.status_code} {r.text}"
        d = r.json()
        assert d["ok"] is False
        assert d["reason"] == "fmcsa_not_configured"
        assert "FMCSA_WEBKEY" in d["hint"]


# ---------- Tailor Hook ----------
class TestTailorHook:
    def test_tailor_real_lead(self, auth):
        rows = auth.get(f"{BASE_URL}/api/prospects?source=real").json()["prospects"]
        chr_row = next((p for p in rows if "Robinson" in p["company"]), None)
        assert chr_row, "C.H. Robinson must be seeded"
        r = auth.post(f"{BASE_URL}/api/leads/{chr_row['id']}/tailor-hook", timeout=90)
        assert r.status_code == 200, f"tailor-hook failed: {r.status_code} {r.text}"
        d = r.json()
        assert d["pain_point"], "pain_point empty"
        assert d["hook"], "hook empty"
        assert d["subject"]
        assert d["body"]
        assert "facts_used" in d
        # verify the hook+pain reference at least one verifiable fact
        combined = (d["pain_point"] + " " + d["hook"] + " " + d["body"]).lower()
        fact_hits = [
            "robinson", "chrobinson", "eden prairie", "209528", "451058",
            "15,000", "chrw", "nasdaq", "3pl",
        ]
        assert any(h in combined for h in fact_hits), \
            f"tailor output does not reference verifiable facts. Got: {combined[:300]}"

    def test_tailor_synthetic_refused(self, auth):
        # Get a synthetic prospect
        rows = auth.get(f"{BASE_URL}/api/prospects?source=synthetic").json()["prospects"]
        if not rows:
            # generate one (small count)
            g = auth.post(f"{BASE_URL}/api/prospects/generate",
                          json={"industry": "general", "count": 2}, timeout=90)
            assert g.status_code == 200, g.text
            rows = g.json().get("prospects", [])
        assert rows, "no synthetic prospects to test refusal"
        syn = rows[0]
        r = auth.post(f"{BASE_URL}/api/leads/{syn['id']}/tailor-hook")
        assert r.status_code == 400
        detail = r.json().get("detail", "").lower()
        assert "synthetic" in detail


# ---------- Generate stamps synthetic ----------
class TestGenerateStampsSynthetic:
    def test_generate_synthetic(self, auth):
        r = auth.post(f"{BASE_URL}/api/prospects/generate",
                      json={"industry": "general", "count": 2}, timeout=120)
        assert r.status_code == 200, r.text
        d = r.json()
        prospects = d.get("prospects", [])
        assert len(prospects) >= 1
        for p in prospects:
            assert p.get("is_synthetic") is True
            assert p.get("is_verified") is False
            assert p.get("verification_source") == "ai_synthesized"


# ---------- Legacy backfill ----------
class TestLegacyBackfill:
    def test_no_unbackfilled_rows(self, auth):
        # After backfill on startup, no record should be missing is_synthetic
        r = auth.get(f"{BASE_URL}/api/prospects?source=synthetic")
        assert r.status_code == 200
        summary = r.json().get("summary", {})
        # synthetic count should be ≥ 11 (the legacy AI records + any new)
        assert summary["synthetic"] >= 11, f"expected ≥11 synthetic, got {summary['synthetic']}"
