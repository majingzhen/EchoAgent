from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import text

from app.db.sqlite import SQLiteDatabase
from app.models.strategy_advisor import StrategyAdvisorSession


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


class StrategyAdvisorRepository:
    def __init__(self, db: SQLiteDatabase) -> None:
        self.db = db

    async def create_session(self, tenant_id: int, question: str, context_info: str) -> StrategyAdvisorSession:
        now = datetime.utcnow()
        sql = text(
            """
            INSERT INTO strategy_advisor_session(tenant_id, question, context_info, status, payload, created_at, updated_at)
            VALUES (:tenant_id, :question, :context_info, 'pending', NULL, :created_at, :updated_at)
            """
        )
        async with self.db.session() as session:
            result = await session.execute(
                sql,
                {
                    "tenant_id": tenant_id,
                    "question": question,
                    "context_info": context_info,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            session_id = int(result.lastrowid)
        return StrategyAdvisorSession(
            id=session_id,
            tenant_id=tenant_id,
            question=question,
            context_info=context_info,
            status="pending",
            created_at=now,
            updated_at=now,
        )

    async def update_session(self, session_id: int, status: str, payload: dict[str, Any]) -> None:
        sql = text(
            """
            UPDATE strategy_advisor_session
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

    async def get_session(self, session_id: int) -> StrategyAdvisorSession | None:
        sql = text(
            "SELECT id, tenant_id, question, context_info, status, payload, created_at, updated_at "
            "FROM strategy_advisor_session WHERE id = :session_id"
        )
        async with self.db.session() as session:
            result = await session.execute(sql, {"session_id": session_id})
            row = result.mappings().first()
        if not row:
            return None
        payload = dict(row)
        payload["payload"] = _from_json(payload.get("payload"))
        return StrategyAdvisorSession(**payload)

    async def list_sessions(self, tenant_id: int) -> list[StrategyAdvisorSession]:
        sql = text(
            "SELECT id, tenant_id, question, context_info, status, payload, created_at, updated_at "
            "FROM strategy_advisor_session WHERE tenant_id = :tenant_id ORDER BY id DESC"
        )
        async with self.db.session() as session:
            result = await session.execute(sql, {"tenant_id": tenant_id})
            rows = result.mappings().all()
        sessions = []
        for row in rows:
            p = dict(row)
            p["payload"] = _from_json(p.get("payload"))
            sessions.append(StrategyAdvisorSession(**p))
        return sessions
