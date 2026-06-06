"""Iteration 11 · Trucker AI endpoints regression tests.

Covers HOS calculator + rules, geocoding, truck-stops (Overpass), routing
(OSRM), NOAA weather, 50-state 511 directory, diesel-prices scaffold.
"""
import os
import pytest
import requests

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") + "/api"
TIMEOUT = 60  # OSM endpoints can be slow


@pytest.fixture(scope="module")
def s():
    return requests.Session()


# ---------------- HOS ----------------
class TestHOS:
    def test_hos_rules(self, s):
        r = s.get(f"{BASE}/trucker/hos-rules", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["driving_limit_hours"] == 11
        assert d["on_duty_limit_hours"] == 14
        assert d["weekly_70_hour_limit"] == 70
        assert "ecfr.gov" in d["source"]

    def test_hos_check_violations(self, s):
        body = {
            "driving_hours_so_far": 11,
            "on_duty_hours_so_far": 13,
            "consecutive_driving_since_break": 8.5,
            "hours_in_last_8_days": 62,
            "pending_drive_hours": 2,
        }
        r = s.post(f"{BASE}/trucker/hos-check", json=body, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is False
        # Expect at least 4 issues: 11h limit, 8h break, pending>driving remain, pending>on_duty remain
        assert len(d["issues"]) >= 4
        cites = " ".join(d["issues"])
        assert "395.3(a)(3)" in cites or "§395.3(a)(3)" in cites
        # Remaining computed
        assert d["remaining"]["driving_h"] == 0.0
        assert d["remaining"]["on_duty_h"] == 1.0

    def test_hos_check_clean(self, s):
        body = {
            "driving_hours_so_far": 5,
            "on_duty_hours_so_far": 8,
            "consecutive_driving_since_break": 3,
            "hours_in_last_8_days": 30,
            "pending_drive_hours": 1,
        }
        r = s.post(f"{BASE}/trucker/hos-check", json=body, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is True
        assert d["issues"] == []
        assert d["remaining"]["driving_h"] == 6
        assert d["remaining"]["on_duty_h"] == 6


# ---------------- Geocode ----------------
class TestGeocode:
    def test_geocode_eagan(self, s):
        r = s.post(f"{BASE}/trucker/geocode", json={"query": "Eagan, MN"}, timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is True
        res = d["result"]
        assert 44.0 < res["lat"] < 45.5
        assert -94.0 < res["lon"] < -92.5
        assert res["source"] == "openstreetmap_nominatim"

    def test_geocode_unknown_no_500(self, s):
        r = s.post(f"{BASE}/trucker/geocode", json={"query": "zzqqxxnotaplace12345"}, timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is False
        assert d["reason"] == "no_match_or_geocoder_error"


# ---------------- Truck stops ----------------
class TestTruckStops:
    def test_truck_stops_eagan(self, s):
        r = s.post(f"{BASE}/trucker/truck-stops",
                   json={"query": "Eagan, MN", "radius_miles": 30}, timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        assert d["source"] == "openstreetmap_overpass"
        assert d["count"] >= 0  # Overpass can be slow/empty but never fabricate
        if d["count"] > 0:
            row = d["stops"][0]
            assert row["source"] == "openstreetmap"
            assert "distance_miles" in row
            assert "lat" in row and "lon" in row
            assert row["source_url"].startswith("https://www.openstreetmap.org/")


# ---------------- Route ----------------
class TestRoute:
    def test_route_eagan_dallas(self, s):
        r = s.post(f"{BASE}/trucker/route",
                   json={"origin": "Eagan, MN", "destination": "Dallas, TX"}, timeout=TIMEOUT)
        if r.status_code == 503:
            pytest.skip("OSRM public router unavailable")
        assert r.status_code == 200
        d = r.json()
        assert 800 < d["distance_miles"] < 1100
        assert d["source"] == "osrm_public"
        assert any("AUTO" in w or "auto" in w for w in d["warnings"])


# ---------------- Weather ----------------
class TestWeather:
    def test_weather_eagan(self, s):
        r = s.post(f"{BASE}/trucker/weather", json={"query": "Eagan, MN"}, timeout=TIMEOUT)
        if r.status_code == 503:
            pytest.skip("NOAA unavailable")
        assert r.status_code == 200
        d = r.json()
        assert d["source"] == "noaa_weather_gov"
        assert len(d["periods"]) == 6
        p = d["periods"][0]
        for k in ("temperature", "temperature_unit", "short_forecast", "detailed_forecast"):
            assert k in p


# ---------------- 511 directory ----------------
class TestState511:
    def test_list_50(self, s):
        r = s.get(f"{BASE}/trucker/state-511", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert len(d["states"]) == 50

    def test_state_mn(self, s):
        r = s.get(f"{BASE}/trucker/state-511/MN", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["name"] == "Minnesota 511"
        assert d["url"] == "https://511mn.org/"

    def test_state_unknown_404(self, s):
        r = s.get(f"{BASE}/trucker/state-511/ZZ", timeout=15)
        assert r.status_code == 404


# ---------------- Diesel ----------------
class TestDiesel:
    def test_diesel_scaffold(self, s):
        r = s.get(f"{BASE}/trucker/diesel-prices", timeout=15)
        assert r.status_code == 200
        d = r.json()
        # If EIA_API_KEY not configured → scaffold
        assert d.get("source") in ("eia_scaffold", "eia_live")
        if d["source"] == "eia_scaffold":
            assert "note" in d
