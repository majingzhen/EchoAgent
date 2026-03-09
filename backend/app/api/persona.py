from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.deps import persona_memory_repository, persona_service
from app.models.common import APIResponse
from app.models.persona import PersonaGenerateRequest

router = APIRouter(prefix="/personas", tags=["personas"])


@router.post("/generate")
async def generate_personas(request: PersonaGenerateRequest) -> APIResponse[dict]:
    task_id, group_id = await persona_service.generate_group_async(request)
    return APIResponse(data={"task_id": task_id, "group_id": group_id})


@router.get("/groups")
async def list_groups() -> APIResponse[list[dict]]:
    groups = await persona_service.list_groups(1)
    return APIResponse(data=[g.model_dump() for g in groups])


@router.get("/groups/{group_id}")
async def group_detail(group_id: int) -> APIResponse[dict]:
    detail = await persona_service.get_group_detail(group_id)
    if not detail:
        raise HTTPException(status_code=404, detail="persona group not found")
    return APIResponse(data=detail.model_dump())


@router.get("/groups/{group_id}/personas")
async def group_personas(group_id: int) -> APIResponse[list[dict]]:
    personas = await persona_service.list_group_personas(group_id)
    if not personas:
        raise HTTPException(status_code=404, detail="persona group not found or empty")
    return APIResponse(data=[p.model_dump() for p in personas])


@router.get("/{persona_id}")
async def persona_detail(persona_id: int) -> APIResponse[dict]:
    persona = await persona_service.get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="persona not found")
    return APIResponse(data=persona.model_dump())


@router.get("/{persona_id}/memories")
async def persona_memories(persona_id: int) -> APIResponse[list[dict]]:
    memories = await persona_memory_repository.list_memories(persona_id)
    return APIResponse(data=memories)


class RecommendRequest(BaseModel):
    scenario: str


@router.post("/recommend-combination")
async def recommend_combination(request: RecommendRequest) -> APIResponse[dict]:
    result = await persona_service.recommend_combination(1, request.scenario)
    return APIResponse(data=result)
