"""Request auth: API key (ADR-0013) and optional Zitadel JWT."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from sift_api.settings import Settings, get_settings
from sift_api.tenant_session import begin_admin_session, begin_tenant_session
from sift_core.auth.api_keys import parse_raw_key, verify_secret


@dataclass(frozen=True, slots=True)
class AuthContext:
    tenant_id: str
    actor: str
    scopes: frozenset[str]
    api_key_id: str | None = None
    user_sub: str | None = None


def require_scopes(*needed: str):
    """Dependency factory: require all listed scopes on the auth context."""

    async def _dep(ctx: Annotated[AuthContext, Depends(get_auth_context)]) -> AuthContext:
        missing = [s for s in needed if s not in ctx.scopes]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"missing scopes: {', '.join(missing)}",
            )
        return ctx

    return _dep


async def get_auth_context(
    settings: Annotated[Settings, Depends(get_settings)],
    x_api_key: Annotated[str | None, Header(alias="X-Api-Key")] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> AuthContext:
    """Resolve caller from API key or Bearer JWT."""
    if x_api_key:
        return await _auth_from_api_key(x_api_key, settings)
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        return await _auth_from_jwt(token, settings)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="missing credentials",
    )


async def _auth_from_api_key(raw: str, settings: Settings) -> AuthContext:
    if not settings.sift_api_key_pepper:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SIFT_API_KEY_PEPPER not configured",
        )
    try:
        _env, prefix, secret = parse_raw_key(raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid api key",
        ) from exc

    pepper = settings.sift_api_key_pepper.encode("utf-8")
    # Lookup by prefix under admin (need cross-check before tenant GUC known).
    session = await begin_admin_session()
    try:
        row = (
            await session.execute(
                text(
                    """
                    SELECT id, tenant_id, hash, scopes, revoked_at, expires_at
                    FROM api_keys
                    WHERE prefix = :prefix
                    ORDER BY created_at DESC
                    LIMIT 5
                    """
                ),
                {"prefix": prefix},
            )
        ).mappings().all()
        match = None
        for candidate in row:
            if verify_secret(pepper, secret, bytes(candidate["hash"])):
                match = candidate
                break
        if match is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid api key")
        if match["revoked_at"] is not None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="api key revoked")
        expires = match["expires_at"]
        if expires is not None and expires <= datetime.now(UTC):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="api key expired")
        await session.execute(
            text("UPDATE api_keys SET last_used_at = now() WHERE id = :id"),
            {"id": match["id"]},
        )
        await session.commit()
        return AuthContext(
            tenant_id=match["tenant_id"],
            actor=f"key:{match['id']}",
            scopes=frozenset(match["scopes"] or []),
            api_key_id=match["id"],
        )
    finally:
        await session.close()


async def _auth_from_jwt(token: str, settings: Settings) -> AuthContext:
    if not settings.sift_zitadel_issuer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT auth requires SIFT_ZITADEL_ISSUER",
        )
    # Lazy import — JWT path optional until Zitadel is configured.
    import jwt
    from jwt import PyJWKClient

    jwks_url = settings.sift_zitadel_issuer.rstrip("/") + "/oauth/v2/keys"
    jwks = PyJWKClient(jwks_url)
    try:
        signing_key = jwks.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            audience=settings.sift_zitadel_audience,
            issuer=settings.sift_zitadel_issuer,
            options={"require": ["exp", "iat", "sub"]},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid token",
        ) from exc

    sub = str(claims["sub"])
    session = await begin_admin_session()
    try:
        membership = (
            await session.execute(
                text(
                    """
                    SELECT tenant_id, role FROM users_in_tenant
                    WHERE user_sub = :sub
                    ORDER BY created_at ASC
                    LIMIT 1
                    """
                ),
                {"sub": sub},
            )
        ).mappings().one_or_none()
        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="no tenant membership",
            )
        # Map tenant role to a default scope set for interactive users.
        scopes = frozenset(
            {
                "documents:read",
                "documents:write",
                "search",
                "vault:read",
                "export",
                "chat",
            }
        )
        return AuthContext(
            tenant_id=membership["tenant_id"],
            actor=f"user:{sub}",
            scopes=scopes,
            user_sub=sub,
        )
    finally:
        await session.close()


async def tenant_db(
    ctx: Annotated[AuthContext, Depends(get_auth_context)],
) -> AsyncIterator[AsyncSession]:
    """DB session bound to the authenticated tenant."""
    session = await begin_tenant_session(ctx.tenant_id)
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
