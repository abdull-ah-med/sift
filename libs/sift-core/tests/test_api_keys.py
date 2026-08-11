"""Unit tests for API key mint/hash/parse (ADR-0013)."""

from __future__ import annotations

import hashlib
import hmac
import re

import pytest

from sift_core.auth.api_keys import (
    ApiKeyEnv,
    hash_secret,
    mint_api_key,
    parse_raw_key,
    verify_secret,
)

_SCANNER = re.compile(r"^sift_(live|test|svc)_[A-Za-z0-9_-]{8}_[A-Za-z0-9_-]{40,}$")


def test_hash_secret_when_known_inputs_matches_stdlib_hmac() -> None:
    pepper = b"test-pepper-32-bytes-pad-pad-pad!!"
    secret = "abc123"
    expected = hmac.new(pepper, secret.encode("utf-8"), "sha256").digest()

    assert hash_secret(pepper, secret) == expected
    assert len(expected) == hashlib.sha256().digest_size


def test_mint_api_key_when_live_matches_scanner_regex_and_prefix() -> None:
    pepper = b"pepper"
    minted = mint_api_key(pepper, env=ApiKeyEnv.LIVE)

    assert _SCANNER.fullmatch(minted.raw) is not None
    assert minted.raw.startswith("sift_live_")
    assert minted.prefix == minted.secret[:8]
    assert minted.hash == hash_secret(pepper, minted.secret)
    assert minted.hash_version == 1


def test_verify_secret_when_matching_returns_true() -> None:
    pepper = b"pepper"
    minted = mint_api_key(pepper, env=ApiKeyEnv.TEST)

    assert verify_secret(pepper, minted.secret, minted.hash) is True


def test_verify_secret_when_wrong_secret_returns_false() -> None:
    pepper = b"pepper"
    minted = mint_api_key(pepper, env=ApiKeyEnv.SVC)

    assert verify_secret(pepper, "not-the-secret", minted.hash) is False


def test_parse_raw_key_when_well_formed_returns_parts() -> None:
    pepper = b"pepper"
    minted = mint_api_key(pepper, env=ApiKeyEnv.LIVE)
    env, prefix, secret = parse_raw_key(minted.raw)

    assert env is ApiKeyEnv.LIVE
    assert prefix == minted.prefix
    assert secret == minted.secret


def test_parse_raw_key_when_malformed_raises() -> None:
    with pytest.raises(ValueError, match="invalid api key"):
        parse_raw_key("sk_live_notours")
