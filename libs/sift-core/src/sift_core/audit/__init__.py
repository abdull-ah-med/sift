"""Audit event hash-chain (ADR-0014)."""

from sift_core.audit.canonical import (
    ALGORITHM,
    GENESIS_PREV_HASH,
    build_canonical_payload,
    compute_event_hash,
    format_occurred_at,
    jcs_bytes,
)
from sift_core.audit.write import AuditEventRecord, VerifyReport, verify_chain, write_audit_event

__all__ = [
    "ALGORITHM",
    "GENESIS_PREV_HASH",
    "AuditEventRecord",
    "VerifyReport",
    "build_canonical_payload",
    "compute_event_hash",
    "format_occurred_at",
    "jcs_bytes",
    "verify_chain",
    "write_audit_event",
]
