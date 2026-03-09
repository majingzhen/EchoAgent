from datetime import datetime
from pydantic import BaseModel, Field


class KnowledgeProject(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class KnowledgeProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None


class KnowledgeDoc(BaseModel):
    id: int
    project_id: int
    filename: str
    file_type: str
    char_count: int
    chunk_count: int
    status: str
    created_at: datetime
    updated_at: datetime


class KnowledgeChunk(BaseModel):
    id: int
    doc_id: int
    project_id: int
    chunk_index: int
    content: str
    embedding: list[float] | None = None
    created_at: datetime


class KnowledgeSearchResult(BaseModel):
    chunk_id: int
    doc_id: int
    filename: str
    content: str
    score: float
