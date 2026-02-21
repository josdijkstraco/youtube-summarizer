# Data Model: Postgres Video Storage

**Feature**: 004-postgres-video-storage
**Date**: 2026-02-21

---

## Entity: VideoRecord (table: `summaries`)

Represents a single processed YouTube video. Immutable once written — no updates, no versioning.

### Fields

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | PRIMARY KEY | Surrogate auto-increment key |
| `video_id` | `TEXT` | NOT NULL, UNIQUE | YouTube video ID (11-character ID extracted from URL, e.g. `dQw4w9WgXcQ`) |
| `title` | `TEXT` | nullable | Video title from YouTube oEmbed API. Null if metadata fetch fails. |
| `thumbnail_url` | `TEXT` | nullable | YouTube thumbnail CDN URL. Null if metadata fetch fails. |
| `summary` | `TEXT` | NOT NULL | Generated summary text |
| `transcript` | `TEXT` | NOT NULL | Full raw transcript text |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | Timestamp of first processing. Never updated. |

### DDL

```sql
CREATE TABLE IF NOT EXISTS summaries (
    id            BIGSERIAL    PRIMARY KEY,
    video_id      TEXT         NOT NULL UNIQUE,
    title         TEXT,
    thumbnail_url TEXT,
    summary       TEXT         NOT NULL,
    transcript    TEXT         NOT NULL,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);
```

### Indexes

The `UNIQUE` constraint on `video_id` creates an implicit B-tree index, which covers:
- Duplicate detection lookup (`WHERE video_id = $1`) — O(log n)
- Upsert conflict target (`ON CONFLICT (video_id)`)

No additional indexes are needed for the 50-item history list (full table scan on small dataset; add `CREATE INDEX IF NOT EXISTS idx_summaries_created_at ON summaries (created_at DESC)` if dataset grows significantly).

---

## Pydantic Models (Backend)

### `VideoRecord` (new — database row representation)

```python
class VideoRecord(BaseModel):
    id: int
    video_id: str
    title: str | None
    thumbnail_url: str | None
    summary: str
    transcript: str
    created_at: datetime
```

### `HistoryItem` (new — API response for history list, omits transcript for payload size)

```python
class HistoryItem(BaseModel):
    video_id: str
    title: str | None
    thumbnail_url: str | None
    summary: str
    created_at: datetime
```

### `HistoryResponse` (new — wraps history list endpoint)

```python
class HistoryResponse(BaseModel):
    items: list[HistoryItem]
```

### Existing `SummarizeResponse` — unchanged

The existing `/api/summarize` response shape is unchanged. The endpoint internally saves to the database as a side-effect but the response contract is not modified.

---

## TypeScript Types (Frontend)

### `HistoryItem` (new, to add to `types/index.ts`)

```typescript
export interface HistoryItem {
  video_id: string;
  title: string | null;
  thumbnail_url: string | null;
  summary: string;
  created_at: string; // ISO 8601 timestamp
}

export interface HistoryResponse {
  items: HistoryItem[];
}
```

---

## Validation Rules

- `video_id` must be exactly 11 alphanumeric/hyphen/underscore characters (enforced by the existing `extract_video_id` function before any DB interaction)
- `summary` and `transcript` must be non-empty strings (guaranteed by the existing summarization pipeline before storage is attempted)
- `created_at` is always set by the database default — never supplied by the application

---

## State Transitions

The `summaries` table is append-only. No update or delete operations are defined for this feature.

```
[New URL submitted]
       │
       ▼
[Lookup by video_id]
       │
  ┌────┴────┐
  │ Found   │ Not Found
  ▼         ▼
[Return   [Process → Save → Return]
 stored]
```
