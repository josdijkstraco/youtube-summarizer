# Tasks: Video Download & In-Browser Playback

Generated from: `prd-video-download-playback.md`

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

**ID**: T005  
**Phase**: 1  
**Module**: `backend/app/db.py`  
**Task**: Add a migration block inside `create_table()` that adds `download_status TEXT`, `download_path TEXT`, and `downloaded_at TIMESTAMPTZ` columns to `youtube_summarizer.summaries` using `ALTER TABLE ADD COLUMN IF NOT EXISTS` inside a `DO $$ ... $$` block.  
**Done when**: Running `create_table()` on a database that already has the `summaries` table adds all three columns without error; running it again is a no-op.  
**Depends on**: —

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

**ID**: T008  
**Phase**: 1  
**Module**: `backend/app/models.py`  
**Task**: Add a `DownloadStatusResponse` Pydantic model with fields `video_id: str`, `status: str` (one of `pending | ready | error | null`), `downloaded_at: datetime | None`, and `error_message: str | None`.  
**Done when**: Model serialises correctly to JSON and matches the shape expected by the frontend `DownloadStatus` type (T020).  
**Depends on**: —

---

### DB functions

---

**ID**: T009  
**Phase**: 1  
**Module**: `backend/app/db.py`  
**Task**: Add `save_download_status(video_id, status, path=None, error=None)` that UPDATEs `download_status`, `download_path`, and `downloaded_at` for the given `video_id`.  
**Done when**: Integration test confirms the correct row is updated and can be read back.  
**Depends on**: T005

---

**ID**: T010  
**Phase**: 1  
**Module**: `backend/app/db.py`  
**Task**: Add `clear_download(video_id)` that sets `download_status`, `download_path`, and `downloaded_at` to NULL for the given `video_id`.  
**Done when**: Integration test confirms all three columns are NULL after calling `clear_download`.  
**Depends on**: T005

---

**ID**: T011  
**Phase**: 1  
**Module**: `backend/app/db.py`  
**Task**: Update `soft_delete(video_id)` to read `download_path` from the row, delete the file at that path if it exists (best-effort: log a warning on `OSError`, never raise), then call `clear_download(video_id)` before setting `deleted_at`.  
**Done when**: Soft-deleting a summary whose `download_path` points to a real file removes that file from disk; if the file is missing, soft-delete still succeeds.  
**Depends on**: T010

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
**Task**: Add `GET /api/videos/{video_id}/download` that reads `download_status`, `download_path`, and `downloaded_at` from the DB and returns `DownloadStatusResponse`.  
**Done when**: Polling the endpoint returns the current status; returns `status: null` (or `"none"`) when no download has ever been triggered.  
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
**Done when**: A successful download transitions DB status from `pending` → `ready`; a yt-dlp failure transitions it to `error`.  
**Depends on**: T006, T009, T012

---

**ID**: T016  
**Phase**: 1  
**Module**: `backend/app/main.py` ↔ `backend/app/db.py`  
**Task**: Wire `GET /download` to read status via `get_download_status(video_id)` DB helper and return the result as `DownloadStatusResponse`.  
**Done when**: Polling the endpoint after a completed download returns `status: "ready"` and a non-null `downloaded_at`.  
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
**Task**: Add `DownloadStatus` TypeScript type with fields `video_id`, `status` (`"pending" | "ready" | "error" | null`), `downloaded_at`, and `error_message` to mirror `DownloadStatusResponse`.  
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

**ID**: T024  
**Phase**: 2  
**Module**: `frontend/src/components/VideoPlayer.vue`  
**Task**: Implement a polling loop that calls `getDownloadStatus()` every 2 seconds while `status === "pending"`, stopping when status transitions to `ready` or `error`.  
**Done when**: Polling fires every 2 s (verified in network tab); stops automatically when status changes.  
**Depends on**: T020, T022

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

**ID**: T029  
**Phase**: 2  
**Module**: `frontend/src/components/VideoPlayer.vue` ↔ tab-strip component  
**Task**: Pass the `videoId` of the currently displayed summary down to `VideoPlayer` as a prop.  
**Done when**: Opening the Video tab for different history items shows the correct download state for each video.  
**Depends on**: T027, T028

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
**Task**: Add integration tests for `save_download_status`, `clear_download`, and the updated `soft_delete` — including the best-effort file-deletion branch (missing file does not block soft-delete).  
**Done when**: All new test cases pass against a real test database; soft-delete with a missing file logs a warning but succeeds.  
**Depends on**: T009, T010, T011

---

**ID**: T034  
**Phase**: 3  
**Module**: `backend/tests/test_main.py`  
**Task**: Add FastAPI TestClient tests for `POST /download` (happy path, 409 while pending, 200 no-op while ready), `GET /download` (all status values), and `GET /stream` (206 partial content, 404 when file missing).  
**Done when**: All new endpoint test cases pass; the 206 test confirms the `Content-Range` header is present.  
**Depends on**: T012, T013, T014, T015, T016, T017

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
**Done when**: TestClient test with a mocked yt-dlp that raises confirms status transitions to `error` and `GET /download` returns the error message.  
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
**Task**: Smoke test the error path: trigger a download for a private or unavailable video, confirm status transitions to `error`, the spinner is replaced by an error message and "Try again" button, and clicking the button restarts the download flow.  
**Done when**: All three UI states (spinner → error → spinner again) are observed in sequence.  
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
| 1 — Backend | T001–T017, T035–T038, T045, T047 |
| 2 — Frontend | T018–T029, T039 |
| 3 — Lifecycle & Tests | T030–T034, T040–T044, T046 |

**Total tasks**: 47
