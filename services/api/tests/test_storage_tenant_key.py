"""Tenant object-key prefix helpers (phase-close security fix)."""

from __future__ import annotations

from pathlib import Path

import pytest

from sift_api.storage import (
    download_object,
    object_key_belongs_to_tenant,
    tenant_object_key_prefix,
)


def test_object_key_belongs_to_tenant() -> None:
    tid = "ten_abc"
    assert object_key_belongs_to_tenant(f"t/{tid}/d/doc/original.pdf", tid)
    assert not object_key_belongs_to_tenant("t/ten_other/d/doc/original.pdf", tid)
    assert tenant_object_key_prefix(tid) == f"t/{tid}/"


def test_download_object_rejects_foreign_tenant_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "sift_api.storage._s3_client",
        lambda _settings: (_ for _ in ()).throw(AssertionError("S3 must not run")),
    )
    with pytest.raises(PermissionError, match="tenant prefix"):
        download_object(
            source_uri="seaweed://bucket/t/ten_other/d/doc/original.pdf",
            dest=tmp_path / "out.pdf",
            tenant_id="ten_self",
        )
