"""Pydantic v2 schemas for /v1 surface."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class WhoAmIResponse(StrictModel):
    tenant_id: str
    actor: str
    scopes: list[str]
    api_key_id: str | None = None
    user_sub: str | None = None


class OrganizationCreate(StrictModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=80)


class OrganizationOut(StrictModel):
    id: str
    name: str
    slug: str
    created_at: datetime


class TenantCreate(StrictModel):
    organization_id: str
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=80)


class TenantOut(StrictModel):
    id: str
    organization_id: str
    name: str
    slug: str
    created_at: datetime


class CollectionCreate(StrictModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=80)
    description: str | None = None


class CollectionOut(StrictModel):
    id: str
    tenant_id: str
    name: str
    slug: str
    description: str | None
    created_at: datetime


class ApiKeyCreate(StrictModel):
    name: str = Field(min_length=1, max_length=200)
    scopes: list[str] = Field(min_length=1)


class ApiKeyCreated(StrictModel):
    id: str
    name: str
    prefix: str
    scopes: list[str]
    raw_key: str


class ApiKeyOut(StrictModel):
    id: str
    name: str
    prefix: str
    scopes: list[str]
    created_at: datetime
    revoked_at: datetime | None = None


class UploadUrlRequest(StrictModel):
    filename: str = Field(min_length=1, max_length=512)
    content_type: str = Field(min_length=1, max_length=200)
    content_length: int = Field(gt=0, le=100 * 1024 * 1024)


class UploadUrlResponse(StrictModel):
    upload_url: str
    object_key: str
    bucket: str
    expires_in: int = 3600
    tus_endpoint: str | None = None
    upload_protocol: str = "s3-presigned"


class TusUploadRequest(StrictModel):
    filename: str = Field(min_length=1, max_length=512)
    content_type: str = Field(min_length=1, max_length=200)
    content_length: int = Field(gt=0, le=100 * 1024 * 1024)


class TusUploadResponse(StrictModel):
    tus_endpoint: str
    upload_url: str
    object_key: str
    doc_id: str
    metadata: dict[str, str]


class DocumentRegister(StrictModel):
    object_key: str
    title: str = Field(min_length=1, max_length=500)
    slug: str = Field(min_length=1, max_length=80)
    source_mime: str
    source_bytes: int = Field(gt=0)
    source_sha256: str = Field(min_length=64, max_length=64)


class DocumentOut(StrictModel):
    id: str
    collection_id: str
    title: str
    slug: str
    status: str
    source_uri: str
    created_at: datetime


class JobOut(StrictModel):
    id: str
    kind: str
    status: str
    document_id: str | None
    progress: float
    created_at: datetime


class AuditEventOut(StrictModel):
    event_id: str
    chain_index: int
    action: str
    actor: str
    target_kind: str
    target_id: str
    occurred_at: datetime
    payload: dict[str, Any]


class BlockOut(StrictModel):
    id: str
    document_id: str
    ordinal: int
    block_type: str
    text: str | None
    html: str | None
    provenance: dict[str, Any]
    confidence: float | None
    review_state: str
    version: int


class BlockPatch(StrictModel):
    text: str = Field(min_length=0, max_length=200_000)


class FinalizeOut(StrictModel):
    document_id: str
    status: str
    block_count: int
    chunk_count: int
    needs_review_count: int


class ReviewDecision(StrictModel):
    block_id: str = Field(min_length=1, max_length=64)
    action: str = Field(min_length=1, max_length=32)
    text: str | None = Field(default=None, max_length=200_000)


class ReviewResumeIn(StrictModel):
    decisions: list[ReviewDecision] = Field(min_length=1, max_length=500)


class ReviewGraphOut(StrictModel):
    thread_id: str
    document_id: str
    status: str
    pending_block_ids: list[str]
    block_batch: list[dict[str, Any]] | None = None


class SearchFilter(StrictModel):
    tags: list[str] | None = Field(default=None, max_length=50)
    document_ids: list[str] | None = Field(default=None, max_length=200)


class SearchRequest(StrictModel):
    query: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=10, ge=1, le=100)
    filter: SearchFilter | None = None
    include_text: bool = True
    include_provenance: bool = True
    rerank: bool = True


class SearchHitOut(StrictModel):
    chunk_id: str
    document_id: str
    document_title: str | None = None
    score: float
    rerank_score: float | None = None
    text: str | None = None
    section_path: list[str] | None = None
    page_numbers: list[int] | None = None
    block_ids: list[str] | None = None


class SearchResponse(StrictModel):
    results: list[SearchHitOut]
    trace_id: str


class VectorBackendRequest(StrictModel):
    backend: str = Field(pattern="^(pgvector|qdrant)$")


class VectorBackendOut(StrictModel):
    collection_id: str
    backend: str
    points: int = 0
    status: str = "ok"


class ChatSessionCreate(StrictModel):
    title: str | None = Field(default=None, max_length=200)


class ChatSessionOut(StrictModel):
    id: str
    collection_id: str
    title: str | None
    created_at: datetime
    last_message_at: datetime | None = None


class ChatTurnOut(StrictModel):
    id: str
    role: str
    content: str
    cited_chunk_ids: list[str] = Field(default_factory=list)
    cited_documents: list[str] = Field(default_factory=list)
    created_at: datetime


class ChatSessionDetail(ChatSessionOut):
    turns: list[ChatTurnOut] = Field(default_factory=list)
    rolling_summary: str | None = None


class ChatAskRequest(StrictModel):
    message: str = Field(min_length=1, max_length=8000)
    session_id: str | None = None
    top_k: int = Field(default=10, ge=1, le=50)


class ChatResumeRequest(StrictModel):
    session_id: str
    approve: bool = True
    text: str | None = Field(default=None, max_length=200_000)
    cited_chunk_ids: list[str] | None = None
    reject: bool = False
    reason: str | None = Field(default=None, max_length=2000)


class InviteAcceptIn(StrictModel):
    token: str = Field(min_length=8, max_length=500)


class InviteOut(StrictModel):
    token: str
    tenant_id: str


class InviteAcceptOut(StrictModel):
    tenant_id: str
    accepted: bool


class ChatCitationOut(StrictModel):
    chunk_id: str
    document_id: str
    text: str | None = None
    page_numbers: list[int] | None = None
    section_path: list[str] | None = None
