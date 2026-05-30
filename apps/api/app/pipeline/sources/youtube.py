"""YouTube VOD retrieval."""
from __future__ import annotations

import re

from app.pipeline.sources.ytdlp import DownloadResult, download

_ID_RE = re.compile(r"(?:v=|youtu\.be/|/shorts/|/live/)([A-Za-z0-9_-]{11})")


def parse_video_id(url: str) -> str | None:
    """Extract the 11-char YouTube video id from common URL shapes."""
    m = _ID_RE.search(url)
    return m.group(1) if m else None


def download_vod(url: str, out_dir: str) -> DownloadResult:
    # TODO(later): honor the user's YouTube OAuth grant for private/unlisted VODs.
    return download(url, out_dir)
