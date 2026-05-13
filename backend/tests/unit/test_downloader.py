from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.downloader import download_video


class TestDownloadVideo:
    def test_returns_output_path_on_success(self, tmp_path: Path) -> None:
        with patch("app.services.downloader.yt_dlp.YoutubeDL") as mock_ydl_class:
            mock_ydl = MagicMock()
            mock_ydl_class.return_value.__enter__ = MagicMock(return_value=mock_ydl)
            mock_ydl_class.return_value.__exit__ = MagicMock(return_value=False)
            mock_ydl.extract_info.return_value = {"ext": "mp4"}
            # Simulate yt-dlp creating the output file
            (tmp_path / "abc123.mp4").touch()

            result = download_video("abc123", "https://www.youtube.com/watch?v=abc123", tmp_path)

        assert result == tmp_path / "abc123.mp4"

    def test_skips_download_if_file_exists(self, tmp_path: Path) -> None:
        """If any file for this video_id already exists, yt-dlp is never called."""
        existing = tmp_path / "abc123.mp4"
        existing.touch()

        with patch("app.services.downloader.yt_dlp.YoutubeDL") as mock_ydl_class:
            result = download_video("abc123", "https://www.youtube.com/watch?v=abc123", tmp_path)
            mock_ydl_class.assert_not_called()

        assert result == existing

    def test_propagates_yt_dlp_exception(self, tmp_path: Path) -> None:
        with patch("app.services.downloader.yt_dlp.YoutubeDL") as mock_ydl_class:
            mock_ydl = MagicMock()
            mock_ydl_class.return_value.__enter__ = MagicMock(return_value=mock_ydl)
            mock_ydl_class.return_value.__exit__ = MagicMock(return_value=False)
            mock_ydl.extract_info.side_effect = Exception("geo-blocked")

            with pytest.raises(Exception, match="geo-blocked"):
                download_video("abc123", "https://www.youtube.com/watch?v=abc123", tmp_path)
