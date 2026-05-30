"""EXTRACT_AUDIO stage — pull audio tracks for transcription and analysis."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.pipeline import storage


def run(ctx, db: Session) -> None:
    """Produce a 16 kHz mono WAV (for Whisper) and keep a full-res track (for
    energy analysis). Both go to object storage; keys land on the context.

    # TODO(milestone-1): implement with ffmpeg, e.g.
    #   ffmpeg -i <media> -ac 1 -ar 16000 -vn speech.wav
    #   ffmpeg -i <media> -vn -c:a pcm_s16le full.wav
    """
    ctx.audio_path = storage.derived_key(ctx.vod_id, "speech.wav")
    # Real implementation downloads ctx.media_path, runs ffmpeg, uploads results.
