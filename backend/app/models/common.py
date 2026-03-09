from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "ok"
    data: T | None = None


class AsyncTask(BaseModel):
    id: str
    tenant_id: int
    task_type: str
    ref_id: int | None = None
    status: str = "pending"
    progress: int = 0
    message: str = "created"
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

