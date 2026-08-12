"""Postgres LangGraph checkpointer factory (Phase 2 §4.3).

Uses ``langgraph-checkpoint-postgres`` so interrupt/resume survives API restart.
"""

from __future__ import annotations

from typing import Any

from sift_api.settings import Settings, get_settings


def postgres_checkpoint_dsn(settings: Settings | None = None) -> str:
    """Return a psycopg DSN suitable for ``AsyncPostgresSaver``."""
    raw = (settings or get_settings()).sift_pg_dsn
    if raw.startswith("postgresql+asyncpg://"):
        return "postgresql://" + raw.removeprefix("postgresql+asyncpg://")
    if raw.startswith("postgresql+psycopg://"):
        return "postgresql://" + raw.removeprefix("postgresql+psycopg://")
    return raw


async def open_postgres_checkpointer(settings: Settings | None = None) -> Any:
    """Open an ``AsyncPostgresSaver`` and run ``setup()``.

    TDD stub — real saver lands in the impl commit.
    """
    del settings
    raise NotImplementedError("TDD stub — AsyncPostgresSaver not wired yet")


async def close_postgres_checkpointer(checkpointer: Any) -> None:
    """Close the checkpointer connection if needed."""
    del checkpointer
