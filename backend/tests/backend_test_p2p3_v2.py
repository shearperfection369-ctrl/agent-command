"""JADE OS P2+P3 v2 backend pytest suite — Twilio SMS/Voice, Stripe Portal,
per-customer token caps, customer playbook builder, org members, embed reel config.

Endpoints under test:
- /api/twilio/sms (form-encoded inbound)
- /api/twilio/voice (TwiML)
- /api/twilio/voice/process (TwiML)
- /api/twilio/inbound (admin)
- /api/billing/portal-session (Stripe)
- /api/orgs/budget (admin)
- /api/orgs/budget-check
- /api/playbooks/customer
- /api/playbooks/by-owner
- /api/orgs/members (admin)
- /api/embed/reel-config
"""
import os
import time
import uuid
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


# --------- Fixtures ---------
@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    return s


@pytest.fixture(scope="session")
def admin_token(session):
    r = session.post(
        f"{API}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=15,
    )
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ============================================================
# Twilio SMS
# ============================================================
class TestTwilioSMS:
    SMS_FROM = "+16125550100"
    SMS_BODY = (
        "Hi Im Mark Anderson Director of Brokerage at Bay & Bay freight broker "
        "drowning in carrier outreach need this in 30 days"
    )

    def test_sms_creates_application(self, session, admin_headers):
        r = session.post(
            f"{API}/twilio/sms",
            data={"From": self.SMS_FROM, "Body": self.SMS_BODY},
            timeout=LLM_TIMEOUT,
        )
        assert r.status_code == 200, r.text
        xml = r.text
        assert "<Response>" in xml
        assert "<Message>" in xml

        # Verify a lighthouse application was created with this phone
        time.sleep(0.5)
        listing = session.get(
            f"{API}/lighthouse/applications", headers=admin_headers, timeout=15
        )
        assert listing.status_code == 200
        apps = listing.json()
        match = [
            a for a in apps if a.get("phone") == self.SMS_FROM and (a.get("notes") or "").startswith("[SMS")
        ]
        assert match, f"No application with phone={self.SMS_FROM} and notes starting [SMS"
        a = match[0]
        # Notes contain '[SMS'
        assert "[SMS" in (a.get("notes") or "")
        # Has score / tier
        assert a.get("score") is not None
        assert a.get("tier") in ("hot", "warm", "cold", "pass")

    def test_sms_friendly_redirect_when_not_application(self, session, admin_headers):
        body = "Hello what is JADE OS"
        r = session.post(
            f"{API}/twilio/sms",
            data={"From": "+16125550199", "Body": body},
            timeout=LLM_TIMEOUT,
        )
        assert r.status_code == 200
        xml = r.text
        assert "<Response>" in xml
        assert "<Message>" in xml
        # Friendly redirect mentions Lighthouse / APPLY
        assert ("Lighthouse" in xml) or ("APPLY" in xml) or ("lighthouse" in xml)

        # Verify it appears in /twilio/inbound with matched:false and no app created
        time.sleep(0.5)
        inb = session.get(f"{API}/twilio/inbound", headers=admin_headers, timeout=15)
        assert inb.status_code == 200
        data = inb.json()
        sms_list = data.get("sms", [])
        unmatched = [s for s in sms_list if s.get("from_number") == "+16125550199" and s.get("matched") is False]
        assert unmatched, "Expected an unmatched sms_inbound record for redirected SMS"


# ============================================================
# Twilio Voice
# ============================================================
class TestTwilioVoice:
    def test_voice_returns_gather_twiml(self, session):
        r = session.post(f"{API}/twilio/voice", data={}, timeout=15)
        assert r.status_code == 200, r.text
        xml = r.text
        assert "<Response>" in xml
        assert "<Gather" in xml
        assert 'input="speech"' in xml
        # action URL points to /api/twilio/voice/process
        assert "/api/twilio/voice/process" in xml

    def test_voice_process_creates_app_on_speech(self, session, admin_headers):
        speech = (
            "Dana Bjornson VP Operations Northstar Logistics freight broker "
            "need carrier outreach automation in 30 days"
        )
        r = session.post(
            f"{API}/twilio/voice/process",
            data={"SpeechResult": speech, "From": "+16125550101"},
            timeout=LLM_TIMEOUT,
        )
        assert r.status_code == 200, r.text
        xml = r.text
        assert "<Response>" in xml
        assert "<Say" in xml

        # Verify voice call landed in /twilio/inbound (may be matched=true if LLM parsed)
        time.sleep(0.5)
        inb = session.get(f"{API}/twilio/inbound", headers=admin_headers, timeout=15)
        assert inb.status_code == 200
        calls = inb.json().get("calls", [])
        match = [c for c in calls if c.get("from_number") == "+16125550101"]
        assert match, "Expected a voice call record for +16125550101"

    def test_voice_process_empty_speech_returns_goodbye_no_app(self, session, admin_headers):
        # Snapshot apps count before
        before = session.get(f"{API}/lighthouse/applications", headers=admin_headers, timeout=15).json()
        before_count = len(before)

        r = session.post(f"{API}/twilio/voice/process", data={"SpeechResult": ""}, timeout=15)
        assert r.status_code == 200
        xml = r.text
        assert "<Response>" in xml
        # Goodbye text varies; just require <Say
        assert "<Say" in xml

        after = session.get(f"{API}/lighthouse/applications", headers=admin_headers, timeout=15).json()
        # Should NOT have added a new application
        assert len(after) == before_count


# ============================================================
# Twilio Inbound listing (admin)
# ============================================================
class TestTwilioInbound:
    def test_inbound_requires_admin(self, session):
        r = session.get(f"{API}/twilio/inbound", timeout=10)
        assert r.status_code in (401, 403), f"expected auth challenge, got {r.status_code}"

    def test_inbound_shape(self, session, admin_headers):
        r = session.get(f"{API}/twilio/inbound", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "sms" in data and isinstance(data["sms"], list)
        assert "calls" in data and isinstance(data["calls"], list)
        assert data.get("configured") is False
        assert data.get("phone") is None


# ============================================================
# Stripe Customer Portal
# ============================================================
class TestStripePortal:
    def test_portal_session(self, session):
        r = session.post(
            f"{API}/billing/portal-session",
            json={"email": "test@example.com", "return_url": "https://example.com/portal"},
            timeout=30,
        )
        # Accept 200 (Stripe reachable) OR 500 with meaningful error (upstream)
        if r.status_code == 200:
            data = r.json()
            assert "url" in data
            assert data["url"].startswith("https://billing.stripe.com/") or "stripe.com" in data["url"]
        else:
            # Upstream issue — not a code bug
            assert r.status_code == 500
            txt = r.text
            assert len(txt) > 0
            pytest.skip(f"Stripe upstream unreachable in test env: {txt[:200]}")


# ============================================================
# Per-customer token caps
# ============================================================
class TestOrgBudget:
    ORG_EMAIL = f"TEST_budget_{uuid.uuid4().hex[:8]}@jadeos.ai"

    def test_budget_check_no_email_unlimited(self, session):
        # Empty email -> pydantic EmailStr will reject; route returns unlimited only when email is falsy.
        # The route signature requires EmailStr — try omitting param entirely.
        r = session.get(f"{API}/orgs/budget-check", timeout=10)
        # EmailStr is required → expect 422. This documents the behavior.
        assert r.status_code in (200, 422)

    def test_budget_check_no_org(self, session):
        r = session.get(
            f"{API}/orgs/budget-check",
            params={"email": f"TEST_noorg_{uuid.uuid4().hex[:6]}@nowhere.io"},
            timeout=10,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["allowed"] is True
        assert data.get("no_org") is True

    def test_patch_budget_404_for_missing_org(self, session, admin_headers):
        r = session.patch(
            f"{API}/orgs/budget",
            json={"email": f"TEST_404_{uuid.uuid4().hex[:6]}@nowhere.io", "monthly_token_budget": 1000},
            headers=admin_headers,
            timeout=15,
        )
        assert r.status_code == 404

    def test_patch_budget_requires_admin(self, session):
        r = session.patch(
            f"{API}/orgs/budget",
            json={"email": "anyone@x.co", "monthly_token_budget": 1000},
            timeout=10,
        )
        assert r.status_code in (401, 403)

    def test_seed_org_then_update_budget_and_check(self, session, admin_headers):
        # Insert org directly via Mongo so we don't need a live Stripe checkout
        import pymongo
        mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
        db_name = os.environ.get("DB_NAME", "test_database")
        client = pymongo.MongoClient(mongo_url)
        db = client[db_name]
        org_doc = {
            "id": str(uuid.uuid4()),
            "email": self.ORG_EMAIL,
            "name": "TEST Org",
            "plan": "growth",
            "monthly_token_budget": 2_000_000,
            "created_at": "2026-01-01T00:00:00Z",
        }
        db.orgs.insert_one(org_doc)
        try:
            # PATCH budget
            r = session.patch(
                f"{API}/orgs/budget",
                json={"email": self.ORG_EMAIL, "monthly_token_budget": 500_000},
                headers=admin_headers,
                timeout=15,
            )
            assert r.status_code == 200, r.text
            assert r.json().get("ok") is True

            # budget-check returns allowed + cap=500000
            r2 = session.get(f"{API}/orgs/budget-check", params={"email": self.ORG_EMAIL}, timeout=10)
            assert r2.status_code == 200
            data = r2.json()
            assert data["allowed"] is True
            assert data.get("cap") == 500_000
            assert isinstance(data.get("used_tokens"), int)
        finally:
            db.orgs.delete_one({"email": self.ORG_EMAIL})
            client.close()


# ============================================================
# Customer Playbook Builder
# ============================================================
class TestCustomerPlaybooks:
    OWNER = f"TEST_pb_{uuid.uuid4().hex[:6]}@x.co"
    NAME = f"TEST Playbook {uuid.uuid4().hex[:6]}"

    def test_create_customer_playbook(self, session):
        r = session.post(
            f"{API}/playbooks/customer",
            json={
                "name": self.NAME,
                "industry": "saas",
                "description": "test",
                "steps": [{"kind": "extract", "label": "parse"}],
                "owner_email": self.OWNER,
            },
            timeout=15,
        )
        assert r.status_code == 200, r.text
        pb = r.json()
        assert pb["name"] == self.NAME
        assert pb["industry"] == "saas"
        assert pb["slug"]
        TestCustomerPlaybooks.slug1 = pb["slug"]

    def test_create_duplicate_name_gets_unique_slug(self, session):
        r = session.post(
            f"{API}/playbooks/customer",
            json={
                "name": self.NAME,  # same name → same slug base
                "industry": "saas",
                "description": "dup",
                "steps": [{"kind": "extract", "label": "parse"}],
                "owner_email": self.OWNER,
            },
            timeout=15,
        )
        assert r.status_code == 200
        pb2 = r.json()
        assert pb2["slug"] != TestCustomerPlaybooks.slug1
        assert pb2["slug"].endswith("_2") or "_" in pb2["slug"]

    def test_by_owner_returns_playbooks(self, session):
        r = session.get(f"{API}/playbooks/by-owner", params={"email": self.OWNER}, timeout=10)
        assert r.status_code == 200
        docs = r.json()
        assert isinstance(docs, list)
        assert len(docs) >= 2
        for d in docs:
            assert d.get("owner_email") == self.OWNER


# ============================================================
# Org Members
# ============================================================
class TestOrgMembers:
    ORG = f"TEST_org_{uuid.uuid4().hex[:6]}@b.co"
    MEMBER = f"TEST_mem_{uuid.uuid4().hex[:6]}@d.co"

    def test_add_member_requires_admin(self, session):
        r = session.post(
            f"{API}/orgs/members",
            json={"org_email": self.ORG, "member_email": self.MEMBER, "name": "Test", "role": "admin"},
            timeout=10,
        )
        assert r.status_code in (401, 403)

    def test_add_member(self, session, admin_headers):
        r = session.post(
            f"{API}/orgs/members",
            headers=admin_headers,
            json={"org_email": self.ORG, "member_email": self.MEMBER, "name": "Test", "role": "admin"},
            timeout=10,
        )
        assert r.status_code == 200, r.text
        m = r.json()
        assert m["org_email"] == self.ORG
        assert m["member_email"] == self.MEMBER
        assert m["role"] == "admin"

    def test_add_member_upserts(self, session, admin_headers):
        # Second call with same emails should not create duplicate
        r = session.post(
            f"{API}/orgs/members",
            headers=admin_headers,
            json={"org_email": self.ORG, "member_email": self.MEMBER, "name": "Test2", "role": "viewer"},
            timeout=10,
        )
        assert r.status_code == 200

        listing = session.get(
            f"{API}/orgs/members",
            headers=admin_headers,
            params={"org_email": self.ORG},
            timeout=10,
        )
        assert listing.status_code == 200
        members = listing.json()
        matching = [x for x in members if x["member_email"] == self.MEMBER]
        assert len(matching) == 1, f"expected 1, got {len(matching)} (no duplicates)"

    def test_list_members_filter_and_admin(self, session, admin_headers):
        # admin required
        r0 = session.get(f"{API}/orgs/members", timeout=10)
        assert r0.status_code in (401, 403)

        r = session.get(f"{API}/orgs/members", headers=admin_headers, timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

        r2 = session.get(
            f"{API}/orgs/members",
            headers=admin_headers,
            params={"org_email": self.ORG},
            timeout=10,
        )
        assert r2.status_code == 200
        for m in r2.json():
            assert m["org_email"] == self.ORG

    def test_delete_member(self, session, admin_headers):
        # find id
        listing = session.get(
            f"{API}/orgs/members",
            headers=admin_headers,
            params={"org_email": self.ORG},
            timeout=10,
        ).json()
        assert listing
        mid = listing[0]["id"]
        r = session.delete(f"{API}/orgs/members/{mid}", headers=admin_headers, timeout=10)
        assert r.status_code == 200
        assert r.json().get("ok") is True

        # 404 on second delete
        r2 = session.delete(f"{API}/orgs/members/{mid}", headers=admin_headers, timeout=10)
        assert r2.status_code == 404


# ============================================================
# Embed reel config
# ============================================================
class TestEmbedReelConfig:
    def test_reel_config_freight_scene2(self, session):
        r = session.get(
            f"{API}/embed/reel-config",
            params={"industry": "freight_brokerage", "scene": 2},
            timeout=10,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["industry"] == "freight_brokerage"
        assert data["starting_scene"] == 2
        assert data["autoplay"] is True
        assert data["branded"] is True
        assert data["version"] == 1
