from typing import Any

from app.repositories.task_repository import TaskRepository
from app.models.common import AsyncTask


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    async def create_task(self, tenant_id: int, task_type: str, ref_id: int | None = None) -> AsyncTask:
        return await self.repository.create_task(tenant_id, task_type, ref_id)

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
        return await self.repository.update_task(
            task_id,
            status=status,
            progress=progress,
            message=message,
            result=result,
            error=error,
        )

    async def get_task(self, task_id: str) -> AsyncTask | None:
        return await self.repository.get_task(task_id)
