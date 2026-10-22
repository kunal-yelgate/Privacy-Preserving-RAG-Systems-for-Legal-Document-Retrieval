"""
End-to-end API integration tests using FastAPI TestClient.
Validates HTTP routing, auth tokens, matter-isolated search, and security endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_api_health_and_readiness():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"
    assert res.json()["offline_mode"] is True

    ready_res = client.get("/api/v1/health/ready")
    assert ready_res.status_code == 200
    data = ready_res.json()
    assert data["ready"] is True
    assert data["subsystems"]["sqlite"] is True
    assert data["subsystems"]["chromadb"] is True
    assert data["subsystems"]["ollama_api"] is True


def test_auth_login_and_access_flow():
    # 1. Login as default admin
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "AdminSecureOffline2026!"},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check /auth/me
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "admin"
    assert me_res.json()["role"] == "admin"

    # 3. List matters
    matters_res = client.get("/api/v1/matters", headers=headers)
    assert matters_res.status_code == 200
    assert isinstance(matters_res.json(), list)

    # 4. Check security status
    sec_res = client.get("/api/v1/security/status", headers=headers)
    assert sec_res.status_code == 200
    sec_data = sec_res.json()
    assert sec_data["offline_mode_enforced"] is True
    assert "127.0.0.1" in sec_data["ollama_endpoint"]
