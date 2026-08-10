"""Liveness/readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    status: str


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")
