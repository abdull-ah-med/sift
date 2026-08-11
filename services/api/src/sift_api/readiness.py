"""Dependency readiness probes for GET /health/ready."""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus

import httpx
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from sift_api.db import ping_postgres
from sift_api.settings import Settings, get_settings


@dataclass(frozen=True, slots=True)
class CheckResult:
    ok: bool
    detail: str


async def check_postgres(settings: Settings | None = None) -> CheckResult:
    """Ping Postgres via SQLAlchemy async engine."""
    _ = settings or get_settings()
    try:
        await ping_postgres()
    except (SQLAlchemyError, OSError) as exc:
        return CheckResult(ok=False, detail=str(exc.__class__.__name__))
    return CheckResult(ok=True, detail="ok")


async def check_valkey(settings: Settings | None = None) -> CheckResult:
    """PING Valkey/Redis using a short-lived pooled client."""
    cfg = settings or get_settings()
    client = Redis.from_url(cfg.sift_valkey_url, socket_connect_timeout=2)
    try:
        pong = await client.ping()
    except (OSError, TimeoutError, RedisError) as exc:
        return CheckResult(ok=False, detail=str(exc.__class__.__name__))
    finally:
        await client.aclose()
    if pong is not True:
        return CheckResult(ok=False, detail="unexpected ping response")
    return CheckResult(ok=True, detail="ok")


async def check_storage(settings: Settings | None = None) -> CheckResult:
    """HTTP GET the SeaweedFS S3 endpoint (same signal as Compose healthcheck)."""
    cfg = settings or get_settings()
    url = cfg.sift_storage_endpoint.rstrip("/") + "/"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(url)
    except (httpx.HTTPError, OSError) as exc:
        return CheckResult(ok=False, detail=str(exc.__class__.__name__))
    # SeaweedFS may return 403 on unauthenticated /; any non-5xx means reachable.
    if response.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
        return CheckResult(ok=False, detail=f"http_{response.status_code}")
    return CheckResult(ok=True, detail=f"http_{response.status_code}")
