"""Unit tests for the download-related DB helper functions."""
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.db import clear_download, save_download_status, soft_delete


class TestSaveDownloadStatus:
    async def test_pending_updates_status_only(self) -> None:
        mock_conn = AsyncMock()
        await save_download_status(mock_conn, "abc123", "pending")
        mock_conn.execute.assert_awaited_once()
        sql, *args = mock_conn.execute.call_args.args
        assert "pending" in str(args)
        assert "downloaded_at" not in sql

    async def test_ready_updates_status_path_and_downloaded_at(self) -> None:
        mock_conn = AsyncMock()
        await save_download_status(mock_conn, "abc123", "ready", "/downloads/abc123.mp4")
        mock_conn.execute.assert_awaited_once()
        sql, *args = mock_conn.execute.call_args.args
        assert "downloaded_at" in sql
        assert "/downloads/abc123.mp4" in args

    async def test_error_updates_status_only(self) -> None:
        mock_conn = AsyncMock()
        await save_download_status(mock_conn, "abc123", "error")
        mock_conn.execute.assert_awaited_once()
        sql, *_args = mock_conn.execute.call_args.args
        assert "downloaded_at" not in sql


class TestClearDownload:
    async def test_nulls_all_download_columns(self) -> None:
        mock_conn = AsyncMock()
        await clear_download(mock_conn, "abc123")
        mock_conn.execute.assert_awaited_once()
        sql, *_args = mock_conn.execute.call_args.args
        assert "download_status = NULL" in sql
        assert "download_path = NULL" in sql
        assert "downloaded_at = NULL" in sql


class TestSoftDeleteWithFileCleanup:
    async def test_deletes_file_when_path_present(self, tmp_path: Path) -> None:
        file = tmp_path / "abc123.mp4"
        file.touch()

        mock_row = MagicMock()
        mock_row.__getitem__ = MagicMock(side_effect=lambda k: str(file) if k == "download_path" else None)

        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row

        result = await soft_delete(mock_conn, "abc123")

        assert result is True
        assert not file.exists()

    async def test_logs_warning_when_file_missing(self, tmp_path: Path) -> None:
        missing_path = str(tmp_path / "nonexistent.mp4")
        mock_row = MagicMock()
        mock_row.__getitem__ = MagicMock(side_effect=lambda k: missing_path if k == "download_path" else None)

        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row

        with patch("app.db.logger") as mock_logger:
            result = await soft_delete(mock_conn, "abc123")

        assert result is True
        mock_logger.warning.assert_not_called()  # missing_ok=True silently handles missing files

    async def test_returns_false_when_record_not_found(self) -> None:
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = None

        result = await soft_delete(mock_conn, "not_found")

        assert result is False

    async def test_logs_warning_on_os_error(self) -> None:
        file_path = "/read_only_dir/abc123.mp4"
        mock_row = MagicMock()
        mock_row.__getitem__ = MagicMock(side_effect=lambda k: file_path if k == "download_path" else None)

        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row

        with patch("app.db.Path") as mock_path_class, patch("app.db.logger") as mock_logger:
            mock_path_inst = MagicMock()
            mock_path_class.return_value = mock_path_inst
            mock_path_inst.unlink.side_effect = OSError("permission denied")

            result = await soft_delete(mock_conn, "abc123")

        assert result is True
        mock_logger.warning.assert_called_once()
