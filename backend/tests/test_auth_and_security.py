import pytest
from app.core.config import settings

def test_unauthenticated_access_rejected(client):
    resp = client.get("/api/datasets")
    assert resp.status_code == 401
    assert "Authentication required" in resp.json()["detail"]

def test_viewer_role_denied_mutation(client, viewer_auth):
    resp = client.post(
        "/api/datasets",
        json={
            "name": "Forbidden Dataset",
            "task_type": "classification",
        },
        headers=viewer_auth["headers"],
    )
    assert resp.status_code == 403
    assert "Access denied" in resp.json()["detail"]

def test_csrf_protection_enforced_without_header(client, analyst_auth):
    # Strip X-CSRF-Token header to trigger CSRF violation
    headers = {"Authorization": f"Bearer {analyst_auth['token']}"}
    resp = client.post(
        "/api/datasets",
        json={"name": "No CSRF Dataset", "task_type": "classification"},
        headers=headers,
    )
    # When Bearer header is passed, our security module allows it; let's test cookie-only with missing CSRF
    client.cookies.set("arena_session", analyst_auth["token"])
    client.cookies.set("arena_csrf", "some-secret-token")
    # Send request without X-CSRF-Token header
    resp2 = client.post(
        "/api/datasets",
        json={"name": "No CSRF Dataset", "task_type": "classification"},
        headers={},  # no auth header, rely on cookie
    )
    assert resp2.status_code == 403
    assert "CSRF" in resp2.json()["detail"]
    # Clean cookies
    client.cookies.clear()

def test_demo_login_invalid_role(client):
    resp = client.post("/api/auth/demo-login", json={"role": "supergod"})
    assert resp.status_code == 400

def test_demo_login_refused_in_production(client, monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    resp = client.post("/api/auth/demo-login", json={"role": "analyst"})
    assert resp.status_code == 403
    assert "disabled in production" in resp.json()["detail"]
