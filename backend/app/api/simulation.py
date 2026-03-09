from fastapi import APIRouter, HTTPException

from app.deps import simulation_engine
from app.models.common import APIResponse
from app.models.simulation import ABTestCreateRequest, SimulationCreateRequest

router = APIRouter(prefix="/simulations", tags=["simulation"])


@router.get("")
async def list_simulations() -> APIResponse[list[dict]]:
    sessions = await simulation_engine.list_sessions(1)
    return APIResponse(data=sessions)


@router.post("")
async def create_simulation(request: SimulationCreateRequest) -> APIResponse[dict]:
    session = await simulation_engine.create_session(request)
    return APIResponse(data=session.model_dump())


@router.post("/{session_id}/start")
async def start_simulation(session_id: int) -> APIResponse[dict]:
    task_id = await simulation_engine.start(session_id)
    if not task_id:
        raise HTTPException(status_code=404, detail="simulation session not found")
    return APIResponse(data={"task_id": task_id, "session_id": session_id})


@router.get("/{session_id}/status")
async def simulation_status(session_id: int) -> APIResponse[dict]:
    session = await simulation_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="simulation session not found")
    return APIResponse(data=session.model_dump())


@router.get("/{session_id}/report")
async def simulation_report(session_id: int) -> APIResponse[dict]:
    report = await simulation_engine.get_report(session_id)
    if not report:
        raise HTTPException(status_code=404, detail="simulation report not ready")
    return APIResponse(data=report.model_dump())


@router.post("/ab-test")
async def create_ab_test(request: ABTestCreateRequest) -> APIResponse[dict]:
    result = await simulation_engine.create_ab_test(request)
    return APIResponse(data=result)


@router.get("/ab-test/{test_id}")
async def get_ab_test(test_id: int) -> APIResponse[dict]:
    result = await simulation_engine.get_ab_test(test_id)
    if not result:
        raise HTTPException(status_code=404, detail="ab test not found")
    return APIResponse(data=result)
