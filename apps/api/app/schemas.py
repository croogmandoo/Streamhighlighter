"""Pydantic request/response models — the public API contract."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models import (
    ClipKind,
    ClipStatus,
    Platform,
    PublishStatus,
    Source,
    Stage,
    VodStatus,
)


class CreateVodRequest(BaseModel):
    user_id: str
    source: Source
    source_url: str | None = None
    title: str | None = None
    weights_preset: str = "balanced"


class JobRef(BaseModel):
    job_id: str
    vod_id: str
    stage: Stage
    progress: float


class ClipOut(BaseModel):
    id: str
    kind: ClipKind
    t_start: float
    t_end: float
    title: str | None
    caption: str | None
    score: float
    status: ClipStatus
    storage_key: str | None

    class Config:
        from_attributes = True


class PublishTargetOut(BaseModel):
    id: str
    platform: Platform
    status: PublishStatus
    external_url: str | None
    error: str | None

    class Config:
        from_attributes = True


class JobOut(BaseModel):
    id: str
    vod_id: str
    stage: Stage
    progress: float
    weights_preset: str
    error: str | None
    created_at: datetime
    updated_at: datetime
    clips: list[ClipOut] = Field(default_factory=list)

    class Config:
        from_attributes = True


class VodOut(BaseModel):
    id: str
    source: Source
    source_url: str | None
    title: str | None
    duration_s: float | None
    status: VodStatus
    created_at: datetime

    class Config:
        from_attributes = True


class PresignUploadRequest(BaseModel):
    user_id: str
    filename: str
    content_type: str = "video/mp4"


class PresignUploadResponse(BaseModel):
    upload_url: str
    storage_key: str


class PublishRequest(BaseModel):
    clip_ids: list[str]
    platforms: list[Platform]
