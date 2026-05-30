"""API-owned ORM models: media & processing.

Identity/billing tables (User, Subscription, ConnectedChannel) are owned by the
web tier via Prisma. We only reference `users.id` by value; we do not map it here.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Source(str, enum.Enum):
    UPLOAD = "UPLOAD"
    TWITCH = "TWITCH"
    YOUTUBE = "YOUTUBE"


class VodStatus(str, enum.Enum):
    PENDING = "PENDING"
    INGESTING = "INGESTING"
    READY = "READY"
    FAILED = "FAILED"


class Stage(str, enum.Enum):
    """Pipeline state machine. Order matters — see pipeline/__init__.py."""
    INGEST = "INGEST"
    EXTRACT_AUDIO = "EXTRACT_AUDIO"
    TRANSCRIBE = "TRANSCRIBE"
    SIGNALS = "SIGNALS"
    SCORE = "SCORE"
    SELECT = "SELECT"
    RENDER = "RENDER"
    READY = "READY"
    PUBLISH = "PUBLISH"
    FAILED = "FAILED"


class ClipKind(str, enum.Enum):
    SHORT = "SHORT"    # vertical 9:16 short-form
    RECUT = "RECUT"    # tightened horizontal 16:9 full VOD


class ClipStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"


class Platform(str, enum.Enum):
    YOUTUBE = "YOUTUBE"
    TIKTOK = "TIKTOK"
    INSTAGRAM = "INSTAGRAM"


class PublishStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    UPLOADING = "UPLOADING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"


class Vod(Base):
    __tablename__ = "vods"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, index=True)
    source: Mapped[Source] = mapped_column(Enum(Source))
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    storage_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    chat_storage_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[VodStatus] = mapped_column(Enum(VodStatus), default=VodStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    jobs: Mapped[list["Job"]] = relationship(back_populates="vod", cascade="all, delete-orphan")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    vod_id: Mapped[str] = mapped_column(ForeignKey("vods.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    stage: Mapped[Stage] = mapped_column(Enum(Stage), default=Stage.INGEST)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    weights_preset: Mapped[str] = mapped_column(String, default="balanced")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    vod: Mapped[Vod] = relationship(back_populates="jobs")
    clips: Mapped[list["Clip"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    events: Mapped[list["PipelineEvent"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class Clip(Base):
    __tablename__ = "clips"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    kind: Mapped[ClipKind] = mapped_column(Enum(ClipKind))
    t_start: Mapped[float] = mapped_column(Float)
    t_end: Mapped[float] = mapped_column(Float)
    storage_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[ClipStatus] = mapped_column(Enum(ClipStatus), default=ClipStatus.DRAFT)

    job: Mapped[Job] = relationship(back_populates="clips")
    targets: Mapped[list["PublishTarget"]] = relationship(
        back_populates="clip", cascade="all, delete-orphan"
    )


class PublishTarget(Base):
    __tablename__ = "publish_targets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    clip_id: Mapped[str] = mapped_column(ForeignKey("clips.id", ondelete="CASCADE"), index=True)
    platform: Mapped[Platform] = mapped_column(Enum(Platform))
    status: Mapped[PublishStatus] = mapped_column(Enum(PublishStatus), default=PublishStatus.QUEUED)
    external_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    clip: Mapped[Clip] = relationship(back_populates="targets")


class PipelineEvent(Base):
    """Append-only progress/audit log; powers the live SSE feed."""
    __tablename__ = "pipeline_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    stage: Mapped[Stage] = mapped_column(Enum(Stage))
    level: Mapped[str] = mapped_column(String, default="info")
    message: Mapped[str] = mapped_column(Text)
    data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job: Mapped[Job] = relationship(back_populates="events")
