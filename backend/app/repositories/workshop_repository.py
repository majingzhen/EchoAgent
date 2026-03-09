from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import text

from app.db.sqlite import SQLiteDatabase
from app.models.workshop import WorkshopSession


def _to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _from_json(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return default


class WorkshopRepository:
    def __init__(self, db: SQLiteDatabase) -> None:
        self.db = db

    async def create_session(
        self,
        tenant_id: int,
        persona_group_id: int,
        platform: str,
        brand_tone: str,
        brief: dict[str, Any],
    ) -> WorkshopSession:
        now = datetime.utcnow()
        sql = text(
            """
            INSERT INTO workshop_session(
                tenant_id, persona_group_id, platform, brand_tone, brief,
                status, payload, insights, created_at, updated_at
            ) VALUES (
                :tenant_id, :persona_group_id, :platform, :brand_tone, :brief,
                'planning', :payload, :insights, :created_at, :updated_at
            )
            """
        )
        async with self.db.session() as session:
            result = await session.execute(
                sql,
                {
                    "tenant_id": tenant_id,
                    "persona_group_id": persona_group_id,
                    "platform": platform,
                    "brand_tone": brand_tone,
                    "brief": _to_json(brief),
                    "payload": _to_json({}),
                    "insights": _to_json([]),
                    "created_at": now,
                    "updated_at": now,
                },
            )
            session_id = int(result.lastrowid)
        return WorkshopSession(
            id=session_id,
            tenant_id=tenant_id,
            persona_group_id=persona_group_id,
            platform=platform,
            brand_tone=brand_tone,
            brief=brief,
            status="planning",
            payload={},
            insights=[],
            ab_test_id=None,
            created_at=now,
            updated_at=now,
        )

    async def get_session(self, session_id: int) -> WorkshopSession | None:
        sql = text(
            """
            SELECT id, tenant_id, persona_group_id, platform, brand_tone, brief, status,
                   payload, insights, ab_test_id, created_at, updated_at
            FROM workshop_session
            WHERE id = :session_id
            """
        )
        async with self.db.session() as session:
            result = await session.execute(sql, {"session_id": session_id})
            row = result.mappings().first()
        if not row:
            return None
        payload = dict(row)
        payload["brief"] = _from_json(payload.get("brief"), {})
        payload["payload"] = _from_json(payload.get("payload"), {})
        payload["insights"] = _from_json(payload.get("insights"), [])
        if payload.get("ab_test_id") is not None:
            payload["ab_test_id"] = int(payload["ab_test_id"])
        return WorkshopSession(**payload)

    async def update_runtime(
        self,
        session_id: int,
        *,
        status: str,
        payload: dict[str, Any],
        insights: list[str] | None = None,
    ) -> None:
        sql = text(
            """
            UPDATE workshop_session
            SET status = :status,
                payload = :payload,
                insights = :insights,
                updated_at = :updated_at
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
                    "insights": _to_json(insights or []),
                    "updated_at": datetime.utcnow(),
                },
            )

    async def update_insights(self, session_id: int, insights: list[str]) -> None:
        sql = text(
            """
            UPDATE workshop_session
            SET insights = :insights,
                updated_at = :updated_at
            WHERE id = :session_id
            """
        )
        async with self.db.session() as session:
            await session.execute(
                sql,
                {
                    "session_id": session_id,
                    "insights": _to_json(insights),
                    "updated_at": datetime.utcnow(),
                },
            )

    async def update_ab_test(self, session_id: int, ab_test_id: int) -> None:
        sql = text(
            """
            UPDATE workshop_session
            SET ab_test_id = :ab_test_id,
                updated_at = :updated_at
            WHERE id = :session_id
            """
        )
        async with self.db.session() as session:
            await session.execute(
                sql,
                {
                    "session_id": session_id,
                    "ab_test_id": ab_test_id,
                    "updated_at": datetime.utcnow(),
                },
            )

    async def list_sessions(self, tenant_id: int) -> list[dict[str, Any]]:
        sql = text(
            """
            SELECT id, tenant_id, persona_group_id, platform, brand_tone, status, created_at, updated_at
            FROM workshop_session
            WHERE tenant_id = :tenant_id
            ORDER BY id DESC
            """
        )
        async with self.db.session() as session:
            result = await session.execute(sql, {"tenant_id": tenant_id})
            rows = result.mappings().all()
        return [dict(row) for row in rows]

    async def save_result(
        self,
        workshop_session_id: int,
        variant: str,
        went_live: bool,
        actual_engagement_rate: float | None,
        actual_conversion_rate: float | None,
        notes: str,
    ) -> int:
        sql = text(
            """
            INSERT INTO content_result(workshop_session_id, variant, went_live, actual_engagement_rate, actual_conversion_rate, notes, created_at)
            VALUES (:workshop_session_id, :variant, :went_live, :actual_engagement_rate, :actual_conversion_rate, :notes, :created_at)
            """
        )
        async with self.db.session() as session:
            result = await session.execute(sql, {
                "workshop_session_id": workshop_session_id,
                "variant": variant,
                "went_live": 1 if went_live else 0,
                "actual_engagement_rate": actual_engagement_rate,
                "actual_conversion_rate": actual_conversion_rate,
                "notes": notes,
                "created_at": datetime.utcnow(),
            })
            return int(result.lastrowid)

    async def get_results(self, workshop_session_id: int) -> list[dict[str, Any]]:
        sql = text(
            """
            SELECT id, variant, went_live, actual_engagement_rate, actual_conversion_rate, notes, created_at
            FROM content_result
            WHERE workshop_session_id = :workshop_session_id
            ORDER BY id DESC
            """
        )
        async with self.db.session() as session:
            result = await session.execute(sql, {"workshop_session_id": workshop_session_id})
            rows = result.mappings().all()
        return [dict(row) for row in rows]
