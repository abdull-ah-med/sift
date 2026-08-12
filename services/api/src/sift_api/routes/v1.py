"""Phase 1 /v1 HTTP routes."""

from __future__ import annotations

import asyncio
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.background import BackgroundTask
from starlette.responses import FileResponse

from sift_api.audit_emit import emit_audit
from sift_api.auth import AuthContext, get_auth_context, require_scopes, tenant_db
from sift_api.schemas import (
    ApiKeyCreate,
    ApiKeyCreated,
    ApiKeyOut,
    AuditEventOut,
    CollectionCreate,
    CollectionOut,
    DocumentOut,
    DocumentRegister,
    JobOut,
    OrganizationCreate,
    OrganizationOut,
    TenantCreate,
    TenantOut,
    TusUploadRequest,
    TusUploadResponse,
    UploadUrlRequest,
    UploadUrlResponse,
    WhoAmIResponse,
)
from sift_api.settings import Settings, get_settings
from sift_api.storage import create_presigned_put, download_object, parse_seaweed_uri, seaweed_uri
from sift_api.tenant_session import begin_admin_session
from sift_core.auth.api_keys import mint_api_key
from sift_core.db import tenant_guc_statements
from sift_core.ids import IdKind, new_id

router = APIRouter(prefix="/v1", tags=["v1"])


def _file_content_allowed(path: Path, settings: Settings) -> bool:
    """Return True when ``path`` is under an allow-listed root (tests/dev)."""
    if not settings.sift_allow_file_content:
        return False
    try:
        resolved = path.resolve()
    except OSError:
        return False
    env_root = os.environ.get("SIFT_FILE_CONTENT_ROOT")
    if not env_root:
        return False
    root = Path(env_root).resolve()
    return resolved == root or root in resolved.parents


@router.get("/whoami", response_model=WhoAmIResponse)
async def whoami(ctx: Annotated[AuthContext, Depends(get_auth_context)]) -> WhoAmIResponse:
    return WhoAmIResponse(
        tenant_id=ctx.tenant_id,
        actor=ctx.actor,
        scopes=sorted(ctx.scopes),
        api_key_id=ctx.api_key_id,
        user_sub=ctx.user_sub,
    )


@router.post("/organizations", response_model=OrganizationOut)
async def create_organization(
    body: OrganizationCreate,
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:write"))],
) -> OrganizationOut:
    # Org create is cross-tenant; use admin role.
    org_id = new_id(IdKind.ORGANIZATION)
    session = await begin_admin_session()
    try:
        now = datetime.now(UTC)
        await session.execute(
            text(
                """
                INSERT INTO organizations (id, name, slug, created_at)
                VALUES (:id, :name, :slug, :created_at)
                """
            ),
            {"id": org_id, "name": body.name, "slug": body.slug, "created_at": now},
        )
        await session.commit()
        return OrganizationOut(id=org_id, name=body.name, slug=body.slug, created_at=now)
    finally:
        await session.close()


@router.get("/organizations", response_model=list[OrganizationOut])
async def list_organizations(
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:read"))],
) -> list[OrganizationOut]:
    session = await begin_admin_session()
    try:
        rows = (
            (
                await session.execute(
                    text(
                        """
                    SELECT id, name, slug, created_at FROM organizations
                    WHERE deleted_at IS NULL ORDER BY created_at
                    """
                    )
                )
            )
            .mappings()
            .all()
        )
        return [
            OrganizationOut(id=r["id"], name=r["name"], slug=r["slug"], created_at=r["created_at"])
            for r in rows
        ]
    finally:
        await session.close()


@router.post("/tenants", response_model=TenantOut)
async def create_tenant(
    body: TenantCreate,
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:write"))],
) -> TenantOut:
    tenant_id = new_id(IdKind.TENANT)
    session = await begin_admin_session()
    try:
        now = datetime.now(UTC)
        await session.execute(
            text(
                """
                INSERT INTO tenants (id, organization_id, name, slug, created_at)
                VALUES (:id, :org, :name, :slug, :created_at)
                """
            ),
            {
                "id": tenant_id,
                "org": body.organization_id,
                "name": body.name,
                "slug": body.slug,
                "created_at": now,
            },
        )
        await session.commit()
        emit_audit(
            tenant_id=tenant_id,
            actor=ctx.actor,
            action="tenant.create",
            target_kind="tenant",
            target_id=tenant_id,
            payload={"tenant_name": body.name, "created_by": ctx.actor},
        )
        return TenantOut(
            id=tenant_id,
            organization_id=body.organization_id,
            name=body.name,
            slug=body.slug,
            created_at=now,
        )
    finally:
        await session.close()


@router.get("/tenants", response_model=list[TenantOut])
async def list_tenants(
    ctx: Annotated[AuthContext, Depends(get_auth_context)],
    session: Annotated[AsyncSession, Depends(tenant_db)],
) -> list[TenantOut]:
    rows = (
        (
            await session.execute(
                text(
                    """
                SELECT id, organization_id, name, slug, created_at
                FROM tenants WHERE deleted_at IS NULL
                """
                )
            )
        )
        .mappings()
        .all()
    )
    return [
        TenantOut(
            id=r["id"],
            organization_id=r["organization_id"],
            name=r["name"],
            slug=r["slug"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


@router.post("/collections", response_model=CollectionOut)
async def create_collection(
    body: CollectionCreate,
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:write"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
) -> CollectionOut:
    col_id = new_id(IdKind.COLLECTION)
    now = datetime.now(UTC)
    await session.execute(
        text(
            """
            INSERT INTO collections (id, tenant_id, name, slug, description, created_at)
            VALUES (:id, :tenant_id, :name, :slug, :description, :created_at)
            """
        ),
        {
            "id": col_id,
            "tenant_id": ctx.tenant_id,
            "name": body.name,
            "slug": body.slug,
            "description": body.description,
            "created_at": now,
        },
    )
    await session.flush()
    emit_audit(
        tenant_id=ctx.tenant_id,
        actor=ctx.actor,
        action="collection.create",
        target_kind="collection",
        target_id=col_id,
        payload={"name": body.name, "slug": body.slug},
    )
    return CollectionOut(
        id=col_id,
        tenant_id=ctx.tenant_id,
        name=body.name,
        slug=body.slug,
        description=body.description,
        created_at=now,
    )


@router.get("/collections", response_model=list[CollectionOut])
async def list_collections(
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:read"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
) -> list[CollectionOut]:
    rows = (
        (
            await session.execute(
                text(
                    """
                SELECT id, tenant_id, name, slug, description, created_at
                FROM collections WHERE deleted_at IS NULL ORDER BY created_at
                """
                )
            )
        )
        .mappings()
        .all()
    )
    return [
        CollectionOut(
            id=r["id"],
            tenant_id=r["tenant_id"],
            name=r["name"],
            slug=r["slug"],
            description=r["description"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


@router.get("/collections/{collection_id}", response_model=CollectionOut)
async def get_collection(
    collection_id: str,
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:read"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
) -> CollectionOut:
    r = (
        (
            await session.execute(
                text(
                    """
                SELECT id, tenant_id, name, slug, description, created_at
                FROM collections WHERE id = :id AND deleted_at IS NULL
                """
                ),
                {"id": collection_id},
            )
        )
        .mappings()
        .one_or_none()
    )
    if r is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    return CollectionOut(
        id=r["id"],
        tenant_id=r["tenant_id"],
        name=r["name"],
        slug=r["slug"],
        description=r["description"],
        created_at=r["created_at"],
    )


@router.delete("/collections/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: str,
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:write"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
) -> None:
    await session.execute(
        text(
            """
            UPDATE collections SET deleted_at = :now
            WHERE id = :id AND deleted_at IS NULL
            """
        ),
        {"id": collection_id, "now": datetime.now(UTC)},
    )


@router.post("/api-keys", response_model=ApiKeyCreated)
async def create_api_key(
    body: ApiKeyCreate,
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:write"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ApiKeyCreated:
    if not settings.sift_api_key_pepper:
        raise HTTPException(status_code=503, detail="SIFT_API_KEY_PEPPER not configured")
    minted = mint_api_key(settings.sift_api_key_pepper.encode("utf-8"))
    key_id = new_id(IdKind.API_KEY)
    now = datetime.now(UTC)
    await session.execute(
        text(
            """
            INSERT INTO api_keys (
              id, tenant_id, name, hash, hash_version, prefix, scopes,
              created_by, created_at
            ) VALUES (
              :id, :tenant_id, :name, :hash, :hash_version, :prefix, :scopes,
              :created_by, :created_at
            )
            """
        ),
        {
            "id": key_id,
            "tenant_id": ctx.tenant_id,
            "name": body.name,
            "hash": minted.hash,
            "hash_version": minted.hash_version,
            "prefix": minted.prefix,
            "scopes": body.scopes,
            "created_by": ctx.actor,
            "created_at": now,
        },
    )
    await session.flush()
    emit_audit(
        tenant_id=ctx.tenant_id,
        actor=ctx.actor,
        action="api_key.create",
        target_kind="api_key",
        target_id=key_id,
        payload={"name": body.name, "scopes": body.scopes, "prefix": minted.prefix},
    )
    return ApiKeyCreated(
        id=key_id,
        name=body.name,
        prefix=minted.prefix,
        scopes=body.scopes,
        raw_key=minted.raw,
    )


@router.get("/api-keys", response_model=list[ApiKeyOut])
async def list_api_keys(
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:read"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
) -> list[ApiKeyOut]:
    rows = (
        (
            await session.execute(
                text(
                    """
                SELECT id, name, prefix, scopes, created_at, revoked_at
                FROM api_keys ORDER BY created_at DESC
                """
                )
            )
        )
        .mappings()
        .all()
    )
    return [
        ApiKeyOut(
            id=r["id"],
            name=r["name"],
            prefix=r["prefix"],
            scopes=list(r["scopes"] or []),
            created_at=r["created_at"],
            revoked_at=r["revoked_at"],
        )
        for r in rows
    ]


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:write"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
) -> None:
    await session.execute(
        text(
            """
            UPDATE api_keys SET revoked_at = :now
            WHERE id = :id AND revoked_at IS NULL
            """
        ),
        {"id": key_id, "now": datetime.now(UTC)},
    )


@router.post(
    "/collections/{collection_id}/documents/upload-url",
    response_model=UploadUrlResponse,
)
async def create_upload_url(
    collection_id: str,
    body: UploadUrlRequest,
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:write"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UploadUrlResponse:
    exists = (
        await session.execute(
            text("SELECT 1 FROM collections WHERE id = :id AND deleted_at IS NULL"),
            {"id": collection_id},
        )
    ).scalar_one_or_none()
    if exists is None:
        raise HTTPException(status_code=404, detail="collection not found")
    doc_id = new_id(IdKind.DOCUMENT)
    upload = create_presigned_put(
        tenant_id=ctx.tenant_id,
        doc_id=doc_id,
        filename=body.filename,
        content_type=body.content_type,
        settings=settings,
    )
    # Stash pending doc id in object key; client must pass object_key on register.
    return UploadUrlResponse(
        upload_url=upload.upload_url,
        object_key=upload.object_key,
        bucket=upload.bucket,
        expires_in=upload.expires_in,
        tus_endpoint=settings.sift_tus_url,
        upload_protocol="s3-presigned",
    )


@router.post(
    "/collections/{collection_id}/documents/tus",
    response_model=TusUploadResponse,
)
async def create_tus_upload(
    collection_id: str,
    body: TusUploadRequest,
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:write"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TusUploadResponse:
    """Return a tus endpoint + reserved object key for resumable upload."""
    exists = (
        await session.execute(
            text("SELECT 1 FROM collections WHERE id = :id AND deleted_at IS NULL"),
            {"id": collection_id},
        )
    ).scalar_one_or_none()
    if exists is None:
        raise HTTPException(status_code=404, detail="collection not found")
    doc_id = new_id(IdKind.DOCUMENT)
    from sift_api.storage import object_key_for

    key = object_key_for(ctx.tenant_id, doc_id, body.filename)
    endpoint = settings.sift_tus_url.rstrip("/") + "/"
    return TusUploadResponse(
        tus_endpoint=endpoint,
        upload_url=endpoint,
        object_key=key,
        doc_id=doc_id,
        metadata={
            "filename": body.filename,
            "filetype": body.content_type,
            "tenant_id": ctx.tenant_id,
            "doc_id": doc_id,
            "object_key": key,
        },
    )


@router.post("/collections/{collection_id}/documents", response_model=DocumentOut)
async def register_document(
    collection_id: str,
    body: DocumentRegister,
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:write"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> DocumentOut:
    exists = (
        await session.execute(
            text("SELECT 1 FROM collections WHERE id = :id AND deleted_at IS NULL"),
            {"id": collection_id},
        )
    ).scalar_one_or_none()
    if exists is None:
        raise HTTPException(status_code=404, detail="collection not found")
    # object key: t/{tenant}/d/{doc_id}/original.ext
    parts = body.object_key.split("/")
    _object_key_min_parts = 4
    doc_id = parts[3] if len(parts) >= _object_key_min_parts else new_id(IdKind.DOCUMENT)
    job_id = new_id(IdKind.JOB)
    now = datetime.now(UTC)
    source_uri = seaweed_uri(settings.sift_storage_bucket, body.object_key)
    await session.execute(
        text(
            """
            INSERT INTO documents (
              id, tenant_id, collection_id, title, slug, source_uri, source_mime,
              source_bytes, source_sha256, status, created_by, created_at
            ) VALUES (
              :id, :tenant_id, :collection_id, :title, :slug, :source_uri, :source_mime,
              :source_bytes, :source_sha256, 'queued', :created_by, :created_at
            )
            """
        ),
        {
            "id": doc_id,
            "tenant_id": ctx.tenant_id,
            "collection_id": collection_id,
            "title": body.title,
            "slug": body.slug,
            "source_uri": source_uri,
            "source_mime": body.source_mime,
            "source_bytes": body.source_bytes,
            "source_sha256": body.source_sha256,
            "created_by": ctx.actor,
            "created_at": now,
        },
    )
    await session.execute(
        text(
            """
            INSERT INTO jobs (
              id, tenant_id, collection_id, document_id, kind, status, progress, created_at
            ) VALUES (
              :id, :tenant_id, :collection_id, :document_id, 'ingest', 'queued', 0, :created_at
            )
            """
        ),
        {
            "id": job_id,
            "tenant_id": ctx.tenant_id,
            "collection_id": collection_id,
            "document_id": doc_id,
            "created_at": now,
        },
    )
    # Commit so the worker (separate connection) can see queued rows.
    await session.commit()
    emit_audit(
        tenant_id=ctx.tenant_id,
        actor=ctx.actor,
        action="document.register",
        target_kind="document",
        target_id=doc_id,
        payload={"collection_id": collection_id, "job_id": job_id},
    )
    # Worker is the sole parse path — enqueue only; never run ingest inline.
    from sift_api.tasks import ingest_document

    try:
        await ingest_document.kiq(doc_id, job_id, ctx.tenant_id)
    except Exception as exc:
        # Commit cleared SET LOCAL role/GUC — rebind before compensating deletes.
        conn = await session.connection()
        await conn.execute(text("SET LOCAL ROLE sift_app"))
        for stmt in tenant_guc_statements(ctx.tenant_id):
            await conn.execute(text(stmt))
        await session.execute(
            text("DELETE FROM jobs WHERE id = :id AND tenant_id = :tid"),
            {"id": job_id, "tid": ctx.tenant_id},
        )
        await session.execute(
            text("DELETE FROM documents WHERE id = :id AND tenant_id = :tid"),
            {"id": doc_id, "tid": ctx.tenant_id},
        )
        await session.commit()
        emit_audit(
            tenant_id=ctx.tenant_id,
            actor=ctx.actor,
            action="document.register_enqueue_failed",
            target_kind="document",
            target_id=doc_id,
            payload={"collection_id": collection_id, "job_id": job_id},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ingest enqueue unavailable",
        ) from exc
    return DocumentOut(
        id=doc_id,
        collection_id=collection_id,
        title=body.title,
        slug=body.slug,
        status="queued",
        source_uri=source_uri,
        created_at=now,
    )


@router.get("/collections/{collection_id}/documents", response_model=list[DocumentOut])
async def list_documents(
    collection_id: str,
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:read"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
) -> list[DocumentOut]:
    rows = (
        (
            await session.execute(
                text(
                    """
                SELECT id, collection_id, title, slug, status, source_uri, created_at
                FROM documents
                WHERE collection_id = :cid AND deleted_at IS NULL
                ORDER BY created_at DESC
                """
                ),
                {"cid": collection_id},
            )
        )
        .mappings()
        .all()
    )
    return [
        DocumentOut(
            id=r["id"],
            collection_id=r["collection_id"],
            title=r["title"],
            slug=r["slug"],
            status=r["status"],
            source_uri=r["source_uri"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


@router.get("/documents/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: str,
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:read"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
) -> DocumentOut:
    r = (
        (
            await session.execute(
                text(
                    """
                SELECT id, collection_id, title, slug, status, source_uri, created_at
                FROM documents WHERE id = :id AND deleted_at IS NULL
                """
                ),
                {"id": document_id},
            )
        )
        .mappings()
        .one_or_none()
    )
    if r is None:
        raise HTTPException(status_code=404, detail="not found")
    return DocumentOut(
        id=r["id"],
        collection_id=r["collection_id"],
        title=r["title"],
        slug=r["slug"],
        status=r["status"],
        source_uri=r["source_uri"],
        created_at=r["created_at"],
    )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:write"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
) -> None:
    await session.execute(
        text(
            """
            UPDATE documents SET deleted_at = :now, status = 'archived'
            WHERE id = :id AND deleted_at IS NULL
            """
        ),
        {"id": document_id, "now": datetime.now(UTC)},
    )


@router.get("/documents/{document_id}/content")
async def document_content(
    document_id: str,
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:read"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Response:
    """Stream the source PDF for the review viewer (Phase 2 §4.4)."""
    row = (
        (
            await session.execute(
                text(
                    """
                    SELECT source_uri, source_mime
                    FROM documents
                    WHERE id = :id AND deleted_at IS NULL
                    """
                ),
                {"id": document_id},
            )
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")

    source_uri = str(row["source_uri"])
    media_type = str(row["source_mime"] or "application/pdf")
    cleanup: BackgroundTask | None = None

    if source_uri.startswith("file://"):
        path = Path(source_uri.removeprefix("file://"))
        if not path.is_file() or not _file_content_allowed(path, settings):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="content missing")
    elif source_uri.startswith("seaweed://"):
        try:
            _bucket, key = parse_seaweed_uri(source_uri)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="invalid source uri",
            ) from exc
        tenant_prefix = f"t/{ctx.tenant_id}/"
        if not key.startswith(tenant_prefix):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="content missing")
        fd, tmp_name = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        tmp_path = Path(tmp_name)
        try:
            await asyncio.to_thread(download_object, source_uri=source_uri, dest=tmp_path)
        except Exception as exc:
            tmp_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="failed to fetch document content",
            ) from exc
        path = tmp_path

        def _cleanup(p: Path = tmp_path) -> None:
            p.unlink(missing_ok=True)

        cleanup = BackgroundTask(_cleanup)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="unsupported source uri",
        )

    return FileResponse(
        path,
        media_type=media_type,
        filename=path.name,
        background=cleanup,
    )


@router.get("/jobs/{job_id}", response_model=JobOut)
async def get_job(
    job_id: str,
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:read"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
) -> JobOut:
    r = (
        (
            await session.execute(
                text(
                    """
                SELECT id, kind, status, document_id, progress, created_at
                FROM jobs WHERE id = :id
                """
                ),
                {"id": job_id},
            )
        )
        .mappings()
        .one_or_none()
    )
    if r is None:
        raise HTTPException(status_code=404, detail="not found")
    return JobOut(
        id=r["id"],
        kind=r["kind"],
        status=r["status"],
        document_id=r["document_id"],
        progress=float(r["progress"]),
        created_at=r["created_at"],
    )


@router.get("/audit/events", response_model=list[AuditEventOut])
async def list_audit_events(
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:read"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
) -> list[AuditEventOut]:
    rows = (
        (
            await session.execute(
                text(
                    """
                SELECT event_id, chain_index, action, actor, target_kind, target_id,
                       occurred_at, payload
                FROM audit_events
                ORDER BY chain_index DESC
                LIMIT 100
                """
                )
            )
        )
        .mappings()
        .all()
    )
    return [
        AuditEventOut(
            event_id=r["event_id"],
            chain_index=int(r["chain_index"]),
            action=r["action"],
            actor=r["actor"],
            target_kind=r["target_kind"],
            target_id=r["target_id"],
            occurred_at=r["occurred_at"],
            payload=dict(r["payload"] or {}),
        )
        for r in rows
    ]
