from unittest.mock import MagicMock, patch

import pytest

from app.services.transcript import calculate_duration, get_transcript


class TestGetTranscript:
    """Test get_transcript() with mocked youtube-transcript-api."""

    def _make_snippet(self, text: str, start: float, duration: float) -> MagicMock:
        """Create a mock transcript snippet."""
        snippet = MagicMock()
        snippet.text = text
        snippet.start = start
        snippet.duration = duration
        return snippet

    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_returns_concatenated_text(self, mock_api_class: MagicMock) -> None:
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        snippets = [
            self._make_snippet("Hello world", 0.0, 2.5),
            self._make_snippet("this is a test", 2.5, 3.0),
            self._make_snippet("of the transcript", 5.5, 2.0),
        ]
        mock_transcript = MagicMock()
        mock_transcript.__iter__ = MagicMock(return_value=iter(snippets))
        mock_transcript.to_raw_data.return_value = [
            {"text": "Hello world", "start": 0.0, "duration": 2.5},
            {"text": "this is a test", "start": 2.5, "duration": 3.0},
            {"text": "of the transcript", "start": 5.5, "duration": 2.0},
        ]
        mock_api.fetch.return_value = mock_transcript

        full_text, segments = get_transcript("dQw4w9WgXcQ")

        assert full_text == "Hello world this is a test of the transcript"
        assert len(segments) == 3

    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_segments_joined_with_spaces(self, mock_api_class: MagicMock) -> None:
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        snippets = [
            self._make_snippet("First part", 0.0, 1.0),
            self._make_snippet("Second part", 1.0, 1.0),
        ]
        mock_transcript = MagicMock()
        mock_transcript.__iter__ = MagicMock(return_value=iter(snippets))
        mock_transcript.to_raw_data.return_value = [
            {"text": "First part", "start": 0.0, "duration": 1.0},
            {"text": "Second part", "start": 1.0, "duration": 1.0},
        ]
        mock_api.fetch.return_value = mock_transcript

        full_text, _ = get_transcript("abc123def45")

        assert full_text == "First part Second part"

    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_calls_fetch_with_video_id(self, mock_api_class: MagicMock) -> None:
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        snippet = self._make_snippet("text", 0.0, 1.0)
        mock_transcript = MagicMock()
        mock_transcript.__iter__ = MagicMock(return_value=iter([snippet]))
        mock_transcript.to_raw_data.return_value = [
            {"text": "text", "start": 0.0, "duration": 1.0}
        ]
        mock_api.fetch.return_value = mock_transcript

        get_transcript("test_video_id")

        mock_api.fetch.assert_called_once_with("test_video_id")

    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_returns_raw_segments(self, mock_api_class: MagicMock) -> None:
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        snippets = [
            self._make_snippet("Hello", 0.0, 1.5),
            self._make_snippet("World", 1.5, 2.0),
        ]
        raw_data = [
            {"text": "Hello", "start": 0.0, "duration": 1.5},
            {"text": "World", "start": 1.5, "duration": 2.0},
        ]
        mock_transcript = MagicMock()
        mock_transcript.__iter__ = MagicMock(return_value=iter(snippets))
        mock_transcript.to_raw_data.return_value = raw_data
        mock_api.fetch.return_value = mock_transcript

        _, segments = get_transcript("dQw4w9WgXcQ")

        assert segments == raw_data

    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_raises_on_transcripts_disabled(self, mock_api_class: MagicMock) -> None:
        from youtube_transcript_api._errors import TranscriptsDisabled

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        mock_api.fetch.side_effect = TranscriptsDisabled("dQw4w9WgXcQ")

        with pytest.raises(TranscriptsDisabled):
            get_transcript("dQw4w9WgXcQ")

    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_raises_on_no_transcript_found(self, mock_api_class: MagicMock) -> None:
        from youtube_transcript_api._errors import NoTranscriptFound

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        mock_api.fetch.side_effect = NoTranscriptFound("dQw4w9WgXcQ", [], [])

        with pytest.raises(NoTranscriptFound):
            get_transcript("dQw4w9WgXcQ")

    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_raises_on_video_unavailable(self, mock_api_class: MagicMock) -> None:
        from youtube_transcript_api._errors import VideoUnavailable

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        mock_api.fetch.side_effect = VideoUnavailable("dQw4w9WgXcQ")

        with pytest.raises(VideoUnavailable):
            get_transcript("dQw4w9WgXcQ")


class TestCalculateDuration:
    """Test calculate_duration() for US3."""

    def test_returns_duration_from_last_segment(self) -> None:
        segments = [
            {"text": "Hello", "start": 0.0, "duration": 2.5},
            {"text": "World", "start": 2.5, "duration": 3.0},
            {"text": "End", "start": 120.5, "duration": 5.3},
        ]
        # Last segment: start(120.5) + duration(5.3) = 125.8 → 125
        assert calculate_duration(segments) == 125

    def test_returns_integer_seconds(self) -> None:
        segments = [
            {"text": "Only", "start": 0.0, "duration": 10.9},
        ]
        # 0.0 + 10.9 = 10.9 → 10
        assert calculate_duration(segments) == 10

    def test_returns_none_for_empty_segments(self) -> None:
        assert calculate_duration([]) is None

    def test_rounds_down_to_integer(self) -> None:
        segments = [
            {"text": "A", "start": 300.0, "duration": 12.7},
        ]
        # 300.0 + 12.7 = 312.7 → 312
        assert calculate_duration(segments) == 312

    def test_handles_long_video(self) -> None:
        segments = [
            {"text": "Start", "start": 0.0, "duration": 5.0},
            {"text": "End", "start": 7200.0, "duration": 3.0},
        ]
        # 7200.0 + 3.0 = 7203.0 → 7203 (2 hours)
        assert calculate_duration(segments) == 7203
