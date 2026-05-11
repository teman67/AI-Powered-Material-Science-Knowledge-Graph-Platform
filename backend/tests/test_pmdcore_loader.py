from pathlib import Path

from app.core.config import get_settings
from app.ontologies.pmdcore_loader import get_pmdcore_mappings


def _clear_caches() -> None:
    get_settings.cache_clear()
    get_pmdcore_mappings.cache_clear()


def test_pmdcore_loader_fallback_when_file_missing(monkeypatch) -> None:
    monkeypatch.setenv("PMDCORE_ONTOLOGY_PATH", "app/ontologies/does-not-exist.ttl")
    _clear_caches()

    mappings = get_pmdcore_mappings()

    assert mappings["class_map"]["material"] == "pmd:Material"
    assert mappings["property_map"]["conductivity"] == "pmd:TransportProperty"

    _clear_caches()


def test_pmdcore_loader_reads_ttl_and_uses_custom_class(monkeypatch, tmp_path: Path) -> None:
    ttl_file = tmp_path / "pmdcore-mini.ttl"
    ttl_file.write_text(
        """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix pmd: <http://example.org/pmd#> .

pmd:Document a owl:Class .
pmd:Material a owl:Class .
pmd:Property a owl:Class .
pmd:Process a owl:Class .
pmd:Application a owl:Class .

pmd:ElectricalProperty a owl:Class .
pmd:MechanicalProperty a owl:Class .
pmd:PhysicalProperty a owl:Class .
pmd:TransportPropertyCustom a owl:Class .
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setenv("PMDCORE_ONTOLOGY_PATH", str(ttl_file))
    _clear_caches()

    mappings = get_pmdcore_mappings()

    assert mappings["class_map"]["material"] == "pmd:Material"
    assert mappings["property_map"]["conductivity"] == "pmd:TransportPropertyCustom"

    _clear_caches()