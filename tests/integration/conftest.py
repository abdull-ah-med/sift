"""Shared Postgres + Alembic fixtures for integration tests."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

REPO_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = REPO_ROOT / "tools" / "db" / "alembic.ini"


def _sync_dsn() -> str:
    raw = os.environ.get("SIFT_PG_DSN") or os.environ.get("DATABASE_URL")
    if not raw:
        raw = "postgresql+psycopg://sift:sift@127.0.0.1:5432/sift"
    if raw.startswith("postgresql+asyncpg://"):
        return "postgresql+psycopg://" + raw.removeprefix("postgresql+asyncpg://")
    if raw.startswith("postgresql://"):
        return "postgresql+psycopg://" + raw.removeprefix("postgresql://")
    return raw


def _postgres_reachable(dsn: str) -> bool:
    engine = create_engine(dsn, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        engine.dispose()


@pytest.fixture(scope="module")
def pg_dsn() -> str:
    dsn = _sync_dsn()
    if not _postgres_reachable(dsn):
        pytest.skip("Postgres not reachable; start deploy/compose/dev.yml postgres")
    return dsn


@pytest.fixture(scope="module")
def pg_engine(pg_dsn: str) -> Iterator[Engine]:
    engine = create_engine(pg_dsn, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def alembic_cfg(pg_dsn: str) -> Iterator[Config]:
    previous = os.environ.get("SIFT_PG_DSN")
    os.environ["SIFT_PG_DSN"] = pg_dsn
    cfg = Config(str(ALEMBIC_INI))
    try:
        yield cfg
    finally:
        if previous is None:
            os.environ.pop("SIFT_PG_DSN", None)
        else:
            os.environ["SIFT_PG_DSN"] = previous


@pytest.fixture(scope="module")
def migrated_db(alembic_cfg: Config, pg_engine: Engine) -> Iterator[Engine]:
    command.upgrade(alembic_cfg, "head")
    yield pg_engine
    command.downgrade(alembic_cfg, "base")
