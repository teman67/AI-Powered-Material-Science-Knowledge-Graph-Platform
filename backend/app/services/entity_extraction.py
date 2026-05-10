import re
from dataclasses import dataclass


@dataclass
class ExtractedEntityCandidate:
    entity_type: str
    entity_value: str
    confidence: float
    source_chunk_index: int
    value: float | None = None
    unit: str | None = None
    property_name: str | None = None


PROPERTY_PATTERN = re.compile(
    r"(?P<property>band\s*gap|bandgap|thermal conductivity|conductivity|young'?s modulus|hardness|density)"
    r"\s*(?:of|=|is|was|at)?\s*(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>eV|W/mK|S/cm|GPa|MPa|g/cm3|kg/m3)?",
    re.IGNORECASE,
)
MATERIAL_PATTERN = re.compile(r"\b(?:[A-Z][a-z]?\d*){2,}\b")

PROCESS_KEYWORDS = [
    "annealing",
    "sintering",
    "deposition",
    "etching",
    "calcination",
]

APPLICATION_KEYWORDS = [
    "nanoelectronics",
    "battery",
    "sensor",
    "catalysis",
    "photovoltaics",
]


def extract_entities_from_chunks(chunks: list[tuple[int, str]]) -> list[ExtractedEntityCandidate]:
    entities: list[ExtractedEntityCandidate] = []
    seen: set[tuple[str, str, int]] = set()

    for chunk_index, content in chunks:
        entities.extend(_extract_materials(content, chunk_index, seen))
        entities.extend(_extract_properties(content, chunk_index, seen))
        entities.extend(_extract_keywords(content, chunk_index, PROCESS_KEYWORDS, "process", seen))
        entities.extend(_extract_keywords(content, chunk_index, APPLICATION_KEYWORDS, "application", seen))

    return entities


def _extract_materials(content: str, chunk_index: int, seen: set[tuple[str, str, int]]) -> list[ExtractedEntityCandidate]:
    output: list[ExtractedEntityCandidate] = []
    for match in MATERIAL_PATTERN.finditer(content):
        material = match.group(0)
        key = ("material", material.lower(), chunk_index)
        if key in seen:
            continue
        seen.add(key)
        output.append(
            ExtractedEntityCandidate(
                entity_type="material",
                entity_value=material,
                confidence=0.85,
                source_chunk_index=chunk_index,
            )
        )
    return output


def _extract_properties(content: str, chunk_index: int, seen: set[tuple[str, str, int]]) -> list[ExtractedEntityCandidate]:
    output: list[ExtractedEntityCandidate] = []
    for match in PROPERTY_PATTERN.finditer(content):
        property_name = _normalize_property_name(match.group("property"))
        value = float(match.group("value"))
        unit = match.group("unit")

        entity_value = f"{property_name}={value}{(' ' + unit) if unit else ''}"
        key = ("property_measurement", entity_value.lower(), chunk_index)
        if key in seen:
            continue
        seen.add(key)

        output.append(
            ExtractedEntityCandidate(
                entity_type="property_measurement",
                entity_value=entity_value,
                confidence=0.8,
                source_chunk_index=chunk_index,
                value=value,
                unit=unit,
                property_name=property_name,
            )
        )
    return output


def _extract_keywords(
    content: str,
    chunk_index: int,
    keywords: list[str],
    entity_type: str,
    seen: set[tuple[str, str, int]],
) -> list[ExtractedEntityCandidate]:
    lowered = content.lower()
    output: list[ExtractedEntityCandidate] = []

    for keyword in keywords:
        if keyword not in lowered:
            continue

        key = (entity_type, keyword, chunk_index)
        if key in seen:
            continue
        seen.add(key)

        output.append(
            ExtractedEntityCandidate(
                entity_type=entity_type,
                entity_value=keyword,
                confidence=0.7,
                source_chunk_index=chunk_index,
            )
        )

    return output


def _normalize_property_name(raw: str) -> str:
    name = re.sub(r"\s+", " ", raw.strip().lower())
    if name in {"band gap", "bandgap"}:
        return "bandgap"
    if name == "young's modulus":
        return "youngs modulus"
    return name
