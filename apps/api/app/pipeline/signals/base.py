"""Common types for highlight signal extraction.

Every signal extractor turns a VOD into a time series of scores over the
timeline. The fusion step (highlight.py) combines them. Adding a new signal means
implementing `SignalExtractor` and registering it — nothing else changes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class SignalPoint:
    """A scored interval on the VOD timeline.

    score is normalized to [0, 1]. For "keep" signals (energy, chat, humor)
    higher means more highlight-worthy. For "cut" signals (silence) higher means
    more likely dead air — the combiner inverts these via `polarity`.
    """
    t_start: float
    t_end: float
    score: float
    meta: dict = field(default_factory=dict)


@runtime_checkable
class SignalExtractor(Protocol):
    #: Stable identifier used as the weight key in fusion presets.
    name: str
    #: +1 for "keep" signals, -1 for "cut" signals (e.g. silence/dead air).
    polarity: int

    def extract(self, ctx, db) -> list[SignalPoint]:
        """Return scored intervals spanning the VOD timeline."""
        ...
