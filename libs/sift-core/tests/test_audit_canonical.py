"""Unit tests for audit hash-chain (ADR-0014) — pure canonicalize + hash seams."""

from __future__ import annotations

from datetime import UTC, datetime

import blake3
import rfc8785

from sift_core.audit.canonical import (
    ALGORITHM,
    GENESIS_PREV_HASH,
    build_canonical_payload,
    compute_event_hash,
    jcs_bytes,
)


def test_jcs_bytes_when_keys_unsorted_emits_lexicographic_order() -> None:
    # Independent of our builder: RFC 8785 requires sorted keys.
    assert jcs_bytes({"b": 1, "a": 2}) == b'{"a":2,"b":1}'


def test_jcs_bytes_matches_rfc8785_library_for_nested_object() -> None:
    obj = {"z": {"b": True, "a": [3, 1]}, "a": "x"}
    assert jcs_bytes(obj) == rfc8785.dumps(obj)


def test_compute_event_hash_when_genesis_matches_blake3_of_zeros_plus_jcs() -> None:
    payload = build_canonical_payload(
        event_id="aud_01HABCDEFGHJKMNPQRSTVWXYZ",
        tenant_id="tenant_01HABCDEFGHJKMNPQRSTVWXYZ",
        chain_index=1,
        occurred_at=datetime(2026, 8, 11, 14, 3, 22, 123456, tzinfo=UTC),
        actor="system",
        action="tenant.create",
        target_kind="tenant",
        target_id="tenant_01HABCDEFGHJKMNPQRSTVWXYZ",
        payload={"tenant_name": "Acme", "created_by": "user:sub-1"},
        request_id=None,
        ip_hash=None,
    )
    jcs = jcs_bytes(payload)
    expected = blake3.blake3(GENESIS_PREV_HASH + jcs).digest()

    assert compute_event_hash(GENESIS_PREV_HASH, payload) == expected
    assert len(expected) == len(GENESIS_PREV_HASH)
    assert ALGORITHM == "BLAKE3-256/JCS/v1"


def test_compute_event_hash_when_chained_uses_previous_event_hash() -> None:
    first = build_canonical_payload(
        event_id="aud_01HAAAAAAAAAAAAAAAAAAAAAAA",
        tenant_id="tenant_01HABCDEFGHJKMNPQRSTVWXYZ",
        chain_index=1,
        occurred_at=datetime(2026, 8, 11, 14, 0, 0, 0, tzinfo=UTC),
        actor="system",
        action="tenant.create",
        target_kind="tenant",
        target_id="tenant_01HABCDEFGHJKMNPQRSTVWXYZ",
        payload={},
        request_id=None,
        ip_hash=None,
    )
    h1 = compute_event_hash(GENESIS_PREV_HASH, first)
    second = build_canonical_payload(
        event_id="aud_01HBBBBBBBBBBBBBBBBBBBBBBB",
        tenant_id="tenant_01HABCDEFGHJKMNPQRSTVWXYZ",
        chain_index=2,
        occurred_at=datetime(2026, 8, 11, 14, 0, 1, 0, tzinfo=UTC),
        actor="user:sub-1",
        action="document.upload",
        target_kind="document",
        target_id="doc_01HCCCCCCCCCCCCCCCCCCCCCCC",
        payload={"bytes": 10},
        request_id="req-1",
        ip_hash="ab" * 32,
    )
    h2 = compute_event_hash(h1, second)

    assert h2 == blake3.blake3(h1 + jcs_bytes(second)).digest()
    assert h1 != h2
