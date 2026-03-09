from datetime import datetime
from typing import Any

from pydantic import BaseModel


class StrategyAdvisorRequest(BaseModel):
    question: str
    context_info: str = ""


class StrategyAdvisorSession(BaseModel):
    id: int
    tenant_id: int
    question: str
    context_info: str
    status: str
    payload: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
