"""Unit contracts for vector-backend / reindex API (p3-8)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from sift_api.reindex import run_reindex_to_qdrant
from sift_api.schemas import VectorBackendRequest


def test_vector_backend_request_accepts_qdrant() -> None:
    body = VectorBackendRequest(backend="qdrant")
    assert body.backend == "qdrant"


def test_run_reindex_upserts_points_and_sets_backend() -> None:
    audits: list[dict[str, Any]] = []

    def fake_audit(**kwargs: Any) -> None:
        audits.append(kwargs)

    mock_eng = MagicMock()
    mock_conn = MagicMock()
    mock_eng.begin.return_value.__enter__.return_value = mock_conn
    mock_eng.begin.return_value.__exit__.return_value = None

    select_result = MagicMock()
    select_result.mappings.return_value.all.return_value = [
        {
            "chunk_id": "chunk_1",
            "document_id": "doc_1",
            "embedding": [0.1, 0.2],
        }
    ]

    def execute(stmt: Any, _params: Any = None) -> Any:
        if "chunk_embeddings" in str(stmt):
            return select_result
        return MagicMock()

    mock_conn.execute.side_effect = execute

    qdrant = MagicMock()
    with patch("sift_api.reindex._collection_exists", return_value=True):
        result = run_reindex_to_qdrant(
            collection_id="col_1",
            tenant_id="ten_1",
            actor="key:test",
            engine=mock_eng,
            qdrant=qdrant,
            audit=fake_audit,
        )
    assert result["points"] == 1
    qdrant.ensure_collection.assert_called_once()
    qdrant.upsert_points.assert_called_once()
    assert audits[0]["action"] == "collection.reindex"
    assert "query" not in audits[0]["payload"]
