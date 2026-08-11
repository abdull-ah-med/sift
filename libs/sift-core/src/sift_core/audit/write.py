"""Append-only audit event writes and chain verification (ADR-0014)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Connection, text

from sift_core.audit.canonical import (
    ALGORITHM,
    GENESIS_PREV_HASH,
    build_canonical_payload,
    compute_event_hash,
)
from sift_core.ids import IdKind, new_id


@dataclass(frozen=True, slots=True)
class AuditEventRecord:
    event_id: str
    tenant_id: str
    chain_index: int
    occurred_at: datetime
    actor: str
    action: str
    target_kind: str
    target_id: str
    payload: dict[str, Any]
    request_id: str | None
    ip_hash: str | None
    prev_hash: bytes
    event_hash: bytes
    algorithm: str = ALGORITHM


@dataclass(frozen=True, slots=True)
class VerifyReport:
    ok: bool
    checked: int
    tampered_at_index: int | None = None
    detail: str | None = None


def write_audit_event(  # noqa: PLR0913 — ADR-0014 field set is the public contract
    connection: Connection,
    *,
    tenant_id: str,
    actor: str,
    action: str,
    target_kind: str,
    target_id: str = "",
    payload: dict[str, Any] | None = None,
    request_id: str | None = None,
    ip_hash: str | None = None,
    occurred_at: datetime | None = None,
    event_id: str | None = None,
) -> AuditEventRecord:
    """Append one hash-chained audit event inside the caller's transaction.

    Acquires ``pg_advisory_xact_lock(hashtextextended(tenant_id, 0))``, reads the
    tip, hashes in-process (ADR-0014), and inserts. Caller must already be in a
    transaction with the correct tenant GUC / role.
    """
    occurred = occurred_at or datetime.now(UTC)
    if occurred.tzinfo is None:
        raise ValueError("occurred_at must be timezone-aware")
    eid = event_id or new_id(IdKind.EVENT)
    body = payload if payload is not None else {}

    connection.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:tenant_id, 0))"),
        {"tenant_id": tenant_id},
    )
    tip = connection.execute(
        text(
            """
            SELECT event_hash, chain_index
            FROM audit_events
            WHERE tenant_id = :tenant_id
            ORDER BY chain_index DESC
            LIMIT 1
            """
        ),
        {"tenant_id": tenant_id},
    ).one_or_none()

    if tip is None:
        prev_hash = GENESIS_PREV_HASH
        chain_index = 1
    else:
        prev_hash = bytes(tip.event_hash)
        chain_index = int(tip.chain_index) + 1

    canonical = build_canonical_payload(
        event_id=eid,
        tenant_id=tenant_id,
        chain_index=chain_index,
        occurred_at=occurred,
        actor=actor,
        action=action,
        target_kind=target_kind,
        target_id=target_id,
        payload=body,
        request_id=request_id,
        ip_hash=ip_hash,
    )
    event_hash = compute_event_hash(prev_hash, canonical)

    connection.execute(
        text(
            """
            INSERT INTO audit_events (
              event_id, tenant_id, chain_index, occurred_at, actor, action,
              target_kind, target_id, payload, request_id, ip_hash,
              prev_hash, event_hash
            ) VALUES (
              :event_id, :tenant_id, :chain_index, :occurred_at, :actor, :action,
              :target_kind, :target_id, CAST(:payload AS jsonb), :request_id, :ip_hash,
              :prev_hash, :event_hash
            )
            """
        ),
        {
            "event_id": eid,
            "tenant_id": tenant_id,
            "chain_index": chain_index,
            "occurred_at": occurred,
            "actor": actor,
            "action": action,
            "target_kind": target_kind,
            "target_id": target_id,
            "payload": json.dumps(body, separators=(",", ":"), sort_keys=True),
            "request_id": request_id,
            "ip_hash": ip_hash,
            "prev_hash": prev_hash,
            "event_hash": event_hash,
        },
    )
    return AuditEventRecord(
        event_id=eid,
        tenant_id=tenant_id,
        chain_index=chain_index,
        occurred_at=occurred,
        actor=actor,
        action=action,
        target_kind=target_kind,
        target_id=target_id,
        payload=body,
        request_id=request_id,
        ip_hash=ip_hash,
        prev_hash=prev_hash,
        event_hash=event_hash,
    )


def verify_chain(
    connection: Connection,
    tenant_id: str,
    *,
    from_index: int = 1,
    to_index: int | None = None,
) -> VerifyReport:
    """Re-hash events in order and report the first tamper index, if any."""
    if from_index == 1:
        expected_prev: bytes | None = GENESIS_PREV_HASH
    else:
        tip = connection.execute(
            text(
                """
                SELECT event_hash FROM audit_events
                WHERE tenant_id = :tenant_id AND chain_index = :idx
                """
            ),
            {"tenant_id": tenant_id, "idx": from_index - 1},
        ).one_or_none()
        if tip is None:
            return VerifyReport(
                ok=False,
                checked=0,
                tampered_at_index=from_index,
                detail="missing predecessor for from_index",
            )
        expected_prev = bytes(tip.event_hash)

    if to_index is None:
        rows_sql = """
            SELECT event_id, tenant_id, chain_index, occurred_at, actor, action,
                   target_kind, target_id, payload, request_id, ip_hash,
                   prev_hash, event_hash
            FROM audit_events
            WHERE tenant_id = :tenant_id
              AND chain_index >= :from_index
            ORDER BY chain_index ASC
            """
        params: dict[str, Any] = {"tenant_id": tenant_id, "from_index": from_index}
    else:
        rows_sql = """
            SELECT event_id, tenant_id, chain_index, occurred_at, actor, action,
                   target_kind, target_id, payload, request_id, ip_hash,
                   prev_hash, event_hash
            FROM audit_events
            WHERE tenant_id = :tenant_id
              AND chain_index >= :from_index
              AND chain_index <= :to_index
            ORDER BY chain_index ASC
            """
        params = {
            "tenant_id": tenant_id,
            "from_index": from_index,
            "to_index": to_index,
        }
    rows = connection.execute(text(rows_sql), params).mappings().all()

    expected_index = from_index
    checked = 0

    for row in rows:
        checked += 1
        chain_index = int(row["chain_index"])
        if chain_index != expected_index:
            return VerifyReport(
                ok=False,
                checked=checked,
                tampered_at_index=chain_index,
                detail=f"gap: expected chain_index {expected_index}",
            )
        prev_hash = bytes(row["prev_hash"])
        if prev_hash != expected_prev:
            return VerifyReport(
                ok=False,
                checked=checked,
                tampered_at_index=chain_index,
                detail="prev_hash mismatch",
            )
        occurred = row["occurred_at"]
        if occurred.tzinfo is None:
            occurred = occurred.replace(tzinfo=UTC)
        canonical = build_canonical_payload(
            event_id=row["event_id"],
            tenant_id=row["tenant_id"],
            chain_index=chain_index,
            occurred_at=occurred,
            actor=row["actor"],
            action=row["action"],
            target_kind=row["target_kind"],
            target_id=row["target_id"],
            payload=dict(row["payload"]),
            request_id=row["request_id"],
            ip_hash=row["ip_hash"],
        )
        recomputed = compute_event_hash(prev_hash, canonical)
        if recomputed != bytes(row["event_hash"]):
            return VerifyReport(
                ok=False,
                checked=checked,
                tampered_at_index=chain_index,
                detail="event_hash mismatch",
            )
        expected_prev = bytes(row["event_hash"])
        expected_index = chain_index + 1

    return VerifyReport(ok=True, checked=checked)
