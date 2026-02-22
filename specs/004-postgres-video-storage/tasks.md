# Tasks: Postgres Video Storage

**Input**: Design documents from `/specs/004-postgres-video-storage/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/openapi.yaml ✅, quickstart.md ✅

**Organization**: Tasks grouped by user story — each story is independently implementable and testable.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the asyncpg dependency and configure the database connection string.

- [X] T001 Add `asyncpg>=0.30.0` to `backend/requirements.txt` and install it in the virtual environment (`pip install asyncpg>=0.30.0`)
- [X] T002 [P] Add `DATABASE_URL=postgresql://user:password@host:5432/youtube_summarizer` placeholder to `backend/.env.example`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core database infrastructure that MUST be complete before any user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 Add `database_url: PostgresDsn` field (required, no default) to `backend/app/config.py`; import `PostgresDsn` from `pydantic`
- [X] T004 [P] Add new Pydantic models to `backend/app/models.py`: `VideoRecord` (id, video_id, title, thumbnail_url, summary, transcript, created_at), `HistoryItem` (video_id, title, thumbnail_url, summary, created_at), `HistoryResponse` (items: list[HistoryItem]); add `storage_warning: bool = False` field to existing `SummarizeResponse`
- [X] T005 Create `backend/app/db.py` with: (1) `create_pool(dsn)` / `close_pool(pool)` async functions for pool lifecycle; (2) async generator `get_db(request)` that acquires a connection from `request.app.state.pool`; (3) `create_table(conn)` that executes `CREATE TABLE IF NOT EXISTS summaries (id BIGSERIAL PRIMARY KEY, video_id TEXT NOT NULL UNIQUE, title TEXT, thumbnail_url TEXT, summary TEXT NOT NULL, transcript TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now())`; (4) `save_record(conn, video_id, title, thumbnail_url, summary, transcript) -> VideoRecord` using INSERT ON CONFLICT DO NOTHING then SELECT; (5) `get_by_video_id(conn, video_id) -> VideoRecord | None` using SELECT by video_id; (6) `list_recent(conn, limit) -> list[HistoryItem]` using SELECT ordered by created_at DESC with limit; (7) `get_full_record(conn, video_id) -> VideoRecord | None` using SELECT * by video_id — note: this function is identical to get_by_video_id but documents the intent of returning the full record including transcript
- [X] T006 Replace `@app.on_event("startup"/"shutdown")` (if present) with a lifespan context manager in `backend/app/main.py`: on startup, call `create_pool(str(settings.database_url))` and store in `app.state.pool`, then call `create_table`; on shutdown, call `close_pool(app.state.pool)`; wire `lifespan` into `FastAPI(lifespan=lifespan)`

**Checkpoint**: Database pool is live, table exists, models are defined. User story implementation can now begin.

---

## Phase 3: User Story 1 — View Past Video Summaries (Priority: P1) 🎯 MVP

**Goal**: Every successfully processed video is persisted to the database. A `GET /api/history` endpoint lists the 50 most recent records. The frontend shows a sticky left-sidebar history panel with thumbnail, link, and summary for each record.

**Independent Test**: Submit any YouTube URL → verify the entry appears in `GET /api/history` with thumbnail, link, and summary → refresh the page → verify the entry is still there → the history panel in the frontend shows the entry without reloading the app.

- [X] T007 [US1] Add persist side-effect to `POST /api/summarize` in `backend/app/main.py`: after a successful `SummarizeResponse` is built, call `save_record(conn, video_id, title, thumbnail_url, summary, transcript)` inside a try/except; on `Exception`, log a warning and set `storage_warning=True` in the response (never raise — DB failure must not block the response); inject `conn` via `Depends(get_db)` added to the `summarize_video` signature
- [X] T008 [US1] Implement `GET /api/history` endpoint in `backend/app/main.py`: accepts optional `limit: int = Query(default=50, ge=1, le=100)`, calls `list_recent(conn, limit)` via `Depends(get_db)`, returns `HistoryResponse`
- [X] T009 [P] [US1] Add `HistoryItem` and `HistoryResponse` TypeScript interfaces to `frontend/src/types/index.ts`: `HistoryItem { video_id: string; title: string | null; thumbnail_url: string | null; summary: string; created_at: string; }`, `HistoryResponse { items: HistoryItem[]; }`
- [X] T010 [P] [US1] Add `fetchHistory(limit = 50): Promise<HistoryResponse>` function to `frontend/src/services/api.ts`, following the same `fetch` + `ApiError` pattern used by the existing `summarizeVideo` and `analyzeFallacies` functions
- [X] T011 [US1] Create `frontend/src/components/HistoryCard.vue`: accepts `item: HistoryItem` prop; renders a thumbnail `<img>` (width=80, height=45, object-fit: cover, @error hides the element), a video `<a>` link to `https://www.youtube.com/watch?v={item.video_id}` (target="_blank", rel="noopener") showing title or video_id, and a `<p>` summary truncated to 3 lines via `-webkit-line-clamp: 3`; scoped CSS only
- [X] T012 [US1] Create `frontend/src/components/HistoryPanel.vue`: declare three `ref`s (`historyItems: HistoryItem[]`, `historyLoading: boolean`, `historyError: string | null`); extract an async `loadHistory()` function that calls `fetchHistory(50)` and populates the refs; call `loadHistory()` in `onMounted`; expose `reload()` via `defineExpose({ reload: loadHistory })`; render four mutually exclusive states using `v-if`/`v-else-if`/`v-else`: loading spinner text, error message with a retry button (`@click="loadHistory"`), empty state ("No summaries yet."), and `<ul>` of `<HistoryCard>` per item; scoped CSS with `position: sticky; top: 1rem; max-height: calc(100vh - 2rem); overflow-y: auto`
- [X] T013 [US1] Update `frontend/src/App.vue`: (1) switch `#app` from `display: flex; flex-direction: column` to `display: grid; grid-template-columns: 280px 1fr` with `@media (max-width: 768px) { grid-template-columns: 1fr }`; (2) import `HistoryPanel` and add `<HistoryPanel ref="historyPanelRef" />` alongside the existing main content wrapped in a `<main>` element; (3) declare `const historyPanelRef = ref<InstanceType<typeof HistoryPanel> | null>(null)` and after a successful `summarizeVideo` call in `handleSubmit`, call `historyPanelRef.value?.reload()`
- [X] T014 [US1] Add integration tests for User Story 1 in `backend/tests/integration/test_api.py`: (1) test that a successful `POST /api/summarize` returns `storage_warning: false` and the record appears in `GET /api/history`; (2) test that `GET /api/history` returns 200 with `items` array when empty; (3) test that `storage_warning: true` is returned when the DB is unavailable (mock the pool to raise)

**Checkpoint**: User Story 1 is fully functional — videos persist, history API returns records, frontend sidebar displays them.

---

## Phase 4: User Story 2 — Avoid Duplicate Processing (Priority: P2)

**Goal**: Submitting a URL for a video already in the database returns the stored result immediately without calling the transcript API or OpenAI.

**Independent Test**: Submit a URL → wait for processing → submit the exact same URL again → second response arrives measurably faster (no AI call) → both responses have identical summary text.

- [X] T015 [US2] Add cache-check branch to `POST /api/summarize` in `backend/app/main.py`: immediately after `extract_video_id` succeeds, call `get_by_video_id(conn, video_id)`; if a record is returned, build and return a `SummarizeResponse` from the stored data (with `metadata` built from stored `title` and `thumbnail_url`, `storage_warning=False`) without proceeding to transcript fetch or summarization; the rest of the existing flow runs only on cache miss
- [X] T016 [US2] Add integration test for the cache-hit path in `backend/tests/integration/test_api.py`: pre-insert a row via `save_record`, POST the same URL to `/api/summarize`, assert the transcript/summarize services were not called (mock them) and the response matches the stored data

**Checkpoint**: Duplicate submissions are served from the database. User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 — Access Full Transcript (Priority: P3)

**Goal**: `GET /api/history/{video_id}` returns the complete stored record including full transcript text.

**Independent Test**: Retrieve any stored `video_id` via `GET /api/history/{video_id}` → response contains non-empty `transcript` field → request a non-existent `video_id` → response is 404.

- [X] T017 [US3] Implement `GET /api/history/{video_id}` endpoint in `backend/app/main.py`: calls `get_full_record(conn, video_id)` via `Depends(get_db)`; returns `VideoRecord` on success (200); returns `ErrorResponse` with `error="not_found"` and 404 status if `None`
- [X] T018 [US3] Add integration tests for `GET /api/history/{video_id}` in `backend/tests/integration/test_api.py`: (1) pre-insert a record, GET by video_id, assert transcript is present in response; (2) GET a non-existent video_id, assert 404

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Test coverage for business logic, code quality, and quickstart validation.

- [X] T019 [P] Create `backend/tests/unit/test_db.py` with unit tests for all `db.py` query functions using a mocked asyncpg `Connection`: `test_save_record_inserts_and_returns_row`, `test_save_record_returns_existing_on_conflict`, `test_get_by_video_id_returns_none_when_missing`, `test_list_recent_returns_items_in_reverse_chronological_order`, `test_get_full_record_returns_transcript`
- [X] T020 [P] Run `ruff check . && ruff format . && mypy app/` from `backend/` and fix any linting or type errors introduced in `backend/app/config.py`, `backend/app/db.py`, `backend/app/main.py`, `backend/app/models.py`
- [ ] T021 Validate all scenarios in `specs/004-postgres-video-storage/quickstart.md` against a running instance with a real database connection; confirm `GET /api/history` returns stored records and the frontend history panel renders correctly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **User Story phases (3, 4, 5)**: All depend on Phase 2 completion; can proceed in priority order or in parallel across team members
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2. No dependency on US2 or US3.
- **US2 (P2)**: Starts after Phase 2. Integrates with US1 (modifies the same endpoint), so implement after US1 is stable.
- **US3 (P3)**: Starts after Phase 2. Adds a new endpoint, no conflict with US1/US2.

### Within Each Phase

- T003 and T004 are independent (different files) — run in parallel
- T005 depends on T003 (imports `settings.database_url`)
- T006 depends on T005 (imports db.py functions)
- In Phase 3: T009 and T010 (frontend types/api) are independent of T007/T008 (backend) — run in parallel across frontend/backend
- T011 (HistoryCard) depends on T009 (HistoryItem type)
- T012 (HistoryPanel) depends on T010 (fetchHistory) and T011 (HistoryCard)
- T013 (App.vue) depends on T012 (HistoryPanel)
- T014 (integration tests) depends on T007 and T008

### Parallel Opportunities

- T003 ‖ T004 (config.py and models.py — different files)
- T007 / T008 (backend) ‖ T009 / T010 (frontend) — completely different stacks, no shared files
- T009 ‖ T010 (different frontend files)
- T019 ‖ T020 (unit tests and linting — different files)

---

## Parallel Example: User Story 1

```bash
# Backend developer:
# T007: add persist to POST /api/summarize (backend/app/main.py)
# T008: add GET /api/history (backend/app/main.py) — after T007

# Frontend developer (simultaneously):
# T009: add HistoryItem type (frontend/src/types/index.ts)
# T010: add fetchHistory (frontend/src/services/api.ts)  ← after T009

# Then sequentially:
# T011: HistoryCard.vue
# T012: HistoryPanel.vue
# T013: App.vue
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational — **BLOCKS everything**
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: `GET /api/history` returns records; frontend history panel visible and populated
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → DB connected, table exists
2. US1 → Videos persist; history list works; frontend panel shows records *(MVP)*
3. US2 → Duplicate submissions return instantly *(performance)*
4. US3 → Full transcript accessible per record *(completeness)*
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With two developers:

1. Both complete Setup + Foundational together
2. Once Phase 2 is done:
   - Dev A: T007–T008 (backend endpoints for US1)
   - Dev B: T009–T013 (frontend history panel for US1)
3. Merge US1 → validate together
4. Continue with US2 and US3 sequentially or in parallel

---

## Notes

- `[P]` = different files, no incomplete dependencies
- `[USN]` maps task to a specific user story for traceability
- Each user story is independently completable and testable
- DB failure MUST NOT block `POST /api/summarize` response (FR-006, SC-005)
- Transcripts are excluded from `GET /api/history` list to keep payloads small (use `GET /api/history/{video_id}` for full record)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently before proceeding
