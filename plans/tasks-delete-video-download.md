# Tasks: Delete Downloaded Video

## Phase 1 — Backend: DB function, endpoint, error handling

### T001 — Add `delete_download()` function to `backend/app/db.py`
- **Module**: `backend/app/db.py`
- **Task**: Add a new async function `delete_download(conn, video_id)` that retrieves the `download_path` for a video, deletes the file from disk using `os.remove()`, and clears all download columns via `clear_download()`. Returns `True` if the file existed and was deleted, `False` if the file was already missing. Logs a warning if `os.remove()` fails for any reason other than "file not found".
- **Done when**: Function exists, handles missing files gracefully, uses `clear_download()` internally, includes docstring.
- **Depends on**: none

### T001a — Ensure `os` module is imported in `backend/app/db.py`
- **Module**: `backend/app/db.py`
- **Task**: Verify `import os` exists at the top of `db.py`. Add it if missing (needed for `os.remove()` in T001).
- **Done when**: `import os` is present, module loads without error.
- **Depends on**: none

### T002 — Add `DELETE /api/videos/{video_id}/download` endpoint to `backend/app/main.py`
- **Module**: `backend/app/main.py`
- **Task**: Add a new DELETE endpoint at `/api/videos/{video_id}/download` that calls `get_download_status()` to check if the record exists (returns 404 if not), then calls `delete_download()` and returns 204 No Content on success.
- **Done when**: Endpoint is registered, returns 404 for non-existent records, returns 204 after successful deletion, follows existing error response patterns.
- **Depends on**: T001

### T003 — Wire `delete_download` import in `backend/app/main.py`
- **Module**: `backend/app/main.py`
- **Task**: Add `delete_download` to the import block from `app.db` alongside `clear_download`, `soft_delete`, etc.
- **Done when**: Import statement includes `delete_download`, module loads without ImportError.
- **Depends on**: T001

### T004 — Backend returns 404 for soft-deleted records
- **Module**: `backend/app/main.py` (via `get_download_status` in `db.py`)
- **Task**: Verify that `get_download_status()` filters by `deleted_at IS NULL`, which it already does (line 349 of `db.py`). No code change needed — this task confirms the behavior is correct.
- **Done when**: Confirmed in code that `get_download_status` includes `AND deleted_at IS NULL` filter.
- **Depends on**: none

---

## Phase 2 — Frontend: API function, VideoPlayer UI, modal, toast

### T005 — Create reusable `Toast.vue` component
- **Module**: `frontend/src/components/Toast.vue` (new file)
- **Task**: Create a simple toast component that accepts a `message` prop and an optional `type` prop (`"success"` | `"error"` | `"info"`). Displays the message in a styled container with auto-dismiss after a configurable duration (default 3 seconds). Uses Vue `Transition` for enter/leave animations.
- **Done when**: Component renders with correct styling, auto-dismisses after 3 seconds, supports all three types with appropriate colors, uses existing font family (Manrope).
- **Depends on**: none

### T006 — Add `deleteDownload()` function to `frontend/src/services/api.ts`
- **Module**: `frontend/src/services/api.ts`
- **Task**: Add new exported async function `deleteDownload(videoId: string): Promise<void>` that calls `DELETE /api/videos/${videoId}/download`. Returns `void` on success (204). Throws `ApiError` on non-204 responses (treat 204 explicitly as success, since it has no body).
- **Done when**: Function exists with correct signature, handles 204 correctly, throws `ApiError` for failures, consistent with existing API client patterns.
- **Depends on**: T002

### T007 — Add delete button to `VideoPlayer.vue` (ready state)
- **Module**: `frontend/src/components/VideoPlayer.vue`
- **Task**: In the `status === 'ready'` block, add a row below the `<video>` element containing a "Delete video" button with red/destructive styling (`video-player__btn--destructive`). Button has a trash icon (▼ or simple text) and a click handler. The button is only visible when `status === 'ready'`.
- **Done when**: Button appears below video in ready state, uses red background (`#DC2626` or similar), has appropriate hover/disabled states, matches existing button patterns.
- **Depends on**: none

### T008 — Add confirmation modal to `VideoPlayer.vue`
- **Module**: `frontend/src/components/VideoPlayer.vue`
- **Task**: Add a confirmation modal that appears when the user clicks "Delete video". Use a simple Vue-controlled modal overlay (not browser `confirm()`). Modal shows: title "Delete video", message "Are you sure you want to delete this downloaded video? You can re-download it later.", and two buttons: "Cancel" (gray, closes modal) and "Delete" (red, triggers deletion). Modal is dismissed by clicking Cancel, clicking outside, or pressing Escape.
- **Done when**: Modal appears on delete click, has correct content and buttons, closes on Cancel/outside/Escape, uses existing font/styling patterns.
- **Depends on**: T007

### T009 — Add deletion loading state to `VideoPlayer.vue`
- **Module**: `frontend/src/components/VideoPlayer.vue`
- **Task**: Add an `isDeleting` ref (similar to `isTriggering`) that disables the delete button and shows a spinner while the deletion API call is in progress. Import the existing spinner animation or create a simple one inline.
- **Done when**: Delete button shows spinner and is disabled during deletion, state resets after success/failure.
- **Depends on**: T007, T008

### T010 — Integrate `deleteDownload()` API call in `VideoPlayer.vue`
- **Module**: `frontend/src/components/VideoPlayer.vue`
- **Task**: Import `deleteDownload` from `@/services/api`. Add a `handleDelete()` function that: (1) sets `isDeleting = true`, (2) calls `deleteDownload(videoId)`, (3) on success, resets status to `idle` and shows success toast, (4) on error, resets `isDeleting = false` and shows error toast. Clear any error message.
- **Done when**: API call is wired, handles success and error, transitions video tab to idle state on success.
- **Depends on**: T006, T008, T009

### T011 — Add success toast to `VideoPlayer.vue`
- **Module**: `frontend/src/components/VideoPlayer.vue`
- **Task**: Import and use the `Toast` component (T005). After successful deletion, show a success toast with message "Video deleted successfully". Toast auto-dismisses after 3 seconds. Use a local ref to control toast visibility.
- **Done when**: Toast appears after deletion with correct message, uses green/success styling, auto-dismisses after 3 seconds.
- **Depends on**: T005, T010

### T012 — Add destructive button variant styles to `VideoPlayer.vue`
- **Module**: `frontend/src/components/VideoPlayer.vue`
- **Task**: Add CSS class `.video-player__btn--destructive` with red background (`#DC2626`), white text, and appropriate hover/disabled states. Matches the pattern of `video-player__btn--primary`.
- **Done when**: Class exists in `<style scoped>`, applies correct colors, hover darkens red, disabled state has reduced opacity.
- **Depends on**: T007

---

## Phase 3 — Tests and QA

### T013 — Unit test for `delete_download()` function
- **Module**: `backend/tests/unit/test_db.py`
- **Task**: Add unit tests for `delete_download()`: (a) file exists → deleted, returns True; (b) file doesn't exist → warning logged, returns False; (c) `os.remove()` raises other exception → warning logged, still clears DB columns; (d) idempotent call when DB columns already null → no-op, returns False. Mock `os.remove` and `clear_download`.
- **Done when**: Tests exist and pass, cover all four scenarios including idempotent behavior.
- **Depends on**: T001

### T014 — Integration test for `DELETE /api/videos/{video_id}/download` endpoint
- **Module**: `backend/tests/integration/test_api.py`
- **Task**: Add integration tests using FastAPI TestClient: (a) 404 when no record exists; (b) 204 when download exists and file is deleted; (c) 204 when download exists but file is already missing (idempotent); (d) 404 when record is soft-deleted; (e) 204 on concurrent second delete call (idempotent re-call). Mock `delete_download()` function.
- **Done when**: Tests exist and pass, cover all five scenarios including idempotent re-calls.
- **Depends on**: T002, T003

### T015 — End-to-end smoke test: delete and re-download flow
- **Module**: manual verification or integration test
- **Task**: Verify the full user flow: (1) trigger a download, (2) wait for ready status, (3) click delete button, (4) confirm deletion, (5) verify toast appears, (6) verify video tab returns to idle state, (7) click download again to re-download, (8) verify download completes successfully.
- **Done when**: Flow works end-to-end without errors.
- **Depends on**: T001–T012

### T015a — Verify async/non-blocking pattern for file deletion
- **Module**: `backend/app/db.py` (code review)
- **Task**: Verify that `delete_download()` uses async patterns consistently (e.g., `asyncio.to_thread` for `os.remove()` if needed, or confirm that synchronous `os.remove()` is acceptable for fast local file operations per existing patterns in the codebase).
- **Done when**: Pattern is consistent with existing file I/O in the codebase (e.g., `downloader.py` patterns).
- **Depends on**: T001

### T015b — Verify delete button visibility only in ready state
- **Module**: `frontend/src/components/VideoPlayer.vue` (component test or manual verification)
- **Task**: Verify that the delete button is only visible when `status === 'ready'` and hidden in all other states (`idle`, `pending`, `error`, `NULL`).
- **Done when**: Button visibility is correct in all states.
- **Depends on**: T007

---

## Open Questions (Decision + Implementation Tasks)

### T016 — Decide: Show file size in confirmation dialog?
- **Module**: `frontend/src/components/VideoPlayer.vue`
- **Task**: Decide whether to show the file size in the confirmation dialog. If yes: fetch file size from download metadata (add `file_size` to `DownloadStatus` type, populate in `get_download_status`, display in modal). If no: keep modal as-is without file size.
- **Done when**: Decision made, implementation matches decision.
- **Depends on**: T008

### T017 — Decide: Add trash icon to delete button?
- **Module**: `frontend/src/components/VideoPlayer.vue`
- **Task**: Decide whether the delete button should have an icon (trash/×) in addition to or instead of text. If yes: add Unicode trash icon (🗑) or CSS-drawn icon. If no: text-only "Delete video" button.
- **Done when**: Decision made, button UI matches decision.
- **Depends on**: T007
