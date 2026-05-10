import re
from dataclasses import dataclass

from app.ontologies import get_pmdcore_mappings
from app.services.entity_extraction import ExtractedEntityCandidate


@dataclass
class MappedEntityRecord:
    entity_type: str
    entity_value: str
    ontology_mapping: str
    confidence: float
    source_chunk_index: int
    numeric_value: float | None = None
    unit: str | None = None
    property_name: str | None = None


def map_entities_to_ontology(candidates: list[ExtractedEntityCandidate]) -> list[MappedEntityRecord]:
    mappings = get_pmdcore_mappings()
    class_map = mappings["class_map"]
    property_map = mappings["property_map"]

    records: list[MappedEntityRecord] = []
    for candidate in candidates:
        ontology_mapping = _mapping_for_candidate(candidate, class_map, property_map)
        records.append(
            MappedEntityRecord(
                entity_type=candidate.entity_type,
                entity_value=candidate.entity_value,
                ontology_mapping=ontology_mapping,
                confidence=candidate.confidence,
                source_chunk_index=candidate.source_chunk_index,
                numeric_value=candidate.value,
                unit=candidate.unit,
                property_name=candidate.property_name,
            )
        )

    return records


def _mapping_for_candidate(
    candidate: ExtractedEntityCandidate,
    class_map: dict[str, str],
    property_map: dict[str, str],
) -> str:
    if candidate.entity_type == "material":
        return class_map["material"]

    if candidate.entity_type == "process":
        return class_map["process"]

    if candidate.entity_type == "application":
        return class_map["application"]

    if candidate.entity_type == "property":
        key = _normalize_key(candidate.property_name or candidate.entity_value)
        return property_map.get(key, class_map["property"])

    if candidate.entity_type == "crystal_structure":
        return class_map["property"]

    if candidate.entity_type == "property_measurement":
        key = _normalize_key(candidate.property_name or candidate.entity_value)
        return property_map.get(key, class_map["property"])

    return class_map["property"]


def _normalize_key(raw: str) -> str:
    return re.sub(r"\s+", " ", raw.strip().lower())
