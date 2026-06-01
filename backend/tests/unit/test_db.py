import logging
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.db import (
    clear_download,
    delete_download,
    get_by_video_id,
    get_download_status,
    get_full_record,
    list_downloaded,
    list_recent,
    save_download_status,
    save_record,
    soft_delete,
)
from app.models import DownloadedItem, HistoryItem, VideoRecord

_FAKE_VIDEO_ID = "dQw4w9WgXcQ"
_FAKE_CREATED_AT = datetime(2026, 1, 1, tzinfo=UTC)

_FAKE_ROW: dict = {
    "id": 1,
    "video_id": _FAKE_VIDEO_ID,
    "title": "Test Video",
    "thumbnail_url": f"https://i.ytimg.com/vi/{_FAKE_VIDEO_ID}/hqdefault.jpg",
    "summary": "Test summary",
    "transcript": "Test transcript",
    "created_at": _FAKE_CREATED_AT,
}


class TestSaveRecord:
    async def test_save_record_inserts_and_returns_row(self) -> None:
        """save_record calls execute (INSERT) then fetchrow (SELECT)."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = _FAKE_ROW

        result = await save_record(
            mock_conn,
            video_id=_FAKE_VIDEO_ID,
            title="Test Video",
            thumbnail_url=f"https://i.ytimg.com/vi/{_FAKE_VIDEO_ID}/hqdefault.jpg",
            summary="Test summary",
            transcript="Test transcript",
        )

        mock_conn.execute.assert_awaited_once()
        mock_conn.fetchrow.assert_awaited_once()
        assert isinstance(result, VideoRecord)
        assert result.video_id == _FAKE_VIDEO_ID
        assert result.summary == "Test summary"
        assert result.transcript == "Test transcript"

    async def test_save_record_returns_existing_on_conflict(self) -> None:
        """When INSERT conflicts (DO NOTHING), SELECT still returns the existing row."""
        existing_row: dict = {
            "id": 42,
            "video_id": _FAKE_VIDEO_ID,
            "title": "Existing Title",
            "thumbnail_url": None,
            "summary": "Existing summary",
            "transcript": "Existing transcript",
            "created_at": _FAKE_CREATED_AT,
        }

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = None
        mock_conn.fetchrow.return_value = existing_row

        result = await save_record(
            mock_conn,
            video_id=_FAKE_VIDEO_ID,
            title="New Title",
            thumbnail_url=None,
            summary="New summary",
            transcript="New transcript",
        )

        assert result.id == 42
        assert result.summary == "Existing summary"
        assert result.transcript == "Existing transcript"


class TestGetByVideoId:
    async def test_get_by_video_id_returns_none_when_missing(self) -> None:
        """get_by_video_id returns None when no row matches the video_id."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = None

        result = await get_by_video_id(mock_conn, "unknownvideo1")

        assert result is None
        mock_conn.fetchrow.assert_awaited_once()

    async def test_get_by_video_id_returns_record_when_found(self) -> None:
        """get_by_video_id returns a VideoRecord when the video_id exists."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = _FAKE_ROW

        result = await get_by_video_id(mock_conn, _FAKE_VIDEO_ID)

        assert isinstance(result, VideoRecord)
        assert result.video_id == _FAKE_VIDEO_ID


class TestListRecent:
    async def test_list_recent_returns_items_in_order(self) -> None:
        """list_recent returns HistoryItems in newest-first order."""
        older_created_at = datetime(2025, 12, 1, tzinfo=UTC)
        rows = [
            {
                "video_id": "newvideo1234",
                "title": "Newer Video",
                "thumbnail_url": None,
                "summary": "Newer summary",
                "created_at": _FAKE_CREATED_AT,
            },
            {
                "video_id": "oldvideo1234",
                "title": "Older Video",
                "thumbnail_url": None,
                "summary": "Older summary",
                "created_at": older_created_at,
            },
        ]

        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = rows

        results = await list_recent(mock_conn, limit=50)

        mock_conn.fetch.assert_awaited_once()
        assert len(results) == 2
        assert all(isinstance(r, HistoryItem) for r in results)
        assert results[0].video_id == "newvideo1234"
        assert results[1].video_id == "oldvideo1234"

    async def test_list_recent_passes_limit_to_query(self) -> None:
        """list_recent passes the limit parameter to the DB query."""
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = []

        await list_recent(mock_conn, limit=10)

        call_args = mock_conn.fetch.call_args
        assert 10 in call_args.args


class TestListDownloaded:
    async def test_returns_downloaded_items_in_order(self) -> None:
        """list_downloaded returns DownloadedItems preserving row order."""
        older_downloaded_at = datetime(2025, 12, 1, tzinfo=UTC)
        rows = [
            {
                "video_id": "newvideo1234",
                "title": "Newer Video",
                "thumbnail_url": None,
                "downloaded_at": _FAKE_CREATED_AT,
            },
            {
                "video_id": "oldvideo1234",
                "title": "Older Video",
                "thumbnail_url": None,
                "downloaded_at": older_downloaded_at,
            },
        ]

        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = rows

        results = await list_downloaded(mock_conn)

        mock_conn.fetch.assert_awaited_once()
        assert len(results) == 2
        assert all(isinstance(r, DownloadedItem) for r in results)
        assert results[0].video_id == "newvideo1234"
        assert results[1].video_id == "oldvideo1234"

    async def test_query_filters_ready_non_deleted_desc(self) -> None:
        """The SQL enforces ready-only, non-deleted, and newest-first ordering."""
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = []

        await list_downloaded(mock_conn)

        sql = mock_conn.fetch.call_args.args[0]
        assert "download_status = 'ready'" in sql
        assert "deleted_at IS NULL" in sql
        assert "ORDER BY downloaded_at DESC" in sql

    async def test_returns_empty_list_when_no_rows(self) -> None:
        """list_downloaded returns an empty list when no rows match."""
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = []

        results = await list_downloaded(mock_conn)

        assert results == []


class TestGetFullRecord:
    async def test_get_full_record_returns_transcript(self) -> None:
        """get_full_record returns a VideoRecord including the full transcript field."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = _FAKE_ROW

        result = await get_full_record(mock_conn, _FAKE_VIDEO_ID)

        assert isinstance(result, VideoRecord)
        assert result.transcript == "Test transcript"
        assert result.video_id == _FAKE_VIDEO_ID

    async def test_get_full_record_returns_none_when_missing(self) -> None:
        """get_full_record returns None when the video_id is not in the DB."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = None

        result = await get_full_record(mock_conn, "notfound1234")

        assert result is None


class TestSaveDownloadStatus:
    async def test_sets_pending_status(self) -> None:
        mock_conn = AsyncMock()

        await save_download_status(mock_conn, _FAKE_VIDEO_ID, "pending")

        mock_conn.execute.assert_awaited_once()
        sql, vid, status, path, error = mock_conn.execute.call_args.args
        assert vid == _FAKE_VIDEO_ID
        assert status == "pending"
        assert path is None
        assert error is None

    async def test_sets_ready_status_with_path(self) -> None:
        mock_conn = AsyncMock()

        await save_download_status(
            mock_conn, _FAKE_VIDEO_ID, "ready", path="/downloads/abc.mp4"
        )

        mock_conn.execute.assert_awaited_once()
        _, vid, status, path, error = mock_conn.execute.call_args.args
        assert vid == _FAKE_VIDEO_ID
        assert status == "ready"
        assert path == "/downloads/abc.mp4"
        assert error is None

    async def test_sets_error_status_with_message(self) -> None:
        mock_conn = AsyncMock()

        await save_download_status(
            mock_conn, _FAKE_VIDEO_ID, "error", error="geo-blocked"
        )

        mock_conn.execute.assert_awaited_once()
        _, vid, status, path, error = mock_conn.execute.call_args.args
        assert vid == _FAKE_VIDEO_ID
        assert status == "error"
        assert path is None
        assert error == "geo-blocked"


class TestClearDownload:
    async def test_nulls_all_download_columns(self) -> None:
        mock_conn = AsyncMock()

        await clear_download(mock_conn, _FAKE_VIDEO_ID)

        mock_conn.execute.assert_awaited_once()
        sql, vid = mock_conn.execute.call_args.args
        assert vid == _FAKE_VIDEO_ID
        assert "NULL" in sql


class TestGetDownloadStatus:
    async def test_returns_none_when_no_row(self) -> None:
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = None

        result = await get_download_status(mock_conn, _FAKE_VIDEO_ID)

        assert result is None

    async def test_returns_dict_when_row_found(self) -> None:
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {
            "download_status": "ready",
            "download_path": "/downloads/abc.mp4",
            "downloaded_at": _FAKE_CREATED_AT,
            "error_message": None,
        }

        result = await get_download_status(mock_conn, _FAKE_VIDEO_ID)

        assert isinstance(result, dict)
        assert result["download_status"] == "ready"
        assert result["download_path"] == "/downloads/abc.mp4"
        assert result["error_message"] is None


class TestSoftDelete:
    async def test_removes_file_and_returns_true(self) -> None:
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {"download_path": "/downloads/abc.mp4"}
        mock_conn.execute.return_value = "UPDATE 1"

        with patch("app.db.os.remove") as mock_remove:
            result = await soft_delete(mock_conn, _FAKE_VIDEO_ID)

        mock_remove.assert_called_once_with("/downloads/abc.mp4")
        assert result is True

    async def test_succeeds_when_file_missing_logs_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {"download_path": "/downloads/gone.mp4"}
        mock_conn.execute.return_value = "UPDATE 1"

        with (
            patch("app.db.os.remove", side_effect=OSError("no such file")),
            caplog.at_level(logging.WARNING, logger="app.db"),
        ):
            result = await soft_delete(mock_conn, _FAKE_VIDEO_ID)

        assert result is True
        assert any("gone.mp4" in msg for msg in caplog.messages)

    async def test_clears_download_columns_even_on_oserror(self) -> None:
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {"download_path": "/downloads/abc.mp4"}
        mock_conn.execute.return_value = "UPDATE 1"

        with patch("app.db.os.remove", side_effect=OSError("no such file")):
            await soft_delete(mock_conn, _FAKE_VIDEO_ID)

        # execute called twice: once by clear_download, once by soft_delete's UPDATE
        assert mock_conn.execute.await_count == 2

    async def test_returns_false_when_no_record(self) -> None:
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = None

        result = await soft_delete(mock_conn, _FAKE_VIDEO_ID)

        assert result is False
        mock_conn.execute.assert_not_awaited()


class TestDeleteDownload:
    async def test_file_exists_deleted_returns_true(self) -> None:
        """File on disk is removed, DB columns cleared, returns True."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {"download_path": "/downloads/abc.mp4"}

        with (
            patch("app.db.os.remove") as mock_remove,
            patch("app.db.clear_download", new_callable=AsyncMock) as mock_clear,
        ):
            result = await delete_download(mock_conn, _FAKE_VIDEO_ID)

        mock_remove.assert_called_once_with("/downloads/abc.mp4")
        mock_clear.assert_awaited_once_with(mock_conn, _FAKE_VIDEO_ID)
        assert result is True

    async def test_file_missing_logs_warning_returns_false(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """FileNotFoundError logs a warning, still clears columns, returns False."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {"download_path": "/downloads/gone.mp4"}

        with (
            patch("app.db.os.remove", side_effect=FileNotFoundError()),
            patch("app.db.clear_download", new_callable=AsyncMock) as mock_clear,
            caplog.at_level(logging.WARNING, logger="app.db"),
        ):
            result = await delete_download(mock_conn, _FAKE_VIDEO_ID)

        assert result is False
        mock_clear.assert_awaited_once_with(mock_conn, _FAKE_VIDEO_ID)
        assert any("gone.mp4" in msg for msg in caplog.messages)

    async def test_other_oserror_logs_warning_clears_db(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Non-FileNotFoundError OSError logs a warning and still clears DB columns."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {"download_path": "/downloads/locked.mp4"}

        with (
            patch("app.db.os.remove", side_effect=OSError("permission denied")),
            patch("app.db.clear_download", new_callable=AsyncMock) as mock_clear,
            caplog.at_level(logging.WARNING, logger="app.db"),
        ):
            result = await delete_download(mock_conn, _FAKE_VIDEO_ID)

        assert result is False
        mock_clear.assert_awaited_once_with(mock_conn, _FAKE_VIDEO_ID)
        assert any("locked.mp4" in msg for msg in caplog.messages)

    async def test_idempotent_when_download_path_null(self) -> None:
        """When download_path is NULL, no file deletion is attempted, returns False."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {"download_path": None}

        with (
            patch("app.db.os.remove") as mock_remove,
            patch("app.db.clear_download", new_callable=AsyncMock) as mock_clear,
        ):
            result = await delete_download(mock_conn, _FAKE_VIDEO_ID)

        mock_remove.assert_not_called()
        mock_clear.assert_awaited_once_with(mock_conn, _FAKE_VIDEO_ID)
        assert result is False

    async def test_idempotent_when_no_row(self) -> None:
        """When no DB record exists (soft-deleted or missing), no deletion, False."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = None

        with (
            patch("app.db.os.remove") as mock_remove,
            patch("app.db.clear_download", new_callable=AsyncMock) as mock_clear,
        ):
            result = await delete_download(mock_conn, _FAKE_VIDEO_ID)

        mock_remove.assert_not_called()
        mock_clear.assert_awaited_once_with(mock_conn, _FAKE_VIDEO_ID)
        assert result is False
