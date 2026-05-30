"""TRANSCRIBE stage — word-level transcript via Whisper.

Backend selectable via TRANSCRIBE_BACKEND:
  - "local":  faster-whisper on GPU (queue=gpu)
  - "openai": OpenAI Whisper API
Results are cached by content hash so re-runs are free.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.config import get_settings


@dataclass
class TranscriptSegment:
    t_start: float
    t_end: float
    text: str


@dataclass
class Transcript:
    segments: list[TranscriptSegment] = field(default_factory=list)

    def text_between(self, t0: float, t1: float) -> str:
        return " ".join(s.text for s in self.segments if s.t_start >= t0 and s.t_end <= t1)


def run(ctx, db: Session) -> None:
    backend = get_settings().transcribe_backend
    if backend == "openai":
        ctx.transcript = _transcribe_openai(ctx.audio_path)
    else:
        ctx.transcript = _transcribe_local(ctx.audio_path)


def transcribe_job(job_id: str) -> str:
    """Standalone task entrypoint (queue=gpu) for retryable transcription."""
    # TODO(milestone-1): load job/ctx, run transcription, persist transcript.
    return job_id


def _transcribe_local(audio_key: str | None) -> Transcript:
    """# TODO(milestone-1): faster-whisper.

    from faster_whisper import WhisperModel
    model = WhisperModel("large-v3", device="cuda", compute_type="float16")
    segments, _ = model.transcribe(local_wav, word_timestamps=True)
    """
    return Transcript(segments=[])


def _transcribe_openai(audio_key: str | None) -> Transcript:
    """# TODO(milestone-1): OpenAI Whisper API with verbose_json timestamps."""
    return Transcript(segments=[])
