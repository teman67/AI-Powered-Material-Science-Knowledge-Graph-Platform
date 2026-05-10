from app.services.entity_extraction import extract_entities_from_chunks


def test_extract_entities_finds_material_property_and_application() -> None:
    text = (
        "MoS2 exhibits a direct bandgap of 1.8 eV and thermal conductivity 85 W/mK. "
        "This enables nanoelectronics applications."
    )

    entities = extract_entities_from_chunks([(0, text)])

    materials = [entity for entity in entities if entity.entity_type == "material"]
    properties = [entity for entity in entities if entity.entity_type == "property_measurement"]
    applications = [entity for entity in entities if entity.entity_type == "application"]

    assert any(entity.entity_value == "MoS2" for entity in materials)
    assert any(entity.property_name == "bandgap" and entity.value == 1.8 and entity.unit == "eV" for entity in properties)
    assert any(entity.entity_value == "nanoelectronics" for entity in applications)


def test_extract_entities_supports_richer_scientific_patterns() -> None:
    text = (
        "Graphene oxide synthesized by chemical vapor deposition shows dielectric constant of 12.5 "
        "and carrier mobility 1200 cm2/Vs in hexagonal phase for sensor applications."
    )

    entities = extract_entities_from_chunks([(0, text)])

    properties = [entity for entity in entities if entity.entity_type == "property_measurement"]
    processes = [entity for entity in entities if entity.entity_type == "process"]
    structures = [entity for entity in entities if entity.entity_type == "crystal_structure"]

    assert any(entity.entity_value == "graphene oxide" for entity in entities if entity.entity_type == "material")
    assert any(entity.property_name == "dielectric constant" and entity.value == 12.5 for entity in properties)
    assert any(entity.property_name == "carrier mobility" and entity.value == 1200.0 and entity.unit == "cm2/Vs" for entity in properties)
    assert any(entity.entity_value == "chemical vapor deposition" for entity in processes)
    assert any(entity.entity_value == "hexagonal" for entity in structures)


def test_extract_entities_avoids_common_acronym_false_materials() -> None:
    text = "XRD and SEM confirm phase purity before annealing of SiC films."

    entities = extract_entities_from_chunks([(0, text)])
    materials = [entity.entity_value for entity in entities if entity.entity_type == "material"]

    assert "XRD" not in materials
    assert "SEM" not in materials
    assert "SiC" in materials
