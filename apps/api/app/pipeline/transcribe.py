"""TRANSCRIBE stage — word/segment-level transcript via Whisper.

Backend via TRANSCRIBE_BACKEND:
  - "local":  faster-whisper (install the `transcribe` extra)
  - "openai": OpenAI Whisper API

Results are cached in object storage keyed by the SHA-256 of the speech WAV, so
re-running a job (or reprocessing the same media) skips transcription entirely.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.config import get_settings
from app.pipeline import storage


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

    def to_json(self) -> str:
        return json.dumps([dataclasses.asdict(s) for s in self.segments])

    @classmethod
    def from_json(cls, raw: bytes | str) -> "Transcript":
        rows = json.loads(raw)
        return cls(segments=[TranscriptSegment(**r) for r in rows])


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(ctx, db: Session) -> None:
    if not ctx.local_speech_wav:
        raise ValueError("TRANSCRIBE requires ctx.local_speech_wav from EXTRACT_AUDIO")

    cache_key = f"transcripts/{_sha256(ctx.local_speech_wav)}.json"
    if storage.exists(cache_key):
        ctx.transcript = Transcript.from_json(storage.get_bytes(cache_key))
        return

    backend = get_settings().transcribe_backend
    transcript = (
        _transcribe_openai(ctx.local_speech_wav)
        if backend == "openai"
        else _transcribe_local(ctx.local_speech_wav)
    )
    ctx.transcript = transcript
    storage.put_bytes(cache_key, transcript.to_json().encode(), content_type="application/json")


def _transcribe_local(wav_path: str) -> Transcript:
    from faster_whisper import WhisperModel  # lazy; needs the `transcribe` extra

    s = get_settings()
    model = WhisperModel(s.whisper_model, device=s.whisper_device, compute_type=s.whisper_compute_type)
    segments, _info = model.transcribe(wav_path, word_timestamps=True)
    return Transcript(
        segments=[TranscriptSegment(t_start=seg.start, t_end=seg.end, text=seg.text.strip())
                  for seg in segments]
    )


def _transcribe_openai(wav_path: str) -> Transcript:
    from openai import OpenAI  # lazy; needs the `transcribe` extra

    client = OpenAI(api_key=get_settings().openai_api_key)
    with open(wav_path, "rb") as f:
        resp = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )
    return Transcript(
        segments=[TranscriptSegment(t_start=s.start, t_end=s.end, text=s.text.strip())
                  for s in resp.segments]
    )


def transcribe_job(job_id: str) -> str:
    """Standalone task entrypoint (queue=gpu) for retryable transcription."""
    return job_id
