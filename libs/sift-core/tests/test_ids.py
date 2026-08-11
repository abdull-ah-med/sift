"""Typed ULID identifiers for sift entities."""

from __future__ import annotations

import re

import pytest

from sift_core.ids import IdKind, new_id, parse_id, validate_id

ULID_BODY = r"[0-9A-HJKMNP-TV-Z]{26}"


@pytest.mark.parametrize(
    ("kind", "prefix"),
    [
        (IdKind.ORGANIZATION, "org"),
        (IdKind.TENANT, "tenant"),
        (IdKind.COLLECTION, "col"),
        (IdKind.DOCUMENT, "doc"),
        (IdKind.BLOCK, "blk"),
        (IdKind.CHUNK, "chunk"),
        (IdKind.JOB, "job"),
        (IdKind.SESSION, "session"),
        (IdKind.API_KEY, "key"),
        (IdKind.EVENT, "aud"),
        (IdKind.TAG, "tag"),
    ],
)
def test_new_id_when_kind_known_uses_typed_prefix(kind: IdKind, prefix: str) -> None:
    value = new_id(kind)

    assert value.startswith(f"{prefix}_")
    assert re.fullmatch(rf"{prefix}_{ULID_BODY}", value)
    assert validate_id(value, kind) == value
    assert parse_id(value) == (kind, value.split("_", 1)[1])


def test_new_id_when_called_twice_returns_distinct_values() -> None:
    assert new_id(IdKind.TENANT) != new_id(IdKind.TENANT)


def test_validate_id_when_wrong_kind_raises() -> None:
    tenant_id = new_id(IdKind.TENANT)

    with pytest.raises(ValueError, match="expected prefix 'col_'"):
        validate_id(tenant_id, IdKind.COLLECTION)


def test_validate_id_when_malformed_raises() -> None:
    with pytest.raises(ValueError, match="invalid id"):
        validate_id("tenant_not-a-ulid", IdKind.TENANT)


def test_parse_id_when_unknown_prefix_raises() -> None:
    with pytest.raises(ValueError, match="unknown id prefix"):
        parse_id("weird_01HABCDEFGHJKMNPQRSTVWXYZ")
