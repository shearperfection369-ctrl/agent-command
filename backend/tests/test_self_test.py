"""Smoke test for /api/admin/self-test."""
import os
import requests

BASE = os.environ.get("BACKEND_URL", "http://localhost:8001")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@jadeos.ai")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "JadeOS!2026")


def _token():
    r = requests.post(
        f"{BASE}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def test_self_test_runs_and_no_failures():
    tok = _token()
    r = requests.get(
        f"{BASE}/api/admin/self-test",
        headers={"Authorization": f"Bearer {tok}"},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    assert "results" in data and "summary" in data
    s = data["summary"]
    assert s["total"] >= 15, f"expected ≥15 checks, got {s['total']}"
    assert s["fail"] == 0, f"failing checks: {[x for x in data['results'] if x['status']=='fail']}"
    # Sanity: every result has required shape
    for r_ in data["results"]:
        assert {"name", "category", "status", "latency_ms", "message"} <= set(r_.keys())
        assert r_["status"] in {"pass", "fail", "skip", "warn"}


def test_self_test_requires_auth():
    r = requests.get(f"{BASE}/api/admin/self-test", timeout=10)
    assert r.status_code == 401
