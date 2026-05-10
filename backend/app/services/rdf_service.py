from dataclasses import dataclass
from datetime import datetime, timezone

from pyshacl import validate
from rdflib import Graph, Literal, Namespace, RDF, URIRef, XSD

from app.models import Chunk, Document
from app.services.entity_extraction import extract_entities_from_chunks
from app.services.ontology_mapping import MappedEntityRecord, map_entities_to_ontology

PMD = Namespace("http://example.org/pmd#")
EX = Namespace("http://example.org/resource/")


@dataclass
class RdfGenerationResult:
    ttl_content: str
    is_valid: bool
    validation_report: str
    entities: list[MappedEntityRecord]


def generate_rdf_for_document(document: Document, chunks: list[Chunk]) -> RdfGenerationResult:
    candidates = extract_entities_from_chunks([(chunk.chunk_index, chunk.content) for chunk in chunks])
    mapped_entities = map_entities_to_ontology(candidates)

    graph = Graph()
    graph.bind("pmd", PMD)
    graph.bind("ex", EX)

    document_node = EX[f"document_{document.id}"]
    graph.add((document_node, RDF.type, PMD.Document))

    if document.title:
        graph.add((document_node, PMD.title, Literal(document.title)))

    material_nodes = _add_materials(graph, document_node, mapped_entities)
    _add_property_measurements(graph, material_nodes, mapped_entities)
    _add_processes(graph, material_nodes, mapped_entities)
    _add_applications(graph, material_nodes, mapped_entities)

    ttl_content = graph.serialize(format="turtle")
    is_valid, validation_report = _validate_graph(graph)

    return RdfGenerationResult(
        ttl_content=ttl_content,
        is_valid=is_valid,
        validation_report=validation_report,
        entities=mapped_entities,
    )


def _add_materials(graph: Graph, document_node: URIRef, entities: list[MappedEntityRecord]) -> list[URIRef]:
    material_nodes: list[URIRef] = []

    materials = [entity for entity in entities if entity.entity_type == "material"]
    if not materials:
        fallback = EX["material_unknown"]
        graph.add((fallback, RDF.type, PMD.Material))
        graph.add((document_node, PMD.mentions, fallback))
        return [fallback]

    for entity in materials:
        resource = EX[f"material_{_slug(entity.entity_value)}"]
        graph.add((resource, RDF.type, PMD.Material))
        graph.add((resource, PMD.label, Literal(entity.entity_value)))
        graph.add((document_node, PMD.mentions, resource))
        material_nodes.append(resource)

    return material_nodes


def _add_property_measurements(graph: Graph, material_nodes: list[URIRef], entities: list[MappedEntityRecord]) -> None:
    if not material_nodes:
        return

    material = material_nodes[0]
    measurements = [entity for entity in entities if entity.entity_type == "property_measurement"]
    for index, entity in enumerate(measurements, start=1):
        property_node = EX[f"property_{_slug(entity.property_name or entity.entity_value)}_{index}"]
        graph.add((property_node, RDF.type, _mapping_to_uri(entity.ontology_mapping)))
        graph.add((property_node, PMD.label, Literal(entity.property_name or entity.entity_value)))
        if entity.numeric_value is not None:
            graph.add((property_node, PMD.value, Literal(entity.numeric_value, datatype=XSD.float)))
        if entity.unit:
            graph.add((property_node, PMD.unit, Literal(entity.unit)))

        graph.add((material, PMD.hasProperty, property_node))


def _add_processes(graph: Graph, material_nodes: list[URIRef], entities: list[MappedEntityRecord]) -> None:
    if not material_nodes:
        return

    material = material_nodes[0]
    processes = [entity for entity in entities if entity.entity_type == "process"]
    for entity in processes:
        process_node = EX[f"process_{_slug(entity.entity_value)}"]
        graph.add((process_node, RDF.type, PMD.Process))
        graph.add((process_node, PMD.label, Literal(entity.entity_value)))
        graph.add((material, PMD.undergoesProcess, process_node))


def _add_applications(graph: Graph, material_nodes: list[URIRef], entities: list[MappedEntityRecord]) -> None:
    if not material_nodes:
        return

    material = material_nodes[0]
    applications = [entity for entity in entities if entity.entity_type == "application"]
    for entity in applications:
        application_node = EX[f"application_{_slug(entity.entity_value)}"]
        graph.add((application_node, RDF.type, PMD.Application))
        graph.add((application_node, PMD.label, Literal(entity.entity_value)))
        graph.add((material, PMD.hasApplication, application_node))


def _validate_graph(graph: Graph) -> tuple[bool, str]:
    shapes_graph = Graph().parse(data=_material_shape_ttl(), format="turtle")

    conforms, _, report_text = validate(
        data_graph=graph,
        shacl_graph=shapes_graph,
        inference="rdfs",
        serialize_report_graph="turtle",
    )
    return bool(conforms), str(report_text)


def _material_shape_ttl() -> str:
    return """
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix pmd: <http://example.org/pmd#> .

pmd:MaterialShape
    a sh:NodeShape ;
    sh:targetClass pmd:Material ;
    sh:property [
        sh:path pmd:hasProperty ;
        sh:minCount 1 ;
    ] .
"""


def _mapping_to_uri(mapping: str) -> URIRef:
    if mapping.startswith("pmd:"):
        return PMD[mapping.split(":", 1)[1]]
    return PMD.Property


def _slug(value: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "_" for char in value.strip())
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or f"entity_{int(datetime.now(tz=timezone.utc).timestamp())}"
