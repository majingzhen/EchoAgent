from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SimulationCreateRequest(BaseModel):
    content_id: int | None = None
    content_text: str
    persona_group_id: int
    platform: str = "小红书"
    config: dict[str, Any] = Field(default_factory=lambda: {"max_rounds": 8})


class SimulationStatus(BaseModel):
    id: int
    tenant_id: int
    persona_group_id: int
    platform: str
    status: str
    total_rounds: int
    current_round: int
    metrics_timeline: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class SimulationActionRecord(BaseModel):
    round_num: int
    persona_id: int
    persona_name: str
    action_type: str
    comment_text: str | None = None
    sentiment_score: float
    purchase_intent: float


class SimulationReport(BaseModel):
    session_id: int
    executive_summary: str
    metrics: dict[str, Any]
    segment_insights: list[dict[str, Any]]
    propagation: dict[str, Any]
    risks: list[str]
    suggestions: list[str]
    sample_comments: list[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ABTestCreateRequest(BaseModel):
    name: str
    persona_group_id: int
    platform: str
    variants: list[str] = Field(min_length=2, max_length=5)

