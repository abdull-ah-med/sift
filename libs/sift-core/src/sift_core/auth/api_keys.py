"""API key minting and peppered HMAC-SHA256 verification (ADR-0013)."""

from __future__ import annotations

import hmac
import re
import secrets
from dataclasses import dataclass
from enum import StrEnum

_RAW_KEY_RE = re.compile(r"^sift_(live|test|svc)_([A-Za-z0-9_-]{8})_([A-Za-z0-9_-]{40,})$")


class ApiKeyEnv(StrEnum):
    LIVE = "live"
    TEST = "test"
    SVC = "svc"


@dataclass(frozen=True, slots=True)
class MintedApiKey:
    """Material returned once at creation time."""

    raw: str
    env: ApiKeyEnv
    prefix: str
    secret: str
    hash: bytes
    hash_version: int = 1


def hash_secret(pepper: bytes, secret: str) -> bytes:
    """``HMAC-SHA256(pepper, secret_utf8)`` — 32 bytes."""
    if not pepper:
        raise ValueError("pepper must be non-empty")
    return hmac.new(pepper, secret.encode("utf-8"), "sha256").digest()


def verify_secret(pepper: bytes, secret: str, expected_hash: bytes) -> bool:
    """Constant-time compare of ``hash_secret(pepper, secret)`` to ``expected_hash``."""
    actual = hash_secret(pepper, secret)
    return hmac.compare_digest(actual, expected_hash)


def mint_api_key(pepper: bytes, *, env: ApiKeyEnv = ApiKeyEnv.LIVE) -> MintedApiKey:
    """Create a new raw key and its stored hash material."""
    secret = secrets.token_urlsafe(32)
    prefix = secret[:8]
    raw = f"sift_{env.value}_{prefix}_{secret}"
    return MintedApiKey(
        raw=raw,
        env=env,
        prefix=prefix,
        secret=secret,
        hash=hash_secret(pepper, secret),
        hash_version=1,
    )


def parse_raw_key(raw: str) -> tuple[ApiKeyEnv, str, str]:
    """Split a raw key into ``(env, prefix, secret)``.

    Raises:
        ValueError: if the key does not match the ADR-0013 format.
    """
    match = _RAW_KEY_RE.fullmatch(raw)
    if match is None:
        raise ValueError("invalid api key format")
    env = ApiKeyEnv(match.group(1))
    prefix = match.group(2)
    secret = match.group(3)
    if secret[:8] != prefix:
        raise ValueError("api key prefix does not match secret")
    return env, prefix, secret
