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


def test_rank_graph_facts_prioritizes_property_intent() -> None:
    facts = [
        graph_service.GraphFact(source="MoS2", relation="USED_IN", target="nanoelectronics"),
        graph_service.GraphFact(source="MoS2", relation="HAS_PROPERTY", target="thermal conductivity"),
        graph_service.GraphFact(source="MoS2", relation="PRODUCED_BY", target="annealing"),
    ]

    ranked = graph_service._rank_graph_facts_for_query(
        "Which materials have high thermal conductivity?",
        facts,
        limit=3,
    )

    assert ranked
    assert ranked[0].relation == "HAS_PROPERTY"


def test_rank_graph_facts_prioritizes_process_intent() -> None:
    facts = [
        graph_service.GraphFact(source="MoS2", relation="HAS_PROPERTY", target="bandgap"),
        graph_service.GraphFact(source="MoS2", relation="PRODUCED_BY", target="chemical vapor deposition"),
        graph_service.GraphFact(source="MoS2", relation="USED_IN", target="sensor"),
    ]

    ranked = graph_service._rank_graph_facts_for_query(
        "How is MoS2 synthesized?",
        facts,
        limit=3,
    )

    assert ranked
    assert ranked[0].relation == "PRODUCED_BY"


def test_rank_graph_facts_prioritizes_application_intent() -> None:
    facts = [
        graph_service.GraphFact(source="MoS2", relation="HAS_PROPERTY", target="bandgap"),
        graph_service.GraphFact(source="MoS2", relation="PRODUCED_BY", target="hydrothermal"),
        graph_service.GraphFact(source="MoS2", relation="USED_IN", target="photovoltaics"),
    ]

    ranked = graph_service._rank_graph_facts_for_query(
        "What applications use MoS2?",
        facts,
        limit=3,
    )

    assert ranked
    assert ranked[0].relation == "USED_IN"
