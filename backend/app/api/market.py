from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.deps import market_service
from app.models.common import APIResponse
from app.models.market import MarketGraphBuildRequest

router = APIRouter(prefix="/market", tags=["market"])


@router.post("/graphs/build")
async def build_market_graph(request: MarketGraphBuildRequest) -> APIResponse[dict]:
    graph = await market_service.build_graph(request)
    return APIResponse(data=graph.model_dump())


@router.post("/graphs/upload")
async def upload_market_graph(
    file: UploadFile = File(...),
    name: str = Form("上传文档图谱"),
) -> APIResponse[dict]:
    graph = await market_service.build_graph_from_upload(1, name, file)
    return APIResponse(data=graph.model_dump())


@router.get("/graphs/{graph_id}")
async def get_market_graph(graph_id: int) -> APIResponse[dict]:
    graph = await market_service.get_graph(graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="market graph not found")
    return APIResponse(data=graph.model_dump())


@router.get("/graphs/{graph_id}/report")
async def get_market_report(graph_id: int) -> APIResponse[dict]:
    report = await market_service.get_report(graph_id)
    if not report:
        raise HTTPException(status_code=404, detail="market graph not found")
    return APIResponse(data=report.model_dump())
