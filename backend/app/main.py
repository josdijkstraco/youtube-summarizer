import logging
import time
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
    add_highlight,
    close_pool,
    create_pool,
    create_table,
    get_by_video_id,
    get_db,
    get_fallacy_analysis,
    get_full_record,
    list_recent,
    remove_highlight,
    restore,
    save_fallacy_analysis,
    save_qa_history,
    save_record,
    soft_delete,
)
from app.models import (
    AskRequest,
    AskResponse,
    ErrorResponse,
    FallacyAnalysisRequest,
    FallacyAnalysisResult,
    Highlight,
    HighlightRequest,
    HistoryItem,
    HistoryResponse,
    SummarizeRequest,
    SummarizeResponse,
    SummaryStats,
    VideoMetadata,
    VideoRecord,
)
from app.services.fallacy_analyzer import analyze_fallacies
from app.services.qa import ask_question
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
    allow_methods=["GET", "POST", "DELETE"],
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


@app.delete("/api/history/{video_id}", status_code=204)
async def delete_history_item(
    video_id: str,
    conn: asyncpg.Connection = Depends(get_db),  # noqa: B008
) -> None:
    deleted = await soft_delete(conn, video_id)
    if not deleted:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="not_found",
                message=f"No record found for video_id: {video_id}",
            ).model_dump(),
        )


@app.post("/api/history/{video_id}/restore", response_model=None)
async def restore_history_item(
    video_id: str,
    conn: asyncpg.Connection = Depends(get_db),  # noqa: B008
) -> HistoryItem | JSONResponse:
    item = await restore(conn, video_id)
    if item is None:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="not_found",
                message=f"No deleted record found for video_id: {video_id}",
            ).model_dump(),
        )
    return item


@app.post("/api/history/{video_id}/highlights", response_model=None)
async def add_highlight_endpoint(
    video_id: str,
    body: HighlightRequest,
    conn: asyncpg.Connection = Depends(get_db),  # noqa: B008
) -> list[Highlight] | JSONResponse:
    result = await add_highlight(conn, video_id, body.start, body.end)
    if result is None:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="not_found",
                message=f"No stored record found for video_id: {video_id}",
            ).model_dump(),
        )
    return result


@app.delete("/api/history/{video_id}/highlights/{index}", response_model=None)
async def remove_highlight_endpoint(
    video_id: str,
    index: int,
    conn: asyncpg.Connection = Depends(get_db),  # noqa: B008
) -> list[Highlight] | JSONResponse:
    result = await remove_highlight(conn, video_id, index)
    if result is None:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="not_found",
                message=f"No stored record found for video_id: {video_id}",
            ).model_dump(),
        )
    return result


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
            highlights=existing.highlights,
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
        t0 = time.monotonic()
        summary_result = generate_summary(
            full_text,
            transcript_word_count=transcript_word_count,
            length_percent=request.length_percent,
        )
        duration = time.monotonic() - t0
        summary = summary_result.content
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
    stats = SummaryStats(
        chars_in=len(full_text),
        chars_out=len(summary),
        total_tokens=summary_result.total_prompt_tokens
        + summary_result.total_completion_tokens,
        generation_seconds=round(duration, 2),
    )
    response = SummarizeResponse(
        summary=summary, transcript=full_text, metadata=metadata, stats=stats
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
    conn: asyncpg.Connection = Depends(get_db),  # noqa: B008
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

    # Check for cached analysis first
    cached = await get_fallacy_analysis(conn, video_id)
    if cached is not None:
        return cached

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

    # Save to database (fire and forget - don't block response)
    try:
        await save_fallacy_analysis(conn, video_id, result.model_dump())
    except Exception:
        logger.warning("Failed to save fallacy analysis for %s", video_id)

    return result


@app.post("/api/ask", response_model=AskResponse)
async def ask(request: AskRequest, conn: asyncpg.Connection = Depends(get_db)) -> AskResponse:  # noqa: B008
    answer = await ask_question(
        transcript=request.transcript,
        question=request.question,
        history=[m.model_dump() for m in request.history],
    )
    if request.video_id:
        full_history = [m.model_dump() for m in request.history]
        full_history.append({"role": "user", "content": request.question})
        full_history.append({"role": "assistant", "content": answer})
        try:
            await save_qa_history(conn, request.video_id, full_history)
        except Exception:
            logger.warning("Failed to save qa_history for %s", request.video_id)
    return AskResponse(answer=answer)
