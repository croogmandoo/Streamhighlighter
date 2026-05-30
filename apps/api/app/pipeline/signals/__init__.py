"""Signal registry + the SIGNALS pipeline stage.

To add a signal: implement SignalExtractor in a new module and append an instance
to REGISTRY. Fusion (highlight.py) and selection (select.py) pick it up
automatically; give it a default weight in highlight.DEFAULT_WEIGHTS.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.pipeline.signals.audio_energy import AudioEnergySignal
from app.pipeline.signals.base import SignalExtractor, SignalPoint
from app.pipeline.signals.chat_velocity import ChatVelocitySignal
from app.pipeline.signals.llm_humor import LlmHumorSignal
from app.pipeline.signals.silence import SilenceSignal

# The four signals chosen for v1. Order is irrelevant; keyed by `.name`.
REGISTRY: list[SignalExtractor] = [
    SilenceSignal(),
    AudioEnergySignal(),
    ChatVelocitySignal(),
    LlmHumorSignal(),
]


def extract_signals(ctx, db: Session) -> None:
    """SIGNALS stage: run every registered extractor and stash results on ctx.

    Extractors are independent and could run in parallel (separate Celery tasks
    or a thread pool); kept sequential here for a clear scaffold.
    """
    results: dict[str, list[SignalPoint]] = {}
    for extractor in REGISTRY:
        results[extractor.name] = extractor.extract(ctx, db)
    ctx.signals = results


__all__ = ["REGISTRY", "extract_signals", "SignalExtractor", "SignalPoint"]
