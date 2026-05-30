"""Tests for the pure URL parsers in the source adapters."""
from __future__ import annotations

import pytest

from app.pipeline.sources import twitch, youtube


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.twitch.tv/videos/123456789", "123456789"),
        ("https://twitch.tv/videos/987", "987"),
        ("https://www.twitch.tv/somestreamer/video/555", "555"),
        ("123456789", "123456789"),  # bare id
        ("https://www.twitch.tv/somestreamer", None),  # live page, no VOD id
    ],
)
def test_twitch_parse_video_id(url, expected):
    assert twitch.parse_video_id(url) == expected


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/shorts/abcdefghijk", "abcdefghijk"),
        ("https://www.youtube.com/live/abcdefghijk", "abcdefghijk"),
        ("https://example.com/not-youtube", None),
    ],
)
def test_youtube_parse_video_id(url, expected):
    assert youtube.parse_video_id(url) == expected
