"""Tests for the pure transcript helpers (serialization + content hashing)."""
from __future__ import annotations

from app.pipeline.transcribe import Transcript, TranscriptSegment, _sha256


def test_transcript_json_roundtrip():
    t = Transcript(segments=[
        TranscriptSegment(0.0, 2.5, "hello"),
        TranscriptSegment(2.5, 4.0, "world"),
    ])
    restored = Transcript.from_json(t.to_json())
    assert restored.segments == t.segments


def test_text_between_filters_by_window():
    t = Transcript(segments=[
        TranscriptSegment(0.0, 1.0, "a"),
        TranscriptSegment(1.0, 2.0, "b"),
        TranscriptSegment(5.0, 6.0, "c"),
    ])
    assert t.text_between(0.0, 2.0) == "a b"


def test_sha256_is_stable_and_content_dependent(tmp_path):
    p1 = tmp_path / "a.bin"
    p2 = tmp_path / "b.bin"
    p1.write_bytes(b"same")
    p2.write_bytes(b"same")
    assert _sha256(str(p1)) == _sha256(str(p2))
    p2.write_bytes(b"different")
    assert _sha256(str(p1)) != _sha256(str(p2))
