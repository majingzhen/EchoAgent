from fastapi import APIRouter

from app.deps import search_service
from app.models.common import APIResponse
from app.models.search import SearchEnhanceRequest, SearchEnhanceResponse

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/enhance")
async def enhance(request: SearchEnhanceRequest) -> APIResponse[SearchEnhanceResponse]:
    result = await search_service.enhance(
        query=request.query,
        module=request.module,
        max_results=request.max_results,
    )
    return APIResponse(data=result)
