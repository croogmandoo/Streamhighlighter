"""SCORE stage — fuse per-signal time series into one highlight curve.

The curve is sampled on a fixed grid over the VOD timeline. For each grid cell we
combine the active signals with preset weights; "cut" signals (polarity -1) push
the keep-score down, "keep" signals push it up. Output is a list of
`(t_start, t_end, keep_score in [0,1])` cells consumed by SELECT.

This module is pure/deterministic and unit-tested — no external services.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.pipeline.signals import REGISTRY
from app.pipeline.signals.base import SignalPoint

GRID_S = 1.0  # highlight-curve resolution in seconds

# Weight presets. Each maps a signal name → weight; missing signals default to 0.
DEFAULT_WEIGHTS: dict[str, dict[str, float]] = {
    "balanced": {"silence": 1.0, "audio_energy": 1.0, "chat_velocity": 1.0, "llm_humor": 1.2},
    "chaos":    {"silence": 1.0, "audio_energy": 1.5, "chat_velocity": 1.6, "llm_humor": 0.8},
    "storytime":{"silence": 1.2, "audio_energy": 0.7, "chat_velocity": 0.6, "llm_humor": 1.8},
}


@dataclass
class HighlightCell:
    t_start: float
    t_end: float
    keep: float  # [0, 1]


def _polarity(name: str) -> int:
    for ex in REGISTRY:
        if ex.name == name:
            return ex.polarity
    return 1


def _value_at(points: list[SignalPoint], t: float) -> float:
    """Score of whichever interval covers time t (0 if none)."""
    for p in points:
        if p.t_start <= t < p.t_end:
            return p.score
    return 0.0


def fuse(
    signals: dict[str, list[SignalPoint]],
    duration_s: float,
    weights: dict[str, float],
    grid_s: float = GRID_S,
) -> list[HighlightCell]:
    """Combine signals into a normalized keep-curve. Pure function."""
    if duration_s <= 0:
        return []

    cells: list[HighlightCell] = []
    n = int(duration_s // grid_s) + 1
    for i in range(n):
        t0 = i * grid_s
        t1 = min(t0 + grid_s, duration_s)
        mid = (t0 + t1) / 2

        num = 0.0
        denom = 0.0
        for name, w in weights.items():
            if w == 0:
                continue
            v = _value_at(signals.get(name, []), mid)
            # Cut signals contribute (1 - v) so dead air drives keep toward 0.
            contribution = (1.0 - v) if _polarity(name) < 0 else v
            num += w * contribution
            denom += w

        keep = (num / denom) if denom else 0.0
        cells.append(HighlightCell(t_start=t0, t_end=t1, keep=max(0.0, min(1.0, keep))))

    return cells


def resolve_weights(preset: str) -> dict[str, float]:
    return DEFAULT_WEIGHTS.get(preset, DEFAULT_WEIGHTS["balanced"])


def score_job(ctx, db: Session) -> None:
    """SCORE pipeline stage: build the highlight curve onto ctx."""
    from app.models import Vod

    vod = db.get(Vod, ctx.vod_id)
    duration = vod.duration_s or 0.0
    weights = resolve_weights(ctx.weights_preset)
    ctx.highlight_curve = fuse(ctx.signals, duration, weights)
