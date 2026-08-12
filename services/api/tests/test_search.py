"""Unit contracts for collection search API (p3-5 / Phase 3 §3.3)."""

from __future__ import annotations

import hashlib
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from sift_api.schemas import SearchFilter, SearchRequest, SearchResponse
from sift_api.search import query_hash, run_collection_search


def test_query_hash_is_sha256_hex_not_raw() -> None:
    digest = query_hash("refund policy SECRET")
    assert digest == hashlib.sha256(b"refund policy SECRET", usedforsecurity=False).hexdigest()
    assert "SECRET" not in digest
    assert len(digest) == 64


def test_search_request_schema_matches_phase3() -> None:
    body = SearchRequest(
        query="refund policy for EU customers",
        top_k=10,
        filter=SearchFilter(tags=["policy"], document_ids=["doc_1"]),
        include_text=True,
        include_provenance=True,
        rerank=True,
    )
    assert body.query.startswith("refund")
    assert body.top_k == 10
    assert body.filter is not None
    assert body.filter.tags == ["policy"]


def test_search_request_rejects_empty_query() -> None:
    with pytest.raises(ValidationError):
        SearchRequest(query="")


def test_run_collection_search_audits_query_hash_never_raw_query() -> None:
    audits: list[dict[str, Any]] = []

    def fake_audit(**kwargs: Any) -> None:
        audits.append(kwargs)

    hits = [
        MagicMock(
            chunk_id="chunk_1",
            document_id="doc_1",
            score=0.8,
            rerank_score=0.9,
            text="refund policy",
        )
    ]
    meta = {
        "chunk_1": {
            "document_title": "EU T&Cs",
            "section_path": ["Refunds"],
            "page_numbers": [12],
            "block_ids": ["blk_1"],
            "text": "refund policy",
        }
    }
    mock_eng = MagicMock()
    mock_conn = MagicMock()
    mock_eng.begin.return_value.__enter__.return_value = mock_conn
    mock_eng.begin.return_value.__exit__.return_value = None

    with (
        patch("sift_api.search._collection_exists", return_value=True),
        patch("sift_api.search._hybrid_retrieve", return_value=(hits, meta)),
        patch("sift_api.search._resolve_document_ids", return_value=None),
    ):
        result = run_collection_search(
            collection_id="col_1",
            tenant_id="ten_1",
            actor="key:test",
            query="raw query MUST NOT LEAK",
            top_k=5,
            document_ids=None,
            tags=None,
            include_text=True,
            include_provenance=True,
            rerank=False,
            engine=mock_eng,
            audit=fake_audit,
        )

    assert isinstance(result, SearchResponse)
    assert result.results[0].chunk_id == "chunk_1"
    assert result.results[0].document_title == "EU T&Cs"
    assert len(audits) == 1
    assert audits[0]["action"] == "search.query"
    payload = audits[0]["payload"]
    assert "query" not in payload
    assert payload["query_hash"] == query_hash("raw query MUST NOT LEAK")
    assert "MUST NOT LEAK" not in str(payload)
