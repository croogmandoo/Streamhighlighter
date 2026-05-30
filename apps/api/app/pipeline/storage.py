"""S3-compatible object storage helpers (AWS S3 / Cloudflare R2 / MinIO).

The DB stores only keys; media bytes live here. Browser uploads use presigned
PUT URLs so large files never transit our API.
"""
from __future__ import annotations

import functools
import uuid

import boto3

from app.config import get_settings


@functools.lru_cache
def _client():
    s = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=s.storage_endpoint or None,
        region_name=s.storage_region,
        aws_access_key_id=s.storage_access_key_id,
        aws_secret_access_key=s.storage_secret_access_key,
    )


def upload_key(user_id: str, filename: str) -> str:
    return f"uploads/{user_id}/{uuid.uuid4()}/{filename}"


def derived_key(vod_id: str, name: str) -> str:
    """Key for a pipeline-derived artifact (audio, clip, recut)."""
    return f"derived/{vod_id}/{name}"


def presign_put(key: str, content_type: str, expires: int = 3600) -> str:
    s = get_settings()
    return _client().generate_presigned_url(
        "put_object",
        Params={"Bucket": s.storage_bucket, "Key": key, "ContentType": content_type},
        ExpiresIn=expires,
    )


def presign_get(key: str, expires: int = 3600) -> str:
    s = get_settings()
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": s.storage_bucket, "Key": key},
        ExpiresIn=expires,
    )


def download_to(key: str, local_path: str) -> str:
    s = get_settings()
    _client().download_file(s.storage_bucket, key, local_path)
    return local_path


def upload_file(local_path: str, key: str, content_type: str | None = None) -> str:
    s = get_settings()
    extra = {"ContentType": content_type} if content_type else None
    _client().upload_file(local_path, s.storage_bucket, key, ExtraArgs=extra)
    return key


def exists(key: str) -> bool:
    """True if an object with this key is present (used for transcript caching)."""
    s = get_settings()
    try:
        _client().head_object(Bucket=s.storage_bucket, Key=key)
        return True
    except Exception:  # noqa: BLE001 — boto raises ClientError(404) for missing keys
        return False


def put_bytes(key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    s = get_settings()
    _client().put_object(Bucket=s.storage_bucket, Key=key, Body=data, ContentType=content_type)
    return key


def get_bytes(key: str) -> bytes:
    s = get_settings()
    return _client().get_object(Bucket=s.storage_bucket, Key=key)["Body"].read()
