"""SELECT stage — turn the highlight curve into concrete clips.

Two outputs:
  * SHORTS: top non-overlapping peaks, 15-60s each, for vertical reframing.
  * RECUT:  keep-mask over the whole VOD with dead air / low-score stretches
            removed, preserving 16:9.

The interval math here is pure and unit-tested; persistence creates Clip rows.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import Clip, ClipKind
from app.pipeline.highlight import HighlightCell

SHORT_MIN_S = 15.0
SHORT_MAX_S = 60.0
SHORT_KEEP_THRESHOLD = 0.6   # a cell must beat this to seed/extend a short
RECUT_KEEP_THRESHOLD = 0.35  # below this, drop from the re-cut
MAX_SHORTS = 12


@dataclass
class Interval:
    t_start: float
    t_end: float
    score: float


def pick_shorts(
    curve: list[HighlightCell],
    *,
    min_s: float = SHORT_MIN_S,
    max_s: float = SHORT_MAX_S,
    threshold: float = SHORT_KEEP_THRESHOLD,
    limit: int = MAX_SHORTS,
) -> list[Interval]:
    """Greedy non-overlapping peak selection.

    Grow a candidate window around each above-threshold run, clamp to
    [min_s, max_s], then take the highest-scoring non-overlapping windows.
    """
    if not curve:
        return []

    # 1. Find contiguous runs above threshold.
    runs: list[Interval] = []
    cur: Interval | None = None
    for c in curve:
        if c.keep >= threshold:
            if cur is None:
                cur = Interval(c.t_start, c.t_end, c.keep)
            else:
                cur.t_end = c.t_end
                cur.score = max(cur.score, c.keep)
        elif cur is not None:
            runs.append(cur)
            cur = None
    if cur is not None:
        runs.append(cur)

    # 2. Clamp each run to the short length window (pad short ones around center).
    candidates: list[Interval] = []
    for r in runs:
        length = r.t_end - r.t_start
        if length < min_s:
            pad = (min_s - length) / 2
            r = Interval(max(0.0, r.t_start - pad), r.t_end + pad, r.score)
        elif length > max_s:
            center = (r.t_start + r.t_end) / 2
            r = Interval(center - max_s / 2, center + max_s / 2, r.score)
        candidates.append(r)

    # 3. Greedily take highest-scoring, non-overlapping.
    candidates.sort(key=lambda x: x.score, reverse=True)
    chosen: list[Interval] = []
    for cand in candidates:
        if all(cand.t_end <= s.t_start or cand.t_start >= s.t_end for s in chosen):
            chosen.append(cand)
        if len(chosen) >= limit:
            break

    chosen.sort(key=lambda x: x.t_start)
    return chosen


def build_recut(
    curve: list[HighlightCell], *, threshold: float = RECUT_KEEP_THRESHOLD
) -> list[Interval]:
    """Merge all above-threshold cells into the keep-mask for the tightened VOD."""
    kept: list[Interval] = []
    cur: Interval | None = None
    for c in curve:
        if c.keep >= threshold:
            if cur is None:
                cur = Interval(c.t_start, c.t_end, c.keep)
            else:
                cur.t_end = c.t_end
                cur.score = max(cur.score, c.keep)
        elif cur is not None:
            kept.append(cur)
            cur = None
    if cur is not None:
        kept.append(cur)
    return kept


def run(ctx, db: Session) -> None:
    """SELECT pipeline stage: persist Clip rows (storage_key filled by RENDER)."""
    curve = ctx.highlight_curve
    shorts = pick_shorts(curve)
    recut = build_recut(curve)
    ctx.selections = {"shorts": shorts, "recut": recut}

    for iv in shorts:
        db.add(Clip(
            job_id=ctx.job_id, kind=ClipKind.SHORT,
            t_start=iv.t_start, t_end=iv.t_end, score=iv.score,
        ))

    # The re-cut is one logical clip spanning the kept mask; RENDER stitches it.
    if recut:
        db.add(Clip(
            job_id=ctx.job_id, kind=ClipKind.RECUT,
            t_start=recut[0].t_start, t_end=recut[-1].t_end,
            score=sum(i.score for i in recut) / len(recut),
        ))
    db.commit()
