# PRD: Delete Downloaded Video

## Overview & Context

- **Product/Feature Summary**: Add the ability to delete a previously downloaded video file while keeping the history record (summary, transcript, fallacy analysis) intact. Users can re-download the video later if needed.
- **Problem Statement**: Users who have downloaded videos may want to free up disk space or remove a download they initiated by accident. Currently, the only way to delete a video file is to soft-delete the entire history record, which also removes the summary and analysis. There is no way to delete just the download.
- **Business Objectives**: Give users granular control over their downloaded content. Reduce disk usage accumulation. Improve user confidence by making downloads reversible.
- **Success Metrics**: Number of delete-download actions performed; reduction in total disk usage; zero user complaints about inability to manage downloads.

---

## Scope

### In Scope
- New backend endpoint: `DELETE /api/videos/{video_id}/download`
- New database function: `delete_download()` that removes the file from disk and clears download columns
- New frontend API function: `deleteDownload(videoId)` in `api.ts`
- Delete button in `VideoPlayer.vue` component (visible when `status === 'ready'`)
- Confirmation modal before deletion
- Loading state on delete button during deletion
- Toast notification on successful deletion
- TypeScript type updates if needed

### Out of Scope
- Bulk delete of multiple downloads
- "Undo delete" functionality (user can re-download instead)
- File size display or disk usage dashboard
- Moving downloads to trash/recycle bin (permanent deletion)
- Deleting downloads from the history panel without opening the video tab

### Release Phases
1. **Phase 1** — Backend: new DB function, new endpoint, error handling
2. **Phase 2** — Frontend: API client function, VideoPlayer UI, confirmation modal, toast
3. **Phase 3** — Tests: backend endpoint tests, frontend component tests

---

## Stakeholders

- **Target Users**: Researchers, students, and content analysts who download videos and need to manage disk space or undo accidental downloads.
- **Internal Stakeholders**: Solo developer / project owner
- **Owners**: josdijkstraco

---

## Requirements

### Functional Requirements

- As a user, I want to delete a downloaded video file so that I can free up disk space while keeping my summary and analysis.
- As a user, I want to see a confirmation dialog before deletion so that I don't accidentally delete a download.
- As a user, I want visual feedback (loading spinner) during deletion so that I know the system is working.
- As a user, I want a success toast notification after deletion so that I know the action completed.
- As a user, I want to be able to re-download the video after deletion so that I can watch it again later.
- As a user, I want the delete button to only appear when a download actually exists so that the UI is never confusing.

### Non-Functional Requirements

- The delete endpoint must be idempotent: calling it when no download exists returns 204 (success) since the desired end state is already achieved.
- File deletion must be best-effort: if the file is missing on disk, log a warning but still clear the DB columns and return success.
- The endpoint must not block the FastAPI event loop (file deletion is fast, but still use async patterns consistently).
- DB column clearing must use the existing `clear_download()` function for consistency.

### Technical Constraints

- No new dependencies required.
- Must follow existing error response pattern (`ErrorResponse` with `error` and `message` fields).
- Must follow existing REST conventions (204 No Content for successful deletion).
- Frontend must use existing toast/notification system (if any) or add minimal new UI.
- TypeScript types in `frontend/src/types/index.ts` must stay in sync with Pydantic models.

---

## User Experience

### User Flows & Journeys

**Happy path — delete a downloaded video:**
1. User opens a history item that has a downloaded video (`download_status = 'ready'`)
2. User clicks **Video** tab — sees the video player with a **Delete video** button below it (red/destructive styling)
3. User clicks **Delete video** button
4. Confirmation modal appears: "Delete video? Are you sure you want to delete this downloaded video? You can re-download it later."
5. User clicks **Delete** in the modal
6. Button shows loading spinner, becomes disabled
7. Backend deletes file from disk, clears DB columns
8. Frontend receives 204 response, hides spinner, shows toast: "Video deleted successfully" (auto-dismisses after 3 seconds)
9. Video tab returns to idle state: "No video downloaded yet" with **Download video** button

**Edge case — file missing on disk:**
1. User clicks **Delete video** button (DB says `ready`, but file is missing)
2. Backend tries `os.remove()`, logs warning, proceeds to clear DB columns
3. Frontend still shows success toast and returns to idle state
4. User experience is identical to happy path

**Edge case — no download exists:**
1. User somehow triggers delete when `download_status` is NULL (shouldn't happen since button is hidden)
2. Backend calls `clear_download()` which is a no-op
3. Returns 204 success
4. Frontend shows success toast (harmless, even if slightly confusing)

### Wireframes / Design Mockups

The delete button appears below the video player in the **ready** state:

```
┌─────────────────────────────────┐
│  ┌───────────────────────────┐  │
│  │                           │  │
│  │     <video player>        │  │
│  │                           │  │
│  └───────────────────────────┘  │
│                                 │
│     [  Delete video  ]          │  ← Red/destructive button
└─────────────────────────────────┘
```

### Edge Cases & Error States

| Scenario | Behaviour |
|---|---|
| Delete when `status = 'ready'` | File deleted, DB columns cleared, 204 returned, toast shown |
| Delete when file missing on disk | Warning logged, DB columns cleared, 204 returned, toast shown |
| Delete when `status = NULL` | DB columns already null, 204 returned (idempotent) |
| Delete when `status = 'pending'` | Not applicable — delete button only shows when `status = 'ready'` |
| Delete when `status = 'error'` | Not applicable — delete button only shows when `status = 'ready'` |
| Delete on soft-deleted record | Backend returns 404 (`get_download_status` filters `deleted_at IS NULL`) |
| Concurrent delete requests | Both succeed (idempotent), file deleted once, DB columns already null on second call |

---

## Modules

### New
| Module | Description | Tests |
|---|---|---|
| `backend/app/db.py::delete_download()` | New function: deletes file from disk and clears download columns. Returns True if file was deleted, False if file didn't exist. | Unit test with mocked `os.remove`, integration test with real file |
| `backend/app/main.py::delete_download_endpoint()` | New endpoint: `DELETE /api/videos/{video_id}/download`. Calls `delete_download()`, returns 204 or 404. | FastAPI TestClient test |
| `frontend/src/services/api.ts::deleteDownload()` | New API client function: calls the delete endpoint, handles errors. | — |

### Modified
| Module | Change | Tests |
|---|---|---|
| `frontend/src/components/VideoPlayer.vue` | Add delete button in `ready` state, confirmation modal, loading state, toast notification | Component test for button visibility, click handler |
| `backend/app/db.py` | Import `os` if not already imported (for `os.remove`) | — |

---

## Success Metrics

- **KPIs**: Number of delete-download actions; disk space reclaimed; re-download rate after deletion
- **Acceptance Criteria**:
  - [ ] `DELETE /api/videos/{video_id}/download` endpoint returns 204 on success
  - [ ] `DELETE /api/videos/{video_id}/download` endpoint returns 404 for soft-deleted records
  - [ ] File is removed from disk when delete endpoint is called
  - [ ] DB columns (`download_status`, `download_path`, `downloaded_at`, `error_message`) are cleared
  - [ ] Delete button only appears when `status === 'ready'`
  - [ ] Confirmation modal appears before deletion
  - [ ] Loading spinner shows on button during deletion
  - [ ] Toast notification appears after successful deletion
  - [ ] Video tab returns to idle state after deletion
  - [ ] Re-downloading after deletion works correctly
  - [ ] Backend tests pass
  - [ ] Frontend tests pass (if added)

---

## Timeline & Milestones

| Milestone | Description | Target Date |
|---|---|---|
| Phase 1 | Backend: DB function, endpoint, error handling | TBD |
| Phase 2 | Frontend: API function, VideoPlayer UI, modal, toast | TBD |
| Phase 3 | Tests and QA | TBD |

- **Dependencies**: None — uses existing infrastructure (yt-dlp, asyncpg, FastAPI, Vue)

---

## Open Questions & Risks

| # | Question / Risk | Owner | Status |
|---|---|---|---|
| 1 | Does the app have an existing toast/notification system, or do we need to add one? | josdijkstraco | Open |
| 2 | Should we show file size in the confirmation dialog ("Delete 450 MB video?")? | josdijkstraco | Open |
| 3 | Should the delete button have an icon (trash) in addition to or instead of text? | josdijkstraco | Open |

---

## Revision History

| Version | Date | Author | Summary of Changes |
|---------|------|--------|--------------------|
| 1.0 | 2026-05-16 | Claude (discuss-feature session) | Initial draft |
