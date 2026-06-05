"""Iteration 9 · Risk Guard backend tests.

Covers:
  - Rate floor CRUD + audit
  - Quote validation severity bands + decisions (CLEAR/LOW/MEDIUM/HIGH/CRITICAL)
  - Below-cost-basis CRITICAL hard-block (P0 assertion)
  - Quote review approve/reject/override flows
  - Audit chain integrity
  - Historical floor (3+ actuals)
  - Formula floor math
  - Alerts persistence + ack
  - Webhook kind='alerts' literal
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://mpls-automation-hub.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@jadeos.ai"
ADMIN_PW = "JadeOS!2026"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PW}, timeout=15)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return r.json()["access_token"] if "access_token" in r.json() else r.json().get("token")


@pytest.fixture(scope="module")
def client(token):
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    return s


# Use unique-per-run lane for isolation
RUN_TAG = uuid.uuid4().hex[:6].upper()
ORIGIN = f"MSP{RUN_TAG}"
DEST = f"DFW{RUN_TAG}"
EQUIP = "R53"
LANE_KEY = f"{ORIGIN}|{DEST}|{EQUIP}"


# ----------------- Rate Floor CRUD -----------------

class TestRateFloorCRUD:
    floor_id = None

    def test_create_floor(self, client):
        r = client.post(f"{API}/rate-floors", json={
            "origin": ORIGIN, "destination": DEST, "equipment": EQUIP,
            "floor_rate_usd": 1200, "cost_basis_usd": 900,
            "rationale": "TEST_iteration9",
        }, timeout=15)
        assert r.status_code == 200, r.text
        f = r.json()
        assert f["lane_key"] == LANE_KEY, f"lane_key not normalized: {f['lane_key']}"
        assert f["floor_rate_usd"] == 1200
        assert f["cost_basis_usd"] == 900
        assert f["source"] == "manual"
        assert "_id" not in f
        TestRateFloorCRUD.floor_id = f["id"]

    def test_list_includes_created(self, client):
        r = client.get(f"{API}/rate-floors?lane_key={LANE_KEY}", timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        ids = [f["id"] for f in body["floors"]]
        assert TestRateFloorCRUD.floor_id in ids

    def test_audit_event_for_create(self, client):
        r = client.get(f"{API}/audit/events?target_type=rate_floor&target_id={TestRateFloorCRUD.floor_id}", timeout=15)
        assert r.status_code == 200
        events = r.json()["events"]
        actions = [e["action"] for e in events]
        assert "rate_floor.created" in actions


# ----------------- Quote validation: CRITICAL -----------------

class TestQuoteValidationCritical:
    review_id = None

    def test_critical_hard_block(self, client):
        # proposed=800, carrier_pay=900, fuel=100 → cost_basis=1000, floor=1200
        # 800 ≤ 1000 → CRITICAL + HARD_BLOCK
        r = client.post(f"{API}/quotes/validate", json={
            "proposed_rate_usd": 800,
            "carrier_pay_usd": 900,
            "fuel_surcharge_usd": 100,
            "origin": ORIGIN, "destination": DEST, "equipment": EQUIP,
            "customer": "TEST_critical_customer",
        }, timeout=15)
        assert r.status_code == 200, r.text
        v = r.json()
        assert v["severity"] == "CRITICAL", f"Expected CRITICAL got {v['severity']}"
        assert v["decision"] == "HARD_BLOCK", f"Expected HARD_BLOCK got {v['decision']}"
        # breach against floor 1200 - 800 = 400
        assert v["breach_amount_usd"] == 400.0, f"Got breach {v['breach_amount_usd']}"
        assert v["status"] == "pending"
        # below_cost_basis indicator can be in floor_candidates or top-level — verify cost basis was honored
        # The floor that wins should be manual (1200) but cost_basis=900 from manual record
        assert v["floor_rate_usd"] == 1200.0
        assert v["cost_basis_usd"] == 900.0
        TestQuoteValidationCritical.review_id = v["id"]

    def test_critical_fires_alert(self, client):
        r = client.get(f"{API}/alerts/unread", timeout=15)
        assert r.status_code == 200
        alerts = r.json()["alerts"]
        # at least one with CRITICAL/page severity referencing our customer
        assert any("TEST_critical_customer" in a.get("title", "") or
                   a.get("metadata", {}).get("quote_review_id") == TestQuoteValidationCritical.review_id
                   for a in alerts), "No alert fired for CRITICAL quote"

    def test_critical_review_in_queue(self, client):
        r = client.get(f"{API}/quote-reviews?severity=CRITICAL", timeout=15)
        assert r.status_code == 200
        rows = r.json()["reviews"]
        assert any(rev["id"] == TestQuoteValidationCritical.review_id for rev in rows)

    def test_override_requires_notes(self, client):
        rid = TestQuoteValidationCritical.review_id
        r = client.post(f"{API}/quote-reviews/{rid}/override", timeout=15)
        assert r.status_code == 400, f"Override without notes should 400; got {r.status_code} {r.text}"

    def test_override_with_notes_succeeds(self, client):
        rid = TestQuoteValidationCritical.review_id
        r = client.post(f"{API}/quote-reviews/{rid}/override?notes=TEST_operator_accepts_risk", timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["status"] == "overridden"
        assert body["reviewer_notes"] == "TEST_operator_accepts_risk"


# ----------------- Severity bands -----------------

class TestSeverityBands:
    def test_medium_at_10pct(self, client):
        # floor=1200; proposed=1080 → breach=120 = 10% exactly → MEDIUM (≤ boundary)
        r = client.post(f"{API}/quotes/validate", json={
            "proposed_rate_usd": 1080,
            "origin": ORIGIN, "destination": DEST, "equipment": EQUIP,
            "customer": "TEST_medium",
        }, timeout=15)
        assert r.status_code == 200, r.text
        v = r.json()
        assert v["severity"] == "MEDIUM", f"10% breach expected MEDIUM, got {v['severity']} (breach_pct={v['breach_pct']})"
        assert v["decision"] == "QUEUE_REVIEW"
        assert v["status"] == "pending"

    def test_high_above_10pct(self, client):
        # floor=1200; proposed=1000 → breach=200 = 16.67% → HIGH
        r = client.post(f"{API}/quotes/validate", json={
            "proposed_rate_usd": 1000,
            "origin": ORIGIN, "destination": DEST, "equipment": EQUIP,
            "customer": "TEST_high",
        }, timeout=15)
        assert r.status_code == 200, r.text
        v = r.json()
        assert v["severity"] == "HIGH", f"16.67% breach expected HIGH, got {v['severity']}"
        assert v["decision"] == "QUEUE_REVIEW"

    def test_clear_above_floor(self, client):
        # proposed=1300 > floor=1200 → CLEAR + AUTO_OK
        r = client.post(f"{API}/quotes/validate", json={
            "proposed_rate_usd": 1300,
            "origin": ORIGIN, "destination": DEST, "equipment": EQUIP,
            "customer": "TEST_clear",
        }, timeout=15)
        assert r.status_code == 200, r.text
        v = r.json()
        assert v["severity"] == "CLEAR"
        assert v["status"] == "auto_ok"

    def test_low_within_5pct(self, client):
        # floor=1200; proposed=1160 → breach=40 = 3.33% → LOW + AUTO_OK
        r = client.post(f"{API}/quotes/validate", json={
            "proposed_rate_usd": 1160,
            "origin": ORIGIN, "destination": DEST, "equipment": EQUIP,
            "customer": "TEST_low",
        }, timeout=15)
        assert r.status_code == 200, r.text
        v = r.json()
        assert v["severity"] == "LOW", f"3.33% breach expected LOW, got {v['severity']}"
        assert v["status"] == "auto_ok"


# ----------------- Review workflow approve/reject -----------------

class TestReviewWorkflow:
    medium_id = None

    def test_create_medium_review(self, client):
        r = client.post(f"{API}/quotes/validate", json={
            "proposed_rate_usd": 1100,  # ~8.33% breach → MEDIUM
            "origin": ORIGIN, "destination": DEST, "equipment": EQUIP,
            "customer": "TEST_workflow_medium",
        }, timeout=15)
        assert r.status_code == 200
        v = r.json()
        assert v["severity"] == "MEDIUM"
        TestReviewWorkflow.medium_id = v["id"]

    def test_approve(self, client):
        rid = TestReviewWorkflow.medium_id
        r = client.post(f"{API}/quote-reviews/{rid}/approve?notes=TEST_ok", timeout=15)
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "approved"

    def test_double_approve_blocked(self, client):
        rid = TestReviewWorkflow.medium_id
        r = client.post(f"{API}/quote-reviews/{rid}/approve?notes=again", timeout=15)
        assert r.status_code == 400  # already approved

    def test_reject_separate_review(self, client):
        # create another MEDIUM and reject it
        r = client.post(f"{API}/quotes/validate", json={
            "proposed_rate_usd": 1100,
            "origin": ORIGIN, "destination": DEST, "equipment": EQUIP,
            "customer": "TEST_reject_flow",
        }, timeout=15).json()
        rid = r["id"]
        rj = client.post(f"{API}/quote-reviews/{rid}/reject?notes=TEST_no", timeout=15)
        assert rj.status_code == 200
        assert rj.json()["status"] == "rejected"


# ----------------- Formula floor (no manual) -----------------

class TestFormulaFloor:
    def test_formula_math(self, client):
        lane_o = f"PHX{RUN_TAG}"
        lane_d = f"SEA{RUN_TAG}"
        # carrier_pay=1000, fuel=50, margin=0.12 → floor = 1000*1.12 + 50 = 1170
        r = client.post(f"{API}/quotes/validate", json={
            "proposed_rate_usd": 1170,  # = floor, CLEAR
            "carrier_pay_usd": 1000, "fuel_surcharge_usd": 50,
            "origin": lane_o, "destination": lane_d, "equipment": "V53",
            "customer": "TEST_formula",
        }, timeout=15)
        assert r.status_code == 200, r.text
        v = r.json()
        assert v["floor_source"] == "formula"
        assert abs(v["floor_rate_usd"] - 1170.0) < 0.01, f"Formula floor wrong: {v['floor_rate_usd']}"


# ----------------- Historical floor -----------------

class TestHistoricalFloor:
    def test_historical_kicks_in_after_3_actuals(self, client):
        lane_o = f"BOS{RUN_TAG}"
        lane_d = f"MIA{RUN_TAG}"
        rates = [1500, 1600, 1700, 1800]
        for q in rates:
            r = client.post(f"{API}/rate-actuals", json={
                "origin": lane_o, "destination": lane_d, "equipment": "V53",
                "quoted_rate_usd": q, "carrier_pay_usd": q * 0.85, "fuel_surcharge_usd": 50,
            }, timeout=15)
            assert r.status_code == 200, r.text

        # Now validate with NO manual floor, NO carrier_pay (so formula won't apply)
        r = client.post(f"{API}/quotes/validate", json={
            "proposed_rate_usd": 1550,
            "origin": lane_o, "destination": lane_d, "equipment": "V53",
            "customer": "TEST_historical",
        }, timeout=15)
        assert r.status_code == 200, r.text
        v = r.json()
        assert v["floor_source"] == "historical", f"Expected historical source, got {v['floor_source']}"


# ----------------- Audit chain -----------------

class TestAuditChain:
    def test_verify_returns_ok(self, client):
        r = client.get(f"{API}/audit/verify", timeout=30)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["ok"] is True, f"Audit chain broken: {body}"
        assert body["checked"] > 0

    def test_filter_by_action_prefix(self, client):
        r = client.get(f"{API}/audit/events?action_prefix=quote.&limit=100", timeout=15)
        assert r.status_code == 200
        actions = [e["action"] for e in r.json()["events"]]
        assert all(a.startswith("quote.") for a in actions)
        assert len(actions) > 0

    def test_filter_by_target_type(self, client):
        r = client.get(f"{API}/audit/events?target_type=quote_review&limit=50", timeout=15)
        assert r.status_code == 200
        rows = r.json()["events"]
        assert len(rows) > 0
        assert all(e["target_type"] == "quote_review" for e in rows)


# ----------------- Alerts -----------------

class TestAlerts:
    def test_unread_lists_then_ack_one(self, client):
        r = client.get(f"{API}/alerts/unread", timeout=15)
        assert r.status_code == 200
        unread = r.json()["alerts"]
        if not unread:
            pytest.skip("no unread alerts to ack")
        aid = unread[0]["id"]
        ack = client.post(f"{API}/alerts/{aid}/ack", timeout=15)
        assert ack.status_code == 200

    def test_ack_all(self, client):
        r = client.post(f"{API}/alerts/ack-all", timeout=15)
        assert r.status_code == 200
        # then unread should be empty
        u = client.get(f"{API}/alerts/unread", timeout=15)
        assert u.status_code == 200
        assert u.json()["count"] == 0


# ----------------- Webhook kind='alerts' literal -----------------

class TestAlertsWebhook:
    hook_id = None

    def test_create_alerts_webhook(self, client):
        r = client.post(f"{API}/webhooks", json={
            "kind": "alerts",
            "url": "https://example.com/test-alerts-webhook",
            "name": "TEST_alerts_hook",
            "label": "TEST_alerts_hook",
            "active": True,
        }, timeout=15)
        assert r.status_code == 200, r.text
        TestAlertsWebhook.hook_id = r.json().get("id") or r.json().get("webhook", {}).get("id")
        assert TestAlertsWebhook.hook_id

    def test_cleanup_webhook(self, client):
        if not TestAlertsWebhook.hook_id:
            pytest.skip("no webhook created")
        r = client.delete(f"{API}/webhooks/{TestAlertsWebhook.hook_id}", timeout=15)
        assert r.status_code in (200, 204)


# ----------------- Cleanup -----------------

def test_zzz_cleanup_floor(client):
    fid = TestRateFloorCRUD.floor_id
    if not fid:
        pytest.skip("no floor created")
    r = client.delete(f"{API}/rate-floors/{fid}", timeout=15)
    assert r.status_code == 200
    # confirm audit event written
    a = client.get(f"{API}/audit/events?target_type=rate_floor&target_id={fid}", timeout=15)
    actions = [e["action"] for e in a.json()["events"]]
    assert "rate_floor.deleted" in actions
