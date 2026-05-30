"""Twitch chat velocity & emote-spike signal.

Chat is a crowd-sourced highlight detector: when something big happens, messages
per second spike and hype emotes (LUL, OMEGALUL, PogChamp, KEKW) burst. Only
available for Twitch VODs with chat replay. Polarity +1.
"""
from __future__ import annotations

from app.pipeline.signals.base import SignalPoint

# Emotes that signal a hype/funny moment, weighted by strength.
HYPE_EMOTES: dict[str, float] = {
    "LUL": 1.0,
    "OMEGALUL": 1.3,
    "KEKW": 1.3,
    "PogChamp": 1.1,
    "Pog": 1.0,
    "POGGERS": 1.0,
    "LULW": 1.1,
}


class ChatVelocitySignal:
    name = "chat_velocity"
    polarity = 1

    def __init__(self, window_s: float = 5.0):
        self.window_s = window_s

    def extract(self, ctx, db) -> list[SignalPoint]:
        """# TODO(milestone-2): parse ctx.chat_path (Twitch chat replay JSON),
        bin messages into `window_s` buckets, and score each bucket by:
            rate_z   = z-score(messages_per_window)
            emote_z  = z-score(sum(HYPE_EMOTES[e] for e in emotes_in_window))
            score    = sigmoid(0.6*rate_z + 0.4*emote_z)
        Returns [] for non-Twitch VODs (no chat available).
        """
        if not ctx.chat_path:
            return []
        return []
