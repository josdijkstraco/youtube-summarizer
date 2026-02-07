from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.services.youtube import extract_video_id, get_video_metadata


class TestExtractVideoId:
    """Test extract_video_id() with various YouTube URL formats."""

    # --- Valid URL formats ---

    def test_standard_watch_url(self) -> None:
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_short_url(self) -> None:
        url = "https://youtu.be/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_shorts_url(self) -> None:
        url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_mobile_url(self) -> None:
        url = "https://m.youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_url_with_extra_params(self) -> None:
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120&feature=share"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_short_url_with_params(self) -> None:
        url = "https://youtu.be/dQw4w9WgXcQ?t=30"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_http_url(self) -> None:
        url = "http://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_no_www_url(self) -> None:
        url = "https://youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_video_id_with_dashes_and_underscores(self) -> None:
        url = "https://www.youtube.com/watch?v=a-b_C1D2E3F"
        assert extract_video_id(url) == "a-b_C1D2E3F"

    # --- Invalid inputs ---

    def test_rejects_empty_string(self) -> None:
        with pytest.raises(ValueError, match="URL must not be empty"):
            extract_video_id("")

    def test_rejects_whitespace(self) -> None:
        with pytest.raises(ValueError, match="URL must not be empty"):
            extract_video_id("   ")

    def test_rejects_non_url_string(self) -> None:
        with pytest.raises(ValueError, match="not a valid YouTube"):
            extract_video_id("hello world")

    def test_rejects_non_youtube_url(self) -> None:
        with pytest.raises(ValueError, match="not a valid YouTube"):
            extract_video_id("https://www.google.com/search?q=test")

    def test_rejects_youtube_homepage(self) -> None:
        with pytest.raises(ValueError, match="not a valid YouTube"):
            extract_video_id("https://www.youtube.com/")

    def test_rejects_youtube_channel_url(self) -> None:
        with pytest.raises(ValueError, match="not a valid YouTube"):
            extract_video_id("https://www.youtube.com/@channel")

    # --- Playlist URLs ---

    def test_rejects_playlist_url(self) -> None:
        with pytest.raises(ValueError, match="[Pp]laylist"):
            extract_video_id(
                "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
            )

    def test_rejects_playlist_only_url(self) -> None:
        """Reject URL that has list= but no v= parameter."""
        with pytest.raises(ValueError, match="[Pp]laylist"):
            extract_video_id(
                "https://www.youtube.com/watch?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
            )

    def test_accepts_video_with_playlist_context(self) -> None:
        """Accept URL that has both v= and list= (video within playlist)."""
        url = (
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            "&list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
        )
        assert extract_video_id(url) == "dQw4w9WgXcQ"


class TestErrorMessageMapping:
    """Test that error messages enable correct error code mapping (US2)."""

    def test_invalid_url_message_contains_not_valid(self) -> None:
        """Non-YouTube URLs produce messages containing 'not a valid YouTube'."""
        with pytest.raises(ValueError, match="not a valid YouTube"):
            extract_video_id("https://www.vimeo.com/12345")

    def test_playlist_message_contains_playlist(self) -> None:
        """Playlist URLs produce messages containing 'Playlist'."""
        with pytest.raises(ValueError, match="Playlist"):
            extract_video_id(
                "https://www.youtube.com/playlist"
                "?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
            )

    def test_empty_url_message_contains_empty(self) -> None:
        """Empty URLs produce messages containing 'empty'."""
        with pytest.raises(ValueError, match="empty"):
            extract_video_id("")

    def test_random_text_raises_invalid_url(self) -> None:
        """Random text that isn't a URL at all."""
        with pytest.raises(ValueError, match="not a valid YouTube"):
            extract_video_id("just some random text")

    def test_other_video_platform_raises_invalid_url(self) -> None:
        """URLs from other video platforms."""
        with pytest.raises(ValueError, match="not a valid YouTube"):
            extract_video_id("https://www.dailymotion.com/video/x12345")


class TestGetVideoMetadata:
    """Test get_video_metadata() with mocked HTTP responses (US3)."""

    _OEMBED_RESPONSE = {
        "title": "Test Video Title",
        "author_name": "Test Channel",
        "author_url": "https://www.youtube.com/@testchannel",
        "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
        "type": "video",
        "provider_name": "YouTube",
    }

    @patch("app.services.youtube.httpx.get")
    def test_parses_oembed_response(self, mock_get: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self._OEMBED_RESPONSE
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        meta = get_video_metadata("dQw4w9WgXcQ")

        assert meta.video_id == "dQw4w9WgXcQ"
        assert meta.title == "Test Video Title"
        assert meta.channel_name == "Test Channel"
        assert meta.thumbnail_url == (
            "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg"
        )

    @patch("app.services.youtube.httpx.get")
    def test_maps_author_name_to_channel_name(self, mock_get: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "title": "Video",
            "author_name": "My Channel",
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        meta = get_video_metadata("abc123def45")
        assert meta.channel_name == "My Channel"

    @patch("app.services.youtube.httpx.get")
    def test_returns_partial_metadata_on_missing_fields(
        self, mock_get: MagicMock
    ) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"title": "Only Title"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        meta = get_video_metadata("dQw4w9WgXcQ")

        assert meta.title == "Only Title"
        assert meta.channel_name is None
        assert meta.thumbnail_url is None

    @patch("app.services.youtube.httpx.get")
    def test_returns_empty_metadata_on_http_error(self, mock_get: MagicMock) -> None:
        mock_get.side_effect = httpx.HTTPError("Connection failed")

        meta = get_video_metadata("dQw4w9WgXcQ")

        assert meta.video_id == "dQw4w9WgXcQ"
        assert meta.title is None
        assert meta.channel_name is None
        assert meta.thumbnail_url is None

    @patch("app.services.youtube.httpx.get")
    def test_returns_empty_metadata_on_non_200(self, mock_get: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=MagicMock(),
        )
        mock_get.return_value = mock_response

        meta = get_video_metadata("dQw4w9WgXcQ")

        assert meta.video_id == "dQw4w9WgXcQ"
        assert meta.title is None

    @patch("app.services.youtube.httpx.get")
    def test_calls_correct_oembed_url(self, mock_get: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self._OEMBED_RESPONSE
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        get_video_metadata("dQw4w9WgXcQ")

        call_args = mock_get.call_args
        url = call_args[0][0]
        assert "youtube.com/oembed" in url
        assert "dQw4w9WgXcQ" in url
        assert "format=json" in url
