from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.deps import (
    focus_group_service,
    sentiment_guard_service,
    simulation_engine,
    strategy_advisor_service,
    workshop_service,
)
from app.services.export_service import ExportService

router = APIRouter(prefix="/export", tags=["export"])

_export_service = ExportService()

_MODULE_LABELS = {
    "simulation": "沙盘推演报告",
    "workshop": "内容工坊报告",
    "sentiment-guard": "舆情哨兵报告",
    "strategy-advisor": "策略参谋报告",
    "focus-group": "焦点小组报告",
}


async def _fetch_data(module: str, session_id: int) -> dict:
    """Fetch session data from the appropriate service."""
    if module == "simulation":
        report = await simulation_engine.get_report(session_id)
        if report:
            return report.model_dump(mode="json")
        session = await simulation_engine.get_session(session_id)
        if session:
            return session.model_dump(mode="json")
    elif module == "workshop":
        session = await workshop_service.get_session(session_id)
        if session:
            return session.model_dump(mode="json")
    elif module == "sentiment-guard":
        session = await sentiment_guard_service.get_session(session_id)
        if session:
            return session.model_dump(mode="json")
    elif module == "strategy-advisor":
        session = await strategy_advisor_service.get_session(session_id)
        if session:
            return session.model_dump(mode="json")
    elif module == "focus-group":
        session = await focus_group_service.get_session(session_id)
        if session:
            return session.model_dump(mode="json")
    return {}


@router.get("/{module}/{session_id}/pdf")
async def download_pdf(module: str, session_id: int):
    if module not in _MODULE_LABELS:
        raise HTTPException(status_code=400, detail=f"未知模块: {module}")
    data = await _fetch_data(module, session_id)
    if not data:
        raise HTTPException(status_code=404, detail="会话不存在")

    title = f"{_MODULE_LABELS[module]} #{session_id}"
    try:
        pdf_bytes = _export_service.export_pdf(module, title, data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 生成失败: {e}")

    filename = f"report_{module}_{session_id}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{module}/{session_id}/pptx")
async def download_pptx(module: str, session_id: int):
    if module not in _MODULE_LABELS:
        raise HTTPException(status_code=400, detail=f"未知模块: {module}")
    data = await _fetch_data(module, session_id)
    if not data:
        raise HTTPException(status_code=404, detail="会话不存在")

    title = f"{_MODULE_LABELS[module]} #{session_id}"
    try:
        pptx_bytes = _export_service.export_pptx(module, title, data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PPTX 生成失败: {e}")

    filename = f"report_{module}_{session_id}.pptx"
    return StreamingResponse(
        iter([pptx_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
