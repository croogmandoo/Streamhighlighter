"""PUBLISH stage — upload approved clips to connected platforms.

Runs after the user reviews/approves clips in the dashboard. Each PublishTarget
is processed independently so a failure on one platform doesn't block others.
OAuth tokens come from the web-owned ConnectedChannel table (decrypted here).
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Clip, Platform, PublishStatus, PublishTarget


def publish_job(job_id: str) -> str:
    with SessionLocal() as db:
        targets = _queued_targets(db, job_id)
        for target in targets:
            target.status = PublishStatus.UPLOADING
            db.commit()
            try:
                url = _dispatch(db, target)
                target.external_url = url
                target.status = PublishStatus.PUBLISHED
                target.clip.status = target.clip.status  # APPROVED → PUBLISHED below
            except Exception as exc:  # noqa: BLE001
                target.status = PublishStatus.FAILED
                target.error = f"{type(exc).__name__}: {exc}"
            db.commit()
    return job_id


def _queued_targets(db: Session, job_id: str) -> list[PublishTarget]:
    return list(
        db.scalars(
            select(PublishTarget)
            .join(Clip, Clip.id == PublishTarget.clip_id)
            .where(Clip.job_id == job_id, PublishTarget.status == PublishStatus.QUEUED)
        ).all()
    )


def _dispatch(db: Session, target: PublishTarget) -> str:
    handler = {
        Platform.YOUTUBE: _publish_youtube,
        Platform.TIKTOK: _publish_tiktok,
        Platform.INSTAGRAM: _publish_instagram,
    }[target.platform]
    return handler(db, target)


def _publish_youtube(db: Session, target: PublishTarget) -> str:
    """# TODO(milestone-4): YouTube Data API resumable upload (Shorts + re-cut)."""
    raise NotImplementedError("YouTube publish pending milestone 4")


def _publish_tiktok(db: Session, target: PublishTarget) -> str:
    """# TODO(milestone-4): TikTok Content Posting API."""
    raise NotImplementedError("TikTok publish pending milestone 4")


def _publish_instagram(db: Session, target: PublishTarget) -> str:
    """# TODO(milestone-4): Instagram Reels via Graph API."""
    raise NotImplementedError("Instagram publish pending milestone 4")
