"""Unit tests for JWT authentication."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.security.auth import authenticate_user, create_access_token, decode_token

client = TestClient(app)


def test_authenticate_admin():
    user = authenticate_user("admin", "admin123")
    assert user is not None
    assert user["role"] == "Admin"


def test_authenticate_invalid():
    assert authenticate_user("admin", "wrong") is None


def test_jwt_roundtrip():
    token = create_access_token({"sub": "u1", "username": "admin", "role": "Admin"})
    payload = decode_token(token)
    assert payload["sub"] == "u1"
    assert payload["role"] == "Admin"


def test_login_endpoint():
    resp = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "Admin"


def test_chat_with_token():
    login = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    token = login.json()["access_token"]
    resp = client.post(
        "/chat",
        json={"query": "Show failed payment incidents", "role": "Admin"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


def test_auth_status():
    resp = client.get("/auth/status")
    assert resp.status_code == 200
    assert resp.json()["auth_enabled"] is True
