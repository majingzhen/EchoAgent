from fastapi import APIRouter, HTTPException

from app.deps import strategy_advisor_service
from app.models.common import APIResponse
from app.models.strategy_advisor import StrategyAdvisorRequest

router = APIRouter(prefix="/strategy-advisor", tags=["strategy-advisor"])


@router.post("/analyze")
async def run_analysis(request: StrategyAdvisorRequest) -> APIResponse[dict]:
    task_id, session_id = await strategy_advisor_service.run_async(request)
    return APIResponse(data={"task_id": task_id, "session_id": session_id})


@router.get("/sessions")
async def list_sessions() -> APIResponse[list[dict]]:
    sessions = await strategy_advisor_service.list_sessions(1)
    return APIResponse(data=[s.model_dump() for s in sessions])


@router.get("/sessions/{session_id}")
async def get_session(session_id: int) -> APIResponse[dict]:
    session = await strategy_advisor_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    return APIResponse(data=session.model_dump())
