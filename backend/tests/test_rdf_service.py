from app.models.document import Document
from app.services.rdf_service import generate_rdf_for_document


class DummyChunk:
    def __init__(self, chunk_index: int, content: str) -> None:
        self.chunk_index = chunk_index
        self.content = content


def test_generate_rdf_for_document_includes_material_and_property() -> None:
    document = Document(id=1, title="MoS2 Study", file_path="dummy.pdf", status="processed")
    chunks = [DummyChunk(0, "MoS2 bandgap is 1.8 eV and used in nanoelectronics.")]

    result = generate_rdf_for_document(document, chunks)

    assert "material_mos2" in result.ttl_content
    assert "hasProperty" in result.ttl_content
    assert result.validation_report
