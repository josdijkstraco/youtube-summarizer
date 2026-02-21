from collections.abc import AsyncGenerator

import asyncpg  # type: ignore[import-untyped]
from fastapi import Request

from app.models import HistoryItem, VideoRecord


async def create_pool(dsn: str) -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn=dsn, min_size=2, max_size=10)


async def close_pool(pool: asyncpg.Pool) -> None:
    await pool.close()


async def get_db(request: Request) -> AsyncGenerator[asyncpg.Connection, None]:
    async with request.app.state.pool.acquire() as conn:
        yield conn


async def create_table(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS youtube_summarizer.summaries (
            id            BIGSERIAL    PRIMARY KEY,
            video_id      TEXT         NOT NULL UNIQUE,
            title         TEXT,
            thumbnail_url TEXT,
            summary       TEXT         NOT NULL,
            transcript    TEXT         NOT NULL,
            created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
        )
        """
    )


async def save_record(
    conn: asyncpg.Connection,
    video_id: str,
    title: str | None,
    thumbnail_url: str | None,
    summary: str,
    transcript: str,
) -> VideoRecord:
    # Step 1: try insert (silently skip if conflict)
    await conn.execute(
        "INSERT INTO youtube_summarizer.summaries (video_id, title, thumbnail_url, summary, transcript) "
        "VALUES ($1, $2, $3, $4, $5) ON CONFLICT (video_id) DO NOTHING",
        video_id,
        title,
        thumbnail_url,
        summary,
        transcript,
    )
    # Step 2: always fetch (inserted or existing)
    row = await conn.fetchrow("SELECT * FROM youtube_summarizer.summaries WHERE video_id = $1", video_id)
    return VideoRecord(**dict(row))


async def get_by_video_id(
    conn: asyncpg.Connection, video_id: str
) -> VideoRecord | None:
    row = await conn.fetchrow("SELECT * FROM youtube_summarizer.summaries WHERE video_id = $1", video_id)
    if row is None:
        return None
    return VideoRecord(**dict(row))


async def list_recent(conn: asyncpg.Connection, limit: int) -> list[HistoryItem]:
    rows = await conn.fetch(
        "SELECT video_id, title, thumbnail_url, summary, created_at "
        "FROM youtube_summarizer.summaries ORDER BY created_at DESC LIMIT $1",
        limit,
    )
    return [HistoryItem(**dict(row)) for row in rows]


async def get_full_record(
    conn: asyncpg.Connection, video_id: str
) -> VideoRecord | None:
    row = await conn.fetchrow("SELECT * FROM youtube_summarizer.summaries WHERE video_id = $1", video_id)
    if row is None:
        return None
    return VideoRecord(**dict(row))
