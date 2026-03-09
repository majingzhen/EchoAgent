from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import text

from app.db.sqlite import SQLiteDatabase
from app.models.persona import PersonaGroupSummary, PersonaProfile


def _to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _from_json(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    if isinstance(value, str):
        return json.loads(value)
    return dict(value)


class PersonaRepository:
    def __init__(self, db: SQLiteDatabase) -> None:
        self.db = db

    async def create_group(
        self,
        tenant_id: int,
        name: str,
        description: str,
        source: str,
        persona_count: int,
    ) -> PersonaGroupSummary:
        now = datetime.utcnow()
        sql = text(
            """
            INSERT INTO persona_group(tenant_id, name, description, source, persona_count, created_at, updated_at)
            VALUES (:tenant_id, :name, :description, :source, :persona_count, :created_at, :updated_at)
            """
        )
        async with self.db.session() as session:
            result = await session.execute(
                sql,
                {
                    "tenant_id": tenant_id,
                    "name": name,
                    "description": description,
                    "source": source,
                    "persona_count": persona_count,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            group_id = int(result.lastrowid)
        return PersonaGroupSummary(
            id=group_id,
            tenant_id=tenant_id,
            name=name,
            description=description,
            source=source,
            persona_count=persona_count,
            created_at=now,
            updated_at=now,
        )

    async def save_single_persona(self, persona: PersonaProfile) -> int:
        sql = text(
            """
            INSERT INTO persona(
                tenant_id, group_id, name, age, gender, city, occupation, monthly_income,
                personality, consumer_profile, media_behavior, social_behavior, agent_config, backstory
            ) VALUES (
                :tenant_id, :group_id, :name, :age, :gender, :city, :occupation, :monthly_income,
                :personality, :consumer_profile, :media_behavior,
                :social_behavior, :agent_config, :backstory
            )
            """
        )
        async with self.db.session() as session:
            result = await session.execute(
                sql,
                {
                    "tenant_id": persona.tenant_id,
                    "group_id": persona.group_id,
                    "name": persona.name,
                    "age": persona.age,
                    "gender": persona.gender,
                    "city": persona.city,
                    "occupation": persona.occupation,
                    "monthly_income": persona.monthly_income,
                    "personality": _to_json(persona.personality.model_dump()),
                    "consumer_profile": _to_json(persona.consumer_profile.model_dump()),
                    "media_behavior": _to_json(persona.media_behavior.model_dump()),
                    "social_behavior": _to_json(persona.social_behavior.model_dump()),
                    "agent_config": _to_json(persona.agent_config.model_dump()),
                    "backstory": persona.backstory,
                },
            )
            return int(result.lastrowid)

    async def create_personas(self, personas: list[PersonaProfile]) -> None:
        sql = text(
            """
            INSERT INTO persona(
                tenant_id, group_id, name, age, gender, city, occupation, monthly_income,
                personality, consumer_profile, media_behavior, social_behavior, agent_config, backstory
            ) VALUES (
                :tenant_id, :group_id, :name, :age, :gender, :city, :occupation, :monthly_income,
                :personality, :consumer_profile, :media_behavior,
                :social_behavior, :agent_config, :backstory
            )
            """
        )
        async with self.db.session() as session:
            for persona in personas:
                await session.execute(
                    sql,
                    {
                        "tenant_id": persona.tenant_id,
                        "group_id": persona.group_id,
                        "name": persona.name,
                        "age": persona.age,
                        "gender": persona.gender,
                        "city": persona.city,
                        "occupation": persona.occupation,
                        "monthly_income": persona.monthly_income,
                        "personality": _to_json(persona.personality.model_dump()),
                        "consumer_profile": _to_json(persona.consumer_profile.model_dump()),
                        "media_behavior": _to_json(persona.media_behavior.model_dump()),
                        "social_behavior": _to_json(persona.social_behavior.model_dump()),
                        "agent_config": _to_json(persona.agent_config.model_dump()),
                        "backstory": persona.backstory,
                    },
                )

    async def list_groups(self, tenant_id: int) -> list[PersonaGroupSummary]:
        sql = text(
            """
            SELECT id, tenant_id, name, description, source, persona_count, created_at, updated_at
            FROM persona_group
            WHERE tenant_id = :tenant_id
            ORDER BY id DESC
            """
        )
        async with self.db.session() as session:
            result = await session.execute(sql, {"tenant_id": tenant_id})
            rows = result.mappings().all()
        return [PersonaGroupSummary(**dict(row)) for row in rows]

    async def get_group(self, group_id: int) -> PersonaGroupSummary | None:
        sql = text(
            """
            SELECT id, tenant_id, name, description, source, persona_count, created_at, updated_at
            FROM persona_group
            WHERE id = :group_id
            """
        )
        async with self.db.session() as session:
            result = await session.execute(sql, {"group_id": group_id})
            row = result.mappings().first()
        if not row:
            return None
        return PersonaGroupSummary(**dict(row))

    async def list_personas_by_group(self, group_id: int) -> list[PersonaProfile]:
        sql = text(
            """
            SELECT id, tenant_id, group_id, name, age, gender, city, occupation, monthly_income,
                   personality, consumer_profile, media_behavior, social_behavior, agent_config, backstory
            FROM persona
            WHERE group_id = :group_id
            ORDER BY id ASC
            """
        )
        async with self.db.session() as session:
            result = await session.execute(sql, {"group_id": group_id})
            rows = result.mappings().all()
        return [self._row_to_persona(dict(row)) for row in rows]

    async def get_persona(self, persona_id: int) -> PersonaProfile | None:
        sql = text(
            """
            SELECT id, tenant_id, group_id, name, age, gender, city, occupation, monthly_income,
                   personality, consumer_profile, media_behavior, social_behavior, agent_config, backstory
            FROM persona
            WHERE id = :persona_id
            """
        )
        async with self.db.session() as session:
            result = await session.execute(sql, {"persona_id": persona_id})
            row = result.mappings().first()
        if not row:
            return None
        return self._row_to_persona(dict(row))

    def _row_to_persona(self, row: dict[str, Any]) -> PersonaProfile:
        return PersonaProfile(
            id=int(row["id"]),
            tenant_id=int(row["tenant_id"]),
            group_id=int(row["group_id"]),
            name=row["name"],
            age=int(row["age"]),
            gender=row["gender"],
            city=row["city"],
            occupation=row["occupation"],
            monthly_income=int(row["monthly_income"]),
            personality=_from_json(row["personality"]),
            consumer_profile=_from_json(row["consumer_profile"]),
            media_behavior=_from_json(row["media_behavior"]),
            social_behavior=_from_json(row["social_behavior"]),
            agent_config=_from_json(row["agent_config"]),
            backstory=row["backstory"],
        )
