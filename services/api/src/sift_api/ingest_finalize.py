"""Shared chunk persist + embed enqueue after parse skip-review or HITL finalize.

``persist_chunks_and_enqueue_embed`` writes ``chunks`` rows on the caller's
connection. Callers must commit that transaction, then call
``enqueue_embed_document`` (sync ingest) or ``embed_document.kiq`` (async
review). Never kiq inside a transaction that can roll back.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Protocol

from sqlalchemy import text

from sift_core.models import Block
from sift_ingest.chunker import chunk_blocks

_log = logging.getLogger(__name__)
_embed_kiq_tasks: set[asyncio.Task[None]] = set()


class _ExecConn(Protocol):
    """Sync SQLAlchemy Connection or Session with ``execute``."""

    def execute(self, statement: Any, parameters: Any = None) -> Any: ...


def persist_chunks_and_enqueue_embed(  # noqa: PLR0913 — plan §4.1 named kwargs
    conn: _ExecConn,
    *,
    tenant_id: str,
    document_id: str,
    collection_id: str,
    document_title: str,
    blocks: list[Block],
    actor: str,
) -> int:
    """Chunk ``blocks`` and INSERT ``chunks`` rows. Returns chunk count.

    Does not enqueue embed. After the caller commits, pass the return value to
    ``enqueue_embed_document`` (or await ``embed_document.kiq`` from async code).
    Skips rejected/empty blocks via ``chunk_blocks``. ``review_state`` is
    ``approved``. ``actor`` is logged as an id only; chunk text is never logged.
    """
    chunks = chunk_blocks(blocks, document_title=document_title)
    conn.execute(
        text("DELETE FROM chunks WHERE document_id = :id"),
        {"id": document_id},
    )
    for chunk in chunks:
        conn.execute(
            text(
                """
                INSERT INTO chunks (
                  id, tenant_id, document_id, collection_id, ordinal,
                  text_raw, text_contextualized, token_count, chunk_type,
                  section_path, page_numbers, block_ids, quality_score, review_state
                ) VALUES (
                  :id, :tenant_id, :document_id, :collection_id, :ordinal,
                  :text_raw, :text_contextualized, :token_count, :chunk_type,
                  :section_path, :page_numbers, :block_ids, :quality_score, 'approved'
                )
                """
            ),
            {
                "id": chunk.id,
                "tenant_id": tenant_id,
                "document_id": document_id,
                "collection_id": collection_id,
                "ordinal": chunk.ordinal,
                "text_raw": chunk.text_raw,
                "text_contextualized": chunk.text_contextualized,
                "token_count": chunk.token_count,
                "chunk_type": chunk.chunk_type.value,
                "section_path": chunk.section_path,
                "page_numbers": chunk.page_numbers,
                "block_ids": chunk.block_ids,
                "quality_score": chunk.quality_score,
            },
        )
    count = len(chunks)
    _log.info(
        "chunks_persisted actor=%s document_id=%s chunk_count=%d",
        actor,
        document_id,
        count,
    )
    return count


def enqueue_embed_document(
    *,
    document_id: str,
    tenant_id: str,
    chunk_count: int,
) -> None:
    """Enqueue ``embed_document`` after chunks are committed. No-op if count is 0."""
    if chunk_count <= 0:
        return

    from sift_api.tasks import embed_document  # noqa: PLC0415 — break tasks→ingest cycle

    async def _kiq() -> None:
        await embed_document.kiq(document_id, tenant_id)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(_kiq())
        return
    task = loop.create_task(_kiq())
    _embed_kiq_tasks.add(task)
    task.add_done_callback(_embed_kiq_tasks.discard)
