# API Endpoints

Base URL: `http://localhost:8002` (Docker) or `http://localhost:8002` (local dev).

All endpoints are defined in [`backend/app/main.py`](../backend/app/main.py).

---

## Health

### `GET /api/health`

Returns server status. Used to verify the backend is running.

**Response `200`**
```json
{ "status": "ok" }
```

---

## Summarization

### `POST /api/summarize`

Fetches a YouTube transcript and generates an AI summary. Returns cached result if the video has been summarized before.

**Request body**
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "length_percent": 25
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `url` | string | yes | Any YouTube URL format |
| `length_percent` | int | no | 10–50, multiple of 5. Default: 25 |

**Response `200` — `SummarizeResponse`**
```json
{
  "summary": "...",
  "transcript": "...",
  "metadata": {
    "video_id": "dQw4w9WgXcQ",
    "title": "...",
    "channel_name": "...",
    "duration_seconds": 212,
    "thumbnail_url": "..."
  },
  "stats": {
    "chars_in": 12500,
    "chars_out": 800,
    "total_tokens": 3200,
    "generation_seconds": 4.21
  },
  "highlights": [],
  "notes": null,
  "storage_warning": false
}
```

`stats` is `null` for cached responses. `highlights` and `notes` are populated from the database for cached responses.

**Errors**

| Status | `error` field | Cause |
|--------|--------------|-------|
| 400 | `invalid_url` | Not a recognized YouTube URL |
| 400 | `playlist_not_supported` | URL points to a playlist |
| 404 | `video_not_found` | Video does not exist |
| 404 | `transcript_unavailable` | Transcripts disabled or not available |
| 502 | `summarization_failed` | OpenAI API error |
| 503 | `ip_blocked` | YouTube blocking server IP |

---

## Fallacy Analysis

### `POST /api/fallacies`

Analyzes a video transcript for logical fallacies. Returns cached result if analysis was already run for this video.

**Request body**
```json
{ "url": "https://www.youtube.com/watch?v=..." }
```

**Response `200` — `FallacyAnalysisResult`**
```json
{
  "summary": {
    "total_fallacies": 3,
    "high_severity": 1,
    "medium_severity": 1,
    "low_severity": 1,
    "primary_tactics": ["Appeal to Authority", "False Dichotomy"]
  },
  "fallacies": [
    {
      "timestamp": "2:34",
      "quote": "Everyone knows that...",
      "fallacy_name": "Appeal to Popularity",
      "category": "Relevance",
      "severity": "medium",
      "explanation": "...",
      "clear_example": {
        "scenario": "...",
        "why_wrong": "..."
      }
    }
  ]
}
```

**Errors** — same as `/api/summarize` plus:

| Status | `error` field | Cause |
|--------|--------------|-------|
| 502 | `analysis_failed` | OpenAI returned no result |

---

## Q&A

### `POST /api/ask`

Answers a question about a video using its transcript as context. Conversation history is included to allow follow-up questions. Saves history to the database if `video_id` is provided.

**Request body**
```json
{
  "transcript": "...",
  "question": "What did the speaker say about climate change?",
  "history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ],
  "video_id": "dQw4w9WgXcQ"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `transcript` | string | yes | Full transcript text |
| `question` | string | yes | Current question |
| `history` | array | no | Prior conversation messages. Default: `[]` |
| `video_id` | string | no | If provided, saves conversation to DB |

**Response `200`**
```json
{ "answer": "The speaker mentioned..." }
```

---

## History

### `GET /api/history`

Returns a paginated list of recently summarized videos (excluding soft-deleted).

**Query params**

| Param | Type | Default | Range |
|-------|------|---------|-------|
| `limit` | int | 50 | 1–100 |

**Response `200` — `HistoryResponse`**
```json
{
  "items": [
    {
      "video_id": "dQw4w9WgXcQ",
      "title": "...",
      "thumbnail_url": "...",
      "summary": "...",
      "has_fallacy_analysis": true,
      "created_at": "2026-04-15T12:00:00Z"
    }
  ]
}
```

---

### `GET /api/history/{video_id}`

Returns the full stored record for a video, including fallacy analysis, highlights, Q&A history, and notes.

**Response `200` — `VideoRecord`**
```json
{
  "id": 42,
  "video_id": "dQw4w9WgXcQ",
  "title": "...",
  "thumbnail_url": "...",
  "summary": "...",
  "transcript": "...",
  "fallacy_analysis": { ... },
  "highlights": [{ "start": 100, "end": 250 }],
  "qa_history": [{ "role": "user", "content": "..." }],
  "notes": "My notes here",
  "created_at": "2026-04-15T12:00:00Z"
}
```

`fallacy_analysis` is `null` if analysis has not been run.

**Errors**

| Status | `error` | Cause |
|--------|---------|-------|
| 404 | `not_found` | No record for this `video_id` |

---

### `DELETE /api/history/{video_id}`

Soft-deletes a video record (sets `deleted_at`). Can be undone within 5 seconds via the restore endpoint.

**Response `204`** — no content on success.

**Errors**

| Status | `error` | Cause |
|--------|---------|-------|
| 404 | `not_found` | No record for this `video_id` |

---

### `POST /api/history/{video_id}/restore`

Restores a soft-deleted record (clears `deleted_at`).

**Response `200` — `HistoryItem`** (the restored record)

**Errors**

| Status | `error` | Cause |
|--------|---------|-------|
| 404 | `not_found` | No deleted record found for this `video_id` |

---

## Highlights

### `POST /api/history/{video_id}/highlights`

Adds a character-range highlight to the transcript. Overlapping or adjacent highlights are automatically merged.

**Request body**
```json
{ "start": 100, "end": 250 }
```

`start` and `end` are character offsets in the `transcript` string. `end` must be greater than `start`.

**Response `200` — `Highlight[]`** (updated, merged list)
```json
[{ "start": 100, "end": 250 }, { "start": 500, "end": 600 }]
```

**Errors**

| Status | `error` | Cause |
|--------|---------|-------|
| 404 | `not_found` | No record for this `video_id` |

---

### `DELETE /api/history/{video_id}/highlights/{index}`

Removes a highlight by its position in the current list.

**Response `200` — `Highlight[]`** (updated list after removal)

**Errors**

| Status | `error` | Cause |
|--------|---------|-------|
| 404 | `not_found` | No record for this `video_id` |

---

## Notes

### `PUT /api/history/{video_id}/notes`

Saves (or clears) notes for a video. Called automatically after a 1-second debounce when the user edits the Notes tab.

**Request body**
```json
{ "notes": "My personal notes about this video." }
```

Pass `"notes": null` to clear notes.

**Response `204`** — no content on success.

**Errors**

| Status | `error` | Cause |
|--------|---------|-------|
| 404 | `not_found` | No record for this `video_id` |
