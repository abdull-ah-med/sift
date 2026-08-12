"""Unit contracts for TEI dense client + embed_document task (p3-3 / ADR-0021)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import httpx

from sift_api import tasks
from sift_api.embed import run_embed_document
from sift_api.settings import Settings
from sift_api.tei import TeiClient


def test_tei_client_embed_returns_dense_vectors() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        return httpx.Response(200, json=[[0.1] * 1024])

    client = TeiClient(
        base_url="http://tei.test",
        model="BAAI/bge-m3",
        transport=httpx.MockTransport(handler),
    )
    vectors = client.embed(["hello chunk"])

    assert "/embed" in captured["url"]
    assert len(vectors) == 1
    assert len(vectors[0]) == 1024
    assert all(isinstance(x, float) for x in vectors[0])


def test_tei_client_does_not_call_embed_sparse() -> None:
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        return httpx.Response(200, json=[[0.0] * 1024, [0.0] * 1024])

    client = TeiClient(
        base_url="http://tei.test",
        transport=httpx.MockTransport(handler),
    )
    client.embed(["a", "b"])
    assert paths == ["/embed"]
    assert all("sparse" not in p for p in paths)


def test_embed_document_task_is_registered() -> None:
    assert hasattr(tasks, "embed_document")
    assert callable(tasks.embed_document)


def test_run_embed_document_upserts_dense_sets_ready_and_audits() -> None:
    chunks = [
        {
            "id": "chunk_a",
            "collection_id": "col_1",
            "text_contextualized": "alpha",
            "review_state": "approved",
        },
        {
            "id": "chunk_b",
            "collection_id": "col_1",
            "text_contextualized": "beta",
            "review_state": "edited",
        },
    ]
    upserts: list[dict[str, Any]] = []
    audits: list[dict[str, Any]] = []
    status_updates: list[str] = []
    index_bumps: list[str] = []

    tei = MagicMock()
    tei.embed.return_value = [[0.01] * 1024, [0.02] * 1024]

    def fake_load(**_kwargs: Any) -> list[dict[str, Any]]:
        return chunks

    def fake_upsert(**kwargs: Any) -> None:
        upserts.append(kwargs)

    def fake_set_ready(**kwargs: Any) -> None:
        status_updates.append(kwargs["document_id"])

    def fake_bump(**kwargs: Any) -> None:
        index_bumps.append(kwargs["collection_id"])

    def fake_audit(**kwargs: Any) -> None:
        audits.append(kwargs)

    result = run_embed_document(
        document_id="doc_1",
        tenant_id="ten_1",
        force=False,
        tei=tei,
        settings=Settings.model_validate(
            {"SIFT_TEI_URL": "http://tei.test", "SIFT_TEI_MODEL": "BAAI/bge-m3"}
        ),
        load_chunks=fake_load,
        upsert=fake_upsert,
        mark_ready=fake_set_ready,
        bump_index=fake_bump,
        audit=fake_audit,
    )

    assert result == "embedded"
    tei.embed.assert_called_once()
    texts = tei.embed.call_args.args[0]
    assert texts == ["alpha", "beta"]
    assert len(upserts) == 1
    assert upserts[0]["sparse"] is None
    assert all(len(v) == 1024 for v in upserts[0]["embeddings"])
    assert status_updates == ["doc_1"]
    assert index_bumps == ["col_1"]
    assert audits[0]["action"] == "document.embed"
    payload = audits[0]["payload"]
    assert payload.get("chunk_count") == 2
    assert payload.get("sparse_stored") is False
    assert "text" not in payload


def test_run_embed_document_idempotent_skips_when_no_pending() -> None:
    tei = MagicMock()
    mark = MagicMock()
    upsert = MagicMock()
    bump = MagicMock()
    audit = MagicMock()

    result = run_embed_document(
        document_id="doc_1",
        tenant_id="ten_1",
        tei=tei,
        load_chunks=lambda **_: [],
        upsert=upsert,
        mark_ready=mark,
        bump_index=bump,
        audit=audit,
    )
    assert result == "noop"
    tei.embed.assert_not_called()
    upsert.assert_not_called()
    mark.assert_called_once()
