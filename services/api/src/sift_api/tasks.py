"""Taskiq broker wiring."""

from __future__ import annotations

from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker

from sift_api.ingest import run_ingest_document
from sift_api.settings import get_settings

_settings = get_settings()
broker = RedisStreamBroker(url=_settings.sift_valkey_url).with_result_backend(
    RedisAsyncResultBackend(redis_url=_settings.sift_valkey_url)
)


@broker.task(task_name="ingest_document")
async def ingest_document(document_id: str, job_id: str, tenant_id: str) -> None:
    run_ingest_document(document_id=document_id, job_id=job_id, tenant_id=tenant_id)
