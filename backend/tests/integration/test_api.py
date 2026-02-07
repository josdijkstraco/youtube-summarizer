from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


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
        # metadata is None for Phase 3 (populated in Phase 5)
        assert "metadata" in data


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
