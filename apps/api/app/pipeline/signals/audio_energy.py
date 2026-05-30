"""Audio energy & laughter detection.

Loudness spikes, audience/streamer laughter, and speech-rate bursts correlate
strongly with highlight moments. Polarity +1.
"""
from __future__ import annotations

from app.pipeline.signals.base import SignalPoint


class AudioEnergySignal:
    name = "audio_energy"
    polarity = 1

    def extract(self, ctx, db) -> list[SignalPoint]:
        """# TODO(milestone-2): combine three sub-features into one score series:
          1. Short-time RMS energy spikes (z-scored loudness).
          2. Laughter detection — a lightweight audio classifier (e.g. a YAMNet
             head or a fine-tuned CNN) over 1s windows.
          3. Speech-rate from transcript word density (words/sec, z-scored).
        Normalize each to [0,1], take a weighted max/mean per window, emit
        SignalPoints over a sliding window (e.g. 5s hop).
        """
        return []
