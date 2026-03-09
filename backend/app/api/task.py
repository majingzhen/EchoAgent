from fastapi import APIRouter, HTTPException

from app.deps import task_service
from app.models.common import APIResponse

router = APIRouter(prefix="/tasks", tags=["task"])


@router.get("/{task_id}")
async def get_task(task_id: str) -> APIResponse[dict]:
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return APIResponse(data=task.model_dump())
