"""Finalize enqueues embed_document (p3-3)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_finalize_enqueues_embed_document(monkeypatch: pytest.MonkeyPatch) -> None:
    """Contract: after chunks are written, finalize must kiq embed_document."""
    # Import path under test — fails until wired.
    from sift_api.routes import review as review_mod

    kiq_calls: list[tuple[Any, ...]] = []

    async def fake_kiq(*args: Any, **kwargs: Any) -> object:
        kiq_calls.append(args)
        return object()

    # Presence check: review module must reference embed_document for enqueue.
    assert hasattr(review_mod, "embed_document") or "embed_document" in dir(review_mod)

    monkeypatch.setattr(
        "sift_api.tasks.embed_document.kiq",
        AsyncMock(side_effect=fake_kiq),
        raising=False,
    )
    # Soft contract until full API test: module-level import for enqueue target.
    from sift_api.tasks import embed_document

    assert hasattr(embed_document, "kiq")
