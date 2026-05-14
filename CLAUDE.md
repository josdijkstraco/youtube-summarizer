# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# youtube-summarizer-4.6 Development Guidelines

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, uvicorn |
| Database driver | asyncpg (async PostgreSQL) |
| AI | OpenAI SDK — `gpt-4o-mini` for summarization/fallacy, `gpt-4o` for Q&A |
| Transcripts | youtube-transcript-api |
| Video download | yt-dlp |
| Metadata | httpx → YouTube oEmbed |
| Config | pydantic-settings (loads `backend/.env`) |
| Frontend | Vue 3, TypeScript 5.5, Vite 5.4 |

## Commands

```bash
# Backend
cd backend
uvicorn app.main:app --reload --port 8002
pytest                              # all tests
pytest tests/unit/test_db.py        # single file
pytest -k test_name                 # single test by name
ruff check .
mypy app/

# Frontend
cd frontend
npm run dev        # dev server at :5173
npm run test       # vitest (jsdom)
npm run build      # type-check + production build
npm run lint

# Docker
docker-compose up -d --build
```

## Project Structure

```
backend/app/
  main.py          # FastAPI app + all 14 endpoints
  models.py        # Pydantic request/response models
  db.py            # PostgreSQL functions (asyncpg)
  config.py        # Settings from .env (includes download_dir)
  services/
    summarizer.py        # OpenAI summarization + chunking
    fallacy_analyzer.py  # Fallacy detection via OpenAI (JSON mode)
    qa.py                # Q&A via gpt-4o
    transcript.py        # YouTube transcript fetching + cookie auth
    youtube.py           # Video ID extraction, oEmbed metadata
    downloader.py        # yt-dlp video download (sync, run via asyncio.to_thread)
backend/tests/
  unit/            # Mocked unit tests (no DB/network)
  integration/     # FastAPI TestClient tests with mocked get_db
frontend/src/
  App.vue                # Root — all top-level state
  components/            # SummaryDisplay, HistoryPanel, VideoPlayer, etc.
  services/api.ts        # All API calls + ApiError class
  types/index.ts         # TypeScript interfaces (mirror Pydantic models)
downloads/               # Downloaded video files (served via /api/videos/{id}/stream)
```

## Architecture Decisions

### Cache-first: always check the database before calling OpenAI
Both `POST /api/summarize` and `POST /api/fallacies` query PostgreSQL before making any OpenAI call. Return the cached result immediately if found. This is the primary cost-control mechanism.

### Storage and metadata failures are non-fatal
`save_record()`, `save_fallacy_analysis()`, and `get_video_metadata()` are all wrapped in try/except. Failures are logged as warnings but never block the response. On save failure, set `storage_warning=True` on the response.

### Fallacy analysis is never overwritten
`save_fallacy_analysis()` uses `UPDATE ... WHERE fallacy_analysis IS NULL`. Once a result is stored, it stays. Don't add logic to force-refresh it without explicit user action.

### Records are never hard-deleted
Always use `soft_delete()` (sets `deleted_at = now()`). All SELECT queries filter `WHERE deleted_at IS NULL`. `restore()` clears `deleted_at`. Never use `DELETE FROM`.

### Highlights are always stored merged
After any add or remove, call `_merge_highlights()` and write the full merged list back. The list stored in JSONB should never contain overlapping ranges.

### The `youtube_summarizer` schema must exist before startup
`create_table()` creates the `summaries` table but not the schema. On a fresh database:
```sql
CREATE SCHEMA IF NOT EXISTS youtube_summarizer;
```

### Schema migrations are additive via `DO $$ ... $$` blocks
New columns are added with `ALTER TABLE ADD COLUMN IF NOT EXISTS` inside PL/pgSQL blocks in `create_table()`. Never drop or rename columns.

### Error responses always use `ErrorResponse`
Every non-2xx response must return `ErrorResponse(error="machine_code", message="human text")`. Use consistent error codes (see `api-endpoints.md` in `wiki/`).

### TypeScript types mirror Pydantic models exactly
When adding a field to a Pydantic model, add the matching field to `frontend/src/types/index.ts`. They must stay in sync — there is no codegen.

### No new dependencies without justification
The backend deps (fastapi, asyncpg, openai, httpx, youtube-transcript-api, yt-dlp, pydantic-settings) cover all current needs. Adding a dependency requires a clear reason it can't be done with what's already installed.

### Cookie auth for YouTube IP blocks
`transcript.py` checks for `/app/cookies.txt` (Netscape format). If present, it builds a `requests.Session` with those cookies and passes it to `YouTubeTranscriptApi`. In Docker this is mounted via `./cookies.txt:/app/cookies.txt:ro`.

### Chunked summarization for long transcripts
`summarizer.py` splits transcripts exceeding 400K characters (≈100K tokens) into word-boundary chunks, summarizes each, then combines. Token counts are aggregated across all calls. The 400K limit leaves headroom for the system prompt within gpt-4o-mini's 128K token context.

### Video download is a two-step async background flow
`POST /api/videos/{video_id}/download` sets status to `pending` and enqueues `_run_download_task` via FastAPI `BackgroundTasks`. The task calls `download_video()` (sync yt-dlp) inside `asyncio.to_thread`, then sets status to `ready` or `error`. The frontend polls `GET /api/videos/{video_id}/download` for status. Videos are capped at 3 hours (`_MAX_DURATION_SECONDS`). `GET /api/videos/{video_id}/stream` serves the file; if the file is missing on disk it auto-heals by calling `clear_download()` so the frontend can retry.
