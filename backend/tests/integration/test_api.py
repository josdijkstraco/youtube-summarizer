from datetime import UTC, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import asyncpg
from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app
from app.models import VideoRecord

client = TestClient(app)

# ---------------------------------------------------------------------------
# Shared fake data for DB-related tests
# ---------------------------------------------------------------------------

_FAKE_VIDEO_ID = "dQw4w9WgXcQ"
_FAKE_CREATED_AT = datetime(2026, 1, 1, tzinfo=UTC)

# A dict that mimics an asyncpg Record row for the summaries table.
_FAKE_DB_ROW: dict = {
    "id": 1,
    "video_id": _FAKE_VIDEO_ID,
    "title": "Test Video",
    "thumbnail_url": f"https://i.ytimg.com/vi/{_FAKE_VIDEO_ID}/hqdefault.jpg",
    "summary": "Test summary",
    "transcript": "Test transcript",
    "created_at": _FAKE_CREATED_AT,
}

# A HistoryItem as returned by list_recent when a record exists.
_FAKE_HISTORY_ROW: dict = {
    "video_id": _FAKE_VIDEO_ID,
    "title": "Test Video",
    "thumbnail_url": f"https://i.ytimg.com/vi/{_FAKE_VIDEO_ID}/hqdefault.jpg",
    "summary": "Test summary",
    "created_at": _FAKE_CREATED_AT,
}


class TestSummarizeEndpointHappyPath:
    """Integration test for POST /api/summarize happy path."""

    def _make_snippet(self, text: str, start: float, duration: float) -> MagicMock:
        snippet = MagicMock()
        snippet.text = text
        snippet.start = start
        snippet.duration = duration
        return snippet

    @patch("app.services.summarizer.OpenAI")
    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_returns_summary_for_valid_url(
        self, mock_ytt_class: MagicMock, mock_openai_class: MagicMock
    ) -> None:
        # Mock transcript
        mock_ytt = MagicMock()
        mock_ytt_class.return_value = mock_ytt
        snippets = [
            self._make_snippet("Hello world", 0.0, 2.5),
            self._make_snippet("this is great content", 2.5, 3.0),
        ]
        mock_transcript = MagicMock()
        mock_transcript.__iter__ = MagicMock(return_value=iter(snippets))
        mock_transcript.to_raw_data.return_value = [
            {"text": "Hello world", "start": 0.0, "duration": 2.5},
            {"text": "this is great content", "start": 2.5, "duration": 3.0},
        ]
        mock_ytt.fetch.return_value = mock_transcript

        # Mock OpenAI
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = "This video talks about great content."
        mock_client.chat.completions.create.return_value = mock_response

        response = client.post(
            "/api/summarize",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert data["summary"] == "This video talks about great content."
        assert "metadata" in data

    @patch("app.services.summarizer.OpenAI")
    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_response_matches_schema(
        self, mock_ytt_class: MagicMock, mock_openai_class: MagicMock
    ) -> None:
        # Mock transcript
        mock_ytt = MagicMock()
        mock_ytt_class.return_value = mock_ytt
        snippets = [self._make_snippet("Test content", 0.0, 5.0)]
        mock_transcript = MagicMock()
        mock_transcript.__iter__ = MagicMock(return_value=iter(snippets))
        mock_transcript.to_raw_data.return_value = [
            {"text": "Test content", "start": 0.0, "duration": 5.0},
        ]
        mock_ytt.fetch.return_value = mock_transcript

        # Mock OpenAI
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "A concise summary."
        mock_client.chat.completions.create.return_value = mock_response

        response = client.post(
            "/api/summarize",
            json={"url": "https://youtu.be/dQw4w9WgXcQ"},
        )

        assert response.status_code == 200
        data = response.json()

        # Validate SummarizeResponse schema
        assert isinstance(data["summary"], str)
        assert len(data["summary"]) > 0
        assert "metadata" in data
        assert "fallacy_analysis" not in data


def _assert_error_response(data: dict, error_code: str) -> None:
    """Validate that a response body matches the ErrorResponse schema."""
    assert "error" in data
    assert "message" in data
    assert data["error"] == error_code
    assert isinstance(data["message"], str)
    assert len(data["message"]) > 0
    # details is optional but must be present in the schema
    assert "details" in data


class TestSummarizeEndpointErrors:
    """Integration tests for error responses (US2)."""

    def test_invalid_url_returns_400(self) -> None:
        response = client.post(
            "/api/summarize",
            json={"url": "https://www.google.com/search"},
        )
        assert response.status_code == 400
        _assert_error_response(response.json(), "invalid_url")

    def test_random_text_returns_400(self) -> None:
        response = client.post(
            "/api/summarize",
            json={"url": "not a url at all"},
        )
        assert response.status_code == 400
        _assert_error_response(response.json(), "invalid_url")

    def test_playlist_url_returns_400(self) -> None:
        response = client.post(
            "/api/summarize",
            json={
                "url": "https://www.youtube.com/playlist"
                "?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
            },
        )
        assert response.status_code == 400
        _assert_error_response(response.json(), "playlist_not_supported")

    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_video_not_found_returns_404(self, mock_ytt_class: MagicMock) -> None:
        from youtube_transcript_api._errors import VideoUnavailable

        mock_ytt = MagicMock()
        mock_ytt_class.return_value = mock_ytt
        mock_ytt.fetch.side_effect = VideoUnavailable("dQw4w9WgXcQ")

        response = client.post(
            "/api/summarize",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        )
        assert response.status_code == 404
        _assert_error_response(response.json(), "video_not_found")

    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_transcripts_disabled_returns_404(self, mock_ytt_class: MagicMock) -> None:
        from youtube_transcript_api._errors import TranscriptsDisabled

        mock_ytt = MagicMock()
        mock_ytt_class.return_value = mock_ytt
        mock_ytt.fetch.side_effect = TranscriptsDisabled("dQw4w9WgXcQ")

        response = client.post(
            "/api/summarize",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        )
        assert response.status_code == 404
        _assert_error_response(response.json(), "transcript_unavailable")

    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_no_transcript_found_returns_404(self, mock_ytt_class: MagicMock) -> None:
        from youtube_transcript_api._errors import NoTranscriptFound

        mock_ytt = MagicMock()
        mock_ytt_class.return_value = mock_ytt
        mock_ytt.fetch.side_effect = NoTranscriptFound("dQw4w9WgXcQ", [], [])

        response = client.post(
            "/api/summarize",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        )
        assert response.status_code == 404
        _assert_error_response(response.json(), "transcript_unavailable")

    @patch("app.services.summarizer.OpenAI")
    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_openai_error_returns_502(
        self,
        mock_ytt_class: MagicMock,
        mock_openai_class: MagicMock,
    ) -> None:
        from openai import APIError

        # Mock transcript success
        mock_ytt = MagicMock()
        mock_ytt_class.return_value = mock_ytt
        snippet = MagicMock()
        snippet.text = "Some text"
        snippet.start = 0.0
        snippet.duration = 1.0
        mock_transcript = MagicMock()
        mock_transcript.__iter__ = MagicMock(return_value=iter([snippet]))
        mock_transcript.to_raw_data.return_value = [
            {"text": "Some text", "start": 0.0, "duration": 1.0}
        ]
        mock_ytt.fetch.return_value = mock_transcript

        # Mock OpenAI failure
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = APIError(
            message="Rate limit exceeded",
            request=MagicMock(),
            body=None,
        )

        response = client.post(
            "/api/summarize",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        )
        assert response.status_code == 502
        _assert_error_response(response.json(), "summarization_failed")

    def test_empty_url_returns_422(self) -> None:
        """Empty URL is caught by Pydantic validation (422)."""
        response = client.post(
            "/api/summarize",
            json={"url": ""},
        )
        # FastAPI Pydantic validation returns 422
        assert response.status_code == 422

    def test_invalid_length_percent_returns_422(self) -> None:
        """Non-multiple-of-5 length_percent returns 422."""
        response = client.post(
            "/api/summarize",
            json={
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "length_percent": 7,
            },
        )
        assert response.status_code == 422


class TestFallaciesEndpoint:
    """Integration tests for POST /api/fallacies."""

    def _make_snippet(self, text: str, start: float, duration: float) -> MagicMock:
        snippet = MagicMock()
        snippet.text = text
        snippet.start = start
        snippet.duration = duration
        return snippet

    def _make_valid_fallacy_json(self) -> str:
        import json

        return json.dumps(
            {
                "summary": {
                    "total_fallacies": 1,
                    "high_severity": 1,
                    "medium_severity": 0,
                    "low_severity": 0,
                    "primary_tactics": ["Ad Hominem"],
                },
                "fallacies": [
                    {
                        "timestamp": None,
                        "quote": "You can't trust him",
                        "fallacy_name": "Ad Hominem",
                        "category": "Relevance",
                        "severity": "high",
                        "explanation": "Attacks the person.",
                        "clear_example": {
                            "scenario": "Example",
                            "why_wrong": "Irrelevant",
                        },
                    }
                ],
            }
        )

    @patch("app.services.fallacy_analyzer.OpenAI")
    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_returns_fallacy_analysis_for_valid_url(
        self,
        mock_ytt_class: MagicMock,
        mock_fallacy_openai: MagicMock,
    ) -> None:
        mock_ytt = MagicMock()
        mock_ytt_class.return_value = mock_ytt
        snippets = [self._make_snippet("Hello world", 0.0, 2.5)]
        mock_transcript = MagicMock()
        mock_transcript.__iter__ = MagicMock(return_value=iter(snippets))
        mock_transcript.to_raw_data.return_value = [
            {"text": "Hello world", "start": 0.0, "duration": 2.5},
        ]
        mock_ytt.fetch.return_value = mock_transcript

        mock_fal_client = MagicMock()
        mock_fallacy_openai.return_value = mock_fal_client
        mock_fal_response = MagicMock()
        mock_fal_response.choices = [MagicMock()]
        mock_fal_response.choices[0].message.content = self._make_valid_fallacy_json()
        mock_fal_client.chat.completions.create.return_value = mock_fal_response

        response = client.post(
            "/api/fallacies",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "fallacies" in data
        assert data["summary"]["total_fallacies"] == 1
        assert len(data["fallacies"]) == 1

    def test_invalid_url_returns_400(self) -> None:
        response = client.post(
            "/api/fallacies",
            json={"url": "not a url at all"},
        )
        assert response.status_code == 400
        _assert_error_response(response.json(), "invalid_url")

    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_transcript_unavailable_returns_404(
        self, mock_ytt_class: MagicMock
    ) -> None:
        from youtube_transcript_api._errors import TranscriptsDisabled

        mock_ytt = MagicMock()
        mock_ytt_class.return_value = mock_ytt
        mock_ytt.fetch.side_effect = TranscriptsDisabled("dQw4w9WgXcQ")

        response = client.post(
            "/api/fallacies",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        )
        assert response.status_code == 404
        _assert_error_response(response.json(), "transcript_unavailable")

    @patch("app.main.analyze_fallacies")
    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_analyzer_failure_returns_502(
        self,
        mock_ytt_class: MagicMock,
        mock_analyze: MagicMock,
    ) -> None:
        mock_ytt = MagicMock()
        mock_ytt_class.return_value = mock_ytt
        snippets = [self._make_snippet("Hello world", 0.0, 2.5)]
        mock_transcript = MagicMock()
        mock_transcript.__iter__ = MagicMock(return_value=iter(snippets))
        mock_transcript.to_raw_data.return_value = [
            {"text": "Hello world", "start": 0.0, "duration": 2.5},
        ]
        mock_ytt.fetch.return_value = mock_transcript

        mock_analyze.return_value = None

        response = client.post(
            "/api/fallacies",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        )
        assert response.status_code == 502
        _assert_error_response(response.json(), "analysis_failed")


class TestSummarizeEndpointLengthPercent:
    """Integration tests for length_percent parameter (US1)."""

    def _make_snippet(self, text: str, start: float, duration: float) -> MagicMock:
        snippet = MagicMock()
        snippet.text = text
        snippet.start = start
        snippet.duration = duration
        return snippet

    @patch("app.services.summarizer.OpenAI")
    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_length_percent_passed_to_summarizer(
        self, mock_ytt_class: MagicMock, mock_openai_class: MagicMock
    ) -> None:
        """POST with length_percent=10 should pass value through to generate_summary."""
        # Mock transcript
        mock_ytt = MagicMock()
        mock_ytt_class.return_value = mock_ytt
        snippets = [
            self._make_snippet("Hello world this is test content", 0.0, 5.0),
        ]
        mock_transcript = MagicMock()
        mock_transcript.__iter__ = MagicMock(return_value=iter(snippets))
        mock_transcript.to_raw_data.return_value = [
            {"text": "Hello world this is test content", "start": 0.0, "duration": 5.0},
        ]
        mock_ytt.fetch.return_value = mock_transcript

        # Mock OpenAI
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Short summary."
        mock_client.chat.completions.create.return_value = mock_response

        response = client.post(
            "/api/summarize",
            json={
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "length_percent": 10,
            },
        )

        assert response.status_code == 200
        # Verify the system prompt includes a word count target
        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs["messages"]
        system_msg = next(m for m in messages if m["role"] == "system")
        assert "10%" in system_msg["content"]

    @patch("app.services.summarizer.OpenAI")
    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_default_length_percent_is_25(
        self, mock_ytt_class: MagicMock, mock_openai_class: MagicMock
    ) -> None:
        """POST without length_percent should use default 25."""
        # Mock transcript
        mock_ytt = MagicMock()
        mock_ytt_class.return_value = mock_ytt
        snippets = [
            self._make_snippet("Hello world this is test content", 0.0, 5.0),
        ]
        mock_transcript = MagicMock()
        mock_transcript.__iter__ = MagicMock(return_value=iter(snippets))
        mock_transcript.to_raw_data.return_value = [
            {"text": "Hello world this is test content", "start": 0.0, "duration": 5.0},
        ]
        mock_ytt.fetch.return_value = mock_transcript

        # Mock OpenAI
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Default summary."
        mock_client.chat.completions.create.return_value = mock_response

        response = client.post(
            "/api/summarize",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        )

        assert response.status_code == 200
        # Verify the system prompt includes 25% target
        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs["messages"]
        system_msg = next(m for m in messages if m["role"] == "system")
        assert "25%" in system_msg["content"]


# ---------------------------------------------------------------------------
# US1: history and storage_warning integration tests
# ---------------------------------------------------------------------------


class TestGetHistoryEndpoint:
    """Integration tests for GET /api/history (US1)."""

    def test_get_history_empty(self) -> None:
        """GET /api/history returns 200 with an empty items list when DB has no rows."""
        mock_conn = AsyncMock(spec=asyncpg.Connection)
        mock_conn.fetch.return_value = []

        async def override_get_db():
            yield mock_conn

        app.dependency_overrides[get_db] = override_get_db
        try:
            response = client.get("/api/history")
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["items"] == []

    def test_get_history_returns_items(self) -> None:
        """GET /api/history returns 200 with the stored video when DB has a row."""
        mock_conn = AsyncMock(spec=asyncpg.Connection)
        mock_conn.fetch.return_value = [_FAKE_HISTORY_ROW]

        async def override_get_db():
            yield mock_conn

        app.dependency_overrides[get_db] = override_get_db
        try:
            response = client.get("/api/history")
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert item["video_id"] == _FAKE_VIDEO_ID
        assert item["title"] == "Test Video"
        assert item["summary"] == "Test summary"


class TestSummarizeStorageWarning:
    """Integration tests for storage_warning field on POST /api/summarize (US1)."""

    def _make_snippet(self, text: str, start: float, duration: float) -> MagicMock:
        snippet = MagicMock()
        snippet.text = text
        snippet.start = start
        snippet.duration = duration
        return snippet

    def _setup_transcript_mock(
        self, mock_ytt_class: MagicMock, text: str = "Hello world"
    ) -> None:
        mock_ytt = MagicMock()
        mock_ytt_class.return_value = mock_ytt
        snippets = [self._make_snippet(text, 0.0, 3.0)]
        mock_transcript = MagicMock()
        mock_transcript.__iter__ = MagicMock(return_value=iter(snippets))
        mock_transcript.to_raw_data.return_value = [
            {"text": text, "start": 0.0, "duration": 3.0},
        ]
        mock_ytt.fetch.return_value = mock_transcript

    def _setup_openai_mock(
        self, mock_openai_class: MagicMock, summary_text: str = "A summary."
    ) -> None:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = summary_text
        mock_client.chat.completions.create.return_value = mock_response

    @patch("app.services.summarizer.OpenAI")
    @patch("app.services.transcript.YouTubeTranscriptApi")
    @patch("app.services.youtube.httpx.get")
    def test_summarize_sets_storage_warning_false_on_success(
        self,
        mock_httpx_get: MagicMock,
        mock_ytt_class: MagicMock,
        mock_openai_class: MagicMock,
    ) -> None:
        """POST /api/summarize returns storage_warning=false when DB save succeeds."""
        self._setup_transcript_mock(mock_ytt_class)
        self._setup_openai_mock(mock_openai_class)

        # Mock oEmbed metadata so it doesn't make a real HTTP call
        mock_httpx_response = MagicMock()
        mock_httpx_response.raise_for_status.return_value = None
        mock_httpx_response.json.return_value = {
            "title": "Test Video",
            "author_name": "Test Channel",
            "thumbnail_url": _FAKE_DB_ROW["thumbnail_url"],
        }
        mock_httpx_get.return_value = mock_httpx_response

        # Mock DB connection where save_record succeeds
        mock_conn = AsyncMock(spec=asyncpg.Connection)
        mock_conn.execute.return_value = None
        mock_conn.fetchrow.return_value = _FAKE_DB_ROW

        async def override_get_db():
            yield mock_conn

        app.dependency_overrides[get_db] = override_get_db
        try:
            response = client.post(
                "/api/summarize",
                json={"url": f"https://www.youtube.com/watch?v={_FAKE_VIDEO_ID}"},
            )
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert data.get("storage_warning") is False

    @patch("app.services.summarizer.OpenAI")
    @patch("app.services.transcript.YouTubeTranscriptApi")
    @patch("app.services.youtube.httpx.get")
    def test_summarize_sets_storage_warning_true_on_db_failure(
        self,
        mock_httpx_get: MagicMock,
        mock_ytt_class: MagicMock,
        mock_openai_class: MagicMock,
    ) -> None:
        """POST /api/summarize returns 200 with storage_warning=true on DB failure."""
        self._setup_transcript_mock(mock_ytt_class)
        self._setup_openai_mock(mock_openai_class)

        # Mock oEmbed metadata
        mock_httpx_response = MagicMock()
        mock_httpx_response.raise_for_status.return_value = None
        mock_httpx_response.json.return_value = {
            "title": "Test Video",
            "author_name": "Test Channel",
            "thumbnail_url": _FAKE_DB_ROW["thumbnail_url"],
        }
        mock_httpx_get.return_value = mock_httpx_response

        # Mock DB connection where save_record raises (DB unavailable)
        mock_conn = AsyncMock(spec=asyncpg.Connection)
        # fetchrow returns None so the cache-check finds no existing record
        mock_conn.fetchrow.return_value = None
        mock_conn.execute.side_effect = Exception("DB connection refused")

        async def override_get_db():
            yield mock_conn

        app.dependency_overrides[get_db] = override_get_db
        try:
            response = client.post(
                "/api/summarize",
                json={"url": f"https://www.youtube.com/watch?v={_FAKE_VIDEO_ID}"},
            )
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert data.get("storage_warning") is True


# ---------------------------------------------------------------------------
# US2: cache-hit path integration tests
# ---------------------------------------------------------------------------


class TestSummarizeCacheHit:
    """Integration tests for the cache-hit path on POST /api/summarize (US2)."""

    def test_summarize_returns_cached_result_without_reprocessing(self) -> None:
        """When a video_id already exists in the DB, the stored result is returned
        immediately. Transcript and summarize services must NOT be called."""
        fake_record = VideoRecord(
            id=1,
            video_id=_FAKE_VIDEO_ID,
            title="Cached Title",
            thumbnail_url=f"https://i.ytimg.com/vi/{_FAKE_VIDEO_ID}/hqdefault.jpg",
            summary="Cached summary",
            transcript="Cached transcript",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )

        async def override_get_db():
            mock_conn = AsyncMock()
            yield mock_conn

        app.dependency_overrides[get_db] = override_get_db

        try:
            with (
                patch(
                    "app.main.get_by_video_id",
                    new_callable=AsyncMock,
                    return_value=fake_record,
                ),
                patch("app.main.get_transcript") as mock_transcript,
                patch("app.main.generate_summary") as mock_summarize,
            ):
                response = client.post(
                    "/api/summarize",
                    json={"url": f"https://www.youtube.com/watch?v={_FAKE_VIDEO_ID}"},
                )
            assert response.status_code == 200
            data = response.json()
            assert data["summary"] == "Cached summary"
            assert data["transcript"] == "Cached transcript"
            mock_transcript.assert_not_called()
            mock_summarize.assert_not_called()
        finally:
            app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# US3: GET /api/history/{video_id} integration tests
# ---------------------------------------------------------------------------


class TestGetHistoryItemEndpoint:
    """Integration tests for GET /api/history/{video_id} (US3)."""

    def test_get_history_item_returns_full_record_with_transcript(self) -> None:
        """GET /api/history/{video_id} returns the full record including transcript."""
        fake_record = VideoRecord(
            id=1,
            video_id=_FAKE_VIDEO_ID,
            title="Full Record Title",
            thumbnail_url="https://example.com/thumb.jpg",
            summary="Full summary",
            transcript="Full transcript content",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )

        def override_get_db():
            mock_conn = AsyncMock()
            yield mock_conn

        app.dependency_overrides[get_db] = override_get_db
        try:
            with patch(
                "app.main.get_full_record",
                new_callable=AsyncMock,
                return_value=fake_record,
            ):
                response = client.get(f"/api/history/{_FAKE_VIDEO_ID}")
            assert response.status_code == 200
            data = response.json()
            assert data["transcript"] == "Full transcript content"
            assert data["summary"] == "Full summary"
            assert data["video_id"] == _FAKE_VIDEO_ID
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_get_history_item_returns_404_for_unknown_video_id(self) -> None:
        """GET /api/history/{video_id} returns 404 when video_id not in storage."""

        def override_get_db():
            mock_conn = AsyncMock()
            yield mock_conn

        app.dependency_overrides[get_db] = override_get_db
        try:
            with patch(
                "app.main.get_full_record",
                new_callable=AsyncMock,
                return_value=None,
            ):
                response = client.get("/api/history/unknownvideo1")
            assert response.status_code == 404
            data = response.json()
            assert data["error"] == "not_found"
        finally:
            app.dependency_overrides.pop(get_db, None)
