"""Thin, well-tested wrappers around the ffmpeg/ffprobe binaries.

Kept dependency-free (subprocess only) so the rest of the pipeline doesn't care
how media is probed or transcoded.
"""
from __future__ import annotations

import json
import shutil
import subprocess


class MediaError(RuntimeError):
    """ffmpeg/ffprobe failed or is unavailable."""


def _require(binary: str) -> str:
    path = shutil.which(binary)
    if not path:
        raise MediaError(f"`{binary}` not found on PATH — install ffmpeg")
    return path


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise MediaError(f"{args[0]} failed ({proc.returncode}): {proc.stderr.strip()[-500:]}")
    return proc


def probe_duration(path: str) -> float:
    """Return media duration in seconds via ffprobe."""
    ffprobe = _require("ffprobe")
    proc = _run([
        ffprobe, "-v", "quiet", "-print_format", "json", "-show_format", path,
    ])
    data = json.loads(proc.stdout)
    return float(data["format"]["duration"])


def extract_speech_wav(src: str, dst: str) -> str:
    """16 kHz mono PCM WAV — the format Whisper expects."""
    ffmpeg = _require("ffmpeg")
    _run([ffmpeg, "-y", "-i", src, "-vn", "-ac", "1", "-ar", "16000", "-f", "wav", dst])
    return dst


def extract_full_wav(src: str, dst: str) -> str:
    """Full-rate stereo WAV for loudness/energy analysis (milestone 2)."""
    ffmpeg = _require("ffmpeg")
    _run([ffmpeg, "-y", "-i", src, "-vn", "-c:a", "pcm_s16le", dst])
    return dst
