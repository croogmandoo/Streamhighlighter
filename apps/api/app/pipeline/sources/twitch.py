"""Twitch VOD retrieval + chat-replay download.

VOD video/audio comes via yt-dlp. Chat replay isn't available through yt-dlp, so
we page Twitch's public GraphQL `VideoCommentsByOffsetOrCursor` query (the same
one the web player uses) with the public web client id. Chat is optional: any
failure (chat disabled, deleted VOD) degrades gracefully to "no chat".
"""
from __future__ import annotations

import json
import re

from app.config import get_settings
from app.pipeline.sources.ytdlp import DownloadResult, download

_ID_RE = re.compile(r"twitch\.tv/(?:videos/|\w+/video/)(\d+)")

GQL_URL = "https://gql.twitch.tv/gql"
# Persisted-query hash for VideoCommentsByOffsetOrCursor (stable, public).
_COMMENTS_HASH = "b70a3591ff0f4e0313d126c6a1502d79a1c02baebb288227c582044aa76adf6a"


def parse_video_id(url: str) -> str | None:
    """Extract the numeric Twitch VOD id from a URL (or accept a bare id)."""
    if url.isdigit():
        return url
    m = _ID_RE.search(url)
    return m.group(1) if m else None


def download_vod(url: str, out_dir: str) -> DownloadResult:
    return download(url, out_dir, fmt="best")


def download_chat(video_id: str) -> list[dict]:
    """Return chat-replay comments as a flat list of
    `{offset, user, message, fragments}` ordered by stream offset seconds.

    Raises on transport errors; callers treat chat as optional and catch.
    """
    import httpx  # lazy

    client_id = get_settings().twitch_gql_client_id
    headers = {"Client-ID": client_id, "Content-Type": "application/json"}

    comments: list[dict] = []
    cursor: str | None = None
    with httpx.Client(timeout=30) as http:
        while True:
            variables: dict = {"videoID": video_id}
            if cursor:
                variables["cursor"] = cursor
            else:
                variables["contentOffsetSeconds"] = 0

            body = [{
                "operationName": "VideoCommentsByOffsetOrCursor",
                "variables": variables,
                "extensions": {
                    "persistedQuery": {"version": 1, "sha256Hash": _COMMENTS_HASH}
                },
            }]
            resp = http.post(GQL_URL, headers=headers, content=json.dumps(body))
            resp.raise_for_status()
            page = resp.json()[0]["data"]["video"]["comments"]

            for edge in page["edges"]:
                node = edge["node"]
                frags = node["message"]["fragments"]
                comments.append({
                    "offset": node["contentOffsetSeconds"],
                    "user": (node.get("commenter") or {}).get("displayName"),
                    "message": "".join(f.get("text", "") for f in frags),
                    "fragments": frags,
                })

            if not page["pageInfo"]["hasNextPage"] or not page["edges"]:
                break
            cursor = page["edges"][-1]["cursor"]

    comments.sort(key=lambda c: c["offset"])
    return comments
