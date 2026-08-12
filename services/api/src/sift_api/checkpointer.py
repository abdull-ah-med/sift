"""Postgres LangGraph checkpointer factory (Phase 2 §4.3).

Uses ``langgraph-checkpoint-postgres`` so interrupt/resume survives API restart.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from sift_api.settings import Settings, get_settings

_POOL_MIN = 1
_POOL_MAX = 4


@dataclass
class _CheckpointerState:
    pool: AsyncConnectionPool[Any] | None = None
    checkpointer: Any | None = None


_STATE = _CheckpointerState()


def postgres_checkpoint_dsn(settings: Settings | None = None) -> str:
    """Return a psycopg DSN suitable for ``AsyncPostgresSaver``."""
    raw = (settings or get_settings()).sift_pg_dsn
    if raw.startswith("postgresql+asyncpg://"):
        return "postgresql://" + raw.removeprefix("postgresql+asyncpg://")
    if raw.startswith("postgresql+psycopg://"):
        return "postgresql://" + raw.removeprefix("postgresql+psycopg://")
    return raw


def reset_checkpointer_cache() -> None:
    """Drop cached pool/checkpointer (simulates process restart in tests)."""
    _STATE.pool = None
    _STATE.checkpointer = None


async def open_postgres_checkpointer(settings: Settings | None = None) -> Any:
    """Open a pooled ``AsyncPostgresSaver`` and run ``setup()`` once."""
    if _STATE.checkpointer is not None:
        return _STATE.checkpointer

    dsn = postgres_checkpoint_dsn(settings)
    pool: AsyncConnectionPool[Any] = AsyncConnectionPool(
        conninfo=dsn,
        min_size=_POOL_MIN,
        max_size=_POOL_MAX,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        },
        open=False,
    )
    await pool.open()
    checkpointer = AsyncPostgresSaver(conn=pool)
    await checkpointer.setup()
    _STATE.pool = pool
    _STATE.checkpointer = checkpointer
    return checkpointer


async def close_postgres_checkpointer(_checkpointer: Any | None = None) -> None:
    """Close the pooled checkpointer connection."""
    del _checkpointer
    pool = _STATE.pool
    reset_checkpointer_cache()
    if pool is not None:
        await pool.close()
