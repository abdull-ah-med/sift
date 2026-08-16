"""Invite token mint/verify (no live Postgres)."""

from __future__ import annotations

import pytest

from sift_api.invites import mint_invite_token, verify_invite_token


def test_mint_and_verify_round_trip() -> None:
    token = mint_invite_token(tenant_id="ten_abc", pepper="pepper-1")
    assert verify_invite_token(token=token, pepper="pepper-1") == "ten_abc"


def test_verify_rejects_wrong_pepper() -> None:
    token = mint_invite_token(tenant_id="ten_abc", pepper="pepper-1")
    with pytest.raises(ValueError, match="invalid"):
        verify_invite_token(token=token, pepper="pepper-2")


def test_verify_rejects_tampered_tenant() -> None:
    token = mint_invite_token(tenant_id="ten_abc", pepper="pepper-1")
    tampered = token.replace("ten_abc", "ten_evil", 1)
    with pytest.raises(ValueError, match="invalid"):
        verify_invite_token(token=tampered, pepper="pepper-1")
