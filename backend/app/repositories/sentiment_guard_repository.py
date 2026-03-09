from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import text

from app.db.sqlite import SQLiteDatabase
from app.models.sentiment_guard import SentimentGuardSession


def _to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _from_json(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return value


class SentimentGuardRepository:
    def __init__(self, db: SQLiteDatabase) -> None:
        self.db = db

    async def create_session(
        self,
        tenant_id: int,
        mode: str,
        event_description: str,
    ) -> SentimentGuardSession:
        now = datetime.utcnow()
        sql = text(
            """
            INSERT INTO sentiment_guard_session(tenant_id, mode, event_description, status, payload, created_at, updated_at)
            VALUES (:tenant_id, :mode, :event_description, 'pending', NULL, :created_at, :updated_at)
            """
        )
        async with self.db.session() as session:
            result = await session.execute(
                sql,
                {
                    "tenant_id": tenant_id,
                    "mode": mode,
                    "event_description": event_description,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            session_id = int(result.lastrowid)
        return SentimentGuardSession(
            id=session_id,
            tenant_id=tenant_id,
            mode=mode,
            event_description=event_description,
            status="pending",
            created_at=now,
            updated_at=now,
        )

    async def update_session(self, session_id: int, status: str, payload: dict[str, Any]) -> None:
        sql = text(
            """
            UPDATE sentiment_guard_session
            SET status = :status, payload = :payload, updated_at = :updated_at
            WHERE id = :session_id
            """
        )
        async with self.db.session() as session:
            await session.execute(
                sql,
                {
                    "session_id": session_id,
                    "status": status,
                    "payload": _to_json(payload),
                    "updated_at": datetime.utcnow(),
                },
            )

    async def get_session(self, session_id: int) -> SentimentGuardSession | None:
        sql = text(
            "SELECT id, tenant_id, mode, event_description, status, payload, created_at, updated_at "
            "FROM sentiment_guard_session WHERE id = :session_id"
        )
        async with self.db.session() as session:
            result = await session.execute(sql, {"session_id": session_id})
            row = result.mappings().first()
        if not row:
            return None
        payload = dict(row)
        payload["payload"] = _from_json(payload.get("payload"))
        return SentimentGuardSession(**payload)

    async def list_sessions(self, tenant_id: int) -> list[SentimentGuardSession]:
        sql = text(
            "SELECT id, tenant_id, mode, event_description, status, payload, created_at, updated_at "
            "FROM sentiment_guard_session WHERE tenant_id = :tenant_id ORDER BY id DESC"
        )
        async with self.db.session() as session:
            result = await session.execute(sql, {"tenant_id": tenant_id})
            rows = result.mappings().all()
        sessions = []
        for row in rows:
            payload = dict(row)
            payload["payload"] = _from_json(payload.get("payload"))
            sessions.append(SentimentGuardSession(**payload))
        return sessions
