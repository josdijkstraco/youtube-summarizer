import logging
import re
from urllib.parse import ParseResult, parse_qs, urlparse

import httpx

from app.models import VideoMetadata

logger = logging.getLogger(__name__)

# Regex to extract YouTube video IDs from common URL formats
_VIDEO_ID_PATTERN = re.compile(
    r"(?:youtube\.com/(?:watch\?.*v=|shorts/)|youtu\.be/)"
    r"([a-zA-Z0-9_-]{11})"
)


def extract_video_id(url: str) -> str:
    """Extract a YouTube video ID from a URL.

    Supports youtube.com/watch, youtu.be, youtube.com/shorts, and m.youtube.com formats.

    Raises:
        ValueError: If the URL is empty, not a YouTube URL, or is a playlist-only URL.
    """
    url = url.strip()
    if not url:
        raise ValueError("URL must not be empty")

    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    # Check for playlist-only URL (has list= but no v=)
    if _is_playlist_only(parsed, query_params):
        raise ValueError(
            "Playlist URLs are not supported. Please provide a single video URL."
        )

    match = _VIDEO_ID_PATTERN.search(url)
    if not match:
        raise ValueError(
            "The provided URL is not a valid YouTube video URL. "
            "Supported formats: youtube.com/watch?v=..., "
            "youtu.be/..., youtube.com/shorts/..."
        )

    return match.group(1)


def get_video_metadata(video_id: str) -> VideoMetadata:
    """Retrieve video metadata from the YouTube oEmbed API.

    Returns a VideoMetadata with whatever fields are available.
    HTTP errors are handled gracefully — returns partial metadata
    with only the video_id on failure.
    """
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    oembed_url = f"https://www.youtube.com/oembed?url={video_url}&format=json"

    try:
        response = httpx.get(oembed_url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPError, httpx.HTTPStatusError):
        logger.warning("Failed to fetch oEmbed metadata for %s", video_id)
        return VideoMetadata(video_id=video_id)

    return VideoMetadata(
        video_id=video_id,
        title=data.get("title"),
        channel_name=data.get("author_name"),
        thumbnail_url=data.get("thumbnail_url"),
    )


def _is_playlist_only(parsed: ParseResult, query_params: dict[str, list[str]]) -> bool:
    """Check if the URL is a playlist URL without a specific video."""
    if parsed.path == "/playlist":
        return True
    return "list" in query_params and "v" not in query_params
