import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg  # type: ignore[import-untyped]
from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import APIError
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

from app.config import settings
from app.db import (
    close_pool,
    create_pool,
    create_table,
    get_by_video_id,
    get_db,
    get_full_record,
    list_recent,
    save_record,
)
from app.models import (
    ErrorResponse,
    FallacyAnalysisRequest,
    FallacyAnalysisResult,
    HistoryResponse,
    SummarizeRequest,
    SummarizeResponse,
    VideoMetadata,
    VideoRecord,
)
from app.services.fallacy_analyzer import analyze_fallacies
from app.services.summarizer import generate_summary
from app.services.transcript import calculate_duration, get_transcript
from app.services.youtube import extract_video_id, get_video_metadata

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.pool = await create_pool(str(settings.database_url))
    async with app.state.pool.acquire() as conn:
        await create_table(conn)
    try:
        yield
    finally:
        await close_pool(app.state.pool)


app = FastAPI(title="YouTube Video Summarizer API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/history")
async def get_history(
    limit: int = Query(default=50, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db),  # noqa: B008
) -> HistoryResponse:
    items = await list_recent(conn, limit)
    return HistoryResponse(items=items)


@app.get("/api/history/{video_id}", response_model=None)
async def get_history_item(
    video_id: str,
    conn: asyncpg.Connection = Depends(get_db),  # noqa: B008
) -> VideoRecord | JSONResponse:
    record = await get_full_record(conn, video_id)
    if record is None:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="not_found",
                message=f"No stored record found for video_id: {video_id}",
            ).model_dump(),
        )
    return record


@app.post("/api/summarize", response_model=None)
async def summarize_video(
    request: SummarizeRequest,
    conn: asyncpg.Connection = Depends(get_db),  # noqa: B008
) -> SummarizeResponse | JSONResponse:
    try:
        video_id = extract_video_id(request.url)
    except ValueError as e:
        msg = str(e)
        if "Playlist" in msg:
            return JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    error="playlist_not_supported",
                    message=msg,
                ).model_dump(),
            )
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error="invalid_url",
                message=msg,
                details=(
                    "Supported formats: youtube.com/watch?v=..., "
                    "youtu.be/..., youtube.com/shorts/..."
                ),
            ).model_dump(),
        )

    # Cache check: return stored result if available
    existing = await get_by_video_id(conn, video_id)
    if existing is not None:
        cached_metadata = VideoMetadata(
            video_id=existing.video_id,
            title=existing.title,
            thumbnail_url=existing.thumbnail_url,
        )
        return SummarizeResponse(
            summary=existing.summary,
            transcript=existing.transcript,
            metadata=cached_metadata,
            storage_warning=False,
        )

    try:
        full_text, segments = get_transcript(video_id)
    except VideoUnavailable:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="video_not_found",
                message=(
                    "The video could not be found. "
                    "It may have been removed or "
                    "the URL may be incorrect."
                ),
            ).model_dump(),
        )
    except (TranscriptsDisabled, NoTranscriptFound):
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="transcript_unavailable",
                message=(
                    "No transcript is available for this video. "
                    "Try a different video that has "
                    "captions enabled."
                ),
            ).model_dump(),
        )

    try:
        transcript_word_count = len(full_text.split())
        summary = generate_summary(
            full_text,
            transcript_word_count=transcript_word_count,
            length_percent=request.length_percent,
        )
    except APIError:
        return JSONResponse(
            status_code=502,
            content=ErrorResponse(
                error="summarization_failed",
                message=(
                    "Unable to generate summary at this time. Please try again later."
                ),
            ).model_dump(),
        )
    except Exception:
        logger.exception("Unexpected error during summarization")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="internal_error",
                message=("An unexpected error occurred. Please try again."),
            ).model_dump(),
        )

    # Fetch metadata — failures must not block the summary
    metadata: VideoMetadata | None = None
    try:
        metadata = get_video_metadata(video_id)
        duration = calculate_duration(segments)
        if metadata and duration is not None:
            metadata.duration_seconds = duration
    except Exception:
        logger.warning("Failed to retrieve metadata for %s", video_id)

    # Build response
    response = SummarizeResponse(
        summary=summary, transcript=full_text, metadata=metadata
    )

    # Persist to database — failures must not block the response
    try:
        await save_record(
            conn,
            video_id=video_id,
            title=metadata.title if metadata else None,
            thumbnail_url=metadata.thumbnail_url if metadata else None,
            summary=summary,
            transcript=full_text,
        )
    except Exception:
        logger.warning("Failed to persist record for %s", video_id)
        response.storage_warning = True

    return response


@app.post("/api/fallacies", response_model=None)
async def analyze_video_fallacies(
    request: FallacyAnalysisRequest,
) -> FallacyAnalysisResult | JSONResponse:
    try:
        video_id = extract_video_id(request.url)
    except ValueError as e:
        msg = str(e)
        if "Playlist" in msg:
            return JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    error="playlist_not_supported",
                    message=msg,
                ).model_dump(),
            )
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error="invalid_url",
                message=msg,
                details=(
                    "Supported formats: youtube.com/watch?v=..., "
                    "youtu.be/..., youtube.com/shorts/..."
                ),
            ).model_dump(),
        )

    try:
        full_text, _segments = get_transcript(video_id)
    except VideoUnavailable:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="video_not_found",
                message=(
                    "The video could not be found. "
                    "It may have been removed or "
                    "the URL may be incorrect."
                ),
            ).model_dump(),
        )
    except (TranscriptsDisabled, NoTranscriptFound):
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="transcript_unavailable",
                message=(
                    "No transcript is available for this video. "
                    "Try a different video that has "
                    "captions enabled."
                ),
            ).model_dump(),
        )

    result = analyze_fallacies(full_text)
    if result is None:
        return JSONResponse(
            status_code=502,
            content=ErrorResponse(
                error="analysis_failed",
                message=(
                    "Unable to analyze fallacies at this time. Please try again later."
                ),
            ).model_dump(),
        )

    return result
