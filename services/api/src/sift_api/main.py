"""HTTP entrypoint for the sift API (Phase 0: health only)."""

from __future__ import annotations

from fastapi import FastAPI

from sift_api.routes.health import router as health_router

app = FastAPI(title="sift-api", version="0.0.0")
app.include_router(health_router)
