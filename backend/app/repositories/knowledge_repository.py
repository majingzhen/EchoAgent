from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import text

from app.db.sqlite import SQLiteDatabase
from app.models.knowledge import KnowledgeChunk, KnowledgeDoc, KnowledgeProject


class KnowledgeRepository:
    def __init__(self, db: SQLiteDatabase) -> None:
        self._db = db

    # ── projects ──────────────────────────────────────────────────────────────

    async def create_project(self, name: str, description: str | None) -> KnowledgeProject:
        now = datetime.utcnow()
        async with self._db.session() as s:
            result = await s.execute(
                text("INSERT INTO knowledge_project(name, description, created_at, updated_at) VALUES (:name,:desc,:now,:now)"),
                {"name": name, "desc": description, "now": now},
            )
            row_id = result.lastrowid
            row = await s.execute(text("SELECT * FROM knowledge_project WHERE id=:id"), {"id": row_id})
            data = dict(row.mappings().first())
        return KnowledgeProject(**data)

    async def list_projects(self) -> list[KnowledgeProject]:
        async with self._db.session() as s:
            result = await s.execute(text("SELECT * FROM knowledge_project ORDER BY created_at DESC"))
            rows = result.mappings().all()
        return [KnowledgeProject(**dict(r)) for r in rows]

    async def get_project(self, project_id: int) -> KnowledgeProject | None:
        async with self._db.session() as s:
            result = await s.execute(
                text("SELECT * FROM knowledge_project WHERE id=:id"), {"id": project_id}
            )
            row = result.mappings().first()
        return KnowledgeProject(**dict(row)) if row else None

    async def delete_project(self, project_id: int) -> None:
        async with self._db.session() as s:
            await s.execute(text("DELETE FROM knowledge_chunk WHERE project_id=:pid"), {"pid": project_id})
            await s.execute(text("DELETE FROM knowledge_doc WHERE project_id=:pid"), {"pid": project_id})
            await s.execute(text("DELETE FROM knowledge_project WHERE id=:pid"), {"pid": project_id})

    # ── docs ─────────────────────────────────────────────────────────────────

    async def create_doc(self, project_id: int, filename: str, file_type: str) -> KnowledgeDoc:
        now = datetime.utcnow()
        async with self._db.session() as s:
            result = await s.execute(
                text(
                    "INSERT INTO knowledge_doc(project_id, filename, file_type, created_at, updated_at) "
                    "VALUES (:pid,:fn,:ft,:now,:now)"
                ),
                {"pid": project_id, "fn": filename, "ft": file_type, "now": now},
            )
            row_id = result.lastrowid
            row = await s.execute(text("SELECT * FROM knowledge_doc WHERE id=:id"), {"id": row_id})
            data = dict(row.mappings().first())
        return KnowledgeDoc(**data)

    async def update_doc_status(
        self, doc_id: int, status: str, char_count: int = 0, chunk_count: int = 0
    ) -> None:
        async with self._db.session() as s:
            await s.execute(
                text(
                    "UPDATE knowledge_doc SET status=:status, char_count=:cc, chunk_count=:nc, updated_at=:now "
                    "WHERE id=:id"
                ),
                {"status": status, "cc": char_count, "nc": chunk_count, "now": datetime.utcnow(), "id": doc_id},
            )

    async def list_docs(self, project_id: int) -> list[KnowledgeDoc]:
        async with self._db.session() as s:
            result = await s.execute(
                text("SELECT * FROM knowledge_doc WHERE project_id=:pid ORDER BY created_at DESC"),
                {"pid": project_id},
            )
            rows = result.mappings().all()
        return [KnowledgeDoc(**dict(r)) for r in rows]

    async def delete_doc(self, doc_id: int) -> None:
        async with self._db.session() as s:
            await s.execute(text("DELETE FROM knowledge_chunk WHERE doc_id=:did"), {"did": doc_id})
            await s.execute(text("DELETE FROM knowledge_doc WHERE id=:did"), {"did": doc_id})

    # ── chunks ────────────────────────────────────────────────────────────────

    async def save_chunks(self, doc_id: int, project_id: int, chunks: list[dict[str, Any]]) -> None:
        """chunks: list of {"chunk_index": int, "content": str, "embedding": list[float]|None}"""
        now = datetime.utcnow()
        async with self._db.session() as s:
            for c in chunks:
                emb = json.dumps(c["embedding"]) if c.get("embedding") else None
                await s.execute(
                    text(
                        "INSERT INTO knowledge_chunk(doc_id, project_id, chunk_index, content, embedding, created_at) "
                        "VALUES (:did,:pid,:ci,:content,:emb,:now)"
                    ),
                    {
                        "did": doc_id,
                        "pid": project_id,
                        "ci": c["chunk_index"],
                        "content": c["content"],
                        "emb": emb,
                        "now": now,
                    },
                )

    async def list_chunks(self, project_id: int) -> list[KnowledgeChunk]:
        async with self._db.session() as s:
            result = await s.execute(
                text("SELECT * FROM knowledge_chunk WHERE project_id=:pid ORDER BY doc_id, chunk_index"),
                {"pid": project_id},
            )
            rows = result.mappings().all()
        chunks = []
        for r in rows:
            data = dict(r)
            if data.get("embedding"):
                data["embedding"] = json.loads(data["embedding"])
            chunks.append(KnowledgeChunk(**data))
        return chunks
