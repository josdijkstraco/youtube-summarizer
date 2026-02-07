# Implementation Plan: YouTube Video Summary

**Branch**: `001-video-summary` | **Date**: 2026-02-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-video-summary/spec.md`

## Summary

Build a web application where users paste a YouTube video URL, the
system retrieves the video transcript via `youtube-transcript-api`,
generates a summary using OpenAI GPT-4o-mini, and displays it
alongside video metadata. The backend is a Python FastAPI service;
the frontend is a Vue.js 3 + Vite + TypeScript single-page app.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI, youtube-transcript-api, openai (backend); Vue 3, Vite (frontend)
**Storage**: N/A (no persistence — summaries are generated on-demand)
**Testing**: pytest + pytest-asyncio (backend), Vitest + Vue Test Utils (frontend)
**Target Platform**: Web browser (frontend), Linux/macOS server (backend)
**Project Type**: web (frontend + backend)
**Performance Goals**: Summary returned in < 30s for videos up to 30 min
**Constraints**: < 500ms p95 for backend processing excluding external API calls (OpenAI, YouTube); OpenAI API key required
**Scale/Scope**: Single-user session-based; 1 page, ~4 components

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Code Quality | All public interfaces have type annotations | PASS — Python type hints + TypeScript enforced |
| I. Code Quality | Automated linting/formatting configured | PASS — Ruff (Python), ESLint + Prettier (TS) |
| I. Code Quality | Dependencies justified (< 50-line threshold) | PASS — youtube-transcript-api, openai, FastAPI all solve complex problems |
| II. Testing Standards | Integration test for each user-facing feature | PASS — planned for all 3 user stories |
| II. Testing Standards | Unit tests for business logic | PASS — transcript parsing, URL validation, summarization service |
| II. Testing Standards | Mocks only for external services | PASS — mock YouTube API + OpenAI only |
| III. UX Consistency | Actionable error messages | PASS — mapped per FR-007 |
| III. UX Consistency | Consistent output format (JSON envelope) | PASS — all API responses use same structure |
| III. UX Consistency | Progress indicator for > 500ms ops | PASS — loading state per FR-006 |
| IV. Performance | API p95 < 500ms excluding external calls | PASS — backend logic is lightweight |
| IV. Performance | External API timeouts + retries | PASS — 30s timeout on OpenAI, retry with backoff |
| IV. Performance | Streaming for large payloads | N/A — summaries are small text responses (< 5KB) |

**Result**: All gates pass. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/001-video-summary/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── api.yaml         # OpenAPI 3.0 spec
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, CORS, route registration
│   ├── models.py            # Pydantic request/response models
│   ├── config.py            # Settings (env vars, OpenAI key)
│   └── services/
│       ├── __init__.py
│       ├── transcript.py    # YouTube transcript retrieval
│       ├── summarizer.py    # OpenAI GPT-4o-mini summarization
│       └── youtube.py       # URL parsing, validation, metadata
├── tests/
│   ├── unit/
│   │   ├── test_youtube.py      # URL parsing + validation
│   │   ├── test_transcript.py   # Transcript retrieval logic
│   │   └── test_summarizer.py   # Summarization logic
│   └── integration/
│       └── test_api.py          # Full API endpoint tests
├── requirements.txt
└── pyproject.toml

frontend/
├── src/
│   ├── App.vue
│   ├── main.ts
│   ├── components/
│   │   ├── UrlInput.vue         # URL input form with submit
│   │   ├── SummaryDisplay.vue   # Summary text + metadata card
│   │   ├── LoadingState.vue     # Progress indicator
│   │   └── ErrorMessage.vue     # Error display with guidance
│   ├── services/
│   │   └── api.ts               # Backend API client (fetch)
│   └── types/
│       └── index.ts             # TypeScript interfaces
├── tests/
│   └── components/
│       ├── UrlInput.spec.ts
│       └── SummaryDisplay.spec.ts
├── index.html
├── vite.config.ts
├── tsconfig.json
└── package.json
```

**Structure Decision**: Web application structure selected because the
feature has a distinct Vue.js frontend and Python FastAPI backend
communicating over HTTP. Both projects live at the repository root as
`frontend/` and `backend/` directories.

## Complexity Tracking

> No violations detected. All constitution gates pass.
