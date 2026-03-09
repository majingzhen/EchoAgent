from __future__ import annotations

from pydantic import BaseModel


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str


class SearchEnhanceRequest(BaseModel):
    query: str
    module: str = "general"  # general / workshop / market / persona
    max_results: int = 5


class SearchEnhanceResponse(BaseModel):
    query: str
    module: str
    results: list[SearchResult]
    summary: str
    insights: list[str]
    suggested_use: str
