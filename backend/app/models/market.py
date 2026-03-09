from datetime import datetime

from pydantic import BaseModel, Field


class MarketGraphBuildRequest(BaseModel):
    name: str
    source_text: str


class MarketEntity(BaseModel):
    entity_id: str
    name: str
    entity_type: str
    score: float


class MarketRelation(BaseModel):
    source: str
    target: str
    relation_type: str
    weight: float


class MarketGraph(BaseModel):
    id: int
    tenant_id: int
    name: str
    source_text: str
    entities: list[MarketEntity] = Field(default_factory=list)
    relations: list[MarketRelation] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class MarketReport(BaseModel):
    graph_id: int
    summary: str
    competitor_landscape: list[str] = Field(default_factory=list)
    key_insights: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
