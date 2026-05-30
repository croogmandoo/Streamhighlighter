"""RENDER stage — cut/encode the selected clips with ffmpeg."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Clip, ClipKind
from app.pipeline import storage


def run(ctx, db: Session) -> None:
    clips = db.scalars(select(Clip).where(Clip.job_id == ctx.job_id)).all()
    for clip in clips:
        key = storage.derived_key(ctx.vod_id, f"{clip.kind.value.lower()}_{clip.id}.mp4")
        if clip.kind == ClipKind.SHORT:
            _render_short(ctx, clip, key)
        else:
            _render_recut(ctx, clip, key)
        clip.storage_key = key
    db.commit()


def _render_short(ctx, clip: Clip, out_key: str) -> None:
    """Vertical 9:16 short with burned captions and a hook title.

    # TODO(milestone-3): download source, ffmpeg trim [t_start, t_end], reframe
    # to 1080x1920 (speaker/cam crop), burn captions from transcript, add hook
    # overlay, upload to out_key. Example:
    #   ffmpeg -ss {t0} -to {t1} -i src.mp4 \
    #     -vf "crop=ih*9/16:ih,scale=1080:1920,subtitles=caps.srt" \
    #     -c:v libx264 -c:a aac out.mp4
    """


def _render_recut(ctx, clip: Clip, out_key: str) -> None:
    """Tightened 16:9 VOD: concat the kept intervals from SELECT.

    # TODO(milestone-3): build an ffmpeg concat/segment filter from
    # ctx.selections["recut"], encode, upload to out_key.
    """


def render_job(job_id: str) -> str:
    """Standalone task entrypoint (queue=render) for retryable rendering."""
    return job_id
