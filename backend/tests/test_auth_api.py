from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.main import app
from app.models import User
from app.db.session import SessionLocal, init_db


def _cleanup_user(email: str) -> None:
    init_db()
    db = SessionLocal()
    try:
        db.execute(delete(User).where(User.email == email))
        db.commit()
    finally:
        db.close()


def _register_and_login(client: TestClient, email: str, password: str = "StrongPass123!") -> str:
    client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Auth Helper",
        },
    )
    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert login_response.status_code == 200
    return str(login_response.json()["access_token"])


def test_auth_register_and_login() -> None:
    email = "auth_test_user@example.com"
    _cleanup_user(email)

    client = TestClient(app)

    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "StrongPass123!",
            "full_name": "Auth Test",
        },
    )

    assert register_response.status_code == 201
    register_payload = register_response.json()
    assert register_payload["email"] == email

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "StrongPass123!",
        },
    )

    assert login_response.status_code == 200
    login_payload = login_response.json()
    assert login_payload["access_token"]
    assert login_payload["token_type"] == "bearer"
    assert login_payload["expires_in"] > 0

    _cleanup_user(email)


def test_auth_register_duplicate_email_returns_conflict() -> None:
    email = "auth_dup_user@example.com"
    _cleanup_user(email)

    client = TestClient(app)
    payload = {
        "email": email,
        "password": "StrongPass123!",
        "full_name": "Dup User",
    }

    first = client.post("/auth/register", json=payload)
    second = client.post("/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409

    _cleanup_user(email)


def test_auth_login_wrong_password_returns_unauthorized() -> None:
    email = "auth_login_user@example.com"
    _cleanup_user(email)

    client = TestClient(app)
    client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "StrongPass123!",
            "full_name": "Login User",
        },
    )

    bad_login = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "WrongPassword123!",
        },
    )

    assert bad_login.status_code == 401

    _cleanup_user(email)


def test_protected_chat_endpoint_requires_auth() -> None:
    client = TestClient(app)

    response = client.post(
        "/chat/query",
        json={"query": "What is thermal conductivity?", "top_k": 3},
    )

    assert response.status_code == 401


def test_protected_chat_endpoint_accepts_valid_bearer_token() -> None:
    email = "auth_guard_user@example.com"
    _cleanup_user(email)

    client = TestClient(app)
    token = _register_and_login(client, email)

    response = client.post(
        "/chat/query",
        json={"query": "What is thermal conductivity?", "top_k": 3},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "answer" in payload
    assert "contexts" in payload

    _cleanup_user(email)


def test_auth_me_requires_auth() -> None:
    client = TestClient(app)
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_auth_me_returns_current_user() -> None:
    email = "auth_me_user@example.com"
    _cleanup_user(email)

    client = TestClient(app)
    token = _register_and_login(client, email)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    payload = response.json()
    assert payload["email"] == email
    assert payload["id"] > 0

    _cleanup_user(email)
