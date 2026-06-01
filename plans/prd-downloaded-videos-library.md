# Product Requirements Document (PRD)

## Overview & Context

- **Product/Feature Summary**: A new **Library** view — a YouTube-frontpage-style responsive grid of every locally downloaded video. Clicking a card opens that video in a **new browser tab** with the existing `SummaryDisplay` opened on its **Video** tab (player front-and-center). Navigation between the existing **Summarize** view and the new **Library** view is handled by a lightweight persistent top **nav bar** (no router).
- **Problem Statement**: Downloaded videos are only reachable by first re-finding their summary and clicking into the (tab-buried) `VideoPlayer`. There is no single place to see *what has been downloaded* or to jump straight into playback. The in-flight green-dot indicator (see `prd-history-download-indicator.md`) tells users *which* history items are downloaded but still doesn't give them a dedicated browsing/playback surface.
- **Business Objectives**: Make locally downloaded videos a first-class, browsable collection; reduce friction to replaying downloaded content; lay down a minimal multi-view navigation pattern the app currently lacks.
- **Success Metrics**: Users can reach any downloaded video in ≤2 clicks from anywhere (nav → card); the Library lists exactly the videos with `download_status = 'ready'`, newest download first; zero new runtime dependencies added.

---

## Scope

- **In Scope**:
  - **Backend**: `db.list_downloaded()` query; `DownloadedItem` / `DownloadedListResponse` Pydantic models; `GET /api/videos/downloaded` endpoint.
  - **Frontend**: persistent top nav bar + `view` state in `App.vue`; `?watch=<video_id>` deep-link boot logic; new `LibraryView.vue` (grid + states) and `VideoCard.vue` (presentational card); `formatRelativeTime()` util; `fetchDownloaded()` + `DownloadedItem` TS type in `api.ts`; new `initialTab` prop on `SummaryDisplay.vue`.
  - **Tests**: M1 (`list_downloaded`, unit), M3 (endpoint, integration), M4 (`formatRelativeTime`, unit), M6/M7 (`VideoCard` / `LibraryView`, component).
- **Out of Scope**:
  - Adding `vue-router` or any new dependency (excluded per the "No new dependencies without justification" ADR in `CLAUDE.md`).
  - Download/un-download flow itself — already exists in `VideoPlayer` (trigger, poll, stream, delete). The Library does **not** add a delete/remove-download affordance on cards; removal stays in the Video tab's existing Delete button.
  - Persisting or displaying channel name / duration on cards (not stored in the `summaries` table).
  - Fallacy panels in the player tab (the player view renders `SummaryDisplay` only). Easy follow-up if wanted.
  - Cross-tab live sync (deleting a download in one tab won't auto-refresh a Library grid open in another tab; the grid refetches on mount/visit).
  - The green-dot history indicator (covered separately by `prd-history-download-indicator.md`).
- **Release Phases / Milestones**: Single release. Backend (M1–M3) and frontend (M4–M9) can land together; backend is independently testable first.

---

## Stakeholders

- **Target Users / Personas**: Users who download videos for offline / faster local playback and want to browse and replay their downloaded collection.
- **Internal Stakeholders**: Product owner, frontend and backend implementers.
- **Owners**: Implementation team.

---

## Requirements

### Functional Requirements

- **FR-1 (Navigation)**: As a user, I want a persistent top nav bar with **Summarize** and **Library** links so I can switch views without losing my place. `App.vue` holds `const view = ref<'summarize' | 'library' | 'player'>('summarize')`; default view is `summarize`. The nav bar renders on **every** view.
- **FR-2 (Library grid)**: As a user, I want the Library to show a responsive grid of all downloaded videos so I can browse them like a video wall. Each card shows a 16:9 thumbnail, a title clamped to ~2 lines, and a relative "Downloaded 3 days ago" line. Cards are sorted newest-download-first (`downloaded_at DESC`).
- **FR-3 (Click to play in a new window)**: As a user, I want clicking a card to open the video in a new browser tab. The card click calls `window.open('/?watch=' + video_id, '_blank')`.
- **FR-4 (Player boot)**: On mount, `App.vue` reads `?watch` from `location.search`; if present, it calls the existing `handleSelectVideo(video_id)` and sets `view = 'player'`, rendering `SummaryDisplay` opened on the **Video** tab so the player is front-and-center.
- **FR-5 (`initialTab`)**: `SummaryDisplay.vue` accepts a new `initialTab?: 'summary' | 'transcript' | 'qa' | 'notes' | 'video'` prop, defaulting to `'summary'`. The player view passes `'video'`. Existing usages (Summarize view, history selection) are unaffected.
- **FR-6 (Data source)**: `GET /api/videos/downloaded` returns `{ items: DownloadedItem[] }` where the list is `summaries` rows with `download_status = 'ready' AND deleted_at IS NULL`, ordered by `downloaded_at DESC`, with **no** row limit. Each `DownloadedItem` carries `video_id`, `title`, `thumbnail_url`, `downloaded_at`.
- **FR-7 (Play-only cards)**: Library cards have no per-card actions other than opening the player tab. Removing a download remains the Delete button inside the Video tab of `SummaryDisplay`/`VideoPlayer`.
- **FR-8 (History drawer unchanged)**: The existing left "Recent Videos" history drawer (`HistoryPanel`) remains exactly as-is and appears **only** on the Summarize view. Library and player views show no drawer.
- **FR-9 (Empty / loading / error states)**: The Library shows a loading indicator while fetching, an error message with a Retry button on failure, and an empty state ("No downloaded videos yet — download a video from its summary to see it here") when there are zero ready downloads — mirroring `HistoryPanel`'s status patterns.
- **FR-10 (Type mirroring)**: A `DownloadedItem` TS interface in `frontend/src/types/index.ts` mirrors the Pydantic model exactly (per the type-mirroring ADR), and `api.ts` exposes `fetchDownloaded()` using the existing `ApiError` pattern.

### Non-Functional Requirements

- **No new dependencies**: Implemented entirely with the existing stack (FastAPI, asyncpg, Vue 3, TypeScript). No `vue-router`.
- **Performance**: `list_downloaded()` is a single indexed-ish scan over `summaries` filtered on `download_status`; no N+1, no per-card extra fetch. Card thumbnails are remote YouTube URLs (already used elsewhere).
- **Consistency**: Endpoint follows the `response_model=None` + `ErrorResponse(error, message)` convention; non-2xx responses use machine codes. Soft-delete and never-hard-delete ADRs are respected (the query filters `deleted_at IS NULL`; nothing is deleted).
- **Accessibility**: Cards are keyboard-activatable and have accessible labels/alt text; nav links are real focusable controls.
- **Resilience**: A thumbnail that fails to load degrades gracefully (matches `HistoryCard`'s `@error` hide pattern). A `?watch` id with no record surfaces the existing `handleSelectVideo` error path.

### Technical Constraints

- The `summaries` table already has `download_status`, `download_path`, `downloaded_at`, `error_message` columns — **no migration needed**.
- The `summaries` table does **not** store channel name or duration, so cards cannot show them without a metadata re-fetch (explicitly out of scope).
- Every downloaded video is necessarily already a summarized row (download is triggered from within `SummaryDisplay`), so the Library is strictly a subset of `summaries`; no separate downloads table.
- Player tab reuses the full SPA via `?watch`; no second Vite entry / standalone HTML page.

---

## User Experience

- **User Flows & Journeys**:
  1. **Browse**: User clicks **Library** in the nav bar → grid of downloaded videos loads (newest first).
  2. **Play**: User clicks a card → new browser tab opens at `/?watch=<id>` → `SummaryDisplay` renders on the Video tab with the `<video>` player visible; Summary / Transcript / Q&A / Notes are one click away.
  3. **Manage**: To remove a download, the user uses the existing Delete button in the Video tab; the card then drops out of the Library on next load.
  4. **Return**: User closes the player tab, or clicks Summarize / Library in the (always-present) nav bar within that tab.

- **Wireframes / Design Mockups** (ASCII):
  ```
  ┌────────────────────────────────────────────┐
  │  YT Summarizer        Summarize · Library    │  ← persistent nav (every view)
  ├────────────────────────────────────────────┤
  │  Library                                     │
  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │
  │  │ ▶ thumb│ │ ▶ thumb│ │ ▶ thumb│ │ ▶ thumb│ │
  │  ├────────┤ ├────────┤ ├────────┤ ├────────┤ │
  │  │ Title… │ │ Title… │ │ Title… │ │ Title… │ │
  │  │ 3 days │ │ 1 wk   │ │ today  │ │ 2 mo   │ │
  │  └────────┘ └────────┘ └────────┘ └────────┘ │
  └────────────────────────────────────────────┘

  Card click → window.open('/?watch=<id>') → new tab:
  ┌────────────────────────────────────────────┐
  │  YT Summarizer        Summarize · Library    │
  ├────────────────────────────────────────────┤
  │  [ Summary | Transcript | Q&A | Notes |▸Video]│
  │              ┌──────────────────┐            │
  │              │   ▶ video player │            │
  │              └──────────────────┘            │
  └────────────────────────────────────────────┘
  ```

- **Edge Cases & Error States**:
  - **No downloads**: empty-state message (FR-9).
  - **Fetch failure**: error message + Retry (FR-9).
  - **Thumbnail load failure**: image hidden, card still renders (title + date).
  - **`?watch` id not found / not ready**: existing `handleSelectVideo` error surfaces in the player tab.
  - **File deleted from disk but row still `ready`**: stream endpoint auto-heals via `clear_download()` (existing behavior); the next Library load no longer lists it.
  - **Stale grid after deleting elsewhere**: acceptable per scope; resolves on next Library load.

---

## Success Metrics

- **KPIs**:
  - Library lists exactly the rows where `download_status = 'ready'` and `deleted_at IS NULL`, ordered `downloaded_at DESC`.
  - Any downloaded video reachable in ≤2 clicks (nav → card).
  - Zero new dependencies in `package.json` / backend deps.
- **Acceptance Criteria**:
  - `GET /api/videos/downloaded` returns `{ items: [...] }` of `DownloadedItem` with `video_id`, `title`, `thumbnail_url`, `downloaded_at`, ready-only, soft-deleted excluded, newest first. (M1, M3)
  - Nav bar appears on all views; Summarize is the default; clicking Library shows the grid; clicking Summarize returns to the summarizer. (M8)
  - Each card renders thumbnail + 2-line title + relative date and opens `/?watch=<id>` in a new tab on click. (M6, M7)
  - A fresh tab at `/?watch=<id>` shows `SummaryDisplay` on the Video tab with playback available. (M8, M9)
  - `formatRelativeTime()` returns correct buckets (just now / minutes / hours / days / weeks / months). (M4)
  - Loading, error+retry, and empty states all render correctly. (M7)
  - Existing Summarize, history-drawer, and `SummaryDisplay` default behavior are unchanged.

---

## Timeline & Milestones

| Milestone | Description | Target Date |
|-----------|-------------|-------------|
| Kickoff | PRD approved, modules confirmed | Done (this session) |
| Backend complete | M1–M3 + unit/integration tests green | TBD |
| Frontend complete | M4–M9 + component/unit tests green | TBD |
| QA | Manual verification in browser (browse, play-in-new-tab, states) | TBD |
| Launch | Production release | TBD |

- **Dependencies**: None external. Database schema already present. Cosmetically adjacent to `prd-history-download-indicator.md` (shared `download_status`), but independent.

---

## Open Questions & Risks

| # | Question / Risk | Owner | Status |
|---|-----------------|-------|--------|
| 1 | Should the player tab autoplay? Default decision: **no** (native `controls` only) to avoid muted-autoplay/mobile-block surprises. | Product | Resolved (no autoplay) |
| 2 | Should nav links clear the `?watch` param via `history.replaceState` when leaving the player view in the same tab? | Eng | Open (minor) |
| 3 | Should the player tab also show fallacy panels (currently rendered only in the Summarize flow)? | Product | Deferred (out of scope) |
| 4 | Grid responsiveness target (min card width / columns per breakpoint)? | Design | Open (implementation detail) |
| 5 | Cross-tab staleness after deleting a download elsewhere — acceptable, or add a focus-refetch? | Product | Accepted as-is |

---

## Modules

| ID | Module | Layer | Deep/Isolated? | Tests |
|----|--------|-------|----------------|-------|
| M1 | `db.list_downloaded()` | Backend | Yes | Unit (`tests/unit/test_db.py`): ready-only filter, soft-delete exclusion, `downloaded_at DESC` ordering |
| M2 | `DownloadedItem` / `DownloadedListResponse` models | Backend | — | (covered via M3) |
| M3 | `GET /api/videos/downloaded` endpoint | Backend | Thin | Integration (`tests/integration/test_api.py`): response shape + items with mocked `get_db` |
| M4 | `formatRelativeTime()` util | Frontend | Yes | Unit (vitest): boundary buckets |
| M5 | `fetchDownloaded()` + `DownloadedItem` TS type | Frontend | — | (covered via M7) |
| M6 | `VideoCard.vue` | Frontend | Yes | Component (Vue Test Utils): renders fields, emits click |
| M7 | `LibraryView.vue` | Frontend | Container | Component: loading / empty / error / grid states |
| M8 | `App.vue` shell (nav, `view` ref, `?watch` boot) | Frontend | Orchestration | (manual QA) |
| M9 | `SummaryDisplay.vue` `initialTab` prop | Frontend | Additive | (manual QA) |

---

## Revision History

| Version | Date | Author | Summary of Changes |
|---------|------|--------|--------------------|
| 1.0 | 2026-06-01 | Claude Code | Initial PRD synthesized from the discuss-feature session |
