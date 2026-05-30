"""FastAPI entrypoint."""
from __future__ import annotations

from fastapi import FastAPI

from app import __version__
from app.routers import jobs, vods

app = FastAPI(
    title="StreamHighlighter API",
    version=__version__,
    description="VOD ingestion + AI editing pipeline.",
)

app.include_router(vods.router)
app.include_router(jobs.router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}
