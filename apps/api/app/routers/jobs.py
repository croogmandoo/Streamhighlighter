"""Job status, live event stream, and publishing."""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal, get_db
from app.deps import require_internal_secret
from app.models import Clip, ClipStatus, Job, PipelineEvent, PublishStatus, PublishTarget
from app.schemas import JobOut, PublishRequest
from app.worker import run_publish

router = APIRouter(prefix="/v1/jobs", tags=["jobs"], dependencies=[Depends(require_internal_secret)])


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/{job_id}/events")
async def stream_events(job_id: str) -> StreamingResponse:
    """Server-Sent Events feed of pipeline progress for the dashboard."""

    async def event_gen():
        last_id = 0
        while True:
            with SessionLocal() as db:
                rows = db.scalars(
                    select(PipelineEvent)
                    .where(PipelineEvent.job_id == job_id, PipelineEvent.id > last_id)
                    .order_by(PipelineEvent.id)
                ).all()
                terminal = False
                for ev in rows:
                    last_id = ev.id
                    payload = {
                        "stage": ev.stage.value,
                        "level": ev.level,
                        "message": ev.message,
                        "data": ev.data,
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
                    if ev.stage.value in ("READY", "FAILED"):
                        terminal = True
                if terminal:
                    return
            await asyncio.sleep(1.0)

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@router.post("/{job_id}/publish")
def publish(job_id: str, payload: PublishRequest, db: Session = Depends(get_db)) -> dict:
    """Approve selected clips and enqueue publishing to the chosen platforms."""
    clips = db.scalars(
        select(Clip).where(Clip.id.in_(payload.clip_ids), Clip.job_id == job_id)
    ).all()
    if not clips:
        raise HTTPException(status_code=404, detail="No matching clips for job")

    for clip in clips:
        clip.status = ClipStatus.APPROVED
        for platform in payload.platforms:
            db.add(PublishTarget(clip_id=clip.id, platform=platform, status=PublishStatus.QUEUED))
    db.commit()

    run_publish.delay(job_id)
    return {"queued": len(clips) * len(payload.platforms)}
