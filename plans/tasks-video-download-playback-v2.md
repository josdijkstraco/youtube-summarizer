# Tasks: Video Download & In-Browser Playback (v2)

Generated from: `prd-video-download-playback.md`  
Revised: gap analysis against PRD (2026-05-13) — changed tasks marked *(updated)*, new tasks marked *(new)*

---

## Phase 1 — Backend

### Infrastructure

---

**ID**: T001  
**Phase**: 1  
**Module**: `backend/requirements.txt`  
**Task**: Add `yt-dlp` as a pip dependency.  
**Done when**: `pip install -r backend/requirements.txt` succeeds and `import yt_dlp` works in the backend virtualenv.  
**Depends on**: —

---

**ID**: T002  
**Phase**: 1  
**Module**: `backend/app/config.py`  
**Task**: Add a `download_dir: Path` setting that defaults to `./downloads` and reads from the `DOWNLOAD_DIR` env var.  
**Done when**: `Settings().download_dir` returns `Path("downloads")` when `DOWNLOAD_DIR` is unset, and an alternative path when the env var is set.  
**Depends on**: —

---

**ID**: T003  
**Phase**: 1  
**Module**: `backend/app/main.py`  
**Task**: On FastAPI startup, create `settings.download_dir` if it does not exist (using `mkdir(parents=True, exist_ok=True)`).  
**Done when**: Starting the app against a fresh directory creates the folder; restarting against an existing folder does not raise.  
**Depends on**: T002

---

**ID**: T004  
**Phase**: 1  
**Module**: `docker-compose.yml`  
**Task**: Add `./downloads:/app/downloads` volume mount to the backend service.  
**Done when**: `docker-compose up --build` starts without error and `docker exec <container> ls /app/downloads` succeeds.  
**Depends on**: T002

---

**ID**: T005 *(updated)*  
**Phase**: 1  
**Module**: `backend/app/db.py`  
**Task**: Add a migration block inside `create_table()` that adds four columns to `youtube_summarizer.summaries` using `ALTER TABLE ADD COLUMN IF NOT EXISTS` inside a `DO $$ ... $$` block:
- `download_status TEXT`
- `download_path TEXT`
- `downloaded_at TIMESTAMPTZ`
- `download_error TEXT` — persists the error message from a failed yt-dlp run so `GET /download` can return it on subsequent polls.

**Done when**: Running `create_table()` on a database that already has the `summaries` table adds all four columns without error; running it again is a no-op.  
**Depends on**: —

> **Gap D fix**: The original task listed three columns. `download_error TEXT` is required to persist the error string that `DownloadStatusResponse.error_message` (T008) promises to surface. Without this column, `error_message` is always `None` on poll responses.

---

### `downloader.py` service

---

**ID**: T006  
**Phase**: 1  
**Module**: `backend/app/services/downloader.py` *(new file)*  
**Task**: Create `download_video(video_id: str, url: str, output_dir: Path) -> Path` that uses `yt-dlp` with the format string `bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best`, outputs to `{output_dir}/{video_id}.mp4`, and returns the output path on success.  
**Done when**: Calling the function for a public YouTube URL produces a valid `.mp4` file at the expected path; the function raises on failure (geo-block, private video, etc.).  
**Depends on**: T001, T002

---

**ID**: T007  
**Phase**: 1  
**Module**: `backend/app/services/downloader.py`  
**Task**: Ensure `download_video` is idempotent — if `{output_dir}/{video_id}.mp4` already exists, skip the yt-dlp call and return the path immediately.  
**Done when**: Calling `download_video` twice for the same `video_id` does not invoke yt-dlp on the second call (verified via mock).  
**Depends on**: T006

---

### Models

---

**ID**: T008 *(updated)*  
**Phase**: 1  
**Module**: `backend/app/models.py`  
**Task**: Add a `DownloadStatusResponse` Pydantic model with fields `video_id: str`, `status: str | None` (one of `pending | ready | error | null`), `downloaded_at: datetime | None`, and `error_message: str | None`.  
**Done when**: Model serialises correctly to JSON and matches the shape expected by the frontend `DownloadStatus` type (T020). `error_message` is populated from the `download_error` DB column (T005) — it is not a transient field.

**Note — `VideoRecord` intentional omission**: `VideoRecord` does not include `download_status`, `download_path`, `downloaded_at`, or `download_error`. Asyncpg returns these columns from `SELECT *` but Pydantic silently drops unknown fields. This is intentional: the VideoPlayer component fetches its own status via `GET /download` on mount (T027) rather than relying on the summary response. No change to `VideoRecord` or the TypeScript `VideoRecord` interface is required.  
**Depends on**: —

> **Gap D/E fix**: Clarifies that `error_message` must be backed by the `download_error` column, not populated transiently. Documents the deliberate decision to omit download fields from `VideoRecord`.

---

### DB functions

---

**ID**: T009 *(updated)*  
**Phase**: 1  
**Module**: `backend/app/db.py`  
**Task**: Add three download-related DB helpers:

1. `get_download_status(video_id) -> tuple[str | None, str | None, datetime | None, str | None]` — returns `(status, path, downloaded_at, error_message)` for the given `video_id`; returns all-`None` tuple if row not found.
2. `save_download_status(video_id, status, path=None, error=None)` — UPDATEs `download_status`, `download_path`, `downloaded_at` (set to `now()` when status is `"ready"`), and `download_error` for the given `video_id`.
3. `clear_download(video_id)` — sets all four download columns to `NULL`.

**Done when**: Integration tests confirm:
- `save_download_status(..., status="error", error="geo-blocked")` writes `"geo-blocked"` to `download_error`.
- `get_download_status(video_id)` returns the correct 4-tuple, including a non-null `error_message` after a failed download.
- `clear_download(video_id)` nulls all four columns.

**Depends on**: T005

> **Gap C/D fix**: `get_download_status()` was referenced by T016 but never explicitly tasked. `save_download_status` must persist the `error` param to `download_error`; the original DB implementation discarded it.

---

**ID**: T010  
**Phase**: 1  
**Module**: `backend/app/db.py`  
**Task**: *(Merged into T009 above.)*  
**Depends on**: T005

---

**ID**: T011  
**Phase**: 1  
**Module**: `backend/app/db.py`  
**Task**: Update `soft_delete(video_id)` to read `download_path` from the row, delete the file at that path if it exists (best-effort: log a warning on `OSError`, never raise), then call `clear_download(video_id)` before setting `deleted_at`.  
**Done when**: Soft-deleting a summary whose `download_path` points to a real file removes that file from disk; if the file is missing, soft-delete still succeeds.  
**Depends on**: T009

---

### API endpoints

---

**ID**: T012  
**Phase**: 1  
**Module**: `backend/app/main.py`  
**Task**: Add `POST /api/videos/{video_id}/download` that spawns `download_video` as a `BackgroundTask` (or `asyncio.to_thread`), sets `download_status` to `pending`, and returns `DownloadStatusResponse`.  
**Done when**: Calling the endpoint returns 200 with `status: "pending"` and the background download starts without blocking the event loop.  
**Depends on**: T005, T006, T008, T009

---

**ID**: T013  
**Phase**: 1  
**Module**: `backend/app/main.py`  
**Task**: Add `GET /api/videos/{video_id}/download` that reads `download_status`, `download_path`, `downloaded_at`, and `download_error` from the DB via `get_download_status()` and returns `DownloadStatusResponse`.  
**Done when**: Polling the endpoint returns the current status including `error_message` when status is `"error"`; returns `status: null` when no download has ever been triggered.  
**Depends on**: T005, T008, T009

---

**ID**: T014  
**Phase**: 1  
**Module**: `backend/app/main.py`  
**Task**: Add `GET /api/videos/{video_id}/stream` that reads `download_path` from the DB and serves the file with HTTP `Range` request support using `FileResponse` or a manual `StreamingResponse`.  
**Done when**: Browser `<video>` tag can seek to an arbitrary timestamp without re-downloading the whole file (confirmed via browser network tab showing 206 Partial Content responses).  
**Depends on**: T005, T009

---

### Wiring: backend modules

---

**ID**: T015  
**Phase**: 1  
**Module**: `backend/app/main.py` ↔ `backend/app/services/downloader.py`  
**Task**: Wire the `POST /download` endpoint to invoke `download_video` in a background task, update status to `ready` on success or `error` on exception, and call `save_download_status` in both branches.  
**Done when**: A successful download transitions DB status from `pending` → `ready`; a yt-dlp failure transitions it to `error` and persists the exception message in `download_error`.  
**Depends on**: T006, T009, T012

---

**ID**: T016  
**Phase**: 1  
**Module**: `backend/app/main.py` ↔ `backend/app/db.py`  
**Task**: Wire `GET /download` to read status via `get_download_status(video_id)` DB helper and return the result as `DownloadStatusResponse`.  
**Done when**: Polling the endpoint after a completed download returns `status: "ready"` and a non-null `downloaded_at`; after a failed download returns `status: "error"` and a non-null `error_message`.  
**Depends on**: T009, T013

---

**ID**: T017  
**Phase**: 1  
**Module**: `backend/app/main.py` ↔ `backend/app/db.py`  
**Task**: Wire `GET /stream` to read `download_path` from DB, return 404 `ErrorResponse` if `download_path` is NULL or the file does not exist on disk.  
**Done when**: Requesting stream for a `video_id` with no downloaded file returns 404 with `error: "not_found"`.  
**Depends on**: T009, T014

---

## Phase 2 — Frontend

### Types & API service

---

**ID**: T018  
**Phase**: 2  
**Module**: `frontend/src/types/index.ts`  
**Task**: Add `DownloadStatus` TypeScript type with fields `video_id`, `status` (`"pending" | "ready" | "error" | null`), `downloaded_at`, `error_message` to mirror `DownloadStatusResponse`.  
**Done when**: Type compiles without error and matches the shape of `DownloadStatusResponse` (T008).  
**Depends on**: T008

---

**ID**: T019  
**Phase**: 2  
**Module**: `frontend/src/services/api.ts`  
**Task**: Add `triggerDownload(videoId: string): Promise<DownloadStatus>` that calls `POST /api/videos/{videoId}/download`.  
**Done when**: Function returns a typed `DownloadStatus` object and throws `ApiError` on non-2xx.  
**Depends on**: T012, T018

---

**ID**: T020  
**Phase**: 2  
**Module**: `frontend/src/services/api.ts`  
**Task**: Add `getDownloadStatus(videoId: string): Promise<DownloadStatus>` that calls `GET /api/videos/{videoId}/download`.  
**Done when**: Function returns a typed `DownloadStatus` object and throws `ApiError` on non-2xx.  
**Depends on**: T013, T018

---

**ID**: T021  
**Phase**: 2  
**Module**: `frontend/src/services/api.ts`  
**Task**: Add `getStreamUrl(videoId: string): string` that returns the absolute URL for `GET /api/videos/{videoId}/stream` (no fetch required — used as `<video src>`).  
**Done when**: The returned string can be set as the `src` of a `<video>` element and the browser plays the file.  
**Depends on**: T014

---

### `VideoPlayer.vue` component

---

**ID**: T022  
**Phase**: 2  
**Module**: `frontend/src/components/VideoPlayer.vue` *(new file)*  
**Task**: Create the `VideoPlayer` Vue component that accepts a `videoId` prop and renders the correct UI for each state: idle (no download), pending (spinner + status text), ready (`<video>` player), and error (message + retry button).  
**Done when**: Component renders all four states correctly when `status` prop is changed manually.  
**Depends on**: T018

---

**ID**: T023  
**Phase**: 2  
**Module**: `frontend/src/components/VideoPlayer.vue`  
**Task**: Implement the "Download video" button that calls `triggerDownload()` on click, disables itself immediately, and shows a spinner with "Downloading…" text.  
**Done when**: Clicking the button disables it, shows the spinner, and the `POST /download` request is visible in the network tab.  
**Depends on**: T019, T022

---

**ID**: T024 *(updated)*  
**Phase**: 2  
**Module**: `frontend/src/components/VideoPlayer.vue`  
**Task**: Implement a polling loop that calls `getDownloadStatus()` every 2 seconds while `status === "pending"`, stopping when status transitions to `ready` or `error`. Store the interval ID and clear it in `onUnmounted` so the interval does not outlive the component.  
**Done when**: Polling fires every 2 s (verified in network tab); stops automatically when status changes; no poll requests appear in the network tab after the component is destroyed (e.g. user navigates away from the Video tab or switches history items).  
**Depends on**: T020, T022

> **Gap A fix**: The original task had no cleanup requirement. Without `clearInterval` in `onUnmounted`, switching history items while a download is pending accumulates orphaned poll loops.

---

**ID**: T025  
**Phase**: 2  
**Module**: `frontend/src/components/VideoPlayer.vue`  
**Task**: Render a `<video controls>` element with `src` set to `getStreamUrl(videoId)` when `status === "ready"`.  
**Done when**: Player appears without user action when the polling loop detects `status: "ready"`; video plays and seeking works.  
**Depends on**: T021, T024

---

**ID**: T026  
**Phase**: 2  
**Module**: `frontend/src/components/VideoPlayer.vue`  
**Task**: Implement the "Try again" retry button that resets local state to idle, calls `triggerDownload()`, and re-enters the polling loop.  
**Done when**: Clicking "Try again" fires a new `POST /download` request and the spinner re-appears.  
**Depends on**: T023, T024

---

**ID**: T027  
**Phase**: 2  
**Module**: `frontend/src/components/VideoPlayer.vue`  
**Task**: On component mount, call `getDownloadStatus()` once and render the player immediately (skipping download button) if `status === "ready"` — supporting the return-visit flow.  
**Done when**: Loading a summary whose `download_status` is `ready` in the DB shows the `<video>` player without any download button.  
**Depends on**: T020, T025

---

### Video tab integration

---

**ID**: T028  
**Phase**: 2  
**Module**: Existing tab-strip component (e.g. `SummaryDisplay.vue`)  
**Task**: Add a **Video** tab to the tab strip alongside Transcript / Fallacies / Q&A / Notes.  
**Done when**: The Video tab is visible on every summary view and clicking it renders `VideoPlayer`.  
**Depends on**: T022

---

**ID**: T029 *(updated)*  
**Phase**: 2  
**Module**: `frontend/src/components/VideoPlayer.vue` ↔ tab-strip component  
**Task**: Pass the `videoId` of the currently displayed summary down to `VideoPlayer` as a prop. Bind `:key="videoId"` on the `<VideoPlayer>` element so Vue destroys and re-creates the component whenever the user switches to a different history item.  
**Done when**: Opening the Video tab for different history items shows the correct download state for each video. Switching from a video with a pending download to another video stops all polling for the previous video (verified in network tab — no further requests to the prior video's `/download` endpoint).  
**Depends on**: T027, T028

> **Gap A fix**: Without `:key="videoId"`, Vue reuses the same VideoPlayer instance across history navigation, leaving the polling interval from the previous video alive. Combined with the `onUnmounted` cleanup in T024, this ensures clean teardown.

---

## Phase 3 — Lifecycle & Tests

### Lifecycle

---

**ID**: T030  
**Phase**: 3  
**Module**: History panel / `App.vue` ↔ `backend/app/db.py`  
**Task**: Confirm that the existing history-panel delete action calls `soft_delete()` on the backend, which (after T011) will now also remove the downloaded file.  
**Done when**: Deleting a summary whose download file exists removes the file from disk (verified by checking the `downloads/` directory before and after).  
**Depends on**: T011

---

**ID**: T031  
**Phase**: 3  
**Module**: Frontend history panel  
**Task**: Confirm that restoring a soft-deleted summary shows the Video tab's download button (not a broken player), because `download_status` is NULL after soft-delete + clear_download.  
**Done when**: Restoring a previously deleted summary opens the Video tab showing "No video downloaded yet" and the download button.  
**Depends on**: T011, T027

---

### Tests

---

**ID**: T032  
**Phase**: 3  
**Module**: `backend/tests/test_downloader.py` *(new file)*  
**Task**: Write unit tests for `download_video` that mock yt-dlp: success case (file created, correct path returned), idempotency case (yt-dlp not called when file exists), and failure case (exception propagates).  
**Done when**: `pytest backend/tests/test_downloader.py` passes with all three scenarios covered.  
**Depends on**: T006, T007

---

**ID**: T033  
**Phase**: 3  
**Module**: `backend/tests/test_db.py`  
**Task**: Add integration tests for `save_download_status`, `clear_download`, `get_download_status`, and the updated `soft_delete` — including:
- `save_download_status(..., status="error", error="some message")` persists `error_message` and is returned by `get_download_status`.
- `clear_download` nulls all four download columns (including `download_error`).
- Best-effort file-deletion branch: missing file does not block soft-delete.

**Done when**: All new test cases pass against a real test database; soft-delete with a missing file logs a warning but succeeds.  
**Depends on**: T009, T011

---

**ID**: T034 *(updated)*  
**Phase**: 3  
**Module**: `backend/tests/test_main.py`  
**Task**: Add FastAPI TestClient tests for:
- `POST /download` — happy path, 409 while pending, 200 no-op while ready, **restart while error (status resets to pending, new task spawned — see T048)**
- `GET /download` — all status values including `error` with `error_message` populated
- `GET /stream` — 206 partial content with `Content-Range` header present, 404 when file missing
- **Non-blocking assertion**: fire `POST /download` and immediately call `GET /download` in the same test; the second call must return before the download completes, confirming the background task does not block the event loop

**Done when**: All new endpoint test cases pass; the 206 test confirms the `Content-Range` header is present; the non-blocking test confirms `GET /download` responds while the background task is still running.  
**Depends on**: T012, T013, T014, T015, T016, T017, T048

> **Gap F fix**: Added explicit non-blocking assertion. The original task relied on framework guarantees alone.

---

### Edge-case tasks

---

**ID**: T035  
**Phase**: 1  
**Module**: `backend/app/main.py`  
**Task**: In `POST /download`, return 409 Conflict with `ErrorResponse(error="download_in_progress")` when the current `download_status` is `pending`.  
**Done when**: TestClient test confirms a second POST while status is `pending` returns 409 and does not spawn a second background task.  
**Depends on**: T012

---

**ID**: T036  
**Phase**: 1  
**Module**: `backend/app/main.py`  
**Task**: In `POST /download`, return 200 with the current `DownloadStatusResponse` (no re-download) when `download_status` is `ready`.  
**Done when**: TestClient test confirms POST while status is `ready` returns 200 with `status: "ready"` and no yt-dlp call is made.  
**Depends on**: T012

---

**ID**: T037  
**Phase**: 1  
**Module**: `backend/app/services/downloader.py` + `backend/app/main.py`  
**Task**: When yt-dlp raises any exception (including unwritable `DOWNLOAD_DIR`), catch it in the background task, log the error, and call `save_download_status(video_id, "error", error=str(e))`.  
**Done when**: TestClient test with a mocked yt-dlp that raises confirms status transitions to `error` and `GET /download` returns the error message in `error_message`.  
**Depends on**: T015

---

**ID**: T038  
**Phase**: 1  
**Module**: `backend/app/main.py`  
**Task**: In `GET /stream`, if `download_path` is set in the DB but the file does not exist on disk, return 404 with `ErrorResponse(error="file_not_found")`.  
**Done when**: TestClient test with a DB row whose `download_path` points to a non-existent file returns 404.  
**Depends on**: T017

---

**ID**: T039  
**Phase**: 2  
**Module**: `frontend/src/components/VideoPlayer.vue`  
**Task**: When `GET /stream` returns 404 (file missing but DB says ready), display an error message and the "Try again" retry button.  
**Done when**: Mocking the stream endpoint to return 404 causes the player to show the error state and retry button rather than a broken `<video>` element.  
**Depends on**: T026, T038

---

**ID**: T040  
**Phase**: 3  
**Module**: `backend/app/db.py`  
**Task**: Confirm that `soft_delete()` file deletion is truly best-effort: wrap `os.remove` in try/except `OSError`, log a warning, and continue to null the columns and set `deleted_at` even if the file removal fails.  
**Done when**: Integration test that patches `os.remove` to raise `OSError` confirms soft-delete succeeds and the warning is logged.  
**Depends on**: T011

---

**ID**: T048 *(new)*  
**Phase**: 1  
**Module**: `backend/app/main.py`  
**Task**: In `POST /download`, when the current `download_status` is `"error"`, treat the request identically to a fresh download: reset status to `"pending"`, clear `download_error`, and spawn a new background task.  
**Done when**: TestClient test confirms that POST while status is `"error"` returns 200 with `status: "pending"` and a new background task is spawned (yt-dlp is called again). This is the backend counterpart to the frontend "Try again" flow (T026).  
**Depends on**: T012, T035, T036

> **Gap B fix**: T035 and T036 specified behaviour for `pending` and `ready`. The `error` state was unspecified, leaving the retry flow's backend contract implicit.

---

### End-to-end smoke tests

---

**ID**: T041  
**Phase**: 3  
**Module**: E2E / manual verification  
**Task**: Smoke test the happy path: summarize a public YouTube video, open the Video tab, click "Download video", watch the spinner appear, confirm the `<video>` player renders within 2 seconds of the download completing, and seek to a non-zero timestamp.  
**Done when**: All steps complete without error; browser network tab shows at least one 206 Partial Content response to `/stream`.  
**Depends on**: T025, T034

---

**ID**: T042  
**Phase**: 3  
**Module**: E2E / manual verification  
**Task**: Smoke test the return-visit flow: reload the app, select a history item whose `download_status` is `ready`, open the Video tab, and confirm the player renders immediately without showing the download button.  
**Done when**: Player is visible within one render cycle of selecting the history item; no download button is shown.  
**Depends on**: T027, T041

---

**ID**: T043  
**Phase**: 3  
**Module**: E2E / manual verification  
**Task**: Smoke test the error path: trigger a download for a private or unavailable video, confirm status transitions to `error`, the spinner is replaced by an error message (including the yt-dlp error text returned in `error_message`) and "Try again" button, and clicking the button restarts the download flow.  
**Done when**: All three UI states (spinner → error with message → spinner again) are observed in sequence.  
**Depends on**: T026, T041

---

**ID**: T044  
**Phase**: 3  
**Module**: E2E / manual verification  
**Task**: Smoke test the deletion lifecycle: download a video, confirm the file exists in `downloads/`, delete the summary from the history panel, confirm the file is removed from `downloads/`, then restore the summary and confirm the Video tab shows the download button.  
**Done when**: File is absent from `downloads/` after deletion and the download button reappears after restore.  
**Depends on**: T030, T031, T041

---

### Open-question tasks

---

**ID**: T045  
**Phase**: 1  
**Module**: `frontend/src/components/VideoPlayer.vue`  
**Task**: Decide whether to display a YouTube ToS disclaimer on the Video tab and implement it (e.g. a one-line note beneath the download button: "For personal/research use only").  
**Done when**: A decision is recorded (disclaimer or not); if yes, the text is visible below the download button.  
**Depends on**: T022

---

**ID**: T046  
**Phase**: 3  
**Module**: `backend/app/main.py` + `backend/app/db.py`  
**Task**: Decide whether `GET /stream` returning 404 (file missing, DB says `ready`) should auto-heal by calling `clear_download(video_id)` to reset status to NULL; implement the chosen behaviour.  
**Done when**: Decision is recorded in code comments or a brief ADR; if auto-heal is chosen, a TestClient test confirms `GET /download` returns NULL status after the stale 404.  
**Depends on**: T038

---

**ID**: T047  
**Phase**: 1  
**Module**: `backend/app/services/downloader.py`  
**Task**: Decide whether to add a max-duration guard in `download_video` (e.g. reject videos longer than 3 hours) and implement it if chosen.  
**Done when**: Decision is recorded; if a guard is added, it raises a descriptive exception before invoking yt-dlp when the video duration exceeds the limit.  
**Depends on**: T006

---

## Summary

| Phase | Tasks |
|-------|-------|
| 1 — Backend | T001–T017, T035–T038, T045, T047, T048 |
| 2 — Frontend | T018–T029, T039 |
| 3 — Lifecycle & Tests | T030–T034, T040–T044, T046 |

**Total tasks**: 48

### Changes from v1

| Change | Gap addressed | Tasks affected |
|--------|--------------|----------------|
| Added `download_error TEXT` column to DB migration | Gap D — `error_message` was always `None` | T005 |
| Added `get_download_status()` as explicit deliverable; `save_download_status` must persist `error` param | Gap C/D — helper untasked, error discarded | T009 |
| Merged T010 into T009 | Consolidation | T009, T010 |
| `VideoRecord` omission documented as intentional | Gap E | T008 |
| Added `onUnmounted` cleanup to polling loop | Gap A — orphaned intervals on video switch | T024 |
| Added `:key="videoId"` requirement | Gap A — Vue reuses component across navigation | T029 |
| Added non-blocking event loop assertion to API tests | Gap F | T034 |
| Updated error path smoke test to verify `error_message` text | Gap D end-to-end | T043 |
| **New T048**: `POST /download` behaviour when status is `"error"` | Gap B — retry path unspecified | T048 |
