from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import delete

import app.api.routes.documents as documents_route
from app.db.session import SessionLocal, init_db
from app.main import app
from app.models import Document, User


def _cleanup_user(email: str) -> None:
    init_db()
    db = SessionLocal()
    try:
        db.execute(delete(User).where(User.email == email))
        db.commit()
    finally:
        db.close()


def _delete_document(document_id: int) -> None:
    db = SessionLocal()
    try:
        db.execute(delete(Document).where(Document.id == document_id))
        db.commit()
    finally:
        db.close()


def _register_and_login(client: TestClient, email: str, password: str = "StrongPass123!") -> str:
    client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Upload Queue User",
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


def test_upload_returns_processing_state_when_queued(monkeypatch, tmp_path: Path) -> None:
    email = "queued_upload_user@example.com"
    _cleanup_user(email)

    client = TestClient(app)
    token = _register_and_login(client, email)

    queued_document_ids: list[int] = []
    stored_pdf_path = tmp_path / "queued_document.pdf"
    stored_pdf_path.write_bytes(b"%PDF-1.4\n% queued\n%%EOF")

    def _enqueue(document_id: int) -> bool:
        queued_document_ids.append(document_id)
        return True

    def _pipeline_should_not_run(document_id: int, db: object) -> dict[str, str]:
        raise AssertionError(f"Synchronous pipeline should not run when queueing is successful: {document_id}.")

    monkeypatch.setattr(documents_route, "save_pdf_bytes", lambda filename, payload: stored_pdf_path)
    monkeypatch.setattr(documents_route, "enqueue_document_processing", _enqueue)
    monkeypatch.setattr(documents_route, "process_document_ingestion", _pipeline_should_not_run)

    document_id: int | None = None
    try:
        upload_response = client.post(
            "/documents/upload",
            files={"file": ("queued.pdf", b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF", "application/pdf")},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert upload_response.status_code == 202
        upload_payload = upload_response.json()
        document_id = int(upload_payload["document_id"])

        assert upload_payload["status"] == "processing"
        assert upload_payload["chunk_count"] == 0
        assert queued_document_ids == [document_id]

        detail_response = client.get(
            f"/documents/{document_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert detail_response.status_code == 200
        assert detail_response.json()["status"] == "processing"
        assert detail_response.json()["chunk_count"] == 0
    finally:
        if document_id is not None:
            _delete_document(document_id)
        _cleanup_user(email)
