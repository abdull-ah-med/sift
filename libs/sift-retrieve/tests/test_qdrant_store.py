"""Unit contracts for Qdrant dense store (p3-8)."""

from __future__ import annotations

import json

import httpx

from sift_retrieve.store.qdrant import QdrantDenseStore, collection_name, point_id_for_chunk


def test_collection_name_is_tenant_scoped() -> None:
    assert collection_name("ten_1", "col_2") == "ten_1__col_2"


def test_point_id_for_chunk_is_uuid() -> None:
    pid = point_id_for_chunk("chunk_01ABCDEF")
    assert len(pid) == 36
    assert pid == point_id_for_chunk("chunk_01ABCDEF")


def test_qdrant_search_maps_hits() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/points/search" in str(request.url)
        body = json.loads(request.content.decode())
        assert body["limit"] == 5
        assert body["filter"]["must"][0]["key"] == "tenant_id"
        return httpx.Response(
            200,
            json={
                "result": [
                    {
                        "id": "chunk_1",
                        "score": 0.91,
                        "payload": {"document_id": "doc_1", "chunk_id": "chunk_1"},
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    store = QdrantDenseStore(
        base_url="http://qdrant.test:6333",
        transport=transport,
    )
    hits = store.search(
        query_vector=[0.1] * 8,
        tenant_id="ten_1",
        collection_id="col_1",
        limit=5,
    )
    assert hits[0].chunk_id == "chunk_1"
    assert hits[0].document_id == "doc_1"
    assert hits[0].score == 0.91


def test_qdrant_empty_document_ids_deny_all() -> None:
    store = QdrantDenseStore(base_url="http://qdrant.test:6333")
    assert (
        store.search(
            query_vector=[0.1],
            tenant_id="t",
            collection_id="c",
            document_ids=[],
        )
        == []
    )
