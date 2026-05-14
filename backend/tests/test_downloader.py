"""Unit tests for backend/app/services/downloader.py — all yt-dlp calls mocked."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yt_dlp  # type: ignore[import-untyped]

from app.services.downloader import _MAX_DURATION_SECONDS, download_video


@pytest.fixture()
def output_dir(tmp_path: Path) -> Path:
    return tmp_path / "downloads"


class TestDownloadVideoSuccess:
    def test_returns_expected_path(self, output_dir: Path) -> None:
        expected = output_dir / "abc123.mp4"

        mock_ydl = MagicMock()
        mock_ydl.__enter__ = lambda s: s
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {"duration": 60}
        mock_ydl.download.side_effect = lambda _: expected.parent.mkdir(parents=True, exist_ok=True) or expected.touch()

        with patch("app.services.downloader.yt_dlp.YoutubeDL", return_value=mock_ydl):
            result = download_video("abc123", "https://youtu.be/abc123", output_dir)

        assert result == expected

    def test_yt_dlp_called_with_correct_url(self, output_dir: Path) -> None:
        expected = output_dir / "abc123.mp4"

        mock_ydl = MagicMock()
        mock_ydl.__enter__ = lambda s: s
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {"duration": 60}
        mock_ydl.download.side_effect = lambda _urls: (expected.parent.mkdir(parents=True, exist_ok=True) or expected.touch())

        with patch("app.services.downloader.yt_dlp.YoutubeDL", return_value=mock_ydl):
            download_video("abc123", "https://youtu.be/abc123", output_dir)

        mock_ydl.download.assert_called_once_with(["https://youtu.be/abc123"])

    def test_info_none_duration_treated_as_zero(self, output_dir: Path) -> None:
        """extract_info returning None should not raise (duration treated as 0)."""
        expected = output_dir / "abc123.mp4"

        mock_ydl = MagicMock()
        mock_ydl.__enter__ = lambda s: s
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = None
        mock_ydl.download.side_effect = lambda _: expected.parent.mkdir(parents=True, exist_ok=True) or expected.touch()

        with patch("app.services.downloader.yt_dlp.YoutubeDL", return_value=mock_ydl):
            result = download_video("abc123", "https://youtu.be/abc123", output_dir)

        assert result == expected


class TestDownloadVideoIdempotency:
    def test_skips_yt_dlp_when_file_exists(self, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        existing = output_dir / "abc123.mp4"
        existing.touch()

        with patch("app.services.downloader.yt_dlp.YoutubeDL") as mock_cls:
            result = download_video("abc123", "https://youtu.be/abc123", output_dir)

        mock_cls.assert_not_called()
        assert result == existing

    def test_returns_existing_path_without_network(self, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        existing = output_dir / "vid.mp4"
        existing.touch()

        with patch("app.services.downloader.yt_dlp.YoutubeDL") as mock_cls:
            result = download_video("vid", "https://youtu.be/vid", output_dir)

        assert result == existing
        mock_cls.assert_not_called()


class TestDownloadVideoFailure:
    def test_yt_dlp_exception_propagates(self, output_dir: Path) -> None:
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = lambda s: s
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.side_effect = Exception("geo-blocked")

        with patch("app.services.downloader.yt_dlp.YoutubeDL", return_value=mock_ydl):
            with pytest.raises(Exception, match="geo-blocked"):
                download_video("abc123", "https://youtu.be/abc123", output_dir)

    def test_missing_output_after_download_raises_file_not_found(self, output_dir: Path) -> None:
        """yt-dlp finishes cleanly but the expected .mp4 is absent (format fallback)."""
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = lambda s: s
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {"duration": 60}
        # download() doesn't create the file — simulates a format-fallback extension
        mock_ydl.download.return_value = None

        with patch("app.services.downloader.yt_dlp.YoutubeDL", return_value=mock_ydl):
            with pytest.raises(FileNotFoundError, match="expected output not found"):
                download_video("abc123", "https://youtu.be/abc123", output_dir)

    def test_download_raises_propagates(self, output_dir: Path) -> None:
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = lambda s: s
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {"duration": 60}
        mock_ydl.download.side_effect = yt_dlp.utils.DownloadError("private video")

        with patch("app.services.downloader.yt_dlp.YoutubeDL", return_value=mock_ydl):
            with pytest.raises(Exception, match="private video"):
                download_video("abc123", "https://youtu.be/abc123", output_dir)


class TestMaxDurationGuard:
    def test_raises_for_video_over_limit(self, output_dir: Path) -> None:
        over_limit = _MAX_DURATION_SECONDS + 1

        mock_ydl = MagicMock()
        mock_ydl.__enter__ = lambda s: s
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {"duration": over_limit}

        with patch("app.services.downloader.yt_dlp.YoutubeDL", return_value=mock_ydl):
            with pytest.raises(ValueError, match="exceeds the 3h download limit"):
                download_video("abc123", "https://youtu.be/abc123", output_dir)

        mock_ydl.download.assert_not_called()

    def test_does_not_raise_at_exact_limit(self, output_dir: Path) -> None:
        expected = output_dir / "abc123.mp4"

        mock_ydl = MagicMock()
        mock_ydl.__enter__ = lambda s: s
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {"duration": _MAX_DURATION_SECONDS}
        mock_ydl.download.side_effect = lambda _: expected.parent.mkdir(parents=True, exist_ok=True) or expected.touch()

        with patch("app.services.downloader.yt_dlp.YoutubeDL", return_value=mock_ydl):
            result = download_video("abc123", "https://youtu.be/abc123", output_dir)

        assert result == expected

    def test_does_not_raise_for_short_video(self, output_dir: Path) -> None:
        expected = output_dir / "abc123.mp4"

        mock_ydl = MagicMock()
        mock_ydl.__enter__ = lambda s: s
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {"duration": 120}
        mock_ydl.download.side_effect = lambda _: expected.parent.mkdir(parents=True, exist_ok=True) or expected.touch()

        with patch("app.services.downloader.yt_dlp.YoutubeDL", return_value=mock_ydl):
            result = download_video("abc123", "https://youtu.be/abc123", output_dir)

        assert result == expected
