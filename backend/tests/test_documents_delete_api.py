from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

import app.api.routes.documents as documents_route
from app.core.config import get_settings
from app.db.session import SessionLocal, init_db
from app.main import app
from app.models import Chunk, Document, DocumentStatus, ExtractedEntity, RdfArtifact, User


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
            "full_name": "Delete User",
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


def _create_document_with_related_rows(file_path: str) -> int:
    settings = get_settings()
    db = SessionLocal()
    try:
        document = Document(file_path=file_path, status=DocumentStatus.processed.value, title="Delete Me")
        db.add(document)
        db.commit()
        db.refresh(document)

        db.add(
            Chunk(
                document_id=document.id,
                chunk_index=0,
                section="body",
                content="MoS2 has high conductivity.",
                embedding=[0.0] * settings.embedding_dimension,
            )
        )
        db.add(
            ExtractedEntity(
                document_id=document.id,
                entity_type="material",
                entity_value="MoS2",
                ontology_mapping="pmd:Material",
                confidence=0.9,
                source_chunk_index=0,
            )
        )
        db.add(
            RdfArtifact(
                document_id=document.id,
                ttl_content="@prefix pmd: <http://example.org/pmd#> .",
                is_valid=True,
                validation_report="ok",
            )
        )
        db.commit()
        return int(document.id)
    finally:
        db.close()


def test_delete_document_requires_auth() -> None:
    client = TestClient(app)
    response = client.delete("/documents/1")
    assert response.status_code == 401


def test_delete_document_removes_file_and_related_data(monkeypatch, tmp_path: Path) -> None:
    email = "delete_document_user@example.com"
    _cleanup_user(email)

    client = TestClient(app)
    token = _register_and_login(client, email)

    stored_file = tmp_path / "delete_me.pdf"
    stored_file.write_bytes(b"%PDF-1.4\n% delete\n%%EOF")
    document_id = _create_document_with_related_rows(str(stored_file))

    called_ids: list[int] = []

    def _mock_remove_document_from_graph(document_id: int) -> dict[str, object]:
        called_ids.append(document_id)
        return {"applied": True, "nodes_deleted": 2, "relationships_deleted": 1}

    monkeypatch.setattr(documents_route, "remove_document_from_graph", _mock_remove_document_from_graph)

    try:
        response = client.delete(f"/documents/{document_id}", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

        payload = response.json()
        assert payload["document_id"] == document_id
        assert payload["file_deleted"] is True
        assert payload["graph_cleanup_applied"] is True
        assert called_ids == [document_id]

        assert not stored_file.exists()

        db = SessionLocal()
        try:
            assert db.get(Document, document_id) is None
            assert db.scalar(select(func.count()).select_from(Chunk).where(Chunk.document_id == document_id)) == 0
            assert db.scalar(select(func.count()).select_from(ExtractedEntity).where(ExtractedEntity.document_id == document_id)) == 0
            assert db.scalar(select(func.count()).select_from(RdfArtifact).where(RdfArtifact.document_id == document_id)) == 0
        finally:
            db.close()
    finally:
        _cleanup_user(email)