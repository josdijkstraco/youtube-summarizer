import pytest
from pydantic import ValidationError

from app.models import (
    ClearExample,
    ErrorResponse,
    Fallacy,
    FallacyAnalysisResult,
    FallacySummary,
    SummarizeRequest,
    SummarizeResponse,
    VideoMetadata,
)


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


class TestSummarizeRequestLengthPercent:
    """Test length_percent field validation."""

    def test_defaults_to_25(self) -> None:
        req = SummarizeRequest(url="https://youtu.be/abc123def45")
        assert req.length_percent == 25

    def test_accepts_minimum_10(self) -> None:
        req = SummarizeRequest(url="https://youtu.be/abc123def45", length_percent=10)
        assert req.length_percent == 10

    def test_accepts_maximum_50(self) -> None:
        req = SummarizeRequest(url="https://youtu.be/abc123def45", length_percent=50)
        assert req.length_percent == 50

    def test_accepts_middle_value_35(self) -> None:
        req = SummarizeRequest(url="https://youtu.be/abc123def45", length_percent=35)
        assert req.length_percent == 35

    def test_rejects_below_minimum(self) -> None:
        with pytest.raises(ValidationError):
            SummarizeRequest(url="https://youtu.be/abc123def45", length_percent=5)

    def test_rejects_above_maximum(self) -> None:
        with pytest.raises(ValidationError):
            SummarizeRequest(url="https://youtu.be/abc123def45", length_percent=55)

    def test_rejects_zero(self) -> None:
        with pytest.raises(ValidationError):
            SummarizeRequest(url="https://youtu.be/abc123def45", length_percent=0)

    def test_rejects_non_multiple_of_5_12(self) -> None:
        with pytest.raises(ValidationError, match="multiple of 5"):
            SummarizeRequest(url="https://youtu.be/abc123def45", length_percent=12)

    def test_rejects_non_multiple_of_5_23(self) -> None:
        with pytest.raises(ValidationError, match="multiple of 5"):
            SummarizeRequest(url="https://youtu.be/abc123def45", length_percent=23)

    def test_rejects_non_multiple_of_5_37(self) -> None:
        with pytest.raises(ValidationError, match="multiple of 5"):
            SummarizeRequest(url="https://youtu.be/abc123def45", length_percent=37)


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


class TestClearExample:
    def test_requires_scenario_and_why_wrong(self) -> None:
        ex = ClearExample(
            scenario="A mechanic example", why_wrong="Irrelevant to diagnosis"
        )
        assert ex.scenario == "A mechanic example"
        assert ex.why_wrong == "Irrelevant to diagnosis"

    def test_rejects_missing_scenario(self) -> None:
        with pytest.raises(ValidationError):
            ClearExample(why_wrong="Missing scenario")  # type: ignore[call-arg]

    def test_rejects_missing_why_wrong(self) -> None:
        with pytest.raises(ValidationError):
            ClearExample(scenario="Missing why_wrong")  # type: ignore[call-arg]


class TestFallacy:
    def _make_clear_example(self) -> ClearExample:
        return ClearExample(scenario="Example scenario", why_wrong="Example reason")

    def test_all_fields(self) -> None:
        f = Fallacy(
            timestamp="1:23",
            quote="You can't trust him",
            fallacy_name="Ad Hominem",
            category="Relevance",
            severity="high",
            explanation="Attacks the person rather than the argument.",
            clear_example=self._make_clear_example(),
        )
        assert f.timestamp == "1:23"
        assert f.quote == "You can't trust him"
        assert f.fallacy_name == "Ad Hominem"
        assert f.category == "Relevance"
        assert f.severity == "high"
        assert f.explanation == "Attacks the person rather than the argument."
        assert f.clear_example.scenario == "Example scenario"

    def test_null_timestamp(self) -> None:
        f = Fallacy(
            timestamp=None,
            quote="Everyone knows this",
            fallacy_name="Bandwagon",
            category="Emotional Appeal",
            severity="medium",
            explanation="Appeal to popularity.",
            clear_example=self._make_clear_example(),
        )
        assert f.timestamp is None

    def test_timestamp_defaults_to_none(self) -> None:
        f = Fallacy(
            quote="Some quote",
            fallacy_name="Straw Man",
            category="Relevance",
            severity="low",
            explanation="Misrepresents the argument.",
            clear_example=self._make_clear_example(),
        )
        assert f.timestamp is None


class TestFallacySummary:
    def test_all_fields(self) -> None:
        s = FallacySummary(
            total_fallacies=5,
            high_severity=2,
            medium_severity=2,
            low_severity=1,
            primary_tactics=["Ad Hominem", "Straw Man"],
        )
        assert s.total_fallacies == 5
        assert s.high_severity == 2
        assert s.medium_severity == 2
        assert s.low_severity == 1
        assert s.primary_tactics == ["Ad Hominem", "Straw Man"]


class TestFallacyAnalysisResult:
    def test_with_summary_and_fallacies(self) -> None:
        result = FallacyAnalysisResult(
            summary=FallacySummary(
                total_fallacies=1,
                high_severity=1,
                medium_severity=0,
                low_severity=0,
                primary_tactics=["Ad Hominem"],
            ),
            fallacies=[
                Fallacy(
                    quote="You can't trust him",
                    fallacy_name="Ad Hominem",
                    category="Relevance",
                    severity="high",
                    explanation="Attacks the person.",
                    clear_example=ClearExample(
                        scenario="Example", why_wrong="Irrelevant"
                    ),
                )
            ],
        )
        assert result.summary.total_fallacies == 1
        assert len(result.fallacies) == 1

    def test_empty_fallacies_list(self) -> None:
        result = FallacyAnalysisResult(
            summary=FallacySummary(
                total_fallacies=0,
                high_severity=0,
                medium_severity=0,
                low_severity=0,
                primary_tactics=[],
            ),
            fallacies=[],
        )
        assert result.fallacies == []


class TestSummarizeResponse:
    def test_requires_summary_and_transcript(self) -> None:
        resp = SummarizeResponse(summary="A summary", transcript="Raw text here")
        assert resp.summary == "A summary"
        assert resp.transcript == "Raw text here"
        assert resp.metadata is None

    def test_with_metadata(self) -> None:
        meta = VideoMetadata(video_id="abc123")
        resp = SummarizeResponse(summary="A summary", transcript="Raw text", metadata=meta)
        assert resp.metadata is not None
        assert resp.metadata.video_id == "abc123"

    def test_rejects_missing_transcript(self) -> None:
        with pytest.raises(ValidationError):
            SummarizeResponse(summary="A summary")  # type: ignore[call-arg]
