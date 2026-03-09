from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.deps import knowledge_service
from app.models.common import APIResponse
from app.models.knowledge import KnowledgeDoc, KnowledgeProject, KnowledgeSearchResult

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


# ── projects ──────────────────────────────────────────────────────────────────

@router.get("/projects")
async def list_projects() -> APIResponse[list[KnowledgeProject]]:
    projects = await knowledge_service.list_projects()
    return APIResponse(data=projects)


@router.post("/projects")
async def create_project(body: ProjectCreate) -> APIResponse[KnowledgeProject]:
    project = await knowledge_service.create_project(body.name, body.description)
    return APIResponse(data=project)


@router.get("/projects/{project_id}")
async def get_project(project_id: int) -> APIResponse[KnowledgeProject]:
    project = await knowledge_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="project not found")
    return APIResponse(data=project)


@router.delete("/projects/{project_id}")
async def delete_project(project_id: int) -> APIResponse[None]:
    project = await knowledge_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="project not found")
    await knowledge_service.delete_project(project_id)
    return APIResponse(data=None)


# ── docs ──────────────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/docs")
async def list_docs(project_id: int) -> APIResponse[list[KnowledgeDoc]]:
    docs = await knowledge_service.list_docs(project_id)
    return APIResponse(data=docs)


@router.post("/projects/{project_id}/docs")
async def upload_doc(
    project_id: int,
    file: UploadFile = File(...),
) -> APIResponse[KnowledgeDoc]:
    project = await knowledge_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="project not found")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="文件内容为空")

    filename = file.filename or "upload"
    doc = await knowledge_service.ingest_file(project_id, filename, raw)
    return APIResponse(data=doc)


@router.delete("/projects/{project_id}/docs/{doc_id}")
async def delete_doc(project_id: int, doc_id: int) -> APIResponse[None]:
    await knowledge_service.delete_doc(doc_id)
    return APIResponse(data=None)


# ── search ────────────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/search")
async def search(project_id: int, q: str, top_k: int = 4) -> APIResponse[list[KnowledgeSearchResult]]:
    results = await knowledge_service.search(project_id, q, top_k)
    return APIResponse(data=results)
