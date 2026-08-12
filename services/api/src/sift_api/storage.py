"""SeaweedFS S3 helpers — presigned PUT for Phase 1 uploads.

Plan called for tus; SeaweedFS is S3-native, so Phase 1 uses presigned PUT
(documented as a plan diff). Tus can wrap this later without changing object keys.
"""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import boto3
from botocore.client import Config

from sift_api.settings import Settings, get_settings


@dataclass(frozen=True, slots=True)
class PresignedUpload:
    upload_url: str
    object_key: str
    bucket: str
    expires_in: int = 3600


def _s3_client(settings: Settings) -> Any:
    return boto3.client(
        "s3",
        endpoint_url=settings.sift_storage_endpoint,
        aws_access_key_id=settings.sift_storage_access_key,
        aws_secret_access_key=settings.sift_storage_secret_key,
        region_name="us-east-1",
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def object_key_for(tenant_id: str, doc_id: str, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "bin"
    return f"t/{tenant_id}/d/{doc_id}/original.{ext}"


def tenant_object_key_prefix(tenant_id: str) -> str:
    """Return the Seaweed/S3 key prefix owned by ``tenant_id``."""
    return f"t/{tenant_id}/"


def object_key_belongs_to_tenant(object_key: str, tenant_id: str) -> bool:
    """True when ``object_key`` is under the tenant's storage prefix."""
    return object_key.startswith(tenant_object_key_prefix(tenant_id))


def create_presigned_put(
    *,
    tenant_id: str,
    doc_id: str,
    filename: str,
    content_type: str,
    settings: Settings | None = None,
    expires_in: int = 3600,
) -> PresignedUpload:
    cfg = settings or get_settings()
    key = object_key_for(tenant_id, doc_id, filename)
    client = _s3_client(cfg)
    # Ensure bucket exists (dev SeaweedFS starts empty).
    try:
        client.head_bucket(Bucket=cfg.sift_storage_bucket)
    except Exception:
        with suppress(Exception):
            client.create_bucket(Bucket=cfg.sift_storage_bucket)
    url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": cfg.sift_storage_bucket,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=expires_in,
    )
    return PresignedUpload(
        upload_url=url,
        object_key=key,
        bucket=cfg.sift_storage_bucket,
        expires_in=expires_in,
    )


def seaweed_uri(bucket: str, object_key: str) -> str:
    return f"seaweed://{bucket}/{object_key}"


def parse_seaweed_uri(uri: str) -> tuple[str, str]:
    """Split ``seaweed://bucket/key`` into ``(bucket, key)``."""
    prefix = "seaweed://"
    if not uri.startswith(prefix):
        raise ValueError(f"unsupported source_uri scheme: {uri!r}")
    rest = uri.removeprefix(prefix)
    bucket, sep, key = rest.partition("/")
    if not sep or not bucket or not key:
        raise ValueError(f"invalid seaweed uri: {uri!r}")
    return bucket, key


def download_object(
    *,
    source_uri: str,
    dest: Path,
    settings: Settings | None = None,
    tenant_id: str | None = None,
) -> Path:
    """Download ``source_uri`` from SeaweedFS/S3 to ``dest``.

    When ``tenant_id`` is set, refuse keys outside ``t/{tenant_id}/``.
    """
    cfg = settings or get_settings()
    bucket, key = parse_seaweed_uri(source_uri)
    if tenant_id is not None and not object_key_belongs_to_tenant(key, tenant_id):
        raise PermissionError(f"object key outside tenant prefix: {key!r}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    client = _s3_client(cfg)
    client.download_file(bucket, key, str(dest))
    return dest
