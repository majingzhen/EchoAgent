from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


WORKFLOW_TEMPLATES: dict[str, dict[str, Any]] = {
    "content_validation": {
        "label": "内容验证流",
        "steps": [
            {"name": "workshop",        "label": "内容工坊",  "required": True},
            {"name": "simulation",      "label": "沙盘推演",  "required": True},
            {"name": "sentiment_guard", "label": "舆情哨兵",  "required": False},
        ],
    },
    "full_campaign": {
        "label": "完整营销活动流",
        "steps": [
            {"name": "market",           "label": "市场智脑",  "required": False},
            {"name": "workshop",         "label": "内容工坊",  "required": True},
            {"name": "simulation",       "label": "沙盘推演",  "required": True},
            {"name": "sentiment_guard",  "label": "舆情哨兵",  "required": False},
            {"name": "strategy_advisor", "label": "策略参谋",  "required": False},
        ],
    },
}


class WorkflowCreateRequest(BaseModel):
    workflow_type: str
    persona_group_id: int
    platform: str = "xiaohongshu"
    brand_tone: str = "专业、可信"
    brief: str
    market_source_text: str = ""
    disabled_steps: list[str] = []


class WorkflowStepRecord(BaseModel):
    name: str
    label: str
    required: bool
    status: str = "pending"  # pending / running / completed / failed / skipped
    result: dict[str, Any] = {}
    session_id: int | None = None
    error: str | None = None


class WorkflowSession(BaseModel):
    id: int
    tenant_id: int
    workflow_type: str
    status: str
    config: dict[str, Any]
    steps: list[WorkflowStepRecord]
    current_step: str | None
    created_at: datetime
    updated_at: datetime
