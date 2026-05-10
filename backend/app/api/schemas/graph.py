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
