from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import text

from app.db.sqlite import SQLiteDatabase
from app.models.workflow import WorkflowSession, WorkflowStepRecord


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


def _row_to_session(row: dict) -> WorkflowSession:
    steps_raw = _from_json(row.get("steps") or "[]") or []
    steps = [WorkflowStepRecord(**s) if isinstance(s, dict) else s for s in steps_raw]
    return WorkflowSession(
        id=int(row["id"]),
        tenant_id=int(row["tenant_id"]),
        workflow_type=row["workflow_type"],
        status=row["status"],
        config=_from_json(row.get("config") or "{}") or {},
        steps=steps,
        current_step=row.get("current_step"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class WorkflowRepository:
    def __init__(self, db: SQLiteDatabase) -> None:
        self.db = db

    async def create(
        self,
        tenant_id: int,
        workflow_type: str,
        config: dict[str, Any],
        steps: list[dict[str, Any]],
    ) -> WorkflowSession:
        now = datetime.utcnow()
        sql = text(
            """
            INSERT INTO workflow_session(tenant_id, workflow_type, status, config, steps, current_step, created_at, updated_at)
            VALUES (:tenant_id, :workflow_type, 'pending', :config, :steps, NULL, :created_at, :updated_at)
            """
        )
        async with self.db.session() as session:
            result = await session.execute(sql, {
                "tenant_id": tenant_id,
                "workflow_type": workflow_type,
                "config": _to_json(config),
                "steps": _to_json(steps),
                "created_at": now,
                "updated_at": now,
            })
            session_id = int(result.lastrowid)
        return WorkflowSession(
            id=session_id,
            tenant_id=tenant_id,
            workflow_type=workflow_type,
            status="pending",
            config=config,
            steps=[WorkflowStepRecord(**s) for s in steps],
            current_step=None,
            created_at=now,
            updated_at=now,
        )

    async def get(self, session_id: int) -> WorkflowSession | None:
        sql = text(
            "SELECT id, tenant_id, workflow_type, status, config, steps, current_step, created_at, updated_at "
            "FROM workflow_session WHERE id = :session_id"
        )
        async with self.db.session() as session:
            result = await session.execute(sql, {"session_id": session_id})
            row = result.mappings().first()
        if not row:
            return None
        return _row_to_session(dict(row))

    async def list(self, tenant_id: int) -> list[WorkflowSession]:
        sql = text(
            "SELECT id, tenant_id, workflow_type, status, config, steps, current_step, created_at, updated_at "
            "FROM workflow_session WHERE tenant_id = :tenant_id ORDER BY id DESC"
        )
        async with self.db.session() as session:
            result = await session.execute(sql, {"tenant_id": tenant_id})
            rows = result.mappings().all()
        return [_row_to_session(dict(r)) for r in rows]

    async def update_status(self, session_id: int, status: str) -> None:
        sql = text(
            "UPDATE workflow_session SET status = :status, updated_at = :updated_at WHERE id = :session_id"
        )
        async with self.db.session() as session:
            await session.execute(sql, {
                "session_id": session_id,
                "status": status,
                "updated_at": datetime.utcnow(),
            })

    async def update_current_step(self, session_id: int, step_name: str | None) -> None:
        sql = text(
            "UPDATE workflow_session SET current_step = :step, updated_at = :updated_at WHERE id = :session_id"
        )
        async with self.db.session() as session:
            await session.execute(sql, {
                "session_id": session_id,
                "step": step_name,
                "updated_at": datetime.utcnow(),
            })

    async def save_step(
        self,
        session_id: int,
        step_name: str,
        status: str,
        result: dict[str, Any],
        sub_session_id: int | None = None,
        error: str | None = None,
    ) -> None:
        ws = await self.get(session_id)
        if not ws:
            return
        steps = ws.steps
        for step in steps:
            if step.name == step_name:
                step.status = status
                step.result = result
                step.session_id = sub_session_id
                step.error = error
                break
        sql = text(
            "UPDATE workflow_session SET steps = :steps, updated_at = :updated_at WHERE id = :session_id"
        )
        async with self.db.session() as session:
            await session.execute(sql, {
                "session_id": session_id,
                "steps": _to_json([s.model_dump() for s in steps]),
                "updated_at": datetime.utcnow(),
            })
