"""INGEST stage — obtain source media (and Twitch chat) into object storage.

After this stage:
  * `ctx.local_media_path` points at a local working copy of the video,
  * `vod.storage_key` references the durable copy in object storage,
  * `vod.duration_s` is populated,
  * `ctx.chat_path` is set for Twitch VODs that have a chat replay.
"""
from __future__ import annotations

import json
import os

from sqlalchemy.orm import Session

from app.models import Source, Vod, VodStatus
from app.pipeline import media, storage
from app.pipeline.sources import twitch, youtube


def run(ctx, db: Session) -> None:
    vod: Vod = db.get(Vod, ctx.vod_id)
    vod.status = VodStatus.INGESTING
    db.commit()

    if vod.source == Source.UPLOAD:
        _ingest_upload(ctx, vod)
    elif vod.source == Source.TWITCH:
        _ingest_twitch(ctx, vod, db)
    elif vod.source == Source.YOUTUBE:
        _ingest_youtube(ctx, vod)
    else:  # pragma: no cover - exhaustive
        raise ValueError(f"Unsupported source {vod.source}")

    if not vod.duration_s and ctx.local_media_path:
        vod.duration_s = media.probe_duration(ctx.local_media_path)
    db.commit()


def _ingest_upload(ctx, vod: Vod) -> None:
    """The browser already PUT the file to vod.storage_key via a presigned URL."""
    if not vod.storage_key:
        raise ValueError("UPLOAD vod has no storage_key; presign+upload must run first")
    local = os.path.join(ctx.workdir, "source")
    storage.download_to(vod.storage_key, local)
    ctx.local_media_path = local
    ctx.media_path = vod.storage_key


def _ingest_twitch(ctx, vod: Vod, db: Session) -> None:
    video_id = twitch.parse_video_id(vod.source_url or "")
    if not video_id:
        raise ValueError(f"Could not parse Twitch video id from {vod.source_url!r}")

    result = twitch.download_vod(vod.source_url, ctx.workdir)
    ctx.local_media_path = result.path
    vod.title = vod.title or result.title
    vod.duration_s = result.duration_s
    vod.storage_key = storage.upload_file(result.path, storage.derived_key(vod.id, "source.mp4"))
    ctx.media_path = vod.storage_key

    _try_download_chat(ctx, vod, db, video_id)


def _ingest_youtube(ctx, vod: Vod) -> None:
    result = youtube.download_vod(vod.source_url, ctx.workdir)
    ctx.local_media_path = result.path
    vod.title = vod.title or result.title
    vod.duration_s = result.duration_s
    vod.storage_key = storage.upload_file(result.path, storage.derived_key(vod.id, "source.mp4"))
    ctx.media_path = vod.storage_key


def _try_download_chat(ctx, vod: Vod, db: Session, video_id: str) -> None:
    """Chat is an optional signal: failures degrade gracefully to 'no chat'."""
    from app.pipeline.orchestrator import emit
    from app.models import Stage

    try:
        comments = twitch.download_chat(video_id)
    except Exception as exc:  # noqa: BLE001
        emit(db, ctx.job_id, Stage.INGEST, f"Chat replay unavailable: {exc}", level="warn")
        return

    key = storage.derived_key(vod.id, "chat.json")
    storage.put_bytes(key, json.dumps(comments).encode(), content_type="application/json")
    vod.chat_storage_key = key
    ctx.chat_path = key
    emit(db, ctx.job_id, Stage.INGEST, f"Downloaded {len(comments)} chat messages")
