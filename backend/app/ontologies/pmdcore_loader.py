from functools import lru_cache
import logging
from pathlib import Path

from rdflib import Graph, OWL, RDF, RDFS, URIRef

from app.core.config import get_settings

LOGGER = logging.getLogger(__name__)

DEFAULT_CLASS_MAP = {
    "document": "pmd:Document",
    "material": "pmd:Material",
    "property": "pmd:Property",
    "process": "pmd:Process",
    "application": "pmd:Application",
}

DEFAULT_PROPERTY_MAP = {
    "bandgap": "pmd:ElectricalProperty",
    "conductivity": "pmd:TransportProperty",
    "thermal conductivity": "pmd:TransportProperty",
    "carrier mobility": "pmd:TransportProperty",
    "seebeck coefficient": "pmd:TransportProperty",
    "youngs modulus": "pmd:MechanicalProperty",
    "tensile strength": "pmd:MechanicalProperty",
    "yield strength": "pmd:MechanicalProperty",
    "fracture toughness": "pmd:MechanicalProperty",
    "hardness": "pmd:MechanicalProperty",
    "density": "pmd:PhysicalProperty",
    "dielectric constant": "pmd:ElectricalProperty",
}

CLASS_TARGETS = {
    "document": ("Document",),
    "material": ("Material",),
    "property": ("Property",),
    "process": ("Process",),
    "application": ("Application",),
}

PROPERTY_TARGETS = {
    "bandgap": ("ElectricalProperty", "BandgapProperty"),
    "dielectric constant": ("ElectricalProperty",),
    "conductivity": ("TransportProperty", "TransportPropertyCustom"),
    "thermal conductivity": ("TransportProperty", "TransportPropertyCustom"),
    "carrier mobility": ("TransportProperty", "TransportPropertyCustom"),
    "seebeck coefficient": ("TransportProperty", "TransportPropertyCustom"),
    "youngs modulus": ("MechanicalProperty",),
    "tensile strength": ("MechanicalProperty",),
    "yield strength": ("MechanicalProperty",),
    "fracture toughness": ("MechanicalProperty",),
    "hardness": ("MechanicalProperty",),
    "density": ("PhysicalProperty",),
}


@lru_cache
def get_pmdcore_mappings() -> dict[str, dict[str, str]]:
    settings = get_settings()
    ontology_path = _resolve_ontology_path(settings.pmdcore_ontology_path)
    if ontology_path is None or not ontology_path.exists():
        if ontology_path is not None:
            LOGGER.warning("PMDcore ontology file not found at %s. Falling back to built-in mappings.", ontology_path)
        return _fallback_mappings()

    graph = Graph()
    try:
        graph.parse(str(ontology_path), format=_guess_rdf_format(ontology_path))
    except Exception as exc:
        LOGGER.warning("Failed to parse PMDcore ontology at %s: %s. Falling back to built-in mappings.", ontology_path, exc)
        return _fallback_mappings()

    class_map = _build_class_map(graph)
    property_map = _build_property_map(graph)

    return {
        "class_map": class_map,
        "property_map": property_map,
    }


def _fallback_mappings() -> dict[str, dict[str, str]]:
    return {
        "class_map": DEFAULT_CLASS_MAP.copy(),
        "property_map": DEFAULT_PROPERTY_MAP.copy(),
    }


def _resolve_ontology_path(raw_path: str) -> Path | None:
    if not raw_path:
        return None

    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate

    backend_root = Path(__file__).resolve().parents[2]
    repo_root = backend_root.parent

    lookup_paths = [
        Path.cwd() / candidate,
        backend_root / candidate,
        repo_root / candidate,
    ]

    # Convenience fallback: if user drops only "pmdcore.ttl" in root, resolve it automatically.
    if candidate.name.lower() == "pmdcore.ttl":
        lookup_paths.extend(
            [
                backend_root / "app" / "ontologies" / "pmdcore.ttl",
                backend_root / "pmdcore.ttl",
                repo_root / "pmdcore.ttl",
            ]
        )

    for path in lookup_paths:
        if path.exists():
            return path.resolve()

    # If configured path points to the default filename but user provided a different
    # PMDcore TTL filename, select the first matching ontology file automatically.
    if candidate.name.lower() == "pmdcore.ttl":
        for root in (backend_root / "app" / "ontologies", backend_root, repo_root):
            if not root.exists():
                continue
            ttl_candidates = sorted(
                [item for item in root.glob("*.ttl") if "pmdcore" in item.name.lower()]
            )
            if ttl_candidates:
                return ttl_candidates[0].resolve()

    return (backend_root / candidate).resolve()


def _guess_rdf_format(path: Path) -> str | None:
    suffix = path.suffix.lower()
    if suffix in {".ttl", ".turtle"}:
        return "turtle"
    if suffix in {".owl", ".rdf", ".xml"}:
        return "xml"
    return None


def _build_class_map(graph: Graph) -> dict[str, str]:
    mapped = DEFAULT_CLASS_MAP.copy()
    for key, candidates in CLASS_TARGETS.items():
        found = _find_first_class(graph, candidates)
        if found is not None:
            mapped[key] = _to_pmd_mapping(found)
    return mapped


def _build_property_map(graph: Graph) -> dict[str, str]:
    mapped = DEFAULT_PROPERTY_MAP.copy()
    for alias, candidates in PROPERTY_TARGETS.items():
        found = _find_first_class(graph, candidates)
        if found is not None:
            mapped[alias] = _to_pmd_mapping(found)
    return mapped


def _find_first_class(graph: Graph, candidates: tuple[str, ...]) -> URIRef | None:
    for class_name in candidates:
        found = _find_class_uri(graph, class_name)
        if found is not None:
            return found
    return None


def _find_class_uri(graph: Graph, class_name: str) -> URIRef | None:
    lower_name = class_name.lower()

    for subject in graph.subjects(RDF.type, OWL.Class):
        if isinstance(subject, URIRef) and _uri_matches_local_name(subject, lower_name):
            return subject

    for subject in graph.subjects(RDF.type, RDFS.Class):
        if isinstance(subject, URIRef) and _uri_matches_local_name(subject, lower_name):
            return subject

    for subject, _, label in graph.triples((None, RDFS.label, None)):
        if not isinstance(subject, URIRef):
            continue
        if str(label).strip().lower() == lower_name:
            return subject

    return None


def _uri_matches_local_name(uri: URIRef, lower_name: str) -> bool:
    return _uri_local_name(uri).lower() == lower_name


def _uri_local_name(uri: URIRef) -> str:
    value = str(uri)
    if "#" in value:
        return value.rsplit("#", 1)[1]
    if "/" in value:
        return value.rsplit("/", 1)[1]
    return value


def _to_pmd_mapping(uri: URIRef) -> str:
    return f"pmd:{_uri_local_name(uri)}"
