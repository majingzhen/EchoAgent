from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import text

from app.db.sqlite import SQLiteDatabase
from app.models.simulation import SimulationReport, SimulationStatus


def _to_json(value: Any) -> str:
    def _default(obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    return json.dumps(value, ensure_ascii=False, default=_default)


def _from_json(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return default


class SimulationRepository:
    def __init__(self, db: SQLiteDatabase) -> None:
        self.db = db

    async def create_session(
        self,
        tenant_id: int,
        persona_group_id: int,
        platform: str,
        content_text: str,
        config: dict[str, Any],
        total_rounds: int,
    ) -> SimulationStatus:
        now = datetime.utcnow()
        sql = text(
            """
            INSERT INTO simulation_session(
                tenant_id, persona_group_id, platform, content_text, config, status,
                total_rounds, current_round, metrics_timeline, actions, created_at, updated_at
            ) VALUES (
                :tenant_id, :persona_group_id, :platform, :content_text, :config, 'pending',
                :total_rounds, 0, :metrics_timeline, :actions, :created_at, :updated_at
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
                    "content_text": content_text,
                    "config": _to_json(config),
                    "total_rounds": total_rounds,
                    "metrics_timeline": _to_json([]),
                    "actions": _to_json([]),
                    "created_at": now,
                    "updated_at": now,
                },
            )
            session_id = int(result.lastrowid)
        return SimulationStatus(
            id=session_id,
            tenant_id=tenant_id,
            persona_group_id=persona_group_id,
            platform=platform,
            status="pending",
            total_rounds=total_rounds,
            current_round=0,
            metrics_timeline=[],
            created_at=now,
            updated_at=now,
        )

    async def get_session_with_payload(self, session_id: int) -> dict[str, Any] | None:
        sql = text(
            """
            SELECT id, tenant_id, persona_group_id, platform, content_text, config, status,
                   total_rounds, current_round, metrics_timeline, actions, created_at, updated_at
            FROM simulation_session WHERE id = :session_id
            """
        )
        async with self.db.session() as session:
            result = await session.execute(sql, {"session_id": session_id})
            row = result.mappings().first()
        if not row:
            return None
        payload = dict(row)
        payload["config"] = _from_json(payload.get("config"), {})
        payload["metrics_timeline"] = _from_json(payload.get("metrics_timeline"), [])
        payload["actions"] = _from_json(payload.get("actions"), [])
        return payload

    async def update_runtime(
        self,
        session_id: int,
        *,
        status: str,
        current_round: int,
        metrics_timeline: list[dict[str, Any]],
        actions: list[dict[str, Any]],
    ) -> None:
        sql = text(
            """
            UPDATE simulation_session
            SET status = :status,
                current_round = :current_round,
                metrics_timeline = :metrics_timeline,
                actions = :actions,
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
                    "current_round": current_round,
                    "metrics_timeline": _to_json(metrics_timeline),
                    "actions": _to_json(actions),
                    "updated_at": datetime.utcnow(),
                },
            )

    async def get_session(self, session_id: int) -> SimulationStatus | None:
        sql = text(
            """
            SELECT id, tenant_id, persona_group_id, platform, status, total_rounds, current_round, metrics_timeline, created_at, updated_at
            FROM simulation_session
            WHERE id = :session_id
            """
        )
        async with self.db.session() as session:
            result = await session.execute(sql, {"session_id": session_id})
            row = result.mappings().first()
        if not row:
            return None
        payload = dict(row)
        payload["metrics_timeline"] = _from_json(payload.get("metrics_timeline"), [])
        return SimulationStatus(**payload)

    async def save_report(self, session_id: int, report_payload: dict[str, Any]) -> None:
        sql = text(
            """
            INSERT INTO simulation_report(session_id, payload, created_at)
            VALUES (:session_id, :payload, :created_at)
            ON CONFLICT(session_id) DO UPDATE SET payload = :payload, created_at = :created_at
            """
        )
        async with self.db.session() as session:
            await session.execute(
                sql,
                {
                    "session_id": session_id,
                    "payload": _to_json(report_payload),
                    "created_at": datetime.utcnow(),
                },
            )

    async def get_report(self, session_id: int) -> SimulationReport | None:
        sql = text("SELECT payload FROM simulation_report WHERE session_id = :session_id")
        async with self.db.session() as session:
            result = await session.execute(sql, {"session_id": session_id})
            row = result.mappings().first()
        if not row:
            return None
        payload = _from_json(row["payload"], {})
        return SimulationReport(**payload)

    async def create_ab_test(
        self,
        tenant_id: int,
        name: str,
        persona_group_id: int,
        platform: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        now = datetime.utcnow()
        sql = text(
            """
            INSERT INTO ab_test(tenant_id, name, persona_group_id, platform, payload, created_at, updated_at)
            VALUES (:tenant_id, :name, :persona_group_id, :platform, :payload, :created_at, :updated_at)
            """
        )
        async with self.db.session() as session:
            result = await session.execute(
                sql,
                {
                    "tenant_id": tenant_id,
                    "name": name,
                    "persona_group_id": persona_group_id,
                    "platform": platform,
                    "payload": _to_json(payload),
                    "created_at": now,
                    "updated_at": now,
                },
            )
            test_id = int(result.lastrowid)
        return {"id": test_id, **payload}

    async def get_ab_test(self, test_id: int) -> dict[str, Any] | None:
        sql = text("SELECT id, payload FROM ab_test WHERE id = :test_id")
        async with self.db.session() as session:
            result = await session.execute(sql, {"test_id": test_id})
            row = result.mappings().first()
        if not row:
            return None
        payload = _from_json(row["payload"], {})
        payload["id"] = int(row["id"])
        return payload

    async def list_sessions(self, tenant_id: int) -> list[dict[str, Any]]:
        sql = text(
            """
            SELECT id, tenant_id, persona_group_id, platform, status, total_rounds, current_round, created_at, updated_at
            FROM simulation_session
            WHERE tenant_id = :tenant_id
            ORDER BY id DESC
            """
        )
        async with self.db.session() as session:
            result = await session.execute(sql, {"tenant_id": tenant_id})
            rows = result.mappings().all()
        return [dict(row) for row in rows]
