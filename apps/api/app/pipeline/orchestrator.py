"""Pipeline orchestrator — the job state machine.

`run_job` walks a VOD through stages in order. Each stage function takes a
`PipelineContext`, does its work, and returns. Stages are idempotent and emit
`pipeline_events` for progress; failures mark the job FAILED and re-raise.

    INGEST → EXTRACT_AUDIO → TRANSCRIBE → SIGNALS → SCORE → SELECT → RENDER → READY
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Job, PipelineEvent, Stage, VodStatus
from app.pipeline import audio, ingest, render, select as select_stage, transcribe
from app.pipeline.highlight import score_job
from app.pipeline.signals import extract_signals


@dataclass
class PipelineContext:
    """Mutable bag carried across stages for one job run."""
    job_id: str
    vod_id: str
    user_id: str
    weights_preset: str
    # Populated as stages run:
    media_path: str | None = None
    audio_path: str | None = None
    chat_path: str | None = None
    transcript: object | None = None
    signals: dict = field(default_factory=dict)
    highlight_curve: list = field(default_factory=list)
    selections: dict = field(default_factory=dict)


def emit(db: Session, job_id: str, stage: Stage, message: str, *, level: str = "info", data=None) -> None:
    db.add(PipelineEvent(job_id=job_id, stage=stage, level=level, message=message, data=data))
    db.commit()


def _set_stage(db: Session, job: Job, stage: Stage, progress: float) -> None:
    job.stage = stage
    job.progress = progress
    db.commit()


# Ordered (stage, handler, progress-after) tuples. Handlers receive (ctx, db).
STAGES: list[tuple[Stage, Callable, float]] = [
    (Stage.INGEST, ingest.run, 0.15),
    (Stage.EXTRACT_AUDIO, audio.run, 0.25),
    (Stage.TRANSCRIBE, transcribe.run, 0.45),
    (Stage.SIGNALS, extract_signals, 0.65),
    (Stage.SCORE, score_job, 0.75),
    (Stage.SELECT, select_stage.run, 0.85),
    (Stage.RENDER, render.run, 0.98),
]


def run_job(job_id: str) -> str:
    """Synchronously drive a job through every stage. Called by the Celery task."""
    with SessionLocal() as db:
        job = db.get(Job, job_id)
        if job is None:
            raise ValueError(f"Job {job_id} not found")

        ctx = PipelineContext(
            job_id=job.id,
            vod_id=job.vod_id,
            user_id=job.user_id,
            weights_preset=job.weights_preset,
        )

        try:
            for stage, handler, progress in STAGES:
                _set_stage(db, job, stage, progress)
                emit(db, job.id, stage, f"Starting {stage.value}")
                handler(ctx, db)
                emit(db, job.id, stage, f"Completed {stage.value}", data={"progress": progress})

            _set_stage(db, job, Stage.READY, 1.0)
            job.vod.status = VodStatus.READY
            db.commit()
            emit(db, job.id, Stage.READY, "Pipeline complete — clips ready for review")
            return "READY"

        except Exception as exc:  # noqa: BLE001 — record then re-raise for Celery retry
            db.rollback()
            job = db.get(Job, job_id)
            job.stage = Stage.FAILED
            job.error = f"{type(exc).__name__}: {exc}"
            job.vod.status = VodStatus.FAILED
            db.commit()
            emit(db, job_id, Stage.FAILED, job.error, level="error")
            raise
