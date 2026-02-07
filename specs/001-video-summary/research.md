# Research: YouTube Video Summary

**Feature Branch**: `001-video-summary`
**Date**: 2026-02-06

## 1. YouTube Transcript Retrieval

**Decision**: Use `youtube-transcript-api` Python library

**Rationale**: The most widely used Python library for fetching YouTube
transcripts without requiring a YouTube Data API key. It supports both
manual and auto-generated captions, multiple languages, and provides
specific exception types for robust error handling.

**Key Findings**:
- Install: `pip install youtube-transcript-api`
- Primary API: `YouTubeTranscriptApi.fetch(video_id)` returns a list
  of transcript segments with `text`, `start`, and `duration` fields
- Supports language selection via `languages` parameter
- Auto-generated captions: use `find_generated_transcript(['en'])` on
  the transcript list
- Exception types for error handling:
  - `TranscriptsDisabled`: subtitles disabled for the video
  - `NoTranscriptFound`: no transcript in requested languages
  - `VideoUnavailable`: video does not exist
  - `InvalidVideoId`: malformed video ID
  - `IpBlocked` / `RequestBlocked`: rate limiting or access issues
- No API key required — scrapes YouTube's caption endpoint directly

**Alternatives Considered**:
- YouTube Data API v3: Requires API key, quota management, and
  separate captions download flow. Overkill for this use case.
- `yt-dlp` subtitle extraction: Heavier dependency, designed for
  video downloading. Transcript-only use is wasteful.

**Gotchas**:
- YouTube may rate-limit or block IPs with heavy usage
- Some videos have captions disabled by the uploader
- Transcript segments need concatenation for full text

## 2. AI Summarization

**Decision**: Use OpenAI GPT-4o-mini via the `openai` Python SDK

**Rationale**: User explicitly requested GPT-4o-mini. It offers a
good balance of quality and cost for summarization tasks with a 128K
token context window (sufficient for most video transcripts).

**Key Findings**:
- Model ID: `gpt-4o-mini` (not "GPT-40-MINI" — user likely meant
  this; the "0" vs "o" confusion is common)
- Context window: 128,000 tokens input, 16,384 tokens output
- Cost: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
  (very affordable for summarization)
- Install: `pip install openai`
- API key required via `OPENAI_API_KEY` environment variable
- Streaming supported for progressive output to the user

**Long Transcript Strategy**:
- A 3-hour video transcript is approximately 30,000-50,000 words
  (~40,000-65,000 tokens). This fits within GPT-4o-mini's 128K
  context window for most videos.
- For extremely long videos exceeding the context window: use a
  chunked summarization approach — split transcript into segments,
  summarize each, then summarize the summaries.

**Alternatives Considered**:
- Claude API: Not requested by user.
- Local models (Ollama/llama.cpp): Higher latency, lower quality
  for summarization, more complex deployment.

## 3. Backend Framework

**Decision**: FastAPI (Python)

**Rationale**: User explicitly requested Python backend. FastAPI is
the modern standard for Python APIs — async by default, automatic
OpenAPI docs, excellent type validation with Pydantic, built-in CORS
middleware.

**Key Findings**:
- CORS: `CORSMiddleware` with `allow_origins` for the Vue dev server
  (localhost:5173)
- Async: FastAPI natively supports `async def` endpoints for
  non-blocking I/O (important since transcript fetch + OpenAI call
  are I/O-bound)
- Pydantic models for request/response validation with type safety
- Streaming: `StreamingResponse` available for real-time summary
  delivery, but standard JSON response is simpler and sufficient
  given GPT-4o-mini's speed

**Project Structure**:
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app, CORS, routes
│   ├── models.py          # Pydantic request/response models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── transcript.py  # YouTube transcript retrieval
│   │   ├── summarizer.py  # OpenAI summarization
│   │   └── youtube.py     # URL parsing + metadata
│   └── config.py          # Settings/env vars
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── pyproject.toml
```

## 4. Frontend Framework

**Decision**: Vue.js 3 with Vite and TypeScript

**Rationale**: User requested "Veed-based" frontend, interpreted as
Vue.js (phonetically similar). Vite is the standard build tool for
Vue 3 projects.

**Key Findings**:
- Setup: `npm create vue@latest` scaffolds Vue 3 + Vite + TypeScript
- Composition API with `<script setup lang="ts">` for type-safe
  reactive state
- HTTP client: Native `fetch` API (no axios needed for simple
  POST requests — avoids unnecessary dependency per constitution
  Principle I)
- Loading states: Use `ref<boolean>` for loading, error, and data
  state management

**Project Structure**:
```
frontend/
├── src/
│   ├── App.vue
│   ├── main.ts
│   ├── components/
│   │   ├── UrlInput.vue       # URL input form
│   │   ├── SummaryDisplay.vue # Summary + metadata display
│   │   ├── LoadingState.vue   # Progress indicator
│   │   └── ErrorMessage.vue   # Error display
│   ├── services/
│   │   └── api.ts             # Backend API client
│   └── types/
│       └── index.ts           # TypeScript interfaces
├── tests/
├── index.html
├── vite.config.ts
├── tsconfig.json
└── package.json
```

**Alternatives Considered**:
- React: Not requested. Vue is simpler for this scope.
- Nuxt.js: SSR is unnecessary for this client-side app.

## 5. YouTube URL Parsing

**Decision**: Regex-based parsing in the backend

**Rationale**: YouTube URLs follow well-known patterns. A regex can
extract the video ID from all common formats without external
dependencies.

**Key Findings**:
- Valid YouTube URL formats:
  - `https://www.youtube.com/watch?v=VIDEO_ID`
  - `https://youtu.be/VIDEO_ID`
  - `https://www.youtube.com/shorts/VIDEO_ID`
  - `https://m.youtube.com/watch?v=VIDEO_ID`
  - With additional query params (e.g., `&t=120`, `&list=...`)
- Video ID format: 11 characters, alphanumeric plus `-` and `_`
  (base64url-safe characters)
- Regex pattern:
  `(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)([a-zA-Z0-9_-]{11})`
- Playlist detection: Check for `list=` parameter without `v=`
  parameter, or `/playlist` path

## 6. YouTube Video Metadata

**Decision**: Use YouTube oEmbed API (no API key required)

**Rationale**: The oEmbed endpoint provides title and author name
without requiring a YouTube Data API key. Duration is not available
via oEmbed, but can be extracted from the transcript segments (sum
of start + duration of last segment).

**Key Findings**:
- Endpoint: `https://www.youtube.com/oembed?url=VIDEO_URL&format=json`
- Returns: `title`, `author_name`, `author_url`, `thumbnail_url`,
  `provider_name`, `type`, `html` (embed code)
- Does NOT return: duration, view count, publish date
- Duration workaround: Calculate from transcript data — the last
  segment's `start` + `duration` gives approximate video length
- Fallback: `noembed.com` provides similar oEmbed aggregation

**Alternatives Considered**:
- YouTube Data API v3: Provides all metadata including duration, but
  requires API key and quota. Avoid for simplicity.
- Web scraping: Fragile, against YouTube ToS.

## 7. Testing Strategy

**Decision**: pytest (backend), Vitest (frontend)

**Rationale**: pytest is the standard for Python testing. Vitest is
the natural testing framework for Vite-based Vue projects (fast,
compatible with Vue Test Utils).

**Key Findings**:
- Backend: `pytest` + `pytest-asyncio` for async endpoint testing,
  `httpx` for TestClient
- Frontend: `vitest` + `@vue/test-utils` for component testing
- Mock strategy (per constitution): Mock only external services
  (YouTube API, OpenAI API), not internal modules
- Integration tests: Test full flow from URL input to summary output
  using mocked external services

## 8. Development Tooling

**Decision**: Ruff (Python linting/formatting), ESLint + Prettier
(frontend)

**Rationale**: Per constitution Principle I, automated linting and
formatting are mandatory. Ruff is the modern, fast Python linter/
formatter. ESLint + Prettier is standard for Vue/TypeScript.

**Key Findings**:
- Backend: `ruff check` + `ruff format` (replaces flake8, black,
  isort in a single tool)
- Frontend: ESLint with `@vue/eslint-config-typescript` + Prettier
- Type checking: `mypy` for Python, `vue-tsc` for TypeScript
