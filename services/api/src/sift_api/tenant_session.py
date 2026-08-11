"""Tenant-scoped async session: SET ROLE sift_app + sift.tenant_id GUC."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from sift_api.db import get_engine
from sift_core.db import tenant_guc_statements


async def open_tenant_session(tenant_id: str) -> AsyncIterator[AsyncSession]:
    """Yield a session under ``sift_app`` with RLS tenant GUC set.

    Must be used as ``async with`` / async context from a dependency.
    """
    engine = get_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        await session.connection(execution_options={"isolation_level": "READ COMMITTED"})
        conn = await session.connection()
        await conn.execute(text("SET LOCAL ROLE sift_app"))
        for stmt in tenant_guc_statements(tenant_id):
            await conn.execute(text(stmt))
        yield session
        await session.commit()


async def begin_tenant_session(tenant_id: str) -> AsyncSession:
    """Open a tenant session (caller must commit/rollback/close)."""
    engine = get_engine()
    session = AsyncSession(engine, expire_on_commit=False)
    await session.connection()
    conn = await session.connection()
    await conn.execute(text("SET LOCAL ROLE sift_app"))
    for stmt in tenant_guc_statements(tenant_id):
        await conn.execute(text(stmt))
    return session


async def begin_admin_session() -> AsyncSession:
    """Open a session as ``sift_admin`` (BYPASSRLS) for bootstrap/seed."""
    engine = get_engine()
    session = AsyncSession(engine, expire_on_commit=False)
    await session.connection()
    conn = await session.connection()
    await conn.execute(text("SET LOCAL ROLE sift_admin"))
    return session
