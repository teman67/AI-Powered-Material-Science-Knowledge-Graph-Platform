from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db.session import SessionLocal, init_db
from app.main import app
from app.models import Document, DocumentStatus, ExtractedEntity, User


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
            "full_name": "Graph Links User",
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


def test_cross_paper_links_requires_auth() -> None:
    client = TestClient(app)
    response = client.get("/graph/cross-paper-links")
    assert response.status_code == 401


def test_cross_paper_links_returns_shared_entities_between_documents() -> None:
    email = "graph_links_user@example.com"
    _cleanup_user(email)

    client = TestClient(app)
    token = _register_and_login(client, email)

    db = SessionLocal()
    doc_ids: list[int] = []
    entity_ids: list[int] = []
    try:
        doc_a = Document(file_path="/tmp/doc_a.pdf", status=DocumentStatus.processed.value, title="Doc A")
        doc_b = Document(file_path="/tmp/doc_b.pdf", status=DocumentStatus.processed.value, title="Doc B")
        db.add_all([doc_a, doc_b])
        db.commit()
        db.refresh(doc_a)
        db.refresh(doc_b)
        doc_ids.extend([doc_a.id, doc_b.id])

        entries = [
            ExtractedEntity(
                document_id=doc_a.id,
                entity_type="material",
                entity_value="MoS2",
                ontology_mapping="pmd:Material",
                confidence=0.95,
            ),
            ExtractedEntity(
                document_id=doc_a.id,
                entity_type="property",
                entity_value="thermal conductivity",
                ontology_mapping="pmd:Property",
                confidence=0.90,
            ),
            ExtractedEntity(
                document_id=doc_b.id,
                entity_type="material",
                entity_value="MoS2",
                ontology_mapping="pmd:Material",
                confidence=0.93,
            ),
            ExtractedEntity(
                document_id=doc_b.id,
                entity_type="property",
                entity_value="thermal conductivity",
                ontology_mapping="pmd:Property",
                confidence=0.88,
            ),
            ExtractedEntity(
                document_id=doc_b.id,
                entity_type="application",
                entity_value="sensor",
                ontology_mapping="pmd:Application",
                confidence=0.85,
            ),
        ]
        db.add_all(entries)
        db.commit()
        for entity in entries:
            db.refresh(entity)
            entity_ids.append(entity.id)

        response = client.get(
            "/graph/cross-paper-links?min_shared=2&limit=20",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert "items" in payload
        assert payload["items"]

        first = payload["items"][0]
        assert first["shared_entity_count"] >= 2
        assert first["document_a_id"] in doc_ids
        assert first["document_b_id"] in doc_ids
        assert any(entity.lower() == "mos2" for entity in first["shared_entities"])
    finally:
        for entity_id in entity_ids:
            db.execute(delete(ExtractedEntity).where(ExtractedEntity.id == entity_id))
        for document_id in doc_ids:
            db.execute(delete(Document).where(Document.id == document_id))
        db.commit()
        db.close()
        _cleanup_user(email)
