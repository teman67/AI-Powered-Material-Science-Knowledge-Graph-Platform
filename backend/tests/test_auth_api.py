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
