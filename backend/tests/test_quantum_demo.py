"""Tests for /api/quantum/* endpoints (JadeOS Quantum AI VC demo)."""
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://mpls-automation-hub.preview.emergentagent.com").rstrip("/")


# ---------- /api/quantum/modules ----------

class TestQuantumModules:
    def test_list_modules_shape(self):
        r = requests.get(f"{BASE_URL}/api/quantum/modules", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["total"] == 54
        assert isinstance(data["categories"], list) and len(data["categories"]) >= 5
        assert isinstance(data["modules"], list) and len(data["modules"]) == 54
        first = data["modules"][0]
        for k in ("id", "cat", "name", "desc", "status"):
            assert k in first
        # voice trigger preserved
        assert data["voice_trigger"] == "Hey Jade"


# ---------- /api/quantum/run-circuit ----------

class TestRunCircuit:
    def test_bell_50_50_counts_sum_to_shots(self):
        r = requests.post(
            f"{BASE_URL}/api/quantum/run-circuit",
            json={"circuit": "bell", "qubits": 2, "shots": 1024, "seed": 42},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        counts = data["counts"]
        assert set(counts.keys()) == {"00", "11"}
        total = sum(counts.values())
        assert total == 1024
        # 50/50 within tolerance
        assert 0.40 < counts["00"] / total < 0.60
        assert 0.40 < counts["11"] / total < 0.60
        # required envelope fields
        for k in ("theory", "gates", "fingerprint", "depth", "ran_at", "max_qubits_supported"):
            assert k in data

    def test_grover2_marked_state_high_frequency(self):
        r = requests.post(
            f"{BASE_URL}/api/quantum/run-circuit",
            json={"circuit": "grover2", "qubits": 2, "shots": 2048, "seed": 7},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        counts = data["counts"]
        total = sum(counts.values())
        assert total == 2048
        frac_11 = counts.get("11", 0) / total
        # ~97% with ±5% tolerance
        assert 0.92 <= frac_11 <= 1.0, f"|11> frac was {frac_11}"

    def test_qft3_uniform_over_8_basis_states(self):
        r = requests.post(
            f"{BASE_URL}/api/quantum/run-circuit",
            json={"circuit": "qft3", "qubits": 3, "shots": 1024, "seed": 99},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        counts = data["counts"]
        assert len(counts) == 8
        expected_states = {f"{i:03b}" for i in range(8)}
        assert set(counts.keys()) == expected_states
        total = sum(counts.values())
        assert total == 1024
        # Each state ~12.5% within a generous statistical tolerance
        for s, c in counts.items():
            frac = c / total
            assert 0.07 <= frac <= 0.20, f"state {s} freq {frac}"

    def test_ghz_3qubit(self):
        r = requests.post(
            f"{BASE_URL}/api/quantum/run-circuit",
            json={"circuit": "ghz", "qubits": 3, "shots": 512, "seed": 5},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        counts = data["counts"]
        assert set(counts.keys()) == {"000", "111"}
        assert sum(counts.values()) == 512


# ---------- /api/quantum/memory-preview ----------

class TestMemoryPreview:
    def test_memory_preview_shape(self):
        r = requests.get(f"{BASE_URL}/api/quantum/memory-preview", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "thread_id" in data and data["thread_id"]
        ledger = data["facts_ledger"]
        for cat in ("HAPPENED", "DECIDED", "OPEN_QUESTIONS", "RISKS", "NEXT_ACTIONS"):
            assert cat in ledger
            assert isinstance(ledger[cat], list) and len(ledger[cat]) >= 1
        turns = data["recent_turns"]
        assert isinstance(turns, list) and len(turns) >= 4
        for t in turns:
            for k in ("role", "text", "at"):
                assert k in t


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
