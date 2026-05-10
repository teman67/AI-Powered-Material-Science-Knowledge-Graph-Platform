from functools import lru_cache


@lru_cache
def get_pmdcore_mappings() -> dict[str, dict[str, str]]:
    class_map = {
        "document": "pmd:Document",
        "material": "pmd:Material",
        "property": "pmd:Property",
        "process": "pmd:Process",
        "application": "pmd:Application",
    }

    property_map = {
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

    return {
        "class_map": class_map,
        "property_map": property_map,
    }
