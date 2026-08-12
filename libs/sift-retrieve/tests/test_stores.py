"""Dense / BM25 store contracts (p3-4 Bugbot fixes)."""

from __future__ import annotations

from unittest.mock import MagicMock

from sift_retrieve.store.bm25 import ParadeBm25Store, phrase_query
from sift_retrieve.store.pgvector import PgvectorDenseStore


def test_empty_document_ids_is_deny_all_for_dense() -> None:
    conn = MagicMock()
    store = PgvectorDenseStore(conn)
    assert (
        store.search(
            query_vector=[0.1, 0.2],
            tenant_id="t",
            collection_id="c",
            document_ids=[],
        )
        == []
    )
    conn.execute.assert_not_called()


def test_empty_document_ids_is_deny_all_for_bm25() -> None:
    conn = MagicMock()
    store = ParadeBm25Store(conn)
    assert (
        store.search(
            query="refund",
            tenant_id="t",
            collection_id="c",
            document_ids=[],
        )
        == []
    )
    conn.execute.assert_not_called()


def test_phrase_query_quotes_and_escapes() -> None:
    assert phrase_query('refund "policy"') == '"refund \\"policy\\""'
    assert phrase_query("plain") == '"plain"'
