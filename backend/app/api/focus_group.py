from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.deps import focus_group_service, persona_service
from app.models.common import APIResponse
from app.models.persona import FocusGroupAskRequest, FocusGroupCreateRequest, FocusGroupProductContext

router = APIRouter(prefix="/focus-groups", tags=["focus-group"])


@router.get("")
async def list_sessions() -> APIResponse[list[dict]]:
    sessions = await focus_group_service.list_sessions(1)
    return APIResponse(data=sessions)


@router.post("")
async def create_session(
    persona_group_id: int = Form(...),
    topic: str = Form(...),
    file: UploadFile | None = File(default=None),
) -> APIResponse[dict]:
    group = await persona_service.get_group_detail(persona_group_id)
    if not group:
        raise HTTPException(status_code=404, detail="persona group not found")

    raw_text = ""
    if file and file.filename:
        from app.utils.file_utils import decode_file, extract_pdf_text
        raw = await file.read()
        if not raw:
            raise HTTPException(status_code=400, detail="文件内容为空")
        filename = file.filename.lower()
        if filename.endswith(".pdf") or raw[:4] == b"%PDF":
            raw_text = extract_pdf_text(raw)
        else:
            raw_text = decode_file(raw)

    request = FocusGroupCreateRequest(
        persona_group_id=persona_group_id,
        topic=topic,
        product_context=FocusGroupProductContext(raw_text=raw_text),
    )
    session = await focus_group_service.create_session(request)
    return APIResponse(data=session.model_dump())


@router.get("/{session_id}")
async def get_session(session_id: int) -> APIResponse[dict]:
    session = await focus_group_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    return APIResponse(data=session.model_dump(mode="json"))


@router.post("/{session_id}/ask")
async def ask_question(
    session_id: int,
    question: str = Form(...),
    mode: str = Form(default="independent"),
    image: UploadFile | None = File(default=None),
) -> APIResponse[dict]:
    session = await focus_group_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")

    image_bytes: bytes | None = None
    mime_type = "image/jpeg"
    if image and image.filename:
        image_bytes = await image.read()
        mime_type = image.content_type or "image/jpeg"

    personas = await persona_service.list_group_personas(session.persona_group_id)
    task_id = await focus_group_service.ask_async(
        session_id, session.tenant_id,
        FocusGroupAskRequest(question=question),
        personas,
        product_context=session.product_context,
        mode=mode,
        image_bytes=image_bytes,
        mime_type=mime_type,
    )
    return APIResponse(data={
        "task_id": task_id,
        "session_id": session_id,
        "persona_count": len(personas),
        "mode": mode,
    })


@router.get("/{session_id}/messages")
async def get_messages(session_id: int) -> APIResponse[list[dict]]:
    session = await focus_group_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    return APIResponse(data=[m.model_dump() for m in session.messages])


@router.post("/{session_id}/summarize")
async def summarize(session_id: int) -> APIResponse[dict]:
    session = await focus_group_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    task_id = await focus_group_service.summarize_async(session_id, session.tenant_id)
    return APIResponse(data={"task_id": task_id, "session_id": session_id})
