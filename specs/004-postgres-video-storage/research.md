# Research: Postgres Video Storage

**Phase**: 0 — Resolve unknowns before design
**Date**: 2026-02-21
**Feature**: 004-postgres-video-storage

---

## R-001: Async Postgres Driver

**Decision**: asyncpg

**Rationale**: Pure-async binary-protocol driver; 5× faster on small payloads vs psycopg3 in benchmarks. The project is exclusively async (FastAPI + async endpoints) so no sync-path flexibility is needed. asyncpg is the performance-first default for this architecture.

**Alternatives considered**: psycopg3 (psycopg[binary]) — more flexible for mixed sync/async use (e.g., pytest without asyncio mode); chosen if the project already had psycopg as a dependency. Since it does not, asyncpg wins on throughput.

---

## R-002: Connection Pool Lifecycle

**Decision**: Lifespan context manager owns the pool in `app.state`; `Depends(get_db)` acquires a connection per request.

**Rationale**: The two are complementary, not alternatives. `lifespan` guarantees the pool is created before the first request and closed after the last — replacing the deprecated `@app.on_event` pattern (superseded in FastAPI 0.93+). Storing in `app.state` avoids module-level globals and makes the pool swappable in tests. `Depends(get_db)` returns the connection back to the pool even on exceptions via async context manager.

Pool sizing: `min_size=2, max_size=10` — keeps 2 warm connections for low cold-start latency, caps at 10 to avoid exhausting RDS connection limits on small instance types.

**Alternatives considered**: Module-level `pool: asyncpg.Pool | None = None` singleton — common in older tutorials but breaks test isolation and is harder to reason about in multi-worker deployments.

---

## R-003: Schema Migration Strategy

**Decision**: `CREATE TABLE IF NOT EXISTS` executed in the lifespan startup block. No migration tool at this stage.

**Rationale**: A single stable table does not justify Alembic's overhead (3 config files, CLI step before deploy, SQLAlchemy models or fully manual scripts). `CREATE TABLE IF NOT EXISTS` is idempotent and safe to run on every startup. If the schema grows beyond 1-2 tables, graduate to numbered SQL migration files (`migrations/001_initial.sql`) tracked by a `schema_migrations` table — no new dependencies, just a small runner.

**Alternatives considered**: Alembic — justified for 3+ tables, rollback history, or team environments. Not warranted here.

---

## R-004: Upsert Pattern (Insert-if-not-exists)

**Decision**: Two-statement pattern — `INSERT ... ON CONFLICT (video_id) DO NOTHING` then `SELECT`.

**Rationale**:
- `RETURNING` on `DO NOTHING` inserts returns empty when the conflict fires — the row is skipped, not returned. Cannot use `INSERT ... ON CONFLICT DO NOTHING RETURNING *` to get the existing row.
- `ON CONFLICT DO UPDATE SET video_id = EXCLUDED.video_id` always returns the row but issues an unnecessary UPDATE (dead MVCC tuples, heavier lock) when the intent is "never overwrite."
- Two-statement approach is correct, readable, and avoids wasted writes. Under the `READ COMMITTED` default and a `UNIQUE` constraint on `video_id`, concurrent duplicate inserts are handled safely: the loser's `DO NOTHING` fires atomically after the winner commits, then the follow-up `SELECT` finds the row.

**Alternatives considered**: Single-statement CTE (`WITH ins AS (...) SELECT * FROM ins UNION ALL SELECT * FROM summaries WHERE video_id = $1`) — one round-trip, valid, but harder to read and debug for no meaningful performance gain at this scale.

---

## R-005: Environment Variable Naming

**Decision**: Single `DATABASE_URL` field typed as `pydantic.PostgresDsn` in pydantic-settings.

**Rationale**: `DATABASE_URL` is the de-facto standard recognised by Heroku, Railway, Render, Fly.io, and AWS App Runner — copy-paste deployment without renaming. `PostgresDsn` provides Pydantic v2 validation (scheme must be `postgresql://`); invalid strings are caught at startup. asyncpg accepts the DSN directly via `asyncpg.create_pool(dsn=str(settings.database_url))` (cast to `str` because `PostgresDsn` is a `Url` object in Pydantic v2).

Format: `postgresql://user:password@host:5432/dbname`

**Alternatives considered**: Individual `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` vars — useful when a secrets manager stores the password separately. Can be composed into a DSN via a `@model_validator` in Settings if needed later.

---

## R-006: Frontend History Panel Architecture

**Decision**: New `HistoryPanel.vue` component (owns fetch + state) containing `HistoryCard.vue` child. Two-column CSS Grid layout in `App.vue` (`280px sidebar + 1fr main`).

**Rationale**: `App.vue` already manages 8 refs and 2 async flows — at the natural cohesion limit. The history panel has its own lifecycle (`onMounted` fetch), its own loading/empty/error state, and its own presentation. Decomposing it follows the same pattern as the existing `FallacyDisplay.vue` / `FallacySummaryPanel.vue` split. CSS Grid with `position: sticky` sidebar and `overflow-y: auto` keeps the panel visible while the main content scrolls.

Fetch pattern: `onMounted` with three `ref`s (`historyItems`, `historyLoading`, `historyError`) + a named `loadHistory()` function called by both `onMounted` and a retry button.

**Alternatives considered**: Extend `App.vue` inline — simpler diff but degrades cohesion. Vue Router page — rejected (project excludes Vue Router; history is a persistent panel, not a navigation target). Pinia store — overkill with no cross-component sharing needed.

---

## R-007: History List Refresh After New Summary

**Decision**: After a successful summarize call in `App.vue`, emit a signal to `HistoryPanel.vue` to reload. Implemented as a template ref + exposed `reload()` method on `HistoryPanel`.

**Rationale**: The history list should update immediately after a video is summarized so the user sees their new entry without refreshing. Since `HistoryPanel` owns its own state, `App.vue` calls `historyPanelRef.value?.reload()` after `summarizeVideo` succeeds. This keeps state encapsulated while enabling the cross-component coordination.

**Alternatives considered**: Poll on interval — unnecessary complexity. Emit event up to App then prop down — unnecessary indirection since App already has the ref.
