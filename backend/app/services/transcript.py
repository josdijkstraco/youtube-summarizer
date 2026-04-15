import os
from http.cookiejar import MozillaCookieJar
from typing import Any

import requests
from youtube_transcript_api import YouTubeTranscriptApi

COOKIES_PATH = "/app/cookies.txt"


def _build_session() -> requests.Session | None:
    """Build a requests.Session with YouTube cookies if available."""
    if not os.path.exists(COOKIES_PATH):
        return None
    jar = MozillaCookieJar(COOKIES_PATH)
    jar.load(ignore_discard=True, ignore_expires=True)
    session = requests.Session()
    session.cookies.update(jar)  # type: ignore[arg-type]
    return session


def get_transcript(video_id: str) -> tuple[str, list[dict[str, Any]]]:
    """Retrieve the transcript for a YouTube video.

    Args:
        video_id: The 11-character YouTube video ID.

    Returns:
        A tuple of (full_text, raw_segments) where full_text is all segment
        texts joined with spaces, and raw_segments is the list of dicts with
        text, start, and duration keys.

    Raises:
        TranscriptsDisabled: If subtitles are disabled for the video.
        NoTranscriptFound: If no transcript is available in any language.
        VideoUnavailable: If the video does not exist or was removed.
    """
    ytt_api = YouTubeTranscriptApi(http_client=_build_session())
    transcript = ytt_api.fetch(video_id)

    full_text = " ".join(snippet.text for snippet in transcript)
    segments = transcript.to_raw_data()

    return full_text, segments


def calculate_duration(segments: list[dict[str, Any]]) -> int | None:
    """Calculate approximate video duration from transcript segments.

    Uses the last segment's start time + duration to estimate total length.

    Returns:
        Duration in seconds as an integer, or None if segments is empty.
    """
    if not segments:
        return None

    last = segments[-1]
    return int(last["start"] + last["duration"])
