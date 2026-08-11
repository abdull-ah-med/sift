"""Typed ULID primary keys used across sift tables and APIs.

Format: ``<prefix>_<ULID>`` (e.g. ``tenant_01H...``). Generated in application
code — never DB sequences — so IDs are sortable, URL-safe, and self-describing.
"""

from __future__ import annotations

import re
from enum import StrEnum

from ulid import ULID

_ULID_RE = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")


class IdKind(StrEnum):
    """Entity kinds that receive typed ULID primary keys."""

    ORGANIZATION = "organization"
    TENANT = "tenant"
    COLLECTION = "collection"
    DOCUMENT = "document"
    BLOCK = "block"
    BLOCK_REVISION = "block_revision"
    CHUNK = "chunk"
    JOB = "job"
    SESSION = "session"
    API_KEY = "api_key"
    EVENT = "event"
    TAG = "tag"


_PREFIX_BY_KIND: dict[IdKind, str] = {
    IdKind.ORGANIZATION: "org",
    IdKind.TENANT: "tenant",
    IdKind.COLLECTION: "col",
    IdKind.DOCUMENT: "doc",
    IdKind.BLOCK: "blk",
    IdKind.BLOCK_REVISION: "brev",
    IdKind.CHUNK: "chunk",
    IdKind.JOB: "job",
    IdKind.SESSION: "session",
    IdKind.API_KEY: "key",
    IdKind.EVENT: "aud",
    IdKind.TAG: "tag",
}

_KIND_BY_PREFIX: dict[str, IdKind] = {prefix: kind for kind, prefix in _PREFIX_BY_KIND.items()}


def prefix_for(kind: IdKind) -> str:
    """Return the string prefix for ``kind`` (without trailing underscore)."""
    return _PREFIX_BY_KIND[kind]


def new_id(kind: IdKind) -> str:
    """Allocate a new typed ULID for ``kind``."""
    return f"{prefix_for(kind)}_{ULID()}"


def parse_id(value: str) -> tuple[IdKind, str]:
    """Split a typed id into ``(kind, ulid_body)``.

    Raises:
        ValueError: if the prefix is unknown or the ULID body is malformed.
    """
    prefix, sep, body = value.partition("_")
    if not sep or not body:
        raise ValueError(f"invalid id: {value!r}")
    kind = _KIND_BY_PREFIX.get(prefix)
    if kind is None:
        raise ValueError(f"unknown id prefix: {prefix!r}")
    if _ULID_RE.fullmatch(body) is None:
        raise ValueError(f"invalid id: {value!r}")
    return kind, body


def validate_id(value: str, kind: IdKind) -> str:
    """Return ``value`` if it is a well-formed id of ``kind``.

    Raises:
        ValueError: if the value is malformed or belongs to another kind.
    """
    expected = prefix_for(kind)
    if not value.startswith(f"{expected}_"):
        raise ValueError(f"expected prefix '{expected}_': {value!r}")
    parsed_kind, _body = parse_id(value)
    if parsed_kind is not kind:
        raise ValueError(f"expected prefix '{expected}_': {value!r}")
    return value
