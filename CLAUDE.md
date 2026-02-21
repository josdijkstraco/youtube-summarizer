# youtube-summarizer-4.6 Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-06

## Active Technologies
- Python 3.11+ (backend), TypeScript 5.x (frontend) + FastAPI, openai, youtube-transcript-api (backend); Vue 3, Vite (frontend) — no new dependencies (002-summary-length-slider)
- N/A (no persistence — percentage is sent per request, slider is session-only) (002-summary-length-slider)
- Python 3.13 (backend), TypeScript 5.x (frontend) + FastAPI, Pydantic, OpenAI Python SDK (backend); Vue 3, Vite (frontend) (003-fallacy-analysis)
- N/A — no persistence, on-demand analysis (003-fallacy-analysis)
- Python 3.13 (backend), TypeScript 5.x (frontend) + FastAPI, asyncpg (new), pydantic-settings, httpx, openai, youtube-transcript-api (backend); Vue 3, Vite (frontend) (004-postgres-video-storage)
- PostgreSQL on AWS RDS — single table `summaries`, schema managed via `CREATE TABLE IF NOT EXISTS` at startup (004-postgres-video-storage)

- Python 3.11+ (backend), TypeScript 5.x (frontend) + FastAPI, youtube-transcript-api, openai (backend); Vue 3, Vite (frontend) (001-video-summary)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+ (backend), TypeScript 5.x (frontend): Follow standard conventions

## Recent Changes
- 004-postgres-video-storage: Added Python 3.13 (backend), TypeScript 5.x (frontend) + FastAPI, asyncpg (new), pydantic-settings, httpx, openai, youtube-transcript-api (backend); Vue 3, Vite (frontend)
- 003-fallacy-analysis: Added Python 3.13 (backend), TypeScript 5.x (frontend) + FastAPI, Pydantic, OpenAI Python SDK (backend); Vue 3, Vite (frontend)
- 002-summary-length-slider: Added Python 3.11+ (backend), TypeScript 5.x (frontend) + FastAPI, openai, youtube-transcript-api (backend); Vue 3, Vite (frontend) — no new dependencies


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
