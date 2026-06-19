"""Integration tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_data():
    client.post("/ingest", json={"regenerate_synthetic": True, "force_reindex": True})


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_chat_incident_query():
    resp = client.post(
        "/chat",
        json={
            "query": "Show failed payment incidents",
            "user_id": "test_user",
            "role": "Engineering",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "sources" in data
    assert "retrieval_trace" in data


def test_sources_endpoint():
    resp = client.get("/sources")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_audit_endpoint():
    resp = client.get("/audit")
    assert resp.status_code == 200


def test_evaluate_endpoint():
    resp = client.post("/evaluate", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert "retrieval_metrics" in data
    assert "security_metrics" in data
