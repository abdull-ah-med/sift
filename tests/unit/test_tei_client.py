"""TEI HTTP client smoke — embed returns 1024-d dense vector (BGE-M3)."""

from __future__ import annotations

import httpx
import pytest

from sift_api.tei import TeiClient, TeiEmbedResult

BGE_M3_DIM = 1024


def test_tei_client_embed_returns_1024d_dense_vector() -> None:
    dense = [0.01] * BGE_M3_DIM
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"embeddings": [dense]})
    )
    client = TeiClient(base_url="http://tei.test", transport=transport)
    result = client.embed(["refund policy"])
    assert isinstance(result, TeiEmbedResult)
    assert len(result.dense) == 1
    assert len(result.dense[0]) == BGE_M3_DIM
    assert result.dense[0] == dense


def test_tei_client_embed_rejects_wrong_dimension() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"embeddings": [[0.1, 0.2]]})
    )
    client = TeiClient(base_url="http://tei.test", transport=transport)
    with pytest.raises(ValueError, match="1024"):
        client.embed(["x"])
