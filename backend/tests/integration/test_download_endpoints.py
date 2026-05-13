"""Integration tests for the 3 video download endpoints."""
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import asyncpg
from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app

client = TestClient(app)

_VIDEO_ID = "test_video_id"


def _make_conn(download_status: str | None = None, download_path: str | None = None) -> AsyncMock:
    mock_conn = AsyncMock(spec=asyncpg.Connection)
    row = MagicMock()
    row.__getitem__ = MagicMock(
        side_effect=lambda k: {
            "download_status": download_status,
            "download_path": download_path,
            "downloaded_at": None,
        }.get(k)
    )
    mock_conn.fetchrow.return_value = row
    mock_conn.execute.return_value = None
    return mock_conn


def _override_db(mock_conn: AsyncMock):
    async def _dep():
        yield mock_conn
    app.dependency_overrides[get_db] = _dep


def _clear_override():
    app.dependency_overrides.pop(get_db, None)


class TestTriggerDownload:
    def test_returns_202_and_schedules_task(self) -> None:
        conn = _make_conn(download_status=None)
        _override_db(conn)
        app.state.pool = MagicMock()
        try:
            with patch("app.main._run_download"):
                res = client.post(f"/api/videos/{_VIDEO_ID}/download")
            assert res.status_code == 202
            assert res.json()["status"] == "pending"
        finally:
            _clear_override()
            del app.state.pool

    def test_returns_409_when_already_pending(self) -> None:
        conn = _make_conn(download_status="pending")
        _override_db(conn)
        try:
            res = client.post(f"/api/videos/{_VIDEO_ID}/download")
            assert res.status_code == 409
            assert res.json()["error"] == "download_in_progress"
        finally:
            _clear_override()

    def test_returns_200_when_already_ready(self) -> None:
        conn = _make_conn(download_status="ready")
        _override_db(conn)
        try:
            res = client.post(f"/api/videos/{_VIDEO_ID}/download")
            assert res.status_code == 200
            assert res.json()["status"] == "ready"
        finally:
            _clear_override()

    def test_returns_404_for_unknown_video(self) -> None:
        mock_conn = AsyncMock(spec=asyncpg.Connection)
        mock_conn.fetchrow.return_value = None

        async def _dep():
            yield mock_conn
        app.dependency_overrides[get_db] = _dep
        try:
            res = client.post(f"/api/videos/{_VIDEO_ID}/download")
            assert res.status_code == 404
        finally:
            _clear_override()


class TestGetDownloadStatus:
    def test_returns_current_status(self) -> None:
        conn = _make_conn(download_status="ready")
        _override_db(conn)
        try:
            res = client.get(f"/api/videos/{_VIDEO_ID}/download")
            assert res.status_code == 200
            assert res.json()["status"] == "ready"
            assert res.json()["video_id"] == _VIDEO_ID
        finally:
            _clear_override()

    def test_returns_null_status_for_not_downloaded(self) -> None:
        conn = _make_conn(download_status=None)
        _override_db(conn)
        try:
            res = client.get(f"/api/videos/{_VIDEO_ID}/download")
            assert res.status_code == 200
            assert res.json()["status"] is None
        finally:
            _clear_override()

    def test_returns_404_for_unknown_video(self) -> None:
        mock_conn = AsyncMock(spec=asyncpg.Connection)
        mock_conn.fetchrow.return_value = None

        async def _dep():
            yield mock_conn
        app.dependency_overrides[get_db] = _dep
        try:
            res = client.get(f"/api/videos/{_VIDEO_ID}/download")
            assert res.status_code == 404
        finally:
            _clear_override()


class TestStreamVideo:
    def test_returns_404_when_not_ready(self) -> None:
        conn = _make_conn(download_status="pending")
        _override_db(conn)
        try:
            res = client.get(f"/api/videos/{_VIDEO_ID}/stream")
            assert res.status_code == 404
        finally:
            _clear_override()

    def test_returns_404_when_file_missing_on_disk(self, tmp_path: Path) -> None:
        missing = str(tmp_path / "missing.mp4")
        conn = _make_conn(download_status="ready", download_path=missing)
        _override_db(conn)
        try:
            res = client.get(f"/api/videos/{_VIDEO_ID}/stream")
            assert res.status_code == 404
            assert res.json()["error"] == "file_not_found"
        finally:
            _clear_override()

    def test_serves_full_file_without_range(self, tmp_path: Path) -> None:
        video_file = tmp_path / "video.mp4"
        video_file.write_bytes(b"fake mp4 content here")
        conn = _make_conn(download_status="ready", download_path=str(video_file))
        _override_db(conn)
        try:
            res = client.get(f"/api/videos/{_VIDEO_ID}/stream")
            assert res.status_code == 200
            assert res.headers["accept-ranges"] == "bytes"
            assert res.content == b"fake mp4 content here"
        finally:
            _clear_override()

    def test_serves_partial_content_with_range_header(self, tmp_path: Path) -> None:
        content = b"0123456789abcdef"  # 16 bytes
        video_file = tmp_path / "video.mp4"
        video_file.write_bytes(content)
        conn = _make_conn(download_status="ready", download_path=str(video_file))
        _override_db(conn)
        try:
            res = client.get(
                f"/api/videos/{_VIDEO_ID}/stream",
                headers={"Range": "bytes=0-7"},
            )
            assert res.status_code == 206
            assert res.headers["content-range"] == f"bytes 0-7/{len(content)}"
            assert res.content == b"01234567"
        finally:
            _clear_override()

    def test_range_request_returns_correct_content_range_header(self, tmp_path: Path) -> None:
        content = b"x" * 1000
        video_file = tmp_path / "video.mp4"
        video_file.write_bytes(content)
        conn = _make_conn(download_status="ready", download_path=str(video_file))
        _override_db(conn)
        try:
            res = client.get(
                f"/api/videos/{_VIDEO_ID}/stream",
                headers={"Range": "bytes=100-199"},
            )
            assert res.status_code == 206
            assert res.headers["content-range"] == "bytes 100-199/1000"
            assert len(res.content) == 100
        finally:
            _clear_override()
