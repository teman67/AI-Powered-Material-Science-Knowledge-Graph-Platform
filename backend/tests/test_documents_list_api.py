from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db.session import SessionLocal, init_db
from app.main import app
from app.models import Document, DocumentStatus, User


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
            "full_name": "Docs List User",
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


def test_documents_list_requires_auth() -> None:
    client = TestClient(app)
    response = client.get("/documents")
    assert response.status_code == 401


def test_documents_list_returns_recent_documents_with_limit() -> None:
    email = "documents_list_user@example.com"
    _cleanup_user(email)

    client = TestClient(app)
    token = _register_and_login(client, email)

    db = SessionLocal()
    inserted_ids: list[int] = []
    try:
        first = Document(file_path="/tmp/first.pdf", status=DocumentStatus.processing.value, title="First")
        second = Document(file_path="/tmp/second.pdf", status=DocumentStatus.processed.value, title="Second")
        db.add_all([first, second])
        db.commit()
        db.refresh(first)
        db.refresh(second)
        inserted_ids.extend([first.id, second.id])

        response = client.get("/documents?limit=1", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        payload = response.json()

        assert "items" in payload
        assert len(payload["items"]) == 1
        assert payload["items"][0]["id"] == max(inserted_ids)
        assert payload["items"][0]["chunk_count"] == 0
    finally:
        for document_id in inserted_ids:
            db.execute(delete(Document).where(Document.id == document_id))
        db.commit()
        db.close()
        _cleanup_user(email)
