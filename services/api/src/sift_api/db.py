"""Async SQLAlchemy engine and session helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from sift_api.settings import Settings, get_settings


@dataclass
class _EngineState:
    engine: AsyncEngine | None = None
    session_factory: async_sessionmaker[AsyncSession] | None = None


_STATE = _EngineState()


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    """Return the process-wide async engine (lazy-created)."""
    if _STATE.engine is None:
        cfg = settings or get_settings()
        _STATE.engine = create_async_engine(
            cfg.sift_pg_dsn,
            pool_pre_ping=True,
        )
        _STATE.session_factory = async_sessionmaker(_STATE.engine, expire_on_commit=False)
    return _STATE.engine


async def dispose_engine() -> None:
    """Dispose the engine (app shutdown)."""
    if _STATE.engine is not None:
        await _STATE.engine.dispose()
        _STATE.engine = None
        _STATE.session_factory = None


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: one session per request."""
    get_engine()
    assert _STATE.session_factory is not None
    async with _STATE.session_factory() as session:
        yield session


async def ping_postgres(connection: AsyncConnection | None = None) -> None:
    """Execute ``SELECT 1``; raises on failure."""
    if connection is not None:
        await connection.execute(text("SELECT 1"))
        return
    engine = get_engine()
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
