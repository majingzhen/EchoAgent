from __future__ import annotations

import asyncio
import json
import logging
import math
from typing import Any

from app.llm.client import LLMClient
from app.models.knowledge import KnowledgeChunk, KnowledgeDoc, KnowledgeProject, KnowledgeSearchResult
from app.repositories.knowledge_repository import KnowledgeRepository
from app.utils.file_utils import extract_text

logger = logging.getLogger(__name__)

# 每个 chunk 约 500 字，chunk 间 50 字重叠
_CHUNK_SIZE = 500
_CHUNK_OVERLAP = 50
# 单次 embedding 批量上限（避免超 token）
_EMBED_BATCH = 20
# RAG 检索返回 top-K
_TOP_K = 4


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _keyword_score(query: str, content: str) -> float:
    """关键词匹配回退评分，无向量时使用。"""
    words = set(query.lower().split())
    content_lower = content.lower()
    hits = sum(1 for w in words if w in content_lower)
    return hits / max(len(words), 1)


def _split_chunks(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + _CHUNK_SIZE
        chunks.append(text[start:end])
        start += _CHUNK_SIZE - _CHUNK_OVERLAP
    return chunks


class KnowledgeService:
    def __init__(self, repository: KnowledgeRepository, llm_client: LLMClient) -> None:
        self._repo = repository
        self._llm = llm_client

    # ── projects ──────────────────────────────────────────────────────────────

    async def create_project(self, name: str, description: str | None) -> KnowledgeProject:
        return await self._repo.create_project(name, description)

    async def list_projects(self) -> list[KnowledgeProject]:
        return await self._repo.list_projects()

    async def get_project(self, project_id: int) -> KnowledgeProject | None:
        return await self._repo.get_project(project_id)

    async def delete_project(self, project_id: int) -> None:
        await self._repo.delete_project(project_id)

    # ── docs / ingest ─────────────────────────────────────────────────────────

    async def ingest_file(
        self, project_id: int, filename: str, raw: bytes
    ) -> KnowledgeDoc:
        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else "txt"
        doc = await self._repo.create_doc(project_id, filename, ext)
        # 异步在后台处理，让 API 快速返回
        asyncio.create_task(self._process_doc(doc, raw))
        return doc

    async def _process_doc(self, doc: KnowledgeDoc, raw: bytes) -> None:
        try:
            text = extract_text(raw, doc.filename)
            chunks_text = _split_chunks(text)

            embeddings: list[list[float] | None] = []
            try:
                for i in range(0, len(chunks_text), _EMBED_BATCH):
                    batch = chunks_text[i : i + _EMBED_BATCH]
                    vecs = await self._llm.embed(batch)
                    embeddings.extend(vecs)
            except Exception as e:
                logger.warning("知识库 embedding 失败，将使用关键词检索回退: %s", e)
                embeddings = [None] * len(chunks_text)

            chunks = [
                {"chunk_index": i, "content": c, "embedding": embeddings[i]}
                for i, c in enumerate(chunks_text)
            ]
            await self._repo.save_chunks(doc.id, doc.project_id, chunks)
            await self._repo.update_doc_status(
                doc.id, "ready", char_count=len(text), chunk_count=len(chunks)
            )
        except Exception as e:
            logger.error("知识库文档处理失败 doc_id=%d: %s", doc.id, e)
            await self._repo.update_doc_status(doc.id, "error")

    async def list_docs(self, project_id: int) -> list[KnowledgeDoc]:
        return await self._repo.list_docs(project_id)

    async def delete_doc(self, doc_id: int) -> None:
        await self._repo.delete_doc(doc_id)

    # ── search / RAG ──────────────────────────────────────────────────────────

    async def search(self, project_id: int, query: str, top_k: int = _TOP_K) -> list[KnowledgeSearchResult]:
        chunks = await self._repo.list_chunks(project_id)
        if not chunks:
            return []

        query_embedding: list[float] | None = None
        try:
            vecs = await self._llm.embed([query])
            query_embedding = vecs[0]
        except Exception as e:
            logger.warning("查询 embedding 失败，使用关键词检索: %s", e)

        scored: list[tuple[float, KnowledgeChunk]] = []
        for chunk in chunks:
            if query_embedding and chunk.embedding:
                score = _cosine(query_embedding, chunk.embedding)
            else:
                score = _keyword_score(query, chunk.content)
            scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:top_k]

        # 批量查 doc 名（避免 N+1）
        doc_names = await self._get_doc_names(project_id)

        return [
            KnowledgeSearchResult(
                chunk_id=c.id,
                doc_id=c.doc_id,
                filename=doc_names.get(c.doc_id, ""),
                content=c.content,
                score=round(score, 4),
            )
            for score, c in top
            if score > 0
        ]

    async def _get_doc_names(self, project_id: int) -> dict[int, str]:
        docs = await self._repo.list_docs(project_id)
        return {d.id: d.filename for d in docs}

    async def build_rag_context(self, project_id: int, query: str) -> str:
        """返回可直接注入 Prompt 的知识库上下文段落，无内容时返回空字符串。"""
        results = await self.search(project_id, query)
        if not results:
            return ""
        lines = ["以下是来自企业知识库的相关参考资料：", ""]
        for i, r in enumerate(results, 1):
            lines.append(f"[参考{i}] 来源：{r.filename}")
            lines.append(r.content.strip())
            lines.append("")
        return "\n".join(lines)
