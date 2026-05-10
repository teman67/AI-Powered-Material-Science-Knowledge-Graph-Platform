import re
from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings

try:
    import spacy
except Exception:
    spacy = None

try:
    from transformers import pipeline as transformers_pipeline
except Exception:
    transformers_pipeline = None


@dataclass
class ExtractedEntityCandidate:
    entity_type: str
    entity_value: str
    confidence: float
    source_chunk_index: int
    value: float | None = None
    unit: str | None = None
    property_name: str | None = None


_SPACY_MODEL: Any = None
_SPACY_LOAD_FAILED = False
_SCIBERT_PIPELINE: Any = None
_SCIBERT_LOAD_FAILED = False

PROPERTY_ALIASES: dict[str, str] = {
    r"band\s*gap|bandgap": "bandgap",
    r"thermal conductivity": "thermal conductivity",
    r"electrical conductivity|ionic conductivity|conductivity": "conductivity",
    r"young'?s modulus|elastic modulus": "youngs modulus",
    r"hardness": "hardness",
    r"density": "density",
    r"carrier mobility": "carrier mobility",
    r"dielectric constant|relative permittivity": "dielectric constant",
    r"tensile strength": "tensile strength",
    r"yield strength": "yield strength",
    r"seebeck coefficient": "seebeck coefficient",
    r"fracture toughness": "fracture toughness",
}

PROPERTY_NAME_PATTERN = re.compile(
    rf"(?P<property>{'|'.join(PROPERTY_ALIASES.keys())})",
    re.IGNORECASE,
)
PROPERTY_MEASUREMENT_PATTERN = re.compile(
    rf"(?P<property>{'|'.join(PROPERTY_ALIASES.keys())})"
    r"\s*(?:of|=|is|was|at|reaches|reached|around|approximately|about)?\s*"
    r"(?P<prefix>[<>~=]|>=|<=|approx\.?|ca\.)?\s*"
    r"(?P<value>-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)"
    r"(?:\s*(?:to|-|\u2013)\s*(?P<value_high>-?\d+(?:\.\d+)?(?:e[+-]?\d+)?))?"
    r"\s*(?P<unit>eV|W/mK|W\s*m-1\s*K-1|S/cm|S\s*m-1|mS/cm|cm2/Vs|cm\^2/Vs|GPa|MPa|Pa|g/cm3|kg/m3|mAh/g|A/g|V|K|%)?",
    re.IGNORECASE,
)

MATERIAL_FORMULA_PATTERN = re.compile(r"\b(?:[A-Z][a-z]?(?:\d+(?:\.\d+)?)?){2,}(?:-[A-Z][a-z]?(?:\d+(?:\.\d+)?)?)*\b")

MATERIAL_STOPWORDS = {
    "XRD",
    "SEM",
    "TEM",
    "EDS",
    "XPS",
    "RDF",
    "DFT",
    "UV",
    "IR",
    "CPU",
    "GPU",
}

MATERIAL_LEXICON = [
    "graphene",
    "graphene oxide",
    "reduced graphene oxide",
    "silicon carbide",
    "titanium dioxide",
    "molybdenum disulfide",
    "lithium iron phosphate",
    "perovskite",
    "mxene",
    "boron nitride",
    "carbon nanotube",
]

PROCESS_KEYWORDS = [
    "annealing",
    "sintering",
    "deposition",
    "chemical vapor deposition",
    "physical vapor deposition",
    "sol-gel",
    "hydrothermal",
    "electrospinning",
    "etching",
    "calcination",
]

APPLICATION_KEYWORDS = [
    "nanoelectronics",
    "battery",
    "supercapacitor",
    "sensor",
    "catalysis",
    "photovoltaics",
    "thermoelectric",
    "optoelectronics",
]

CRYSTAL_STRUCTURE_KEYWORDS = [
    "hexagonal",
    "cubic",
    "tetragonal",
    "orthorhombic",
    "monoclinic",
    "trigonal",
    "wurtzite",
    "perovskite structure",
]


def extract_entities_from_chunks(chunks: list[tuple[int, str]]) -> list[ExtractedEntityCandidate]:
    settings = get_settings()
    best_candidates: dict[tuple[str, str, int], ExtractedEntityCandidate] = {}

    for chunk_index, content in chunks:
        for candidate in _extract_materials(content, chunk_index):
            _upsert_candidate(best_candidates, candidate)
        for candidate in _extract_property_measurements(content, chunk_index):
            _upsert_candidate(best_candidates, candidate)
        for candidate in _extract_property_mentions(content, chunk_index):
            _upsert_candidate(best_candidates, candidate)
        for candidate in _extract_keywords(content, chunk_index, PROCESS_KEYWORDS, "process"):
            _upsert_candidate(best_candidates, candidate)
        for candidate in _extract_keywords(content, chunk_index, APPLICATION_KEYWORDS, "application"):
            _upsert_candidate(best_candidates, candidate)
        for candidate in _extract_keywords(content, chunk_index, CRYSTAL_STRUCTURE_KEYWORDS, "crystal_structure"):
            _upsert_candidate(best_candidates, candidate)

        if settings.extraction_enable_spacy:
            for candidate in _extract_with_spacy(content, chunk_index):
                _upsert_candidate(best_candidates, candidate)

        if settings.extraction_enable_scibert:
            for candidate in _extract_with_scibert(content, chunk_index):
                _upsert_candidate(best_candidates, candidate)

    return sorted(
        best_candidates.values(),
        key=lambda item: (item.source_chunk_index, item.entity_type, item.entity_value.lower()),
    )


def _extract_materials(content: str, chunk_index: int) -> list[ExtractedEntityCandidate]:
    output: list[ExtractedEntityCandidate] = []

    for match in MATERIAL_FORMULA_PATTERN.finditer(content):
        material = match.group(0)

        if material.upper() in MATERIAL_STOPWORDS:
            continue
        if material.isupper() and len(material) <= 4:
            continue

        output.append(
            ExtractedEntityCandidate(
                entity_type="material",
                entity_value=material,
                confidence=0.86,
                source_chunk_index=chunk_index,
            )
        )

    lowered = content.lower()
    for term in MATERIAL_LEXICON:
        if not re.search(rf"\b{re.escape(term)}\b", lowered):
            continue

        output.append(
            ExtractedEntityCandidate(
                entity_type="material",
                entity_value=term,
                confidence=0.82,
                source_chunk_index=chunk_index,
            )
        )

    return output


def _extract_property_measurements(content: str, chunk_index: int) -> list[ExtractedEntityCandidate]:
    output: list[ExtractedEntityCandidate] = []
    for match in PROPERTY_MEASUREMENT_PATTERN.finditer(content):
        property_name = _normalize_property_name(match.group("property"))
        value_text = match.group("value")
        value_high_text = match.group("value_high")
        unit = match.group("unit")

        if value_text is None:
            continue

        value = float(value_text)
        display_value = value_text if value_high_text is None else f"{value_text}-{value_high_text}"
        entity_value = f"{property_name}={display_value}{(' ' + unit) if unit else ''}"

        confidence = 0.82
        if unit:
            confidence += 0.04
        if value_high_text:
            confidence += 0.02

        output.append(
            ExtractedEntityCandidate(
                entity_type="property_measurement",
                entity_value=entity_value,
                confidence=min(confidence, 0.95),
                source_chunk_index=chunk_index,
                value=value,
                unit=unit,
                property_name=property_name,
            )
        )

    return output


def _extract_property_mentions(content: str, chunk_index: int) -> list[ExtractedEntityCandidate]:
    output: list[ExtractedEntityCandidate] = []
    for match in PROPERTY_NAME_PATTERN.finditer(content):
        property_name = _normalize_property_name(match.group("property"))
        trailing = content[match.end() : match.end() + 20]

        if re.search(r"\d", trailing):
            continue

        output.append(
            ExtractedEntityCandidate(
                entity_type="property",
                entity_value=property_name,
                confidence=0.7,
                source_chunk_index=chunk_index,
                property_name=property_name,
            )
        )

    return output


def _extract_keywords(
    content: str,
    chunk_index: int,
    keywords: list[str],
    entity_type: str,
) -> list[ExtractedEntityCandidate]:
    lowered = content.lower()
    output: list[ExtractedEntityCandidate] = []

    for keyword in keywords:
        if keyword not in lowered:
            continue

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

    for pattern, canonical in PROPERTY_ALIASES.items():
        if re.fullmatch(pattern, name, flags=re.IGNORECASE):
            return canonical

    return name


def _upsert_candidate(
    destination: dict[tuple[str, str, int], ExtractedEntityCandidate],
    candidate: ExtractedEntityCandidate,
) -> None:
    key = (candidate.entity_type, candidate.entity_value.lower(), candidate.source_chunk_index)
    existing = destination.get(key)

    if existing is None:
        destination[key] = candidate
        return

    if _candidate_score(candidate) > _candidate_score(existing):
        destination[key] = candidate


def _candidate_score(candidate: ExtractedEntityCandidate) -> float:
    richness_bonus = 0.0
    if candidate.unit:
        richness_bonus += 0.03
    if candidate.value is not None:
        richness_bonus += 0.03
    if candidate.property_name:
        richness_bonus += 0.02
    return candidate.confidence + richness_bonus


def _extract_with_spacy(content: str, chunk_index: int) -> list[ExtractedEntityCandidate]:
    nlp = _get_spacy_model()
    if nlp is None:
        return []

    entities: list[ExtractedEntityCandidate] = []
    doc = nlp(content)

    for named_entity in doc.ents:
        text = named_entity.text.strip()
        if len(text) < 2:
            continue

        entity_type = _map_external_label_to_entity_type(named_entity.label_.upper(), text)
        if entity_type is None:
            continue

        confidence = 0.64
        if entity_type == "material" and _looks_like_material(text):
            confidence = 0.74

        entities.append(
            ExtractedEntityCandidate(
                entity_type=entity_type,
                entity_value=text,
                confidence=confidence,
                source_chunk_index=chunk_index,
                property_name=text if entity_type == "property" else None,
            )
        )

    return entities


def _extract_with_scibert(content: str, chunk_index: int) -> list[ExtractedEntityCandidate]:
    ner_pipeline = _get_scibert_pipeline()
    if ner_pipeline is None:
        return []

    try:
        inferred = ner_pipeline(content)
    except Exception:
        return []

    entities: list[ExtractedEntityCandidate] = []
    for item in inferred:
        text = str(item.get("word") or "").strip()
        if len(text) < 2:
            continue

        label = str(item.get("entity_group") or item.get("entity") or "").upper()
        entity_type = _map_external_label_to_entity_type(label, text)
        if entity_type is None:
            continue

        score = float(item.get("score") or 0.0)
        confidence = min(0.95, max(0.58, score))

        entities.append(
            ExtractedEntityCandidate(
                entity_type=entity_type,
                entity_value=text,
                confidence=confidence,
                source_chunk_index=chunk_index,
                property_name=text if entity_type == "property" else None,
            )
        )

    return entities


def _get_spacy_model() -> Any:
    global _SPACY_MODEL, _SPACY_LOAD_FAILED

    settings = get_settings()
    if not settings.extraction_enable_spacy:
        return None

    if _SPACY_MODEL is not None:
        return _SPACY_MODEL
    if _SPACY_LOAD_FAILED or spacy is None:
        return None

    try:
        _SPACY_MODEL = spacy.load(settings.extraction_spacy_model)
    except Exception:
        _SPACY_LOAD_FAILED = True
        return None

    return _SPACY_MODEL


def _get_scibert_pipeline() -> Any:
    global _SCIBERT_PIPELINE, _SCIBERT_LOAD_FAILED

    settings = get_settings()
    if not settings.extraction_enable_scibert or not settings.extraction_scibert_model:
        return None

    if _SCIBERT_PIPELINE is not None:
        return _SCIBERT_PIPELINE
    if _SCIBERT_LOAD_FAILED or transformers_pipeline is None:
        return None

    try:
        _SCIBERT_PIPELINE = transformers_pipeline(
            "token-classification",
            model=settings.extraction_scibert_model,
            aggregation_strategy="simple",
            device=settings.extraction_scibert_device,
        )
    except Exception:
        _SCIBERT_LOAD_FAILED = True
        return None

    return _SCIBERT_PIPELINE


def _map_external_label_to_entity_type(label: str, text: str) -> str | None:
    normalized = label.upper()

    if any(token in normalized for token in ["MAT", "CHEM", "MATERIAL"]):
        return "material"
    if any(token in normalized for token in ["PROP", "PROPERTY"]):
        return "property"
    if any(token in normalized for token in ["PROC", "METHOD"]):
        return "process"
    if any(token in normalized for token in ["APP", "DEVICE", "PRODUCT"]):
        return "application"
    if any(token in normalized for token in ["CRYSTAL", "STRUCT"]):
        return "crystal_structure"

    if _looks_like_material(text):
        return "material"

    return None


def _looks_like_material(text: str) -> bool:
    stripped = text.strip()
    lower_text = stripped.lower()

    if re.fullmatch(MATERIAL_FORMULA_PATTERN, stripped):
        return True
    if lower_text in MATERIAL_LEXICON:
        return True
    return False
