"""Silence / dead-air detection.

Marks stretches where RMS loudness sits below a threshold for longer than
`min_silence_s`. Polarity is -1: these intervals push the keep-score *down* and
are the primary driver of the dead-air removal in the re-cut.
"""
from __future__ import annotations

from app.pipeline.signals.base import SignalPoint


class SilenceSignal:
    name = "silence"
    polarity = -1

    def __init__(self, threshold_db: float = -40.0, min_silence_s: float = 1.5):
        self.threshold_db = threshold_db
        self.min_silence_s = min_silence_s

    def extract(self, ctx, db) -> list[SignalPoint]:
        """# TODO(milestone-2): compute short-time RMS over ctx full-res audio,
        threshold at `threshold_db`, and merge runs longer than `min_silence_s`
        into SignalPoints with score=1.0 (definite dead air).

        Reference approach (librosa):
            import librosa, numpy as np
            y, sr = librosa.load(audio, sr=None, mono=True)
            rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
            db = librosa.amplitude_to_db(rms)
            quiet = db < self.threshold_db
            # group consecutive quiet frames > min_silence_s → SignalPoint(score=1)
        """
        return []
