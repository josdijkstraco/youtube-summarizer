# Implementation Plan: Postgres Video Storage

**Branch**: `004-postgres-video-storage` | **Date**: 2026-02-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-postgres-video-storage/spec.md`

## Summary

Persist each processed YouTube video (URL, thumbnail, summary, transcript) to an AWS-hosted PostgreSQL database using asyncpg. The `/api/summarize` endpoint gains a cache-check before processing (return stored result for known videos) and a persist-after-processing side-effect. Two new endpoints expose stored records: `GET /api/history` (list, no transcript) and `GET /api/history/{video_id}` (full record). The frontend adds a sticky history sidebar panel that loads on mount and refreshes after each new summary.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI, asyncpg (new), pydantic-settings, httpx, openai, youtube-transcript-api (backend); Vue 3, Vite (frontend)
**Storage**: PostgreSQL on AWS RDS — single table `summaries`, schema managed via `CREATE TABLE IF NOT EXISTS` at startup
**Testing**: pytest + pytest-asyncio (backend); no dedicated frontend test tooling currently present
**Target Platform**: Linux server (backend), browser (frontend)
**Project Type**: Web application (backend/ + frontend/ directories)
**Performance Goals**: History list p95 < 500ms; cache-hit summarize response < 1s (SC-001, SC-003)
**Constraints**: Transcripts are unbounded text — `TEXT` column, no size cap; constitution requires paginating large payloads (SC-004: capped at 50 items); DB failure must never block the summarize response (FR-006, SC-005)
**Scale/Scope**: Single shared Postgres instance; no multi-tenancy; no auth

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Code Quality — single responsibility | PASS | `db.py` module owns pool/queries; `main.py` calls it; history routes separated |
| I. Code Quality — type annotations | PASS | All new functions will have full type annotations; asyncpg `Record` typed via TypedDict or cast |
| I. Code Quality — linting/formatting | PASS | ruff already enforced; no new tooling needed |
| I. Code Quality — no dead code | PASS | No legacy patterns introduced |
| I. Code Quality — dependency justified | PASS | asyncpg solves async Postgres connectivity; cannot be replaced with <50 lines |
| II. Testing — integration test per user feature | PASS | Integration test for summarize+persist+cache-hit flow; GET /api/history; GET /api/history/{id} |
| II. Testing — unit tests for business logic | PASS | Unit tests for DB module functions (with mocked connection); upsert logic; cache-hit branch |
| II. Testing — deterministic tests | PASS | DB calls will be mocked in unit tests; integration tests use a real or in-memory test DB |
| II. Testing — mocks only for external services | PASS | asyncpg connection mocked in unit tests; real DB used in integration tests |
| III. UX — actionable error messages | PASS | `storage_warning` flag on failed persist; history error shows retry button |
| III. UX — consistent response envelope | PASS | Existing `ErrorResponse` schema reused for new endpoints |
| III. UX — loading state >500ms | PASS | `historyLoading` ref drives inline loading indicator in `HistoryPanel` |
| IV. Performance — API p95 < 500ms excl. external | PASS | History list is a single indexed SELECT; cache hit is SELECT + early return |
| IV. Performance — stable memory | PASS | Connection pool with max_size=10; no unbounded accumulation |
| IV. Performance — large payloads paginated | PASS | `/api/history` caps at `limit` (default 50, max 100); transcript excluded from list endpoint |
| IV. Performance — external call timeouts | PASS | asyncpg pool has connection timeout; no new external calls introduced |

**Post-design re-check**: All principles satisfied. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/004-postgres-video-storage/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── openapi.yaml     # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── config.py              # MODIFY: add database_url: PostgresDsn field
│   ├── db.py                  # NEW: pool lifecycle helpers + all SQL query functions
│   ├── main.py                # MODIFY: add lifespan, history routes, update /api/summarize
│   └── models.py              # MODIFY: add HistoryItem, HistoryResponse, VideoRecord models;
│                              #         add storage_warning to SummarizeResponse
└── tests/
    ├── integration/
    │   └── test_api.py        # MODIFY: add history + cache-hit integration tests
    └── unit/
        └── test_db.py         # NEW: unit tests for db.py functions (mocked connection)

frontend/
└── src/
    ├── App.vue                # MODIFY: two-column grid layout, add <HistoryPanel />, reload on submit
    ├── types/index.ts         # MODIFY: add HistoryItem, HistoryResponse interfaces
    ├── services/api.ts        # MODIFY: add fetchHistory() function
    └── components/
        ├── HistoryPanel.vue   # NEW: sidebar with loading/empty/error/list states
        └── HistoryCard.vue    # NEW: single video card (thumbnail, link, truncated summary)
```

**Structure Decision**: Web application layout (Option 2). Backend files land in `backend/app/`; frontend files in `frontend/src/`. No new top-level directories.

## Complexity Tracking

> No constitution violations require justification for this feature.
