from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.deps import workshop_service
from app.models.common import APIResponse
from app.models.workshop import (
    WorkshopCreateRequest,
    WorkshopInjectInsightsRequest,
    WorkshopRunRequest,
)


class ContentResultRequest(BaseModel):
    variant: str
    went_live: bool = False
    actual_engagement_rate: float | None = None
    actual_conversion_rate: float | None = None
    notes: str = ""

router = APIRouter(prefix="/workshop", tags=["workshop"])


@router.get("/sessions")
async def list_workshop_sessions() -> APIResponse[list[dict]]:
    sessions = await workshop_service.list_sessions(1)
    return APIResponse(data=sessions)


@router.post("/sessions")
async def create_workshop_session(request: WorkshopCreateRequest) -> APIResponse[dict]:
    session = await workshop_service.create_session(request)
    return APIResponse(data=session.model_dump())


@router.post("/sessions/{session_id}/run")
async def run_workshop_session(session_id: int, request: WorkshopRunRequest) -> APIResponse[dict]:
    session = await workshop_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="workshop session not found")
    task_id = await workshop_service.run_session_async(
        session_id, session.tenant_id, request.market_graph_id
    )
    return APIResponse(data={"task_id": task_id, "session_id": session_id})


@router.get("/sessions/{session_id}")
async def get_workshop_session(session_id: int) -> APIResponse[dict]:
    session = await workshop_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="workshop session not found")
    return APIResponse(data=session.model_dump())


@router.post("/sessions/{session_id}/inject-insights")
async def inject_workshop_insights(session_id: int, request: WorkshopInjectInsightsRequest) -> APIResponse[dict]:
    insights = await workshop_service.inject_insights(session_id, request.graph_id)
    if insights is None:
        raise HTTPException(status_code=404, detail="workshop session or graph not found")
    return APIResponse(data={"insights": insights})


@router.post("/sessions/{session_id}/ab-test")
async def workshop_create_ab_test(session_id: int) -> APIResponse[dict]:
    result = await workshop_service.create_ab_test(session_id)
    if not result:
        raise HTTPException(status_code=400, detail="workshop session has no valid variants")
    return APIResponse(data=result)


@router.post("/sessions/{session_id}/results")
async def save_content_result(session_id: int, request: ContentResultRequest) -> APIResponse[dict]:
    session = await workshop_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="workshop session not found")
    result_id = await workshop_service.save_result(
        session_id,
        variant=request.variant,
        went_live=request.went_live,
        actual_engagement_rate=request.actual_engagement_rate,
        actual_conversion_rate=request.actual_conversion_rate,
        notes=request.notes,
    )
    return APIResponse(data={"id": result_id, "session_id": session_id})


@router.get("/sessions/{session_id}/results")
async def get_content_results(session_id: int) -> APIResponse[list[dict]]:
    results = await workshop_service.get_results(session_id)
    return APIResponse(data=results)
