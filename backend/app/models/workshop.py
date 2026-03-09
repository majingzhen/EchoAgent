from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class WorkshopCreateRequest(BaseModel):
    persona_group_id: int
    platform: str = "小红书"
    brand_tone: str = "专业可信、真诚克制"
    brief: str
    goal: str = "提升转化率"
    product: str = "新品"


class WorkshopRunRequest(BaseModel):
    market_graph_id: int | None = None


class WorkshopInjectInsightsRequest(BaseModel):
    graph_id: int


class WorkshopSession(BaseModel):
    id: int
    tenant_id: int
    persona_group_id: int
    platform: str
    brand_tone: str
    brief: dict[str, Any]
    status: str
    payload: dict[str, Any] = Field(default_factory=dict)
    insights: list[str] = Field(default_factory=list)
    ab_test_id: int | None = None
    created_at: datetime
    updated_at: datetime
