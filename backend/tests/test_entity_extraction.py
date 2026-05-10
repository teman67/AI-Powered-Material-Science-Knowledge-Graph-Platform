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
