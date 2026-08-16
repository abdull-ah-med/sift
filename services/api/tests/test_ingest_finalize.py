"""Unit tests for skip-review chunk persist (p4demo-1)."""

from __future__ import annotations

from typing import Any

import pytest

from sift_api.ingest_finalize import enqueue_embed_document, persist_chunks_and_enqueue_embed
from sift_core.ids import IdKind, new_id
from sift_core.models import Block, BlockType, BoundingBox, Provenance, ReviewState


class _FakeConn:
    def __init__(self) -> None:
        self.sql: list[str] = []
        self.params: list[Any] = []

    def execute(self, statement: Any, parameters: Any = None) -> Any:
        self.sql.append(str(statement))
        self.params.append(parameters)
        return None


def _block(*, text: str, state: ReviewState = ReviewState.APPROVED) -> Block:
    return Block(
        id=new_id(IdKind.BLOCK),
        ordinal=0,
        block_type=BlockType.PARAGRAPH,
        text=text,
        provenance=Provenance(
            page_no=1,
            bbox=BoundingBox(x0=0, y0=0, x1=1, y1=1),
            extractor="digital-pdf",
            model_version="pypdfium2",
        ),
        confidence=0.99,
        review_state=state,
    )


def test_persist_inserts_chunks_for_approved_text() -> None:
    conn = _FakeConn()
    count = persist_chunks_and_enqueue_embed(
        conn,
        tenant_id="ten_1",
        document_id="doc_1",
        collection_id="col_1",
        document_title="Memo",
        blocks=[_block(text="Refunds complete within thirty days.")],
        actor="system",
    )
    assert count == 1
    assert any("DELETE FROM chunks" in sql for sql in conn.sql)
    inserts = [
        params
        for sql, params in zip(conn.sql, conn.params, strict=True)
        if "INSERT INTO chunks" in sql
    ]
    assert len(inserts) == 1
    row = inserts[0]
    assert row["tenant_id"] == "ten_1"
    assert row["document_id"] == "doc_1"
    assert row["collection_id"] == "col_1"
    assert "Memo" in row["text_contextualized"]
    assert "thirty days" in row["text_raw"]


def test_persist_empty_or_rejected_returns_zero() -> None:
    conn = _FakeConn()
    count = persist_chunks_and_enqueue_embed(
        conn,
        tenant_id="ten_1",
        document_id="doc_1",
        collection_id="col_1",
        document_title="Empty",
        blocks=[
            _block(text="   "),
            _block(text="gone", state=ReviewState.REJECTED),
        ],
        actor="system",
    )
    assert count == 0
    assert any("DELETE FROM chunks" in sql for sql in conn.sql)
    assert not any("INSERT INTO chunks" in sql for sql in conn.sql)


def test_enqueue_skips_kiq_when_zero_chunks(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("embed_document.kiq must not run for zero chunks")

    monkeypatch.setattr("sift_api.tasks.embed_document.kiq", boom)
    enqueue_embed_document(document_id="doc_1", tenant_id="ten_1", chunk_count=0)
