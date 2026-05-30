"""yt-dlp wrapper shared by the Twitch/YouTube source adapters.

`yt_dlp` is imported lazily so importing the adapters (e.g. for unit-testing the
pure URL parsers) doesn't require the dependency.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class DownloadResult:
    path: str
    duration_s: float | None
    title: str | None


def download(url: str, out_dir: str, fmt: str = "best[ext=mp4]/best") -> DownloadResult:
    """Download a single VOD into out_dir; return its local path + metadata."""
    import yt_dlp  # lazy

    opts = {
        "format": fmt,
        "outtmpl": os.path.join(out_dir, "source.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        path = ydl.prepare_filename(info)

    return DownloadResult(
        path=path,
        duration_s=float(info["duration"]) if info.get("duration") else None,
        title=info.get("title"),
    )
