"""Transcript + LLM humor/engagement scoring.

Slides a window over the transcript and asks Claude to rate each window for
comedic payoff, story tension, and clip-worthiness. This is the signal that
understands *content* rather than just reaction. Polarity +1.
"""
from __future__ import annotations

from app.config import get_settings
from app.pipeline.signals.base import SignalPoint

SCORING_PROMPT = """\
You are an expert short-form video editor for a {genre} streamer. Below is a \
transcript window from a livestream VOD with timestamps. Rate how clip-worthy \
this window is for a TikTok/Shorts highlight on a 0-100 scale, considering: \
comedic payoff, surprise, story tension/resolution, and a strong opening hook.

Return STRICT JSON: {{"score": <0-100>, "hook": "<=8 word title>", "reason": "<one line>"}}.

Transcript:
{window}
"""


class LlmHumorSignal:
    name = "llm_humor"
    polarity = 1

    def __init__(self, window_s: float = 45.0, hop_s: float = 30.0, genre: str = "variety"):
        self.window_s = window_s
        self.hop_s = hop_s
        self.genre = genre

    def extract(self, ctx, db) -> list[SignalPoint]:
        """# TODO(milestone-2): window ctx.transcript, batch windows to Claude
        with prompt caching on the system preamble, parse JSON, and map score/100
        to [0,1]. Carry `hook` through meta so SELECT can title the clip.

        from anthropic import Anthropic
        client = Anthropic(api_key=get_settings().anthropic_api_key)
        # use claude-haiku for cheap bulk scoring, claude-opus to re-rank finalists
        """
        if not getattr(ctx.transcript, "segments", None):
            return []
        _ = get_settings().anthropic_api_key  # presence checked at integration time
        return []
