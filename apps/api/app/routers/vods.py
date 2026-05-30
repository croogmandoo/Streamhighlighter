"""VOD creation + upload presigning. All routes require the internal secret."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_internal_secret
from app.models import Job, Stage, Vod, VodStatus
from app.pipeline import storage
from app.schemas import (
    CreateVodRequest,
    JobRef,
    PresignUploadRequest,
    PresignUploadResponse,
    VodOut,
)
from app.worker import run_pipeline

router = APIRouter(prefix="/v1/vods", tags=["vods"], dependencies=[Depends(require_internal_secret)])


@router.post("", response_model=JobRef)
def create_vod(payload: CreateVodRequest, db: Session = Depends(get_db)) -> JobRef:
    """Create a VOD + its first job, then enqueue the pipeline."""
    vod = Vod(
        user_id=payload.user_id,
        source=payload.source,
        source_url=payload.source_url,
        title=payload.title,
        status=VodStatus.PENDING,
    )
    db.add(vod)
    db.flush()

    job = Job(
        vod_id=vod.id,
        user_id=payload.user_id,
        stage=Stage.INGEST,
        weights_preset=payload.weights_preset,
    )
    db.add(job)
    db.commit()

    # Hand off to the worker pool; the pipeline runs asynchronously.
    run_pipeline.delay(job.id)

    return JobRef(job_id=job.id, vod_id=vod.id, stage=job.stage, progress=job.progress)


@router.post("/presign-upload", response_model=PresignUploadResponse)
def presign_upload(payload: PresignUploadRequest) -> PresignUploadResponse:
    """Mint a presigned PUT URL so the browser can upload directly to storage."""
    key = storage.upload_key(payload.user_id, payload.filename)
    url = storage.presign_put(key, payload.content_type)
    return PresignUploadResponse(upload_url=url, storage_key=key)


@router.get("/{vod_id}", response_model=VodOut)
def get_vod(vod_id: str, db: Session = Depends(get_db)) -> Vod:
    return db.get(Vod, vod_id)
