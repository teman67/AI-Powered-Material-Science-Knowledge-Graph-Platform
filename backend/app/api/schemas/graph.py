from pydantic import BaseModel


class GraphMaterialItem(BaseModel):
    material: str
    property_count: int
    process_count: int
    application_count: int


class GraphMaterialsResponse(BaseModel):
    items: list[GraphMaterialItem]


class GraphRelationItem(BaseModel):
    source: str
    relation: str
    target: str


class GraphRelationsResponse(BaseModel):
    items: list[GraphRelationItem]


class CrossPaperLinkItem(BaseModel):
    document_a_id: int
    document_a_title: str | None
    document_b_id: int
    document_b_title: str | None
    shared_entity_count: int
    shared_entities: list[str]


class CrossPaperLinksResponse(BaseModel):
    items: list[CrossPaperLinkItem]
