"""EXTRACT_AUDIO stage — derive audio tracks for transcription and analysis."""
from __future__ import annotations

import os

from sqlalchemy.orm import Session

from app.pipeline import media, storage


def run(ctx, db: Session) -> None:
    """Produce a 16 kHz mono WAV (for Whisper) and a full-rate WAV (for energy
    analysis). Both are kept locally for downstream stages and persisted to
    object storage for reprocessing.
    """
    if not ctx.local_media_path:
        raise ValueError("EXTRACT_AUDIO requires ctx.local_media_path from INGEST")

    speech = os.path.join(ctx.workdir, "speech.wav")
    full = os.path.join(ctx.workdir, "full.wav")
    media.extract_speech_wav(ctx.local_media_path, speech)
    media.extract_full_wav(ctx.local_media_path, full)

    ctx.local_speech_wav = speech
    ctx.local_full_wav = full
    ctx.audio_path = storage.upload_file(speech, storage.derived_key(ctx.vod_id, "speech.wav"))
    storage.upload_file(full, storage.derived_key(ctx.vod_id, "full.wav"))
