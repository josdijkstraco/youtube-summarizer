import json
from collections.abc import AsyncGenerator

import asyncpg  # type: ignore[import-untyped]
from fastapi import Request

from app.models import FallacyAnalysisResult, Highlight, HistoryItem, QaMessage, VideoRecord


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
            created_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),
            deleted_at       TIMESTAMPTZ  DEFAULT NULL
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
    # Add deleted_at column to existing tables if it doesn't exist
    await conn.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'youtube_summarizer'
                AND table_name = 'summaries'
                AND column_name = 'deleted_at'
            ) THEN
                ALTER TABLE youtube_summarizer.summaries
                ADD COLUMN deleted_at TIMESTAMPTZ DEFAULT NULL;
            END IF;
        END $$;
        """
    )
    # Add highlights column to existing tables if it doesn't exist
    await conn.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'youtube_summarizer'
                AND table_name = 'summaries'
                AND column_name = 'highlights'
            ) THEN
                ALTER TABLE youtube_summarizer.summaries
                ADD COLUMN highlights JSONB DEFAULT '[]'::jsonb;
            END IF;
        END $$;
        """
    )
    # Add qa_history column to existing tables if it doesn't exist
    await conn.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'youtube_summarizer'
                AND table_name = 'summaries'
                AND column_name = 'qa_history'
            ) THEN
                ALTER TABLE youtube_summarizer.summaries
                ADD COLUMN qa_history JSONB DEFAULT '[]'::jsonb;
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
    row = await conn.fetchrow(
        "SELECT * FROM youtube_summarizer.summaries WHERE video_id = $1 AND deleted_at IS NULL",
        video_id,
    )
    if row is None:
        return None
    return _parse_video_record(row)


async def list_recent(conn: asyncpg.Connection, limit: int) -> list[HistoryItem]:
    rows = await conn.fetch(
        "SELECT video_id, title, thumbnail_url, summary, created_at, "
        "(fallacy_analysis IS NOT NULL) as has_fallacy_analysis "
        "FROM youtube_summarizer.summaries "
        "WHERE deleted_at IS NULL "
        "ORDER BY created_at DESC LIMIT $1",
        limit,
    )
    return [HistoryItem(**dict(row)) for row in rows]


async def get_full_record(
    conn: asyncpg.Connection, video_id: str
) -> VideoRecord | None:
    row = await conn.fetchrow(
        "SELECT * FROM youtube_summarizer.summaries WHERE video_id = $1 AND deleted_at IS NULL",
        video_id,
    )
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
        raw = data["fallacy_analysis"]
        if isinstance(raw, str):
            raw = json.loads(raw)
        data["fallacy_analysis"] = FallacyAnalysisResult(**raw)
    # Parse highlights JSON
    if data.get("highlights"):
        raw = data["highlights"]
        if isinstance(raw, str):
            raw = json.loads(raw)
        data["highlights"] = [Highlight(**h) for h in raw]
    else:
        data["highlights"] = []
    # Parse qa_history JSON
    raw_qa = data.get("qa_history") or "[]"
    if isinstance(raw_qa, str):
        raw_qa = json.loads(raw_qa)
    data["qa_history"] = [QaMessage(**m) for m in raw_qa]
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


async def save_qa_history(
    conn: asyncpg.Connection, video_id: str, history: list[dict]
) -> None:
    await conn.execute(
        """
        UPDATE youtube_summarizer.summaries
           SET qa_history = $2
         WHERE video_id = $1
           AND deleted_at IS NULL
        """,
        video_id,
        json.dumps(history),
    )


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
    raw = row["fallacy_analysis"]
    if isinstance(raw, str):
        raw = json.loads(raw)
    return FallacyAnalysisResult(**raw)


async def soft_delete(conn: asyncpg.Connection, video_id: str) -> bool:
    """Soft-delete a video record. Returns True if a record was deleted."""
    result = await conn.execute(
        "UPDATE youtube_summarizer.summaries SET deleted_at = now() "
        "WHERE video_id = $1 AND deleted_at IS NULL",
        video_id,
    )
    return result == "UPDATE 1"


async def restore(conn: asyncpg.Connection, video_id: str) -> HistoryItem | None:
    """Restore a soft-deleted video record. Returns the restored item or None."""
    row = await conn.fetchrow(
        "UPDATE youtube_summarizer.summaries SET deleted_at = NULL "
        "WHERE video_id = $1 AND deleted_at IS NOT NULL "
        "RETURNING video_id, title, thumbnail_url, summary, created_at, "
        "(fallacy_analysis IS NOT NULL) as has_fallacy_analysis",
        video_id,
    )
    if row is None:
        return None
    return HistoryItem(**dict(row))


def _merge_highlights(highlights: list[Highlight]) -> list[Highlight]:
    """Sort and merge overlapping/adjacent highlight ranges."""
    if not highlights:
        return []
    sorted_hl = sorted(highlights, key=lambda h: h.start)
    merged: list[Highlight] = [sorted_hl[0]]
    for hl in sorted_hl[1:]:
        last = merged[-1]
        if hl.start <= last.end:
            merged[-1] = Highlight(start=last.start, end=max(last.end, hl.end))
        else:
            merged.append(hl)
    return merged


async def add_highlight(
    conn: asyncpg.Connection,
    video_id: str,
    start: int,
    end: int,
) -> list[Highlight] | None:
    """Add a highlight to a video record. Returns updated list or None if not found."""
    row = await conn.fetchrow(
        "SELECT highlights FROM youtube_summarizer.summaries WHERE video_id = $1 AND deleted_at IS NULL",
        video_id,
    )
    if row is None:
        return None
    raw = row["highlights"]
    if isinstance(raw, str):
        raw = json.loads(raw)
    current = [Highlight(**h) for h in (raw or [])]
    current.append(Highlight(start=start, end=end))
    merged = _merge_highlights(current)
    await conn.execute(
        "UPDATE youtube_summarizer.summaries SET highlights = $2 WHERE video_id = $1",
        video_id,
        json.dumps([h.model_dump() for h in merged]),
    )
    return merged


async def remove_highlight(
    conn: asyncpg.Connection,
    video_id: str,
    index: int,
) -> list[Highlight] | None:
    """Remove a highlight by index. Returns updated list or None if not found."""
    row = await conn.fetchrow(
        "SELECT highlights FROM youtube_summarizer.summaries WHERE video_id = $1 AND deleted_at IS NULL",
        video_id,
    )
    if row is None:
        return None
    raw = row["highlights"]
    if isinstance(raw, str):
        raw = json.loads(raw)
    current = [Highlight(**h) for h in (raw or [])]
    if 0 <= index < len(current):
        current.pop(index)
    await conn.execute(
        "UPDATE youtube_summarizer.summaries SET highlights = $2 WHERE video_id = $1",
        video_id,
        json.dumps([h.model_dump() for h in current]),
    )
    return current
