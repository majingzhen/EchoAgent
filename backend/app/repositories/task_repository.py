from __future__ import annotations

from datetime import datetime
from typing import Any

from app.db.memory_store import MemoryStore
from app.models.common import AsyncTask


class TaskRepository:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store
        self._seq_key = "echo:task:seq"
        self._task_prefix = "echo:task:"

    def _key(self, task_id: str) -> str:
        return f"{self._task_prefix}{task_id}"

    async def create_task(self, tenant_id: int, task_type: str, ref_id: int | None = None) -> AsyncTask:
        seq = await self.store.incr(self._seq_key)
        task_id = f"TASK-{seq:06d}"
        now = datetime.utcnow()
        task = AsyncTask(
            id=task_id,
            tenant_id=tenant_id,
            task_type=task_type,
            ref_id=ref_id,
            status="pending",
            progress=0,
            message="task created",
            created_at=now,
            updated_at=now,
        )
        await self.store.hset_json(self._key(task_id), task.model_dump())
        return task

    async def get_task(self, task_id: str) -> AsyncTask | None:
        raw = await self.store.hgetall_json(self._key(task_id))
        if not raw:
            return None
        return AsyncTask(**raw)

    async def update_task(
        self,
        task_id: str,
        *,
        status: str | None = None,
        progress: int | None = None,
        message: str | None = None,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> AsyncTask | None:
        task = await self.get_task(task_id)
        if not task:
            return None
        if status is not None:
            task.status = status
        if progress is not None:
            task.progress = max(0, min(progress, 100))
        if message is not None:
            task.message = message
        if result is not None:
            task.result = result
        if error is not None:
            task.error = error
        task.updated_at = datetime.utcnow()
        await self.store.hset_json(self._key(task_id), task.model_dump())
        return task
