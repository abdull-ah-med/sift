"""Liveness and readiness endpoints."""

from __future__ import annotations

from http import HTTPStatus

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from sift_api.readiness import check_postgres, check_storage, check_valkey

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    status: str


class CheckPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    ok: bool
    detail: str


class ReadyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    status: str
    checks: dict[str, CheckPayload]


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/health/ready", response_model=ReadyResponse)
async def ready() -> ReadyResponse | JSONResponse:
    postgres = await check_postgres()
    valkey = await check_valkey()
    storage = await check_storage()
    checks = {
        "postgres": CheckPayload(ok=postgres.ok, detail=postgres.detail),
        "valkey": CheckPayload(ok=valkey.ok, detail=valkey.detail),
        "storage": CheckPayload(ok=storage.ok, detail=storage.detail),
    }
    all_ok = all(c.ok for c in checks.values())
    body = ReadyResponse(
        status="ok" if all_ok else "not_ready",
        checks=checks,
    )
    if all_ok:
        return body
    return JSONResponse(
        status_code=HTTPStatus.SERVICE_UNAVAILABLE,
        content=body.model_dump(),
    )
