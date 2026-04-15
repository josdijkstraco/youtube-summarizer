# Glossary

Terms used throughout the codebase and wiki.

---

### asyncpg pool
A connection pool managed by the `asyncpg` library. Created once at app startup (`min_size=2, max_size=10`), stored in `app.state.pool`, and acquired per-request via the `get_db` FastAPI dependency. See [`backend/app/db.py:10`](../backend/app/db.py).

### deleted_at
A nullable `TIMESTAMPTZ` column on the `summaries` table. When set, the row is treated as deleted. All queries filter `WHERE deleted_at IS NULL`. Setting it back to `NULL` restores the record. This is the **soft-delete** pattern.

### fallacy categories
The six categories used to classify logical fallacies in the analysis:
- **Relevance** — argument irrelevant to the conclusion
- **Presumption** — assumes something not established
- **Ambiguity** — exploits vague or shifting meanings
- **Emotional Appeal** — appeals to emotion instead of reason
- **Statistical** — misuse or misrepresentation of data
- **Manipulation** — rhetorical tricks to bypass critical thinking

### FallacyAnalysisResult
The structured result from `POST /api/fallacies`. Contains a `summary` (counts by severity) and a list of `Fallacy` objects. Stored as JSONB in the `fallacy_analysis` column. Defined in [`backend/app/models.py:57`](../backend/app/models.py).

### gpt-4o-mini vs gpt-4o
Two OpenAI models used in this project:
- **gpt-4o-mini** — used for summarization (`summarizer.py`) and fallacy analysis (`fallacy_analyzer.py`). Faster and cheaper; sufficient for bulk text processing.
- **gpt-4o** — used for Q&A (`qa.py`). Full model for conversational quality where nuance matters.

### highlight
A character-range selection in the transcript text, stored as `{start: int, end: int}`. Positions refer to byte offsets in the `transcript` string. Overlapping highlights are automatically merged when saved. Stored as a JSONB array in the `highlights` column.

### JSONB
PostgreSQL's binary JSON storage type. Used for three columns in `summaries`:
- `fallacy_analysis` — full `FallacyAnalysisResult` object
- `highlights` — array of `{start, end}` objects
- `qa_history` — array of `{role, content}` message objects

JSONB is indexed, efficient for reads, and allows partial updates.

### length_percent
Integer field on `SummarizeRequest` controlling how long the summary should be relative to the transcript. Range: 10–50, must be a multiple of 5. Default: 25. Used to compute a target word count: `transcript_words * length_percent / 100`.

### oEmbed
A standard protocol for embedding content. Used here to fetch video metadata (title, channel, thumbnail) from YouTube's public endpoint: `https://www.youtube.com/oembed?url=...`. See [`backend/app/services/youtube.py:57`](../backend/app/services/youtube.py).

### qa_history
The conversation log for a video's Q&A tab. Stored as a JSONB array of `{role, content}` objects where `role` is `"user"` or `"assistant"`. Persisted to the database after each Q&A exchange when a `video_id` is provided.

### soft-delete
A deletion pattern where records are hidden but never removed from the database. Setting `deleted_at = now()` hides the record; clearing it restores it. Enables undo within the UI (5-second toast window). See [`backend/app/db.py:275`](../backend/app/db.py).

### SummaryStats
Metadata about a summarization run returned in `SummarizeResponse`:
- `chars_in` — transcript character count
- `chars_out` — summary character count
- `total_tokens` — total OpenAI tokens consumed (all chunks)
- `generation_seconds` — wall-clock time for the OpenAI call(s)

### transcript
The full text of a YouTube video's captions, fetched via `youtube_transcript_api`. Segments (with timestamps) are joined with spaces into a single string. Stored in the `transcript` TEXT column and sent to the frontend for display and Q&A context.

### video_id
The 11-character alphanumeric identifier YouTube assigns to every video (e.g., `dQw4w9WgXcQ`). Extracted from URLs by regex in [`backend/app/services/youtube.py:12`](../backend/app/services/youtube.py). Used as the unique key (`UNIQUE` constraint) in the database.

### VITE_API_URL
Build-time environment variable that tells the frontend where the backend lives. Defaults to `http://localhost:8000` in development. Set to `http://localhost:8002` in `docker-compose.yml` at build time. See [`frontend/src/services/api.ts:13`](../frontend/src/services/api.ts).
