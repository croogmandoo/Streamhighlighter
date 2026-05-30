"""INGEST stage — obtain the source media (and chat) into object storage."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Source, Vod, VodStatus


def run(ctx, db: Session) -> None:
    vod: Vod = db.get(Vod, ctx.vod_id)
    vod.status = VodStatus.INGESTING
    db.commit()

    if vod.source == Source.UPLOAD:
        # File already PUT to storage via presigned URL; key is set on the vod.
        ctx.media_path = vod.storage_key
    elif vod.source == Source.TWITCH:
        ctx.media_path, ctx.chat_path = _pull_twitch(vod)
    elif vod.source == Source.YOUTUBE:
        ctx.media_path = _pull_youtube(vod)
    else:  # pragma: no cover - exhaustive
        raise ValueError(f"Unsupported source {vod.source}")

    vod.storage_key = ctx.media_path
    vod.chat_storage_key = ctx.chat_path
    db.commit()


def _pull_twitch(vod: Vod) -> tuple[str, str | None]:
    """Download a Twitch VOD + chat replay.

    # TODO(milestone-1): use Twitch Helix API to resolve the VOD, `yt-dlp` to
    # download video, and the comments endpoint for chat replay. Upload both to
    # object storage and return their keys.
    """
    raise NotImplementedError("Twitch ingest pending milestone 1")


def _pull_youtube(vod: Vod) -> str:
    """Download a YouTube VOD.

    # TODO(milestone-1): `yt-dlp` download honoring the user's OAuth grant for
    # private/unlisted VODs; upload and return the storage key.
    """
    raise NotImplementedError("YouTube ingest pending milestone 1")
