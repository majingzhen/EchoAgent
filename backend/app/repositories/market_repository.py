from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import text

from app.db.sqlite import SQLiteDatabase
from app.models.market import MarketGraph, MarketReport


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


class MarketRepository:
    def __init__(self, db: SQLiteDatabase) -> None:
        self.db = db

    async def create_graph(
        self,
        tenant_id: int,
        name: str,
        source_text: str,
        entities: list[dict[str, Any]],
        relations: list[dict[str, Any]],
    ) -> MarketGraph:
        now = datetime.utcnow()
        sql = text(
            """
            INSERT INTO market_graph(
                tenant_id, name, source_text, entities, relations, created_at, updated_at
            ) VALUES (
                :tenant_id, :name, :source_text, :entities, :relations, :created_at, :updated_at
            )
            """
        )
        async with self.db.session() as session:
            result = await session.execute(
                sql,
                {
                    "tenant_id": tenant_id,
                    "name": name,
                    "source_text": source_text,
                    "entities": _to_json(entities),
                    "relations": _to_json(relations),
                    "created_at": now,
                    "updated_at": now,
                },
            )
            graph_id = int(result.lastrowid)
        return MarketGraph(
            id=graph_id,
            tenant_id=tenant_id,
            name=name,
            source_text=source_text,
            entities=entities,
            relations=relations,
            created_at=now,
            updated_at=now,
        )

    async def get_graph(self, graph_id: int) -> MarketGraph | None:
        sql = text(
            """
            SELECT id, tenant_id, name, source_text, entities, relations, created_at, updated_at
            FROM market_graph
            WHERE id = :graph_id
            """
        )
        async with self.db.session() as session:
            result = await session.execute(sql, {"graph_id": graph_id})
            row = result.mappings().first()
        if not row:
            return None
        payload = dict(row)
        payload["entities"] = _from_json(payload.get("entities"), [])
        payload["relations"] = _from_json(payload.get("relations"), [])
        return MarketGraph(**payload)

    async def save_report(self, graph_id: int, payload: dict[str, Any]) -> None:
        sql = text(
            """
            INSERT INTO market_report(graph_id, payload, created_at)
            VALUES (:graph_id, :payload, :created_at)
            ON CONFLICT(graph_id) DO UPDATE SET payload = :payload, created_at = :created_at
            """
        )
        async with self.db.session() as session:
            await session.execute(
                sql,
                {
                    "graph_id": graph_id,
                    "payload": _to_json(payload),
                    "created_at": datetime.utcnow(),
                },
            )

    async def get_report(self, graph_id: int) -> MarketReport | None:
        sql = text("SELECT payload FROM market_report WHERE graph_id = :graph_id")
        async with self.db.session() as session:
            result = await session.execute(sql, {"graph_id": graph_id})
            row = result.mappings().first()
        if not row:
            return None
        payload = _from_json(row["payload"], {})
        return MarketReport(**payload)
