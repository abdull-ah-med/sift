"""Canonical payload + BLAKE3 hash for audit events (ADR-0014)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import blake3
import rfc8785

ALGORITHM = "BLAKE3-256/JCS/v1"
GENESIS_PREV_HASH = bytes(32)

_CANONICAL_KEYS = (
    "action",
    "actor",
    "chain_index",
    "event_id",
    "ip_hash",
    "occurred_at",
    "payload",
    "request_id",
    "target_id",
    "target_kind",
    "tenant_id",
)


def format_occurred_at(value: datetime) -> str:
    """Format ``value`` as RFC 3339 UTC with microsecond precision."""
    if value.tzinfo is None:
        raise ValueError("occurred_at must be timezone-aware")
    utc = value.astimezone(UTC)
    return utc.strftime("%Y-%m-%dT%H:%M:%S.") + f"{utc.microsecond:06d}Z"


def build_canonical_payload(  # noqa: PLR0913 — ADR-0014 canonical key set
    *,
    event_id: str,
    tenant_id: str,
    chain_index: int,
    occurred_at: datetime,
    actor: str,
    action: str,
    target_kind: str,
    target_id: str,
    payload: dict[str, Any],
    request_id: str | None,
    ip_hash: str | None,
) -> dict[str, Any]:
    """Build the exact ADR-0014 canonical object (unsorted; JCS sorts on dump)."""
    return {
        "event_id": event_id,
        "tenant_id": tenant_id,
        "chain_index": chain_index,
        "occurred_at": format_occurred_at(occurred_at),
        "actor": actor,
        "action": action,
        "target_kind": target_kind,
        "target_id": target_id,
        "payload": payload,
        "request_id": request_id,
        "ip_hash": ip_hash,
    }


def jcs_bytes(obj: Any) -> bytes:
    """RFC 8785 JSON Canonicalization Scheme bytes."""
    return rfc8785.dumps(obj)


def compute_event_hash(prev_hash: bytes, canonical_payload: dict[str, Any]) -> bytes:
    """``BLAKE3_256(prev_hash || jcs_bytes(canonical_payload))``."""
    if len(prev_hash) != len(GENESIS_PREV_HASH):
        raise ValueError(f"prev_hash must be 32 bytes, got {len(prev_hash)}")
    missing = [k for k in _CANONICAL_KEYS if k not in canonical_payload]
    if missing:
        raise ValueError(f"canonical payload missing keys: {missing}")
    extra = [k for k in canonical_payload if k not in _CANONICAL_KEYS]
    if extra:
        raise ValueError(f"canonical payload has unexpected keys: {extra}")
    return blake3.blake3(prev_hash + jcs_bytes(canonical_payload)).digest()
