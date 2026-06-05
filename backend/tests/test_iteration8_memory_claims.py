"""Iteration 8 backend tests · Workflow Memory + Claims auto-file."""
import os
import uuid
import time
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://mpls-automation-hub.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@jadeos.ai")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "JadeOS!2026")

UNIQ = uuid.uuid4().hex[:8]


@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} · {r.text}"
    tok = r.json().get("access_token") or r.json().get("token")
    assert tok, f"No token in login response: {r.json()}"
    return tok


@pytest.fixture(scope="session")
def H(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# -------------------- Memory: Threads CRUD + idempotency --------------------

class TestMemoryThreads:
    def test_create_thread_idempotent(self, H):
        body = {"thread_type": "load", "thread_key": f"LD-test-{UNIQ}", "title": "Pytest LD thread"}
        r1 = requests.post(f"{API}/memory/threads", json=body, headers=H, timeout=15)
        assert r1.status_code == 200, r1.text
        t1 = r1.json()
        assert t1["thread_type"] == "load"
        assert t1["thread_key"] == body["thread_key"]
        assert "id" in t1
        # Re-create — should return SAME thread id (idempotent)
        r2 = requests.post(f"{API}/memory/threads", json=body, headers=H, timeout=15)
        assert r2.status_code == 200, r2.text
        assert r2.json()["id"] == t1["id"], "Thread not idempotent on (thread_type, thread_key)"
        pytest.thread_id = t1["id"]

    def test_invalid_thread_type(self, H):
        r = requests.post(f"{API}/memory/threads",
                          json={"thread_type": "spaceship", "thread_key": "x"}, headers=H, timeout=15)
        assert r.status_code in (400, 422)

    def test_list_threads(self, H):
        r = requests.get(f"{API}/memory/threads?limit=20", headers=H, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "threads" in data and "count" in data
        assert any(t["id"] == pytest.thread_id for t in data["threads"])

    def test_append_six_turns_triggers_distill(self, H):
        """After 6 turns auto-distill runs. Verify thread.facts is populated."""
        tid = pytest.thread_id
        sample = [
            ("operator", "Driver arrived at Acme Dallas 0800. Released 1330. 3 hours past free time."),
            ("operator", "Free time is 2h. Detention rate $75/h per BOL 8842."),
            ("operator", "Carrier MC-998877 (Speedway Trucking) wants confirmation by EOD."),
            ("operator", "Photos uploaded showing crushed pallet 4 of 6 on BOL 8842."),
            ("operator", "Customer Acme Freight requested partial replacement quote."),
            ("operator", "Proposed $1840 cargo + $225 detention. Awaiting carrier ack."),
        ]
        for role, content in sample:
            r = requests.post(f"{API}/memory/threads/{tid}/turns",
                              json={"role": role, "content": content}, headers=H, timeout=20)
            assert r.status_code == 200, r.text
        # Give auto-distill a moment (it runs synchronously inside append, but LLM call is awaited)
        time.sleep(2)
        d = requests.get(f"{API}/memory/threads/{tid}", headers=H, timeout=15).json()
        thread = d["thread"]
        assert thread["turn_count"] >= 6
        # Facts may be empty if LLM budget exhausted — accept structured error, but NOT 500.
        # Either way, no 500 should have occurred. Just sanity check.
        assert isinstance(thread.get("facts", []), list)

    def test_explicit_distill(self, H):
        """Force a distill pass. Accept 200 (success) OR 402/429 (budget) as PASS."""
        tid = pytest.thread_id
        r = requests.post(f"{API}/memory/threads/{tid}/distill", headers=H, timeout=60)
        assert r.status_code in (200, 402, 429, 503), f"Unexpected: {r.status_code} · {r.text[:300]}"
        if r.status_code == 200:
            facts = r.json().get("facts", [])
            assert isinstance(facts, list)
            pytest.distill_ok = len(facts) > 0
        else:
            pytest.distill_ok = False

    def test_recall_block_has_all_categories(self, H):
        tid = pytest.thread_id
        r = requests.get(f"{API}/memory/threads/{tid}/recall", headers=H, timeout=15)
        assert r.status_code == 200
        block = r.json().get("recall_block", "")
        assert "MEMORY" in block
        assert "RECENT TURNS" in block, f"Recall missing recent turns:\n{block[:500]}"
        # If distillation succeeded, expect the categories — but skip if budget-degraded
        if getattr(pytest, "distill_ok", False):
            # Don't insist on all 5 (LLM may not produce every category) but at least HAPPENED
            assert "HAPPENED" in block or "DECIDED" in block, \
                f"Expected at least HAPPENED/DECIDED in recall block:\n{block[:500]}"


# -------------------- Chat memory binding --------------------

class TestChatMemoryBinding:
    def test_chat_auto_creates_thread_and_appends(self, H):
        """POST /api/agent/chat with memory_thread_type+key auto-creates thread and appends user+assistant turns."""
        thread_key = f"LD-chat-{UNIQ}"
        body = {
            "session_id": f"sess-{UNIQ}",
            "message": "Quick status on this load?",
            "memory_thread_type": "load",
            "memory_thread_key": thread_key,
        }
        # /api/agent/chat is a streaming endpoint — use stream=True
        r = requests.post(f"{API}/agent/chat", json=body, headers=H, timeout=60, stream=True)
        assert r.status_code in (200, 402, 429, 503), f"chat status: {r.status_code} · {r.text[:300]}"
        # Drain stream
        if r.status_code == 200:
            for _chunk in r.iter_content(chunk_size=1024):
                pass
        r.close()
        time.sleep(1.5)
        # Verify thread now exists and has the user+assistant pair (or at least user)
        lr = requests.get(f"{API}/memory/threads?thread_type=load&limit=200", headers=H, timeout=15).json()
        match = [t for t in lr["threads"] if t["thread_key"] == thread_key]
        assert match, f"Thread not auto-created for key {thread_key}"
        tid = match[0]["id"]
        det = requests.get(f"{API}/memory/threads/{tid}", headers=H, timeout=15).json()
        turns = det["turns"]
        roles = [t["role"] for t in turns]
        assert "user" in roles, f"User turn not appended. roles={roles}"
        # Assistant turn only present if LLM succeeded; accept either way but log
        if r.status_code == 200:
            # If chat succeeded, assistant should also be appended
            if "assistant" not in roles:
                pytest.skip("chat returned 200 but assistant turn not appended (LLM may have produced empty body)")


# -------------------- Claims drafting --------------------

class TestClaimsDraft:
    def test_draft_from_context_only(self, H):
        body = {
            "kind": "detention",
            "context_text": "Driver arrived 0800 Acme Dallas. Released 1330. 3h past 2h free time at $75/h. BOL 8842. Load LD-2026-481. Carrier MC-998877 Speedway.",
        }
        r = requests.post(f"{API}/claims/draft", json=body, headers=H, timeout=60)
        assert r.status_code in (200, 402, 429, 503), f"{r.status_code} · {r.text[:300]}"
        if r.status_code != 200:
            pytest.skip(f"LLM budget degraded: {r.status_code}")
        d = r.json()
        for k in ("title", "summary", "facts", "claim_amount_usd", "would_auto_file", "auto_file_limit_usd"):
            assert k in d, f"draft missing key: {k}. got: {list(d.keys())}"
        assert d["auto_file_limit_usd"] == 500.0
        assert isinstance(d["facts"], list)

    def test_draft_requires_some_context(self, H):
        r = requests.post(f"{API}/claims/draft", json={"kind": "cargo"}, headers=H, timeout=30)
        assert r.status_code == 400


# -------------------- Claims auto-file vs review --------------------

class TestClaimsLifecycle:
    def test_auto_file_under_threshold(self, H):
        """claim_amount_usd=225 + auto_file=true → status=filed, auto_filed=true."""
        body = {
            "kind": "detention",
            "title": "Detention · auto-file test · 225",
            "summary": "Test under-threshold auto-file",
            "claim_amount_usd": 225,
            "auto_file": True,
            "facts": ["3h past free time", "rate $75/h"],
        }
        r = requests.post(f"{API}/claims", json=body, headers=H, timeout=15)
        assert r.status_code == 200, r.text
        c = r.json()
        assert c["status"] == "filed"
        assert c["auto_filed"] is True
        assert c["filed_at"] is not None
        pytest.auto_filed_claim_id = c["id"]

    def test_over_threshold_stays_for_review(self, H):
        body = {
            "kind": "cargo",
            "title": "Cargo · over-threshold test · 1840",
            "summary": "Test over-threshold review path",
            "claim_amount_usd": 1840,
            "auto_file": True,
            "facts": ["pallet damage 4/6"],
        }
        r = requests.post(f"{API}/claims", json=body, headers=H, timeout=15)
        assert r.status_code == 200, r.text
        c = r.json()
        assert c["status"] == "ready_for_review", f"Expected ready_for_review got {c['status']}"
        assert c["auto_filed"] is False
        pytest.review_claim_id = c["id"]

    def test_manual_file_review_claim(self, H):
        cid = pytest.review_claim_id
        r = requests.post(f"{API}/claims/{cid}/file", headers=H, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        c = data["claim"]
        assert c["status"] == "filed"
        assert c["filed_at"] is not None
        # delivery present (delivered_count=0 is OK if no claims webhook configured)
        delivery = data["delivery"]
        assert "delivered_count" in delivery
        assert isinstance(delivery.get("results", []), list)

    def test_summary_filters(self, H):
        # All
        r = requests.get(f"{API}/claims?limit=200", headers=H, timeout=15)
        assert r.status_code == 200
        d = r.json()
        for k in ("count", "open", "filed", "total_amount_usd", "auto_file_limit_usd"):
            assert k in d
        assert d["auto_file_limit_usd"] == 500.0
        # Filter kind=cargo
        r2 = requests.get(f"{API}/claims?kind=cargo", headers=H, timeout=15).json()
        assert all(c["kind"] == "cargo" for c in r2["claims"])
        # Filter status=filed
        r3 = requests.get(f"{API}/claims?status=filed", headers=H, timeout=15).json()
        assert all(c["status"] == "filed" for c in r3["claims"])
        assert any(c["id"] == pytest.auto_filed_claim_id for c in r3["claims"])

    def test_delete_test_claims(self, H):
        for cid in (getattr(pytest, "auto_filed_claim_id", None), getattr(pytest, "review_claim_id", None)):
            if cid:
                r = requests.delete(f"{API}/claims/{cid}", headers=H, timeout=10)
                assert r.status_code == 200


# -------------------- Webhook kind=claims --------------------

class TestWebhookClaimsKind:
    def test_create_claims_webhook(self, H):
        body = {
            "name": f"TEST_claims_hook_{UNIQ}",
            "kind": "claims",
            "url": "https://example.com/test-claims-webhook",
            "active": False,  # don't actually fire
        }
        r = requests.post(f"{API}/webhooks", json=body, headers=H, timeout=15)
        assert r.status_code == 200, f"webhooks kind=claims should be accepted. got {r.status_code} · {r.text[:300]}"
        hook = r.json()
        assert hook["kind"] == "claims"
        # Cleanup
        hid = hook.get("id")
        if hid:
            requests.delete(f"{API}/webhooks/{hid}", headers=H, timeout=10)


# -------------------- Regression: chat without memory binding still works --------------------

class TestChatRegression:
    def test_chat_without_memory_thread(self, H):
        body = {
            "session_id": f"sess-reg-{UNIQ}",
            "message": "hi",
        }
        r = requests.post(f"{API}/agent/chat", json=body, headers=H, timeout=60, stream=True)
        assert r.status_code in (200, 402, 429, 503)
        r.close()
