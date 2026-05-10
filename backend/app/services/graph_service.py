from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings
from app.services.ontology_mapping import MappedEntityRecord

try:
    from neo4j import GraphDatabase
except Exception:
    GraphDatabase = None

_DRIVER: Any = None
_DRIVER_INIT_FAILED = False


@dataclass
class GraphFact:
    source: str
    relation: str
    target: str


def ingest_document_entities_to_graph(
    document_id: int,
    document_title: str | None,
    entities: list[MappedEntityRecord],
) -> dict[str, int]:
    material_names = [entity.entity_value for entity in entities if entity.entity_type == "material"]
    if not material_names:
        material_names = ["unknown_material"]

    unique_materials = _dedupe_keep_order(material_names)
    properties = _dedupe_keep_order(
        [entity.property_name or entity.entity_value for entity in entities if entity.entity_type in {"property", "property_measurement", "crystal_structure"}]
    )
    processes = _dedupe_keep_order([entity.entity_value for entity in entities if entity.entity_type == "process"])
    applications = _dedupe_keep_order([entity.entity_value for entity in entities if entity.entity_type == "application"])

    driver = _get_driver()
    if driver is None:
        return {
            "materials": len(unique_materials),
            "properties": len(properties),
            "processes": len(processes),
            "applications": len(applications),
            "relationships": 0,
        }

    with driver.session() as session:
        session.execute_write(
            _merge_document_and_materials,
            document_id,
            document_title,
            unique_materials,
        )

        relationship_count = 0
        for material in unique_materials:
            relationship_count += session.execute_write(
                _merge_related_nodes,
                material,
                properties,
                "Property",
                "HAS_PROPERTY",
            )
            relationship_count += session.execute_write(
                _merge_related_nodes,
                material,
                processes,
                "Process",
                "PRODUCED_BY",
            )
            relationship_count += session.execute_write(
                _merge_related_nodes,
                material,
                applications,
                "Application",
                "USED_IN",
            )

    return {
        "materials": len(unique_materials),
        "properties": len(properties),
        "processes": len(processes),
        "applications": len(applications),
        "relationships": relationship_count,
    }


def fetch_materials(limit: int = 50) -> list[dict[str, Any]]:
    driver = _get_driver()
    if driver is None:
        return []

    query = """
    MATCH (m:Material)
    OPTIONAL MATCH (m)-[:HAS_PROPERTY]->(p:Property)
    OPTIONAL MATCH (m)-[:PRODUCED_BY]->(pr:Process)
    OPTIONAL MATCH (m)-[:USED_IN]->(a:Application)
    RETURN m.name AS material,
           count(DISTINCT p) AS property_count,
           count(DISTINCT pr) AS process_count,
           count(DISTINCT a) AS application_count
    ORDER BY material ASC
    LIMIT $limit
    """

    try:
        with driver.session() as session:
            rows = session.run(query, limit=limit)
            return [dict(row) for row in rows]
    except Exception:
        return []


def fetch_relations(limit: int = 100, material: str | None = None) -> list[dict[str, str]]:
    driver = _get_driver()
    if driver is None:
        return []

    if material:
        query = """
        MATCH (m:Material {name: $material})-[r]->(n)
        RETURN m.name AS source, type(r) AS relation, n.name AS target
        ORDER BY relation ASC, target ASC
        LIMIT $limit
        """
        parameters = {"material": material, "limit": limit}
    else:
        query = """
        MATCH (m:Material)-[r]->(n)
        RETURN m.name AS source, type(r) AS relation, n.name AS target
        ORDER BY source ASC, relation ASC, target ASC
        LIMIT $limit
        """
        parameters = {"limit": limit}

    try:
        with driver.session() as session:
            rows = session.run(query, **parameters)
            return [dict(row) for row in rows]
    except Exception:
        return []


def retrieve_graph_facts_for_query(query_text: str, limit: int = 5) -> list[GraphFact]:
    driver = _get_driver()
    if driver is None:
        return []

    tokens = [token.strip().lower() for token in query_text.split() if len(token.strip()) >= 3]
    if not tokens:
        tokens = [query_text.strip().lower()]

    cypher = """
    MATCH (m:Material)-[r]->(n)
    WHERE any(token IN $tokens WHERE toLower(m.name) CONTAINS token OR toLower(n.name) CONTAINS token)
    RETURN m.name AS source, type(r) AS relation, n.name AS target
    ORDER BY source ASC, relation ASC, target ASC
    LIMIT $limit
    """

    try:
        with driver.session() as session:
            rows = session.run(cypher, tokens=tokens, limit=limit)
            return [GraphFact(source=row["source"], relation=row["relation"], target=row["target"]) for row in rows]
    except Exception:
        return []


def _merge_document_and_materials(tx: Any, document_id: int, document_title: str | None, materials: list[str]) -> None:
    tx.run(
        """
        MERGE (d:Document {id: $document_id})
        SET d.title = coalesce($document_title, d.title)
        """,
        document_id=document_id,
        document_title=document_title,
    )

    for material in materials:
        tx.run(
            """
            MERGE (m:Material {name: $material})
            WITH m
            MATCH (d:Document {id: $document_id})
            MERGE (d)-[:MENTIONS]->(m)
            """,
            material=material,
            document_id=document_id,
        )


def _merge_related_nodes(
    tx: Any,
    material: str,
    related_values: list[str],
    label: str,
    relation_name: str,
) -> int:
    created = 0
    for value in related_values:
        if not value:
            continue

        query = (
            "MERGE (m:Material {name: $material}) "
            f"MERGE (n:{label} {{name: $value}}) "
            f"MERGE (m)-[:{relation_name}]->(n)"
        )
        tx.run(query, material=material, value=value)
        created += 1

    return created


def _get_driver() -> Any:
    global _DRIVER, _DRIVER_INIT_FAILED

    settings = get_settings()
    if not settings.graph_enabled:
        return None

    if GraphDatabase is None:
        return None

    if _DRIVER is not None:
        return _DRIVER
    if _DRIVER_INIT_FAILED:
        return None

    try:
        _DRIVER = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        with _DRIVER.session() as session:
            session.run("RETURN 1").single()
    except Exception:
        _DRIVER_INIT_FAILED = True
        return None

    return _DRIVER


def _dedupe_keep_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        key = value.strip().lower()
        if not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        output.append(value.strip())
    return output
