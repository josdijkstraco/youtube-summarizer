# YouTube Summarizer API

Base URL: `http://localhost:8002`

All error responses follow the shape:
```json
{ "error": "machine_code", "message": "human text", "details": "optional" }
```

---

## Health

### `GET /api/health`

Returns `{"status": "ok"}`. Used for liveness checks.

---

## Summarization

### `POST /api/summarize`

Fetches the transcript for a YouTube video, generates a summary via OpenAI, and persists the result. Returns the cached result immediately if the video has already been summarized.

**Request**
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "length_percent": 25
}
```

| Field | Type | Default | Constraints |
|---|---|---|---|
| `url` | string | required | Non-empty YouTube URL |
| `length_percent` | integer | `25` | 10–50, multiple of 5 |

**Response `200`**
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
  "storage_warning": false,
  "stats": {
    "chars_in": 12000,
    "chars_out": 800,
    "total_tokens": 3200,
    "generation_seconds": 4.12
  },
  "highlights": [],
  "notes": null
}
```

`storage_warning: true` means the summary was generated but could not be saved to the database.

**Errors**

| Status | `error` | Cause |
|---|---|---|
| 400 | `invalid_url` | URL is not a recognized YouTube URL |
| 400 | `playlist_not_supported` | URL points to a playlist |
| 404 | `video_not_found` | Video does not exist |
| 404 | `transcript_unavailable` | No transcript available for the video |
| 503 | `ip_blocked` | YouTube is blocking this server's IP |
| 502 | `summarization_failed` | OpenAI API error |
| 500 | `internal_error` | Unexpected server error |

---

## Fallacy Analysis

### `POST /api/fallacies`

Analyzes the transcript of a YouTube video for logical fallacies using OpenAI. Returns cached analysis if already computed (never overwritten once stored).

**Request**
```json
{ "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ" }
```

**Response `200`**
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
      "timestamp": "2:14",
      "quote": "Everyone knows this is true.",
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

**Errors**

| Status | `error` | Cause |
|---|---|---|
| 400 | `invalid_url` | Unrecognized YouTube URL |
| 400 | `playlist_not_supported` | URL is a playlist |
| 404 | `video_not_found` | Video does not exist |
| 404 | `transcript_unavailable` | No transcript available |
| 503 | `ip_blocked` | YouTube blocking server IP |
| 502 | `analysis_failed` | OpenAI returned no result |
| 500 | `transcript_error` | Unexpected transcript fetch failure |

---

## Q&A

### `POST /api/ask`

Answers a question about a video using its transcript. Optionally persists the full conversation history when `video_id` is provided.

**Request**
```json
{
  "transcript": "...",
  "question": "What is the main argument?",
  "history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ],
  "video_id": "dQw4w9WgXcQ"
}
```

| Field | Type | Default | Notes |
|---|---|---|---|
| `transcript` | string | required | Full video transcript |
| `question` | string | required | User's question |
| `history` | `QaMessage[]` | `[]` | Prior turns for multi-turn context |
| `video_id` | string | `null` | If set, conversation is saved to DB |

**Response `200`**
```json
{ "answer": "The main argument is..." }
```

---

## History

### `GET /api/history`

Returns recently summarized videos (soft-deleted records excluded).

**Query params**

| Param | Default | Range |
|---|---|---|
| `limit` | `50` | 1–100 |

**Response `200`**
```json
{
  "items": [
    {
      "video_id": "dQw4w9WgXcQ",
      "title": "...",
      "thumbnail_url": "...",
      "summary": "...",
      "has_fallacy_analysis": false,
      "created_at": "2026-05-14T10:00:00Z"
    }
  ]
}
```

---

### `GET /api/history/{video_id}`

Returns the full stored record for a video, including transcript, highlights, Q&A history, and fallacy analysis.

**Response `200`** — `VideoRecord`
```json
{
  "id": 1,
  "video_id": "dQw4w9WgXcQ",
  "title": "...",
  "thumbnail_url": "...",
  "summary": "...",
  "transcript": "...",
  "fallacy_analysis": null,
  "highlights": [],
  "qa_history": [],
  "notes": null,
  "created_at": "2026-05-14T10:00:00Z"
}
```

**Errors:** `404 not_found`

---

### `DELETE /api/history/{video_id}`

Soft-deletes a record (sets `deleted_at`; data is not removed). Returns `204 No Content` on success.

**Errors:** `404 not_found`

---

### `POST /api/history/{video_id}/restore`

Restores a previously soft-deleted record.

**Response `200`** — `HistoryItem`

**Errors:** `404 not_found` (record not found or not deleted)

---

### `POST /api/history/{video_id}/highlights`

Adds a highlight range to a video record. Ranges are merged on write so there are no overlaps.

**Request**
```json
{ "start": 120, "end": 180 }
```

`start` and `end` are in seconds (`end > start`, both ≥ 0).

**Response `200`** — updated `Highlight[]`
```json
[{ "start": 120, "end": 180 }]
```

**Errors:** `404 not_found`

---

### `DELETE /api/history/{video_id}/highlights/{index}`

Removes the highlight at the given 0-based index from the stored list.

**Response `200`** — updated `Highlight[]`

**Errors:** `404 not_found`

---

### `PUT /api/history/{video_id}/notes`

Saves (or clears) free-text notes for a video record.

**Request**
```json
{ "notes": "Interesting point at 3:20." }
```

Pass `"notes": null` to clear existing notes.

**Response `204 No Content`**

**Errors:** `404 not_found`

---

## Video Download

Downloads are a two-step async flow: trigger the download, then poll for status.

### `POST /api/videos/{video_id}/download`

Enqueues a background yt-dlp download for the video. Videos longer than 3 hours are rejected by the downloader.

- If status is already `pending` → `409 download_in_progress`
- If status is already `ready` → returns the existing `DownloadStatusResponse` immediately
- Otherwise → sets status to `pending`, starts background task, returns `{ status: "pending" }`

**Response `200`** — `DownloadStatusResponse`
```json
{
  "video_id": "dQw4w9WgXcQ",
  "status": "pending",
  "downloaded_at": null,
  "error_message": null
}
```

**Errors:** `404 not_found`, `409 download_in_progress`

---

### `GET /api/videos/{video_id}/download`

Returns the current download status for a video. Poll this after triggering a download.

**Response `200`** — `DownloadStatusResponse`

| `status` | Meaning |
|---|---|
| `pending` | Download is running in the background |
| `ready` | File is available; use the stream endpoint |
| `error` | Download failed; see `error_message` |

**Errors:** `404 not_found`

---

### `GET /api/videos/{video_id}/stream`

Streams the downloaded MP4 file (`Content-Type: video/mp4`).

If the file is missing from disk, the DB record is auto-healed (reset to no download) so the client can trigger a fresh download.

**Response `200`** — binary MP4 stream

**Errors**

| Status | `error` | Cause |
|---|---|---|
| 404 | `not_found` | No record for this video_id |
| 404 | `file_not_found` | No download path stored, or file missing on disk |
