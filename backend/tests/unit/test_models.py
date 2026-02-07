import pytest
from pydantic import ValidationError

from app.models import ErrorResponse, SummarizeRequest, VideoMetadata


class TestSummarizeRequest:
    def test_valid_url(self) -> None:
        req = SummarizeRequest(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert req.url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    def test_strips_whitespace(self) -> None:
        req = SummarizeRequest(url="  https://youtu.be/abc123def45  ")
        assert req.url == "https://youtu.be/abc123def45"

    def test_rejects_empty_string(self) -> None:
        with pytest.raises(ValidationError, match="URL must not be empty"):
            SummarizeRequest(url="")

    def test_rejects_whitespace_only(self) -> None:
        with pytest.raises(ValidationError, match="URL must not be empty"):
            SummarizeRequest(url="   ")

    def test_rejects_missing_url(self) -> None:
        with pytest.raises(ValidationError):
            SummarizeRequest()  # type: ignore[call-arg]


class TestVideoMetadata:
    def test_all_fields(self) -> None:
        meta = VideoMetadata(
            video_id="dQw4w9WgXcQ",
            title="Test Video",
            channel_name="Test Channel",
            duration_seconds=300,
            thumbnail_url="https://example.com/thumb.jpg",
        )
        assert meta.video_id == "dQw4w9WgXcQ"
        assert meta.title == "Test Video"

    def test_nullable_fields_default_to_none(self) -> None:
        meta = VideoMetadata(video_id="dQw4w9WgXcQ")
        assert meta.title is None
        assert meta.channel_name is None
        assert meta.duration_seconds is None
        assert meta.thumbnail_url is None

    def test_requires_video_id(self) -> None:
        with pytest.raises(ValidationError):
            VideoMetadata()  # type: ignore[call-arg]


class TestErrorResponse:
    def test_requires_error_and_message(self) -> None:
        err = ErrorResponse(error="invalid_url", message="Bad URL")
        assert err.error == "invalid_url"
        assert err.message == "Bad URL"
        assert err.details is None

    def test_with_details(self) -> None:
        err = ErrorResponse(
            error="invalid_url",
            message="Bad URL",
            details="Try youtube.com/watch?v=...",
        )
        assert err.details == "Try youtube.com/watch?v=..."

    def test_rejects_missing_error(self) -> None:
        with pytest.raises(ValidationError):
            ErrorResponse(message="Bad URL")  # type: ignore[call-arg]

    def test_rejects_missing_message(self) -> None:
        with pytest.raises(ValidationError):
            ErrorResponse(error="invalid_url")  # type: ignore[call-arg]
