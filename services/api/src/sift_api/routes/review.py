"""HITL block review HTTP routes (Phase 2)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from sift_api.audit_emit import emit_audit
from sift_api.auth import AuthContext, require_scopes, tenant_db
from sift_api.schemas import BlockOut, BlockPatch, FinalizeOut
from sift_core.ids import IdKind, new_id
from sift_core.models import ReviewState
from sift_core.review import (
    ReviewAction,
    ReviewTransitionError,
    document_ready_to_finalize,
    next_review_state,
)

router = APIRouter(prefix="/v1", tags=["review"])

_PAGE_SIZE = 50


def _row_to_block(row: Any) -> BlockOut:
    return BlockOut(
        id=row["id"],
        document_id=row["document_id"],
        ordinal=row["ordinal"],
        block_type=row["block_type"],
        text=row["text"],
        html=row["html"],
        provenance=dict(row["provenance"]),
        confidence=row["confidence"],
        review_state=row["review_state"],
        version=row["version"],
    )


async def _load_block(session: AsyncSession, block_id: str) -> Any:
    row = (
        (
            await session.execute(
                text(
                    """
                SELECT id, document_id, ordinal, block_type, text, html,
                       provenance, confidence, review_state, version
                FROM blocks WHERE id = :id
                """
                ),
                {"id": block_id},
            )
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="block not found")
    return row


async def _refresh_needs_review(session: AsyncSession, document_id: str) -> int:
    count = (
        await session.execute(
            text(
                """
                SELECT count(*) FROM blocks
                WHERE document_id = :doc_id
                  AND review_state IN ('pending', 'needs_review', 'in_review', 'conflict')
                """
            ),
            {"doc_id": document_id},
        )
    ).scalar_one()
    await session.execute(
        text(
            """
            UPDATE documents SET needs_review_count = :count
            WHERE id = :doc_id
            """
        ),
        {"count": int(count), "doc_id": document_id},
    )
    return int(count)


async def _apply_action(
    *,
    session: AsyncSession,
    ctx: AuthContext,
    block_id: str,
    action: ReviewAction,
    expected_version: int | None = None,
    new_text: str | None = None,
    reason: str | None = None,
) -> BlockOut:
    row = await _load_block(session, block_id)
    if expected_version is not None and int(row["version"]) != expected_version:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="version mismatch",
        )
    try:
        new_state = next_review_state(ReviewState(row["review_state"]), action)
    except ReviewTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    text_before = row["text"]
    text_after = new_text if new_text is not None else text_before
    revision_id = None
    if action is ReviewAction.EDIT:
        revision_id = new_id(IdKind.BLOCK_REVISION)
        await session.execute(
            text(
                """
                INSERT INTO block_revisions (
                  id, tenant_id, block_id, text_before, text_after,
                  diff_summary, action, actor_sub, reason
                ) VALUES (
                  :id, :tenant_id, :block_id, :before, :after,
                  :summary, 'edit', :actor, :reason
                )
                """
            ),
            {
                "id": revision_id,
                "tenant_id": ctx.tenant_id,
                "block_id": block_id,
                "before": text_before,
                "after": text_after,
                "summary": "text edit",
                "actor": ctx.actor,
                "reason": reason,
            },
        )

    result = (
        (
            await session.execute(
                text(
                    """
                UPDATE blocks
                SET review_state = :state,
                    text = :text,
                    version = version + 1,
                    latest_revision_id = COALESCE(:revision_id, latest_revision_id)
                WHERE id = :id AND version = :version
                RETURNING id, document_id, ordinal, block_type, text, html,
                          provenance, confidence, review_state, version
                """
                ),
                {
                    "state": new_state.value,
                    "text": text_after,
                    "revision_id": revision_id,
                    "id": block_id,
                    "version": int(row["version"]),
                },
            )
        )
        .mappings()
        .one_or_none()
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="version mismatch",
        )

    await _refresh_needs_review(session, result["document_id"])
    await session.commit()
    emit_audit(
        tenant_id=ctx.tenant_id,
        actor=ctx.actor,
        action=f"block.{action.value}",
        target_kind="block",
        target_id=block_id,
        payload={
            "document_id": result["document_id"],
            "from": row["review_state"],
            "to": new_state.value,
            "version": result["version"],
        },
    )
    return _row_to_block(result)


@router.get("/documents/{document_id}/blocks", response_model=list[BlockOut])
async def list_blocks(
    document_id: str,
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:read"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
    state: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
) -> list[BlockOut]:
    _ = ctx
    exists = (
        await session.execute(
            text("SELECT 1 FROM documents WHERE id = :id AND deleted_at IS NULL"),
            {"id": document_id},
        )
    ).scalar_one_or_none()
    if exists is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="document not found")

    offset = (page - 1) * _PAGE_SIZE
    if state:
        rows = (
            (
                await session.execute(
                    text(
                        """
                    SELECT id, document_id, ordinal, block_type, text, html,
                           provenance, confidence, review_state, version
                    FROM blocks
                    WHERE document_id = :doc_id AND review_state = :state
                    ORDER BY ordinal
                    LIMIT :limit OFFSET :offset
                    """
                    ),
                    {
                        "doc_id": document_id,
                        "state": state,
                        "limit": _PAGE_SIZE,
                        "offset": offset,
                    },
                )
            )
            .mappings()
            .all()
        )
    else:
        rows = (
            (
                await session.execute(
                    text(
                        """
                    SELECT id, document_id, ordinal, block_type, text, html,
                           provenance, confidence, review_state, version
                    FROM blocks
                    WHERE document_id = :doc_id
                    ORDER BY ordinal
                    LIMIT :limit OFFSET :offset
                    """
                    ),
                    {"doc_id": document_id, "limit": _PAGE_SIZE, "offset": offset},
                )
            )
            .mappings()
            .all()
        )
    return [_row_to_block(r) for r in rows]


@router.get("/blocks/{block_id}", response_model=BlockOut)
async def get_block(
    block_id: str,
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:read"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
) -> BlockOut:
    _ = ctx
    return _row_to_block(await _load_block(session, block_id))


@router.post("/blocks/{block_id}/claim", response_model=BlockOut)
async def claim_block(
    block_id: str,
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:write"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
) -> BlockOut:
    return await _apply_action(
        session=session, ctx=ctx, block_id=block_id, action=ReviewAction.CLAIM
    )


@router.post("/blocks/{block_id}/approve", response_model=BlockOut)
async def approve_block(
    block_id: str,
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:write"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
) -> BlockOut:
    return await _apply_action(
        session=session, ctx=ctx, block_id=block_id, action=ReviewAction.APPROVE
    )


@router.post("/blocks/{block_id}/reject", response_model=BlockOut)
async def reject_block(
    block_id: str,
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:write"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
) -> BlockOut:
    return await _apply_action(
        session=session, ctx=ctx, block_id=block_id, action=ReviewAction.REJECT
    )


@router.patch("/blocks/{block_id}", response_model=BlockOut)
async def patch_block(
    block_id: str,
    body: BlockPatch,
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:write"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> BlockOut:
    if if_match is None:
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail="If-Match header required",
        )
    try:
        expected = int(if_match.strip().strip('"'))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="If-Match must be an integer version",
        ) from exc
    return await _apply_action(
        session=session,
        ctx=ctx,
        block_id=block_id,
        action=ReviewAction.EDIT,
        expected_version=expected,
        new_text=body.text,
    )


@router.post("/documents/{document_id}/finalize", response_model=FinalizeOut)
async def finalize_document(
    document_id: str,
    ctx: Annotated[AuthContext, Depends(require_scopes("documents:write"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
) -> FinalizeOut:
    doc = (
        (
            await session.execute(
                text(
                    """
                SELECT id, status FROM documents
                WHERE id = :id AND deleted_at IS NULL
                """
                ),
                {"id": document_id},
            )
        )
        .mappings()
        .one_or_none()
    )
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="document not found")

    states = [
        ReviewState(r[0])
        for r in (
            await session.execute(
                text("SELECT review_state FROM blocks WHERE document_id = :id"),
                {"id": document_id},
            )
        ).all()
    ]
    if not document_ready_to_finalize(states):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="document still has blocks awaiting review",
        )

    needs = await _refresh_needs_review(session, document_id)
    await session.execute(
        text(
            """
            UPDATE documents SET status = 'indexing'
            WHERE id = :id
            """
        ),
        {"id": document_id},
    )
    await session.commit()
    emit_audit(
        tenant_id=ctx.tenant_id,
        actor=ctx.actor,
        action="document.finalize",
        target_kind="document",
        target_id=document_id,
        payload={"status": "indexing", "block_count": len(states)},
    )
    return FinalizeOut(
        document_id=document_id,
        status="indexing",
        block_count=len(states),
        needs_review_count=needs,
    )
