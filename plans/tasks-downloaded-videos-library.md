# Tasks: Downloaded Videos Library

Derived from `prd-downloaded-videos-library.md`. Modules M1–M9 map to task IDs below.
All PRD "Open Questions & Risks" are resolved with concrete decisions — see
**Resolved Decisions** and the per-task notes (no decision is deferred to implementation time).

---

## Phase 1 — Backend: query, models, endpoint, wiring

### T001 — Add `list_downloaded()` to `backend/app/db.py`  *(M1)*
- **Module**: `backend/app/db.py`
- **Task**: Add `async def list_downloaded(conn) -> list[DownloadedItem]` that runs:
  `SELECT video_id, title, thumbnail_url, downloaded_at FROM youtube_summarizer.summaries WHERE deleted_at IS NULL AND download_status = 'ready' ORDER BY downloaded_at DESC`
  and maps each row to `DownloadedItem`. No row limit. Import `DownloadedItem` from `app.models`.
- **Done when**: Function exists, returns ready-only / non-soft-deleted rows ordered by `downloaded_at DESC`, has a docstring, `mypy app/` clean.
- **Depends on**: T002

### T002 — Add `DownloadedItem` + `DownloadedListResponse` to `backend/app/models.py`  *(M2)*
- **Module**: `backend/app/models.py`
- **Task**: Add `DownloadedItem(video_id: str, title: str | None, thumbnail_url: str | None, downloaded_at: datetime)` and `DownloadedListResponse(items: list[DownloadedItem])`.
- **Done when**: Both models exist as Pydantic v2 `BaseModel`s; field names/types exactly match the TS interface in T005.
- **Depends on**: none

### T003 — Add `GET /api/videos/downloaded` endpoint to `backend/app/main.py`  *(M3)*
- **Module**: `backend/app/main.py`
- **Task**: Register `@app.get("/api/videos/downloaded")` (place it **before** the `/api/videos/{video_id}/download` routes so `downloaded` is never captured as a `video_id` path param). Handler: `async def list_downloaded_videos(conn = Depends(get_db))` → `return DownloadedListResponse(items=await list_downloaded(conn))`. Wrap any unexpected failure to return `ErrorResponse(error="internal_error", message=...)` consistent with existing endpoints.
- **Done when**: Endpoint returns `{ "items": [...] }`; route ordering verified so `/api/videos/downloaded` does not collide with `/api/videos/{video_id}/...`; follows `ErrorResponse` convention.
- **Depends on**: T001, T002, T004

### T004 — Wire `list_downloaded` import in `backend/app/main.py`
- **Module**: `backend/app/main.py`
- **Task**: Add `list_downloaded` to the existing `from app.db import (...)` block; add `DownloadedListResponse` (and `DownloadedItem` if referenced) to the `from app.models import (...)` block.
- **Done when**: Module imports without `ImportError`; `ruff check .` clean.
- **Depends on**: T001, T002

---

## Phase 2 — Frontend foundation: type, API client, util

### T005 — Add `DownloadedItem` interface to `frontend/src/types/index.ts`  *(M5)*
- **Module**: `frontend/src/types/index.ts`
- **Task**: Add `export interface DownloadedItem { video_id: string; title: string | null; thumbnail_url: string | null; downloaded_at: string; }` (ISO 8601 string), mirroring the Pydantic model from T002 (type-mirroring ADR).
- **Done when**: Interface exists and matches T002 field-for-field.
- **Depends on**: none (keep in sync with T002)

### T006 — Add `fetchDownloaded()` to `frontend/src/services/api.ts`  *(M5)*
- **Module**: `frontend/src/services/api.ts`
- **Task**: Add `export async function fetchDownloaded(): Promise<{ items: DownloadedItem[] }>` that GETs `${API_BASE}/api/videos/downloaded`, throwing `ApiError` on non-OK using the existing error-parsing pattern. Import `DownloadedItem` type.
- **Done when**: Function exists, returns `{ items }`, throws `ApiError` on failure, consistent with `fetchHistory()`.
- **Depends on**: T005

### T007 — Add `formatRelativeTime()` util  *(M4)*
- **Module**: `frontend/src/utils/relativeTime.ts` (new file)
- **Task**: Add `export function formatRelativeTime(iso: string, now?: Date): string` returning buckets: `< 60s` → "just now"; minutes → "N minute(s) ago"; hours → "N hour(s) ago"; days → "N day(s) ago"; weeks → "N week(s) ago"; months → "N month(s) ago"; years → "N year(s) ago". Accept an optional `now` arg for deterministic testing. Used by `VideoCard` as `Downloaded {{ formatRelativeTime(item.downloaded_at) }}`.
- **Done when**: Pure function, no side effects, correct singular/plural, optional `now` injection for tests.
- **Depends on**: none

---

## Phase 3 — Frontend components

### T008 — Create `VideoCard.vue`  *(M6)*
- **Module**: `frontend/src/components/VideoCard.vue` (new file)
- **Task**: Presentational card. Props: `item: DownloadedItem`. Emits `play: [videoId: string]`. Renders a 16:9 thumbnail (`item.thumbnail_url`, with `@error` to hide a broken image like `HistoryCard`), a title clamped to 2 lines (`-webkit-line-clamp: 2`, falls back to `item.video_id` when title is null), and a `Downloaded {{ formatRelativeTime(item.downloaded_at) }}` line. Whole card is clickable (and keyboard-activatable: `role="button"`, `tabindex="0"`, Enter/Space → emit `play`) with an accessible label. No delete/secondary actions (play-only per FR-7).
- **Done when**: Renders all three fields, emits `play` on click and Enter/Space, broken thumbnail degrades gracefully, has alt text + accessible label.
- **Depends on**: T005, T007

### T009 — Create `LibraryView.vue`  *(M7)*
- **Module**: `frontend/src/components/LibraryView.vue` (new file)
- **Task**: Container view. On mount, call `fetchDownloaded()` into local state with `loading` / `error` / `items` refs. Render:
  - **loading**: status text ("Loading your library…") mirroring `HistoryPanel`.
  - **error**: message + a "Retry" button that re-fetches (mirrors `HistoryPanel` error pattern).
  - **empty** (`items.length === 0`): "No downloaded videos yet — download a video from its summary to see it here."
  - **grid**: a responsive CSS grid of `VideoCard`, `:key="item.video_id"`. Grid CSS: `display:grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 1.25rem;` inside a centered container (`max-width: 1100px`). Listen to each card's `play` and call `openPlayer(videoId)` → `window.open('/?watch=' + encodeURIComponent(videoId), '_blank', 'noopener')`.
- **Done when**: All four states render correctly; cards open a new tab at `/?watch=<id>`; grid is responsive (1 col narrow → ~4 cols wide); refetches whenever the component mounts.
- **Depends on**: T006, T008

---

## Phase 4 — Frontend shell & wiring (App.vue, SummaryDisplay)

### T010 — Add `initialTab` prop to `SummaryDisplay.vue`  *(M9)*
- **Module**: `frontend/src/components/SummaryDisplay.vue`
- **Task**: Add optional prop `initialTab?: "summary" | "transcript" | "qa" | "notes" | "video"`. Initialize `activeTab` from `props.initialTab ?? "summary"`. Do not change any existing caller (Summarize view passes nothing → stays `"summary"`).
- **Done when**: Prop exists; omitting it preserves current behavior; passing `"video"` opens on the Video tab.
- **Depends on**: none

### T011 — Add nav bar + `view` state to `App.vue`  *(M8)*
- **Module**: `frontend/src/App.vue`
- **Task**: Add `const view = ref<'summarize' | 'library' | 'player'>('summarize')`. Add a persistent top nav bar rendered on **every** view with brand text + two links: **Summarize** and **Library**. Clicking Summarize → `goTo('summarize')`; Library → `goTo('library')`. `goTo(v)` sets `view.value = v` and, when leaving the player, clears the deep-link param via `window.history.replaceState({}, '', '/')` so a refresh won't reopen the player (resolves Open Q2). Active link is highlighted for `summarize`/`library`; **no** active link when `view === 'player'`.
- **Done when**: Nav bar shows on all views; clicking links switches `view`; `?watch` is cleared from the URL when navigating away from the player; player view shows no active link.
- **Depends on**: none

### T012 — Boot deep link `?watch=<id>` in `App.vue`  *(M8)*
- **Module**: `frontend/src/App.vue`
- **Task**: In `onMounted`, read `new URLSearchParams(window.location.search).get('watch')`. If present and non-empty, set `view.value = 'player'` and call the existing `handleSelectVideo(id)` to load the full record. (Reuses the existing error path for not-found / not-ready ids.)
- **Done when**: Opening `/?watch=<id>` in a fresh tab loads that record and shows the player view; no `?watch` → normal Summarize view; invalid id surfaces the existing error UI.
- **Depends on**: T011, T015

### T013 — Conditional view rendering in `App.vue`  *(M8, FR-8)*
- **Module**: `frontend/src/App.vue`
- **Task**: Restructure the template so exactly one view renders under the nav bar, using `v-if`/`v-else-if` (not `v-show`) so `LibraryView` remounts and refetches on every visit (resolves Open Q5 / cross-tab staleness within a tab):
  - `view === 'summarize'`: existing header + controls + loading/error/`SummaryDisplay`/fallacy panels, **and** the existing history drawer (`HistoryPanel`). Drawer markup moves inside this branch only.
  - `view === 'library'`: `<LibraryView />`, no drawer, no fallacy panels.
  - `view === 'player'`: loading/error + `SummaryDisplay` with `initial-tab="video"`, no drawer, no header/controls, no fallacy panels (player renders `SummaryDisplay` only — resolves Open Q3).
- **Done when**: Only one view shows at a time; drawer appears only on Summarize; LibraryView remounts on each Library visit.
- **Depends on**: T009, T010, T011, T014

### T014 — Wire `LibraryView` import into `App.vue`  *(M8)*
- **Module**: `frontend/src/App.vue`
- **Task**: `import LibraryView from "@/components/LibraryView.vue"` and reference it in the `library` branch.
- **Done when**: Import present; Library view renders without error.
- **Depends on**: T009

### T015 — Render player view via `SummaryDisplay(initial-tab="video")` in `App.vue`  *(M8)*
- **Module**: `frontend/src/App.vue`
- **Task**: In the `player` branch, render the same loading/error elements as Summarize plus `<SummaryDisplay ... :initial-tab="'video'" />` bound to the existing refs (`summary`, `transcript`, `metadata`, `currentVideoId`, `currentHighlights`, `currentQaHistory`, `currentNotes`). No URL input, length slider, header, or fallacy panels.
- **Done when**: Player view shows the populated `SummaryDisplay` opened on the Video tab with playback available; reuses existing `handleSelectVideo` data.
- **Depends on**: T010

---

## Phase 5 — Tests

### T016 — Unit test `list_downloaded()`  *(M1)*
- **Module**: `backend/tests/unit/test_db.py`
- **Task**: Add tests verifying: (a) only `download_status = 'ready'` rows returned (pending/error/null excluded); (b) `deleted_at IS NOT NULL` rows excluded; (c) ordering is `downloaded_at DESC`; (d) empty result → `[]`. Use the existing test_db patterns (mocked/fake conn or fixture).
- **Done when**: Tests exist and pass under `pytest tests/unit/test_db.py`.
- **Depends on**: T001

### T017 — Integration test `GET /api/videos/downloaded`  *(M3)*
- **Module**: `backend/tests/integration/test_api.py`
- **Task**: Using FastAPI TestClient with mocked `get_db`: (a) returns 200 with `{ "items": [...] }` shape; (b) items carry `video_id`, `title`, `thumbnail_url`, `downloaded_at`; (c) empty downloads → `{ "items": [] }`; (d) route resolves to the list endpoint and is not shadowed by `/api/videos/{video_id}/download`.
- **Done when**: Tests exist and pass under `pytest tests/integration/test_api.py`.
- **Depends on**: T003

### T018 — Unit test `formatRelativeTime()`  *(M4)*
- **Module**: `frontend/` vitest (e.g. `src/utils/relativeTime.spec.ts`)
- **Task**: Test each bucket boundary using the injectable `now`: just now (<60s), minutes, hours, days, weeks, months, years, and singular vs plural ("1 day ago" vs "2 days ago").
- **Done when**: Tests pass under `npm run test`.
- **Depends on**: T007

### T019 — Component test `VideoCard.vue`  *(M6)*
- **Module**: `frontend/` vitest + Vue Test Utils (e.g. `src/components/VideoCard.spec.ts`)
- **Task**: Mount with a sample `item`; assert thumbnail/title/relative-date render; assert clicking the card and pressing Enter both emit `play` with the `video_id`; assert null title falls back to `video_id`.
- **Done when**: Tests pass.
- **Depends on**: T008

### T020 — Component test `LibraryView.vue`  *(M7)*
- **Module**: `frontend/` vitest + Vue Test Utils (e.g. `src/components/LibraryView.spec.ts`)
- **Task**: With `fetchDownloaded` mocked: assert loading state shows, then grid of `VideoCard`s on success; empty state when `items` is `[]`; error state + working Retry on rejection; clicking a card invokes `window.open` with `/?watch=<id>` (stub `window.open`).
- **Done when**: All four states + open-player behavior covered; tests pass.
- **Depends on**: T009

---

## Phase 6 — Edge cases, NFRs, regression, QA

### T021 — Edge: empty Library state  *(PRD edge case)*
- **Module**: `frontend/src/components/LibraryView.vue` (verify) / Manual QA
- **Task**: With zero ready downloads, the empty-state copy renders (no grid, no error).
- **Done when**: Verified in T020 and in browser.
- **Depends on**: T009, T020

### T022 — Edge: fetch failure → error + Retry  *(PRD edge case)*
- **Module**: `frontend/src/components/LibraryView.vue` (verify) / Manual QA
- **Task**: Simulate API failure; error message + Retry shown; Retry re-fetches successfully.
- **Done when**: Verified in T020 and in browser.
- **Depends on**: T009, T020

### T023 — Edge: thumbnail load failure  *(PRD edge case)*
- **Module**: `frontend/src/components/VideoCard.vue` (verify) / Manual QA
- **Task**: With a broken `thumbnail_url`, the image hides via `@error` and the card still shows title + date.
- **Done when**: Card renders gracefully with no broken-image icon.
- **Depends on**: T008

### T024 — Edge: `?watch=<id>` not found / not ready  *(PRD edge case)*
- **Module**: `frontend/src/App.vue` (verify) / Manual QA
- **Task**: Opening `/?watch=<bogus>` shows the existing `handleSelectVideo` error UI in the player view (no crash, nav bar still present).
- **Done when**: Error path verified; nav bar remains usable.
- **Depends on**: T012

### T025 — Edge: downloaded row whose file is missing on disk  *(PRD edge case)*
- **Module**: Manual QA (existing stream auto-heal)
- **Task**: For a `ready` row whose file was removed, playing it hits `/api/videos/{id}/stream`, which auto-heals via `clear_download()`. Confirm the video then no longer appears in the Library after a refetch.
- **Done when**: Auto-heal behavior confirmed; Library list converges to actually-present files.
- **Depends on**: T003, T009

### T026 — NFR: no new dependencies  *(PRD NFR)*
- **Module**: `frontend/package.json`, backend deps
- **Task**: Confirm no dependency was added (no `vue-router`, etc.); feature uses only existing stack.
- **Done when**: `git diff` shows no additions to `package.json` dependencies or backend requirements.
- **Depends on**: T001–T015

### T027 — NFR: accessibility of nav + cards  *(PRD NFR)*
- **Module**: `frontend/src/App.vue`, `frontend/src/components/VideoCard.vue` / Manual QA
- **Task**: Nav links are real focusable controls; cards are keyboard-activatable with accessible labels and `alt` text.
- **Done when**: Keyboard-only navigation can reach Library and open a card; screen-reader labels present.
- **Depends on**: T008, T011

### T028 — NFR: query efficiency (no N+1)  *(PRD NFR)*
- **Module**: `backend/app/db.py` (code review)
- **Task**: Confirm `list_downloaded()` is a single query with no per-row follow-up fetch and the endpoint does no extra metadata fetch per card.
- **Done when**: Single-query confirmed by review.
- **Depends on**: T001, T003

### T029 — Regression: existing flows unchanged  *(PRD acceptance)*
- **Module**: Manual QA + existing test suite
- **Task**: Verify Summarize flow, history drawer (select/delete/restore), and `SummaryDisplay` default (opens on Summary tab) all behave as before. Run `pytest` and `npm run test`.
- **Done when**: All pre-existing tests pass; Summarize + drawer behavior unchanged.
- **Depends on**: T010, T011, T013

---

## Resolved Decisions (from PRD "Open Questions & Risks")

These were resolved during planning; the resolution is baked into the referenced task so no
decision is deferred to implementation time.

| PRD Q | Decision | Where enforced |
|-------|----------|----------------|
| Q1 — Autoplay in player tab? | **No autoplay.** Keep native `<video controls>` only (avoids muted-autoplay/mobile-block surprises). `VideoPlayer.vue` is unchanged — no `autoplay` attr added. | T015 (no change to `VideoPlayer`); QA T029 |
| Q2 — Clear `?watch` on nav away? | **Yes.** When `goTo()` leaves the player view, call `window.history.replaceState({}, '', '/')` so a refresh won't reopen the player and the URL reflects the active view. | T011 |
| Q3 — Fallacy panels in player tab? | **No (out of scope).** Player view renders `SummaryDisplay` only; fallacy panels stay exclusive to the Summarize flow. | T013, T015 |
| Q4 — Grid responsiveness target? | **`grid-template-columns: repeat(auto-fill, minmax(240px, 1fr))`, gap `1.25rem`, container `max-width: 1100px`** → 1 col on narrow screens up to ~4 cols on wide. | T009 |
| Q5 — Cross-tab staleness after delete elsewhere? | **Accept as-is, with same-tab freshness via remount.** Use `v-if` for views so `LibraryView` remounts and refetches on each Library visit; no cross-tab live sync / focus-refetch added. | T009, T013 |

---

## Cross-Check Audit (PRD ↔ tasks)

Audit of `prd-downloaded-videos-library.md` against the tasks above. Result: **no gaps; no
unresolved/deferred decisions.**

**1. User flows — every step has a covering task**
- Browse (nav → grid): T011, T013, T014, T009 ✅
- Play (card → new tab): T009 (`window.open`), T008 (emit) ✅
- Player boot (`?watch` → Video tab): T012, T015, T010 ✅
- Manage (remove via Video tab): existing `VideoPlayer` Delete; T013 keeps it reachable; T025 confirms list converges ✅
- Return (close tab / nav): T011 ✅

**2. Modules — all PRD modules mapped**
- M1→T001, M2→T002, M3→T003 (+T004 wiring), M4→T007, M5→T005+T006, M6→T008, M7→T009, M8→T011+T012+T013+T014+T015, M9→T010 ✅

**3. Edge cases — every PRD edge row has a task**
- No downloads→T021; fetch failure→T022; thumbnail fail→T023; `?watch` not found→T024; file-missing/auto-heal→T025; stale grid→resolved via T009/T013 (Q5) ✅

**4. NFRs — each has a verification task**
- No new deps→T026; performance/no-N+1→T028; accessibility→T027; consistency (`ErrorResponse`/route order)→T003; type-mirroring→T005 (vs T002) ✅

**5. Open questions — converted AND resolved (not merely mapped)**
- Q1 RESOLVED (no autoplay)·Q2 RESOLVED (replaceState)·Q3 RESOLVED (no fallacy panels)·Q4 RESOLVED (explicit grid CSS)·Q5 RESOLVED (v-if remount). See Resolved Decisions table. No task uses "decide/TBD/choose" wording. ✅

**6. Wiring — explicit connection tasks present**
- Backend import wiring→T004; route registration/ordering→T003; `App.vue` ⇄ `LibraryView` import→T014; nav ⇄ `view` state→T011; `?watch` ⇄ `handleSelectVideo`→T012; view ⇄ `SummaryDisplay(initial-tab)`→T015; drawer scoping→T013 ✅

**Human-decision-required items**: none. All PRD-deferred choices were decidable from the PRD/context and are now concrete.

---

## Revision History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0 | 2026-06-01 | Claude Code | Initial task list generated from PRD (prd-to-tasks) and cross-checked; all open questions resolved with concrete decisions baked into tasks. |
