# Database

**Engine:** PostgreSQL  
**Schema:** `youtube_summarizer`  
**Table:** `summaries`  
**Driver:** asyncpg (async connection pool)  
**File:** [`backend/app/db.py`](../backend/app/db.py)

---

## Table Schema

```sql
CREATE TABLE IF NOT EXISTS youtube_summarizer.summaries (
    id               BIGSERIAL    PRIMARY KEY,
    video_id         TEXT         NOT NULL UNIQUE,  -- 11-char YouTube ID
    title            TEXT,                          -- video title (nullable)
    thumbnail_url    TEXT,                          -- oEmbed thumbnail
    summary          TEXT         NOT NULL,         -- generated summary
    transcript       TEXT         NOT NULL,         -- full transcript text
    fallacy_analysis JSONB        DEFAULT NULL,     -- FallacyAnalysisResult JSON
    highlights       JSONB        DEFAULT '[]',     -- [{start, end}, ...] char ranges
    qa_history       JSONB        DEFAULT '[]',     -- [{role, content}, ...] messages
    notes            TEXT         DEFAULT NULL,     -- user-written notes
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    deleted_at       TIMESTAMPTZ  DEFAULT NULL      -- soft-delete flag
);
```

### Column notes

| Column | Notes |
|--------|-------|
| `video_id` | `UNIQUE` constraint — primary lookup key. `ON CONFLICT DO NOTHING` in inserts. |
| `transcript` | Can be large (100K+ chars for long videos). Sent to frontend as-is. |
| `fallacy_analysis` | `NULL` until `POST /api/fallacies` is called. Once set, not overwritten. |
| `highlights` | Character offsets into `transcript`. Stored merged (no overlaps). |
| `qa_history` | Full conversation array, replaced on each update. |
| `deleted_at` | `NULL` = active. Non-null = soft-deleted. All SELECT queries filter `WHERE deleted_at IS NULL`. |

### Schema migration

`create_table()` uses `CREATE TABLE IF NOT EXISTS` plus `DO $$ ... ALTER TABLE ADD COLUMN IF NOT EXISTS $$` blocks for each newer column (`fallacy_analysis`, `deleted_at`, `highlights`, `qa_history`, `notes`). This allows the schema to be updated on existing deployments without manual migrations.

---

## Connection Pool

```python
async def create_pool(dsn: str) -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn=dsn, min_size=2, max_size=10)
```

Pool is created at app startup via FastAPI's lifespan context and stored in `app.state.pool`. Each request acquires a connection via the `get_db` dependency:

```python
async def get_db(request: Request) -> AsyncGenerator[asyncpg.Connection, None]:
    async with request.app.state.pool.acquire() as conn:
        yield conn
```

---

## Functions

### Pool management

| Function | Signature | Purpose |
|----------|-----------|---------|
| `create_pool` | `(dsn: str) -> Pool` | Create asyncpg pool (min 2, max 10) |
| `close_pool` | `(pool: Pool) -> None` | Graceful shutdown |
| `get_db` | `(request: Request) -> AsyncGenerator[Connection, None]` | FastAPI dependency — yields one connection per request |
| `create_table` | `(conn: Connection) -> None` | Create schema + run additive column migrations |

### Record operations

| Function | Signature | Purpose |
|----------|-----------|---------|
| `save_record` | `(conn, video_id, title, thumbnail_url, summary, transcript) -> VideoRecord` | Insert or skip on conflict; always returns the stored record |
| `get_by_video_id` | `(conn, video_id) -> VideoRecord \| None` | Fetch non-deleted record (used as summarization cache) |
| `get_full_record` | `(conn, video_id) -> VideoRecord \| None` | Same query, used by `GET /api/history/{id}` |
| `list_recent` | `(conn, limit: int) -> list[HistoryItem]` | Paginated history, ordered by `created_at DESC` |

### Fallacy

| Function | Signature | Purpose |
|----------|-----------|---------|
| `get_fallacy_analysis` | `(conn, video_id) -> FallacyAnalysisResult \| None` | Fetch cached fallacy result |
| `save_fallacy_analysis` | `(conn, video_id, analysis: dict) -> bool` | `UPDATE ... WHERE fallacy_analysis IS NULL` — never overwrites; returns `True` if saved |

### Q&A and notes

| Function | Signature | Purpose |
|----------|-----------|---------|
| `save_qa_history` | `(conn, video_id, history: list[dict]) -> None` | Replace full `qa_history` array |
| `save_notes` | `(conn, video_id, notes: str \| None) -> bool` | Update notes; returns `True` if record found |

### Soft-delete

| Function | Signature | Purpose |
|----------|-----------|---------|
| `soft_delete` | `(conn, video_id) -> bool` | Sets `deleted_at = now()`; returns `True` if found |
| `restore` | `(conn, video_id) -> HistoryItem \| None` | Clears `deleted_at`; returns the restored `HistoryItem` |

### Highlights

| Function | Signature | Purpose |
|----------|-----------|---------|
| `add_highlight` | `(conn, video_id, start: int, end: int) -> list[Highlight] \| None` | Appends, merges, saves; returns updated list |
| `remove_highlight` | `(conn, video_id, index: int) -> list[Highlight] \| None` | Removes by index, saves; returns updated list |

---

## Soft-Delete Pattern

Records are never physically removed. Deletion sets `deleted_at = now()`, restoration sets it back to `NULL`.

```sql
-- Delete
UPDATE summaries SET deleted_at = now()
WHERE video_id = $1 AND deleted_at IS NULL;

-- Restore
UPDATE summaries SET deleted_at = NULL
WHERE video_id = $1 AND deleted_at IS NOT NULL;

-- All active-record queries
SELECT ... FROM summaries WHERE ... AND deleted_at IS NULL
```

The frontend provides a 5-second undo toast after deletion, calling `POST /api/history/{id}/restore` if the user clicks Undo.

---

## Highlight Merge Logic

`_merge_highlights(highlights)` in `db.py` sorts by `start`, then performs a standard interval merge:

```python
sorted_hl = sorted(highlights, key=lambda h: h.start)
merged = [sorted_hl[0]]
for hl in sorted_hl[1:]:
    last = merged[-1]
    if hl.start <= last.end:          # overlapping or adjacent
        merged[-1] = Highlight(start=last.start, end=max(last.end, hl.end))
    else:
        merged.append(hl)
```

Called by `add_highlight()` after appending the new range. The result is written back to the database and returned to the caller.

---

## JSONB Column Structures

### `highlights`
```json
[
  { "start": 100, "end": 250 },
  { "start": 500, "end": 620 }
]
```
Always stored merged (no overlapping ranges).

### `qa_history`
```json
[
  { "role": "user", "content": "What is the main argument?" },
  { "role": "assistant", "content": "The speaker argues that..." }
]
```
Full conversation array, replaced on each save.

### `fallacy_analysis`
```json
{
  "summary": {
    "total_fallacies": 2,
    "high_severity": 1,
    "medium_severity": 1,
    "low_severity": 0,
    "primary_tactics": ["Ad Hominem"]
  },
  "fallacies": [
    {
      "timestamp": "1:23",
      "quote": "...",
      "fallacy_name": "Ad Hominem",
      "category": "Relevance",
      "severity": "high",
      "explanation": "...",
      "clear_example": { "scenario": "...", "why_wrong": "..." }
    }
  ]
}
```
