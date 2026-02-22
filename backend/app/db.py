import json
from collections.abc import AsyncGenerator

import asyncpg  # type: ignore[import-untyped]
from fastapi import Request

from app.models import FallacyAnalysisResult, HistoryItem, VideoRecord


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
            id               BIGSERIAL    PRIMARY KEY,
            video_id         TEXT         NOT NULL UNIQUE,
            title            TEXT,
            thumbnail_url    TEXT,
            summary          TEXT         NOT NULL,
            transcript       TEXT         NOT NULL,
            fallacy_analysis JSONB        DEFAULT NULL,
            created_at       TIMESTAMPTZ  NOT NULL DEFAULT now()
        )
        """
    )
    # Add fallacy_analysis column to existing tables if it doesn't exist
    await conn.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'youtube_summarizer'
                AND table_name = 'summaries'
                AND column_name = 'fallacy_analysis'
            ) THEN
                ALTER TABLE youtube_summarizer.summaries
                ADD COLUMN fallacy_analysis JSONB DEFAULT NULL;
            END IF;
        END $$;
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
    return _parse_video_record(row)


async def get_by_video_id(
    conn: asyncpg.Connection, video_id: str
) -> VideoRecord | None:
    row = await conn.fetchrow("SELECT * FROM youtube_summarizer.summaries WHERE video_id = $1", video_id)
    if row is None:
        return None
    return _parse_video_record(row)


async def list_recent(conn: asyncpg.Connection, limit: int) -> list[HistoryItem]:
    rows = await conn.fetch(
        "SELECT video_id, title, thumbnail_url, summary, created_at, "
        "(fallacy_analysis IS NOT NULL) as has_fallacy_analysis "
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
    return _parse_video_record(row)


def _parse_video_record(row: asyncpg.Record | None) -> VideoRecord | None:
    """Parse a database row into a VideoRecord, handling fallacy_analysis JSON."""
    if row is None:
        return None
    data = dict(row)
    # Parse fallacy_analysis JSON if present
    if data.get("fallacy_analysis"):
        data["fallacy_analysis"] = FallacyAnalysisResult(**data["fallacy_analysis"])
    return VideoRecord(**data)


async def save_fallacy_analysis(
    conn: asyncpg.Connection,
    video_id: str,
    fallacy_analysis: dict,
) -> bool:
    """Save fallacy analysis for a video.

    Returns True if saved, False if analysis already exists (no overwrite).
    """
    result = await conn.execute(
        """
        UPDATE youtube_summarizer.summaries
        SET fallacy_analysis = $2
        WHERE video_id = $1 AND fallacy_analysis IS NULL
        """,
        video_id,
        json.dumps(fallacy_analysis),
    )
    return result == "UPDATE 1"


async def get_fallacy_analysis(
    conn: asyncpg.Connection,
    video_id: str,
) -> FallacyAnalysisResult | None:
    """Get fallacy analysis for a video."""
    row = await conn.fetchrow(
        "SELECT fallacy_analysis FROM youtube_summarizer.summaries WHERE video_id = $1",
        video_id,
    )
    if row is None or row["fallacy_analysis"] is None:
        return None
    return FallacyAnalysisResult(**row["fallacy_analysis"])
