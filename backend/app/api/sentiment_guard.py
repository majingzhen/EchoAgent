from fastapi import APIRouter, HTTPException

from app.deps import sentiment_guard_service
from app.models.common import APIResponse
from app.models.sentiment_guard import SentimentGuardRequest

router = APIRouter(prefix="/sentiment-guard", tags=["sentiment-guard"])


@router.post("/assess")
async def run_assessment(request: SentimentGuardRequest) -> APIResponse[dict]:
    task_id, session_id = await sentiment_guard_service.run_async(request)
    return APIResponse(data={"task_id": task_id, "session_id": session_id})


@router.get("/sessions")
async def list_sessions() -> APIResponse[list[dict]]:
    sessions = await sentiment_guard_service.list_sessions(1)
    return APIResponse(data=[s.model_dump() for s in sessions])


@router.get("/sessions/{session_id}")
async def get_session(session_id: int) -> APIResponse[dict]:
    session = await sentiment_guard_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    return APIResponse(data=session.model_dump())
