import os
import pytest
from fastapi.testclient import TestClient

# These tests assume DB env vars are set and schema exists.
# If not set, we skip.

def _has_db_env():
    required = ["DB_SERVER", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    return all(os.getenv(k) for k in required)

@pytest.mark.skipif(not _has_db_env(), reason="DB env not configured")
def test_health():
    from api.app import app
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"

@pytest.mark.skipif(not _has_db_env(), reason="DB env not configured")
def test_create_intake_housing_crisis():
    from api.app import app
    client = TestClient(app)

    payload = {
        "caller_id": "test-001",
        "channel": "phone",
        "domain_module": "Housing",
        "priority": "High",
        "crisis": True,
        "narrative": "Risk of eviction within 7 days.",
        "attributes": {"risk_days": 7}
    }

    r = client.post("/intakes", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["queue"] in ["HousingEscalation", "General"]  # depends on seed rules
