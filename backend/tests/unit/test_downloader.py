import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import app.services.downloader as downloader_module
from app.services.downloader import (
    delete_video_file,
    get_download_status,
    start_download,
)


class TestGetDownloadStatus:
    def test_returns_not_downloaded_when_no_file_and_not_downloading(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(downloader_module, "DATA_DIR", tmp_path)
        monkeypatch.setattr(downloader_module, "_downloading", set())
        assert get_download_status("abc123") == "not_downloaded"

    def test_returns_downloading_when_video_id_in_set(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(downloader_module, "DATA_DIR", tmp_path)
        monkeypatch.setattr(downloader_module, "_downloading", {"abc123"})
        assert get_download_status("abc123") == "downloading"

    def test_returns_ready_when_mp4_file_exists(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(downloader_module, "DATA_DIR", tmp_path)
        monkeypatch.setattr(downloader_module, "_downloading", set())
        (tmp_path / "abc123.mp4").touch()
        assert get_download_status("abc123") == "ready"


class TestDeleteVideoFile:
    def test_removes_file_when_it_exists(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(downloader_module, "DATA_DIR", tmp_path)
        mp4 = tmp_path / "abc123.mp4"
        mp4.touch()
        delete_video_file("abc123")
        assert not mp4.exists()

    def test_is_noop_when_file_absent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(downloader_module, "DATA_DIR", tmp_path)
        delete_video_file("abc123")  # must not raise


class TestStartDownload:
    async def test_calls_ytdlp_with_correct_format(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(downloader_module, "DATA_DIR", tmp_path)
        monkeypatch.setattr(downloader_module, "_downloading", set())
        monkeypatch.setattr(downloader_module, "COOKIES_PATH", tmp_path / "no_cookies.txt")

        with patch("app.services.downloader.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock()
            await start_download("abc123")

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "yt-dlp" in args
        assert "-f" in args
        assert downloader_module.FORMAT in args
        assert f"https://www.youtube.com/watch?v=abc123" in args

    async def test_appends_cookiefile_when_cookies_exist(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(downloader_module, "DATA_DIR", tmp_path)
        monkeypatch.setattr(downloader_module, "_downloading", set())
        cookies_path = tmp_path / "cookies.txt"
        cookies_path.touch()
        monkeypatch.setattr(downloader_module, "COOKIES_PATH", cookies_path)

        with patch("app.services.downloader.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock()
            await start_download("abc123")

        args = mock_run.call_args[0][0]
        assert "--cookiefile" in args
        assert str(cookies_path) in args

    async def test_is_noop_when_already_downloading(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(downloader_module, "DATA_DIR", tmp_path)
        downloading_set: set[str] = {"abc123"}
        monkeypatch.setattr(downloader_module, "_downloading", downloading_set)

        with patch("app.services.downloader.subprocess.run") as mock_run:
            await start_download("abc123")

        mock_run.assert_not_called()
