from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import text

from app.db.sqlite import SQLiteDatabase
from app.models.persona import FocusGroupMessage, FocusGroupSession


def _to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _from_json(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return dict(value)


class FocusGroupRepository:
    def __init__(self, db: SQLiteDatabase) -> None:
        self.db = db

    async def create_session(
        self,
        tenant_id: int,
        persona_group_id: int,
        topic: str,
        product_context: dict | None = None,
    ) -> FocusGroupSession:
        now = datetime.utcnow()
        pc = product_context or {}
        sql = text(
            """
            INSERT INTO focus_group_session(tenant_id, persona_group_id, topic, product_context, status, summary, created_at, updated_at)
            VALUES (:tenant_id, :persona_group_id, :topic, :product_context, 'active', NULL, :created_at, :updated_at)
            """
        )
        async with self.db.session() as session:
            result = await session.execute(
                sql,
                {
                    "tenant_id": tenant_id,
                    "persona_group_id": persona_group_id,
                    "topic": topic,
                    "product_context": _to_json(pc),
                    "created_at": now,
                    "updated_at": now,
                },
            )
            session_id = int(result.lastrowid)
        return FocusGroupSession(
            id=session_id,
            tenant_id=tenant_id,
            persona_group_id=persona_group_id,
            topic=topic,
            product_context=pc,
            status="active",
            summary=None,
            messages=[],
            created_at=now,
            updated_at=now,
        )

    async def get_session(self, session_id: int) -> FocusGroupSession | None:
        sql = text(
            """
            SELECT id, tenant_id, persona_group_id, topic, product_context, status, summary, created_at, updated_at
            FROM focus_group_session
            WHERE id = :session_id
            """
        )
        async with self.db.session() as session:
            result = await session.execute(sql, {"session_id": session_id})
            row = result.mappings().first()
        if not row:
            return None
        messages = await self.list_messages(session_id)
        payload = dict(row)
        payload["summary"] = _from_json(payload.get("summary"))
        payload["product_context"] = _from_json(payload.get("product_context")) or {}
        payload["messages"] = messages
        return FocusGroupSession(**payload)

    async def append_messages(self, session_id: int, messages: list[FocusGroupMessage]) -> None:
        sql = text(
            """
            INSERT INTO focus_group_message(session_id, sender_type, persona_id, persona_name, content, created_at)
            VALUES (:session_id, :sender_type, :persona_id, :persona_name, :content, :created_at)
            """
        )
        async with self.db.session() as session:
            for item in messages:
                await session.execute(
                    sql,
                    {
                        "session_id": session_id,
                        "sender_type": item.sender_type,
                        "persona_id": item.persona_id,
                        "persona_name": item.persona_name,
                        "content": item.content,
                        "created_at": item.created_at,
                    },
                )
            await session.execute(
                text("UPDATE focus_group_session SET updated_at = :updated_at WHERE id = :session_id"),
                {"updated_at": datetime.utcnow(), "session_id": session_id},
            )

    async def list_messages(self, session_id: int) -> list[FocusGroupMessage]:
        sql = text(
            """
            SELECT sender_type, persona_id, persona_name, content, created_at
            FROM focus_group_message
            WHERE session_id = :session_id
            ORDER BY id ASC
            """
        )
        async with self.db.session() as session:
            result = await session.execute(sql, {"session_id": session_id})
            rows = result.mappings().all()
        return [FocusGroupMessage(**dict(row)) for row in rows]

    async def update_summary(self, session_id: int, summary: dict[str, Any]) -> None:
        sql = text(
            """
            UPDATE focus_group_session
            SET summary = :summary, updated_at = :updated_at
            WHERE id = :session_id
            """
        )
        async with self.db.session() as session:
            await session.execute(
                sql,
                {
                    "session_id": session_id,
                    "summary": _to_json(summary),
                    "updated_at": datetime.utcnow(),
                },
            )

    async def list_sessions(self, tenant_id: int) -> list[dict[str, Any]]:
        sql = text(
            """
            SELECT id, tenant_id, persona_group_id, topic, status, created_at, updated_at
            FROM focus_group_session
            WHERE tenant_id = :tenant_id
            ORDER BY id DESC
            """
        )
        async with self.db.session() as session:
            result = await session.execute(sql, {"tenant_id": tenant_id})
            rows = result.mappings().all()
        return [dict(row) for row in rows]
