from app.services import graph_service


def test_graph_service_returns_empty_when_driver_missing(monkeypatch) -> None:
    monkeypatch.setattr(graph_service, "GraphDatabase", None)
    monkeypatch.setattr(graph_service, "_DRIVER", None)
    monkeypatch.setattr(graph_service, "_DRIVER_INIT_FAILED", False)

    assert graph_service.fetch_materials(limit=10) == []
    assert graph_service.fetch_relations(limit=10) == []
    assert graph_service.retrieve_graph_facts_for_query("MoS2", limit=5) == []


def test_ingest_returns_counts_without_driver(monkeypatch) -> None:
    class DummyEntity:
        def __init__(self, entity_type: str, entity_value: str, property_name: str | None = None) -> None:
            self.entity_type = entity_type
            self.entity_value = entity_value
            self.property_name = property_name

    entities = [
        DummyEntity("material", "MoS2"),
        DummyEntity("property_measurement", "bandgap=1.8 eV", "bandgap"),
        DummyEntity("process", "annealing"),
        DummyEntity("application", "nanoelectronics"),
    ]

    monkeypatch.setattr(graph_service, "GraphDatabase", None)
    monkeypatch.setattr(graph_service, "_DRIVER", None)
    monkeypatch.setattr(graph_service, "_DRIVER_INIT_FAILED", False)

    summary = graph_service.ingest_document_entities_to_graph(
        document_id=1,
        document_title="Doc",
        entities=entities,
    )

    assert summary["materials"] == 1
    assert summary["properties"] == 1
    assert summary["processes"] == 1
    assert summary["applications"] == 1
