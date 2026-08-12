"""Unit tests for sift search CLI (p3-6 / Phase 3 §7)."""

from __future__ import annotations

from typing import Any

import pytest

from sift_cli.search import (
    format_search_json,
    format_search_rows,
    looks_like_collection_id,
    resolve_collection_id,
)


def test_looks_like_collection_id() -> None:
    assert looks_like_collection_id("col_abc")
    assert not looks_like_collection_id("policies")


def test_resolve_collection_id_matches_slug() -> None:
    collections = [
        {"id": "col_aaa", "slug": "other"},
        {"id": "col_bbb", "slug": "policies"},
    ]
    assert resolve_collection_id(collections, "policies") == "col_bbb"


def test_resolve_collection_id_accepts_raw_id() -> None:
    collections = [{"id": "col_xyz", "slug": "policies"}]
    assert resolve_collection_id(collections, "col_xyz") == "col_xyz"


def test_resolve_collection_id_missing_raises() -> None:
    with pytest.raises(LookupError):
        resolve_collection_id([{"id": "col_a", "slug": "a"}], "missing")


def test_format_search_rows_includes_citations() -> None:
    payload: dict[str, Any] = {
        "results": [
            {
                "chunk_id": "chunk_1",
                "document_id": "doc_1",
                "document_title": "EU T&Cs",
                "score": 0.12,
                "rerank_score": 0.94,
                "text": "refund policy for EU customers",
                "section_path": ["Refunds", "EU"],
                "page_numbers": [12, 13],
            }
        ],
        "trace_id": "tr_1",
    }
    rows = format_search_rows(payload)
    assert rows[0]["document"] == "EU T&Cs"
    assert rows[0]["score"] == "0.940"
    assert "refund" in rows[0]["snippet"]


def test_format_search_json_passthrough() -> None:
    payload = {"results": [], "trace_id": "t"}
    assert format_search_json(payload) == payload
