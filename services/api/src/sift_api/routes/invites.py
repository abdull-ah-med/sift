"""Mint and accept HMAC tenant invite tokens."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text

from sift_api.audit_emit import emit_audit
from sift_api.auth import AuthContext, require_scopes
from sift_api.invites import mint_invite_token, verify_invite_token
from sift_api.schemas import InviteAcceptIn, InviteAcceptOut, InviteOut
from sift_api.settings import Settings, get_settings
from sift_api.tenant_session import begin_admin_session

router = APIRouter(prefix="/v1", tags=["invites"])


@router.post("/invites", response_model=InviteOut)
async def mint_invite(
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:write"))],
    settings: Annotated[Settings, Depends(get_settings)],
) -> InviteOut:
    """Mint an invite for the caller's current tenant."""
    if not settings.sift_api_key_pepper:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SIFT_API_KEY_PEPPER not configured",
        )
    token = mint_invite_token(tenant_id=ctx.tenant_id, pepper=settings.sift_api_key_pepper)
    emit_audit(
        tenant_id=ctx.tenant_id,
        actor=ctx.actor,
        action="invite.mint",
        target_kind="tenant",
        target_id=ctx.tenant_id,
        payload={},
    )
    return InviteOut(token=token, tenant_id=ctx.tenant_id)


@router.post("/invites/accept", response_model=InviteAcceptOut)
async def accept_invite(
    body: InviteAcceptIn,
    ctx: Annotated[AuthContext, Depends(require_scopes("chat"))],
    settings: Annotated[Settings, Depends(get_settings)],
) -> InviteAcceptOut:
    """Join the tenant encoded in ``body.token``. Requires an OIDC user_sub."""
    if not ctx.user_sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invite accept requires a user session",
        )
    if not settings.sift_api_key_pepper:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SIFT_API_KEY_PEPPER not configured",
        )
    try:
        tenant_id = verify_invite_token(token=body.token, pepper=settings.sift_api_key_pepper)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid invite token",
        ) from exc

    admin = await begin_admin_session()
    try:
        exists = (
            await admin.execute(
                text("SELECT 1 FROM tenants WHERE id = :id"),
                {"id": tenant_id},
            )
        ).scalar_one_or_none()
        if exists is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tenant not found")
        email = f"{ctx.user_sub}@users.local"
        await admin.execute(
            text(
                """
                INSERT INTO users_in_tenant (tenant_id, user_sub, email, role, created_at)
                VALUES (:tenant_id, :sub, :email, 'member', now())
                ON CONFLICT DO NOTHING
                """
            ),
            {"tenant_id": tenant_id, "sub": ctx.user_sub, "email": email},
        )
        await admin.commit()
    finally:
        await admin.close()

    emit_audit(
        tenant_id=tenant_id,
        actor=ctx.actor,
        action="invite.accept",
        target_kind="tenant",
        target_id=tenant_id,
        payload={},
    )
    return InviteAcceptOut(tenant_id=tenant_id, accepted=True)
