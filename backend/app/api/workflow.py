from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.deps import workflow_engine
from app.models.common import APIResponse
from app.models.workflow import WORKFLOW_TEMPLATES, WorkflowCreateRequest

router = APIRouter(prefix="/workflows", tags=["workflow"])


@router.get("/templates")
async def list_templates() -> APIResponse[dict]:
    return APIResponse(data={
        k: {"label": v["label"], "steps": v["steps"]}
        for k, v in WORKFLOW_TEMPLATES.items()
    })


@router.post("")
async def create_workflow(request: WorkflowCreateRequest) -> APIResponse[dict]:
    if request.workflow_type not in WORKFLOW_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"未知工作流类型: {request.workflow_type}")
    session = await workflow_engine.create_workflow(request)
    return APIResponse(data=session.model_dump(mode="json"))


@router.get("")
async def list_workflows() -> APIResponse[list]:
    sessions = await workflow_engine.list(1)
    return APIResponse(data=[s.model_dump(mode="json") for s in sessions])


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: int) -> APIResponse[dict]:
    session = await workflow_engine.get(workflow_id)
    if not session:
        raise HTTPException(status_code=404, detail="workflow not found")
    return APIResponse(data=session.model_dump(mode="json"))


@router.get("/{workflow_id}/status")
async def get_workflow_status(workflow_id: int) -> APIResponse[dict]:
    session = await workflow_engine.get(workflow_id)
    if not session:
        raise HTTPException(status_code=404, detail="workflow not found")
    return APIResponse(data={
        "id": session.id,
        "status": session.status,
        "current_step": session.current_step,
        "steps": [s.model_dump() for s in session.steps],
    })


class CompleteStepRequest(BaseModel):
    notes: str = ""


@router.post("/{workflow_id}/steps/{step_name}/complete")
async def complete_workflow_step(workflow_id: int, step_name: str, request: CompleteStepRequest = CompleteStepRequest()) -> APIResponse[dict]:
    session = await workflow_engine.get(workflow_id)
    if not session:
        raise HTTPException(status_code=404, detail="workflow not found")
    updated = await workflow_engine.complete_step(workflow_id, step_name, notes=request.notes)
    if not updated:
        raise HTTPException(status_code=400, detail="step not found or already completed")
    return APIResponse(data=updated.model_dump(mode="json"))

