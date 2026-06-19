"""Integration tests for plug-and-play APIs."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_roles_endpoint():
    resp = client.get("/roles")
    assert resp.status_code == 200
    data = resp.json()
    assert "Admin" in data["roles"]
    assert "hierarchy" in data


def test_config_endpoint():
    resp = client.get("/config")
    assert resp.status_code == 200
    assert "connectors" in resp.json()


def test_config_reload():
    resp = client.post("/config/reload")
    assert resp.status_code == 200
    assert resp.json()["status"] == "reloaded"


def test_add_inline_document():
    resp = client.post("/documents", json={
        "connector_name": "test_runtime",
        "document_id": "test_doc_001",
        "source": "test_policy.txt",
        "text": "All contractors must complete security training within 30 days.",
        "metadata": {
            "department": "compliance",
            "allowed_roles": ["Compliance", "Admin"],
            "data_source": "inline",
        },
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "indexed"

    chat = client.post("/chat", json={
        "query": "contractor security training requirements",
        "role": "Compliance",
    })
    assert chat.status_code == 200
