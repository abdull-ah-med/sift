# syntax=docker/dockerfile:1

FROM python:3.13-slim-bookworm AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.8.4 /uv /usr/local/bin/uv

FROM base AS deps
COPY pyproject.toml uv.lock ./
COPY libs/sift-core ./libs/sift-core
COPY libs/sift-parse ./libs/sift-parse
COPY libs/sift-obs ./libs/sift-obs
COPY services/api ./services/api
COPY services/worker ./services/worker
COPY apps/cli ./apps/cli
RUN uv sync --frozen --no-dev --package sift-api

FROM base AS runtime
COPY --from=deps /app /app
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "sift_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
