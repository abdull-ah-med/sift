"""HTTP entrypoint for the sift API (Phase 0: health + parse smoke)."""

from __future__ import annotations

from fastapi import FastAPI

from sift_api.routes.health import router as health_router
from sift_api.routes.parse_smoke import router as parse_smoke_router

app = FastAPI(title="sift-api", version="0.0.0")
app.include_router(health_router)
app.include_router(parse_smoke_router)
