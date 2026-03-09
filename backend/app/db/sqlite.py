from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings


class SQLiteDatabase:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._engine: AsyncEngine | None = None
        self._sessionmaker: async_sessionmaker[AsyncSession] | None = None
        self._init_lock = asyncio.Lock()
        self._initialized = False

    async def ensure_ready(self) -> None:
        if self._initialized:
            return
        async with self._init_lock:
            if self._initialized:
                return
            db_path = Path(self.settings.sqlite.path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            dsn = f"sqlite+aiosqlite:///{db_path}"
            self._engine = create_async_engine(
                dsn,
                connect_args={"check_same_thread": False},
            )

            # WAL 模式提升并发读写性能
            @event.listens_for(self._engine.sync_engine, "connect")
            def _set_wal(dbapi_conn, _connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.close()

            self._sessionmaker = async_sessionmaker(self._engine, expire_on_commit=False)
            await self._run_migrations()
            self._initialized = True

    async def _run_migrations(self) -> None:
        if not self._engine:
            return
        migration_file = Path(__file__).resolve().parents[2] / "migrations" / "init.sql"
        sql_text = migration_file.read_text(encoding="utf-8")
        statements = [statement.strip() for statement in sql_text.split(";") if statement.strip()]
        async with self._engine.begin() as conn:
            for statement in statements:
                await conn.execute(text(statement))

    @asynccontextmanager
    async def session(self):
        await self.ensure_ready()
        if not self._sessionmaker:
            raise RuntimeError("sqlite sessionmaker not initialized")
        session = self._sessionmaker()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def close(self) -> None:
        if self._engine:
            await self._engine.dispose()
        self._engine = None
        self._sessionmaker = None
        self._initialized = False
