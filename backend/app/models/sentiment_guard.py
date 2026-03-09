from datetime import datetime
from typing import Any

from pydantic import BaseModel


class SentimentGuardRequest(BaseModel):
    mode: str = "proactive"  # proactive | reactive
    event_description: str
    current_sentiment: str = ""  # 事后应对模式时填入当前舆情状态


class SentimentGuardSession(BaseModel):
    id: int
    tenant_id: int
    mode: str
    event_description: str
    status: str
    payload: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class SentimentGuardReport(BaseModel):
    session_id: int
    mode: str
    risk_assessment: dict[str, Any]
    spread_simulation: dict[str, Any]
    response_plans: list[dict[str, Any]]
    validation_results: list[dict[str, Any]]
    best_plan: str
    execution_window: str
    summary: str
