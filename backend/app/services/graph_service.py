import re
from collections.abc import Iterable
from dataclasses import dataclass
from itertools import combinations
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Document, ExtractedEntity
from app.services.ontology_mapping import MappedEntityRecord

try:
    from neo4j import GraphDatabase
except Exception:
    GraphDatabase = None

_DRIVER: Any = None
_DRIVER_INIT_FAILED = False

_LINKABLE_ENTITY_TYPES = {
    "material",
    "property",
    "property_measurement",
    "process",
    "application",
    "crystal_structure",
}


@dataclass
class GraphFact:
    source: str
    relation: str
    target: str


def fetch_cross_paper_links(db: Session, limit: int = 50, min_shared: int = 2) -> list[dict[str, Any]]:
    rows = db.execute(
        select(
            ExtractedEntity.document_id,
            ExtractedEntity.entity_type,
            ExtractedEntity.entity_value,
            ExtractedEntity.ontology_mapping,
        ).where(ExtractedEntity.entity_type.in_(_LINKABLE_ENTITY_TYPES))
    ).all()

    if not rows:
        return []

    entities_by_document: dict[int, set[str]] = {}
    key_to_display: dict[str, str] = {}

    for document_id, entity_type, entity_value, ontology_mapping in rows:
        normalized_value = _normalize_entity_value(str(entity_value))
        if not normalized_value:
            continue

        entity_key = f"{str(ontology_mapping).lower()}|{str(entity_type).lower()}|{normalized_value}"
        entities_by_document.setdefault(int(document_id), set()).add(entity_key)
        key_to_display.setdefault(entity_key, str(entity_value).strip())

    if len(entities_by_document) < 2:
        return []

    document_ids = sorted(entities_by_document.keys())
    title_rows = db.execute(select(Document.id, Document.title).where(Document.id.in_(document_ids))).all()
    title_by_document_id = {int(document_id): title for document_id, title in title_rows}

    links: list[dict[str, Any]] = []
    for doc_a_id, doc_b_id in combinations(document_ids, 2):
        shared_keys = entities_by_document[doc_a_id].intersection(entities_by_document[doc_b_id])
        if len(shared_keys) < min_shared:
            continue

        shared_entities = sorted({key_to_display[key] for key in shared_keys})[:8]
        links.append(
            {
                "document_a_id": doc_a_id,
                "document_a_title": title_by_document_id.get(doc_a_id),
                "document_b_id": doc_b_id,
                "document_b_title": title_by_document_id.get(doc_b_id),
                "shared_entity_count": len(shared_keys),
                "shared_entities": shared_entities,
            }
        )

    links.sort(
        key=lambda item: (
            int(item["shared_entity_count"]),
            -int(item["document_a_id"]),
            -int(item["document_b_id"]),
        ),
        reverse=True,
    )
    return links[:limit]


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

    tokens = _tokenize_text(query_text)
    relation_boosts = _relation_intent_boosts(query_text, tokens)
    preferred_relations = list(relation_boosts.keys())

    settings = get_settings()
    candidate_limit = max(settings.chat_graph_candidate_pool, limit * 5)

    cypher = """
    MATCH (m:Material)-[r]->(n)
    WHERE size($tokens) = 0
       OR any(token IN $tokens WHERE toLower(m.name) CONTAINS token OR toLower(n.name) CONTAINS token)
       OR type(r) IN $preferred_relations
    RETURN m.name AS source, type(r) AS relation, n.name AS target
    LIMIT $candidate_limit
    """

    try:
        with driver.session() as session:
            rows = session.run(
                cypher,
                tokens=tokens,
                preferred_relations=preferred_relations,
                candidate_limit=candidate_limit,
            )
            facts = [GraphFact(source=row["source"], relation=row["relation"], target=row["target"]) for row in rows]
            return _rank_graph_facts_for_query(query_text, facts, limit=limit)
    except Exception:
        return []


def _rank_graph_facts_for_query(query_text: str, facts: list[GraphFact], limit: int) -> list[GraphFact]:
    if not facts:
        return []

    tokens = _tokenize_text(query_text)
    relation_boosts = _relation_intent_boosts(query_text, tokens)
    lowered_query = query_text.lower().strip()

    scored = [
        (
            _score_graph_fact(fact, tokens=tokens, query_lower=lowered_query, relation_boosts=relation_boosts),
            fact,
        )
        for fact in facts
    ]

    scored.sort(
        key=lambda item: (
            item[0],
            item[1].source.lower(),
            item[1].relation.lower(),
            item[1].target.lower(),
        ),
        reverse=True,
    )

    return [fact for score, fact in scored if score > 0][:limit]


def _score_graph_fact(
    fact: GraphFact,
    tokens: list[str],
    query_lower: str,
    relation_boosts: dict[str, float],
) -> float:
    source_lower = fact.source.lower()
    target_lower = fact.target.lower()
    relation_upper = fact.relation.upper()

    source_overlap = sum(1 for token in tokens if token in source_lower)
    target_overlap = sum(1 for token in tokens if token in target_lower)

    relation_score = relation_boosts.get(relation_upper, 0.2)
    lexical_score = (source_overlap * 0.5) + (target_overlap * 0.7)

    material_question_bonus = 0.0
    if any(phrase in query_lower for phrase in ["which material", "what material", "materials have", "material has"]):
        material_question_bonus = 0.6

    direct_phrase_bonus = 0.0
    if source_lower in query_lower:
        direct_phrase_bonus += 0.9
    if target_lower in query_lower:
        direct_phrase_bonus += 0.8

    short_target_penalty = -0.15 if len(target_lower) <= 2 else 0.0

    return relation_score + lexical_score + material_question_bonus + direct_phrase_bonus + short_target_penalty


def _relation_intent_boosts(query_text: str, tokens: list[str]) -> dict[str, float]:
    query_lower = query_text.lower()

    has_property_terms = {
        "property",
        "properties",
        "conductivity",
        "bandgap",
        "hardness",
        "density",
        "mobility",
        "dielectric",
        "strength",
        "toughness",
        "thermal",
        "electrical",
    }
    process_terms = {
        "how",
        "process",
        "method",
        "synthesis",
        "synthesized",
        "fabrication",
        "prepared",
        "annealing",
        "deposition",
        "calcination",
        "hydrothermal",
    }
    application_terms = {
        "application",
        "applications",
        "use",
        "used",
        "device",
        "battery",
        "sensor",
        "catalysis",
        "photovoltaic",
        "thermoelectric",
    }

    boosts = {
        "HAS_PROPERTY": 0.35,
        "PRODUCED_BY": 0.35,
        "USED_IN": 0.35,
    }

    token_set = set(tokens)

    if token_set.intersection(has_property_terms):
        boosts["HAS_PROPERTY"] += 1.0
    if token_set.intersection(process_terms) or "how" in query_lower:
        boosts["PRODUCED_BY"] += 1.0
    if token_set.intersection(application_terms):
        boosts["USED_IN"] += 1.0

    if "synth" in query_lower or "fabricat" in query_lower:
        boosts["PRODUCED_BY"] += 0.5
    if "used in" in query_lower or "application of" in query_lower:
        boosts["USED_IN"] += 0.4

    return boosts


def _tokenize_text(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z0-9_\-]+", text.lower())
    return [token for token in tokens if len(token) >= 3]


def _normalize_entity_value(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value.strip().lower())
    cleaned = re.sub(r"[^a-z0-9\-\.\+ ]", "", cleaned)
    return cleaned.strip()


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
