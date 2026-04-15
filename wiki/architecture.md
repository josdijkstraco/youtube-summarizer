# Architecture

## System Diagram

```
Browser
  │
  │  HTTP (port 3002)
  ▼
nginx (Docker)
  │  serves built Vue app
  │  VITE_API_URL → http://localhost:8002
  │
  │  HTTP API calls (port 8002)
  ▼
FastAPI (uvicorn)
  ├── GET/POST/DELETE /api/*
  │       │
  │       ├── youtube_transcript_api ──► YouTube (transcript)
  │       ├── httpx ──────────────────► YouTube oEmbed (metadata)
  │       ├── OpenAI SDK ─────────────► OpenAI API (gpt-4o-mini / gpt-4o)
  │       └── asyncpg pool
  │                │
  │                ▼
  │          PostgreSQL
  │          schema: youtube_summarizer
  │          table:  summaries
  │
  └── Startup: create_pool() + create_table()
```

## Tech Stack

| Layer | Technology | Version | Role |
|-------|-----------|---------|------|
| Frontend framework | Vue 3 | 3.x | Reactive UI |
| Frontend build | Vite | 5.4 | Dev server + production build |
| Frontend types | TypeScript | 5.5 | Type safety |
| Backend framework | FastAPI | 0.115+ | Async REST API |
| Backend server | uvicorn | 0.30+ | ASGI server |
| Database driver | asyncpg | 0.30+ | Async PostgreSQL |
| Database | PostgreSQL | 14+ | Persistent storage |
| AI | OpenAI SDK | 1.50+ | Summarization, fallacy, Q&A |
| Transcript | youtube-transcript-api | 0.6+ | YouTube captions |
| HTTP client | httpx | 0.27+ | oEmbed metadata |
| Config | pydantic-settings | 2.5+ | `.env` loading |
| Container | Docker + Compose | - | Deployment |

## Key Data Flows

### 1. Summarization

```
User pastes URL
  → App.vue handleSubmit()
  → api.ts summarizeVideo()
  → POST /api/summarize

Backend:
  1. extract_video_id(url)           # regex from URL
  2. get_by_video_id(conn, id)       # PostgreSQL cache check
     └─ if hit → return cached SummarizeResponse
  3. get_transcript(video_id)        # youtube_transcript_api
  4. generate_summary(text, %)       # OpenAI gpt-4o-mini (chunked if >400K chars)
  5. get_video_metadata(video_id)    # httpx → YouTube oEmbed
  6. save_record(conn, ...)          # INSERT ... ON CONFLICT DO NOTHING (async)
  7. return SummarizeResponse

Frontend:
  → SummaryDisplay renders summary/transcript/Q&A/notes tabs
  → HistoryPanel reloads
```

### 2. Fallacy Analysis

```
User clicks "Analyze Fallacies"
  → App.vue handleAnalyzeFallacies()
  → api.ts analyzeFallacies(url)
  → POST /api/fallacies

Backend:
  1. extract_video_id(url)
  2. get_fallacy_analysis(conn, id)  # PostgreSQL cache check
     └─ if hit → return cached FallacyAnalysisResult
  3. get_transcript(video_id)
  4. analyze_fallacies(text)         # OpenAI gpt-4o-mini, JSON mode
  5. save_fallacy_analysis(conn, id) # UPDATE ... WHERE fallacy_analysis IS NULL
  6. return FallacyAnalysisResult

Frontend:
  → FallacyDisplay renders fallacy table
  → FallacySummaryPanel renders severity counts
```

### 3. Q&A

```
User types question + presses Enter
  → SummaryDisplay handleAsk()
  → api.ts askQuestion(transcript, question, history, videoId)
  → POST /api/ask

Backend:
  1. Build messages: [system(transcript)] + history + [user question]
  2. OpenAI gpt-4o async call
  3. save_qa_history(conn, video_id, full_history)  # if video_id provided
  4. return AskResponse { answer }

Frontend:
  → Appends assistant message to conversation view
  → Auto-scrolls to latest
```

### 4. History & Persistence

```
Any summarization → record saved to PostgreSQL

User opens History sidebar:
  → GET /api/history?limit=50
  → HistoryPanel lists HistoryCard items

User clicks a card:
  → GET /api/history/{video_id}
  → Loads VideoRecord (summary + transcript + fallacy + highlights + qa + notes)
  → App.vue populates all state refs

User deletes entry:
  → DELETE /api/history/{video_id}  (sets deleted_at)
  → 5-second undo toast
  → POST /api/history/{video_id}/restore  (clears deleted_at)
```

## Caching Strategy

PostgreSQL acts as the primary cache. Before calling OpenAI, both `/api/summarize` and `/api/fallacies` query the database:

- **Summary cache**: `get_by_video_id()` — returns full `VideoRecord` if it exists
- **Fallacy cache**: `get_fallacy_analysis()` — returns `FallacyAnalysisResult` if `fallacy_analysis IS NOT NULL`

Cache is per `video_id`. There is no TTL — cached results are permanent unless the record is deleted. `save_record()` uses `ON CONFLICT (video_id) DO NOTHING` so duplicate summarization requests never overwrite stored data.

## Error Handling Strategy

Backend errors always return `ErrorResponse { error: string, message: string, details?: string }`.

| HTTP Status | When |
|-------------|------|
| 400 | Invalid/empty URL, playlist URL, malformed `length_percent` |
| 404 | Video not found, transcript unavailable, no DB record |
| 502 | OpenAI API failure |
| 503 | YouTube IP block |
| 500 | Unexpected internal error |

Frontend catches `ApiError` (wraps `ErrorResponse`) and displays it via `ErrorMessage.vue`. Network errors show "Could not reach server".

Storage and metadata failures are non-fatal — the summary is returned with `storage_warning: true` if saving fails.
