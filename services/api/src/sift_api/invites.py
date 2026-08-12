"""HMAC-signed tenant invite tokens (no extra table)."""

from __future__ import annotations

import hmac
from hashlib import sha256

_PREFIX = "inv_v1"
_TOKEN_PARTS_MIN = 3


def mint_invite_token(*, tenant_id: str, pepper: str) -> str:
    """Return ``inv_v1.{tenant_id}.{mac}`` bound to ``pepper``."""
    mac = hmac.new(pepper.encode("utf-8"), f"invite-v1:{tenant_id}".encode(), sha256).hexdigest()
    return f"{_PREFIX}.{tenant_id}.{mac}"


def verify_invite_token(*, token: str, pepper: str) -> str:
    """Return tenant_id if the token is valid; raise ValueError otherwise."""
    parts = token.strip().split(".")
    if len(parts) < _TOKEN_PARTS_MIN or parts[0] != _PREFIX:
        raise ValueError("invalid invite token")
    mac = parts[-1]
    tenant_id = ".".join(parts[1:-1])
    if not tenant_id or not mac:
        raise ValueError("invalid invite token")
    expected = hmac.new(
        pepper.encode("utf-8"),
        f"invite-v1:{tenant_id}".encode(),
        sha256,
    ).hexdigest()
    if not hmac.compare_digest(mac, expected):
        raise ValueError("invalid invite token")
    return tenant_id
