"""Celery app + task entrypoints.

Tasks are thin wrappers; the real orchestration lives in `app.pipeline`. Heavy
stages are routed to dedicated queues so GPU and render work scale separately.
"""
from __future__ import annotations

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "streamhighlighter",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.conf.update(
    task_track_started=True,
    task_routes={
        "app.worker.run_transcribe": {"queue": "gpu"},
        "app.worker.run_render": {"queue": "render"},
    },
)


@celery_app.task(name="app.worker.run_pipeline", bind=True, max_retries=2)
def run_pipeline(self, job_id: str) -> str:
    """Advance a job through the editing pipeline to READY."""
    from app.pipeline.orchestrator import run_job

    return run_job(job_id)


@celery_app.task(name="app.worker.run_transcribe")
def run_transcribe(job_id: str) -> str:
    from app.pipeline.transcribe import transcribe_job

    return transcribe_job(job_id)


@celery_app.task(name="app.worker.run_render")
def run_render(job_id: str) -> str:
    from app.pipeline.render import render_job

    return render_job(job_id)


@celery_app.task(name="app.worker.run_publish")
def run_publish(job_id: str) -> str:
    from app.pipeline.publish import publish_job

    return publish_job(job_id)
