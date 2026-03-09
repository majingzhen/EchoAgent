from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import text

from app.db.sqlite import SQLiteDatabase


class PersonaMemoryRepository:
    def __init__(self, db: SQLiteDatabase) -> None:
        self.db = db

    async def save_memory(
        self,
        persona_id: int,
        session_type: str,
        session_id: int,
        memory_summary: str,
    ) -> int:
        sql = text(
            """
            INSERT INTO persona_memory(persona_id, session_type, session_id, memory_summary, created_at)
            VALUES (:persona_id, :session_type, :session_id, :memory_summary, :created_at)
            """
        )
        async with self.db.session() as session:
            result = await session.execute(
                sql,
                {
                    "persona_id": persona_id,
                    "session_type": session_type,
                    "session_id": session_id,
                    "memory_summary": memory_summary,
                    "created_at": datetime.utcnow(),
                },
            )
            return int(result.lastrowid)

    async def list_memories(self, persona_id: int, limit: int = 5) -> list[dict[str, Any]]:
        sql = text(
            """
            SELECT id, persona_id, session_type, session_id, memory_summary, created_at
            FROM persona_memory
            WHERE persona_id = :persona_id
            ORDER BY id DESC
            LIMIT :limit
            """
        )
        async with self.db.session() as session:
            result = await session.execute(sql, {"persona_id": persona_id, "limit": limit})
            rows = result.mappings().all()
        return [dict(row) for row in rows]

    async def list_memories_batch(self, persona_ids: list[int], limit_per: int = 3) -> dict[int, str]:
        """批量获取多个画像的记忆摘要，返回 {persona_id: "记忆1; 记忆2; ..."}"""
        if not persona_ids:
            return {}
        placeholders = ",".join([str(pid) for pid in persona_ids])
        sql = text(
            f"""
            SELECT persona_id, memory_summary
            FROM persona_memory
            WHERE persona_id IN ({placeholders})
            ORDER BY id DESC
            """
        )
        async with self.db.session() as session:
            result = await session.execute(sql)
            rows = result.mappings().all()

        grouped: dict[int, list[str]] = {}
        for row in rows:
            pid = int(row["persona_id"])
            if pid not in grouped:
                grouped[pid] = []
            if len(grouped[pid]) < limit_per:
                grouped[pid].append(row["memory_summary"])

        return {pid: "; ".join(memories) for pid, memories in grouped.items()}
