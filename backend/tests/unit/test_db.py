from datetime import UTC, datetime
from unittest.mock import AsyncMock

from app.db import (
    get_by_video_id,
    get_full_record,
    list_recent,
    save_record,
)
from app.models import HistoryItem, VideoRecord

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
