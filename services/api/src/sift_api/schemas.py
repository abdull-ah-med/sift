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
