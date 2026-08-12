"""Finalize enqueues embed_document (p3-3)."""

from __future__ import annotations

import inspect

from sift_api.routes import review as review_mod
from sift_api.tasks import embed_document


def test_finalize_module_imports_embed_document() -> None:
    assert hasattr(review_mod, "embed_document")
    assert review_mod.embed_document is embed_document
    assert hasattr(embed_document, "kiq")


def test_finalize_document_source_calls_embed_kiq() -> None:
    source = inspect.getsource(review_mod.finalize_document)
    assert "embed_document.kiq" in source
    assert "document_id" in source
    assert "ctx.tenant_id" in source
