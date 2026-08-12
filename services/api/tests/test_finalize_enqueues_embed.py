"""Finalize enqueues embed_document (p3-3)."""

from __future__ import annotations

from sift_api.routes import review as review_mod
from sift_api.tasks import embed_document


def test_finalize_module_imports_embed_document() -> None:
    assert hasattr(review_mod, "embed_document")
    assert review_mod.embed_document is embed_document
    assert hasattr(embed_document, "kiq")
