# PRD: Video Download & In-Browser Playback

## Overview & Context

- **Product/Feature Summary**: Allow users to download a YouTube video to the server and watch it in an embedded HTML5 player inside the app, without leaving the summarizer UI.
- **Problem Statement**: Users currently get a transcript, summary, and fallacy analysis — but to actually watch the video they must leave the app and navigate to YouTube. This breaks the research flow, especially for long-form content where users want to verify a summarized claim at a specific point in the video.
- **Business Objectives**: Increase session depth and time-on-app by making the summarizer the single pane of glass for consuming and analysing a video.
- **Success Metrics**: % of summarized videos that have a download initiated; average session length before and after; user-reported workflow satisfaction.

---

## Scope

### In Scope
- `yt-dlp`-powered server-side video download (best pre-merged MP4, no ffmpeg)
- Configurable `DOWNLOAD_DIR` env var (defaults to `./downloads`); Docker volume mount
- `POST /api/videos/{video_id}/download` — trigger async background download
- `GET /api/videos/{video_id}/download` — poll status (`pending | ready | error`)
- `GET /api/videos/{video_id}/stream` — serve file with HTTP range request support
- New **Video tab** in the existing tab strip (alongside Transcript / Fallacies / Q&A / Notes)
- Download button → 2-second polling spinner → `<video>` player on success
- Retry button on download error
- Auto-delete file from disk (and clear DB columns) when summary is soft-deleted from history
- Three new columns on `youtube_summarizer.summaries`: `download_status TEXT`, `download_path TEXT`, `downloaded_at TIMESTAMPTZ`
- Tests for `downloader.py`, `db.py` download functions, and the 3 new API endpoints

### Out of Scope
- ffmpeg / video transcoding or quality selection beyond best pre-merged MP4
- A dedicated "downloads manager" UI or disk usage dashboard
- Download from the history panel without opening the summary view
- Separate delete button for the download (lifecycle tied to summary deletion)
- Subtitles / caption overlay in the player
- Mobile-optimised player controls

### Release Phases
1. **Phase 1** — Backend: `downloader.py` service, DB migration, 3 endpoints, config
2. **Phase 2** — Frontend: Video tab, polling loop, `<video>` player, retry UX
3. **Phase 3** — Lifecycle: `soft_delete()` file cleanup + tests

---

## Stakeholders

- **Target Users**: Researchers, students, and content analysts who use the summarizer as a primary tool for consuming YouTube content.
- **Internal Stakeholders**: Solo developer / project owner
- **Owners**: josdijkstraco

---

## Requirements

### Functional Requirements

- As a user, I want to click a "Download video" button on the Video tab so that the server fetches the video without me leaving the app.
- As a user, I want to see a progress spinner and status message while the video downloads so that I know the system is working.
- As a user, I want an embedded video player to appear automatically when the download completes so that I can watch without any additional action.
- As a user, I want a "Try again" button when a download fails so that I can retry without re-summarizing the video.
- As a user, I want the downloaded file to be removed when I delete the summary from history so that I don't accumulate disk usage silently.
- As a user, I want to be able to seek through the video freely so that I can jump to the timestamp of a flagged fallacy or highlighted section.

### Non-Functional Requirements

- The `GET /stream` endpoint must support HTTP `Range` requests so the browser `<video>` tag can seek without re-downloading.
- The download background task must not block the FastAPI event loop (use `asyncio.to_thread` or `BackgroundTasks`).
- `DOWNLOAD_DIR` must be created on startup if it does not exist; startup must not fail if the directory already exists.
- Downloaded files must be named `{video_id}.mp4` to ensure idempotency — a second download trigger for the same `video_id` while status is `ready` is a no-op.
- File deletion on soft-delete must be best-effort (log warning on failure, never block the delete response).

### Technical Constraints

- New pip dependency: `yt-dlp` (added to `backend/requirements.txt`)
- No `ffmpeg` system dependency — yt-dlp format string: `bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best`
- DB migration must use `ALTER TABLE ADD COLUMN IF NOT EXISTS` inside a `DO $$ ... $$` block in `create_table()`, consistent with existing migration pattern
- Docker: `./downloads:/app/downloads` volume mount added to `docker-compose.yml`
- FastAPI `FileResponse` or manual `StreamingResponse` with `Range` header handling for the stream endpoint

---

## User Experience

### User Flows & Journeys

**Happy path — first download:**
1. User summarizes a video (existing flow unchanged)
2. User clicks **Video** tab
3. Tab shows "No video downloaded yet" and a **Download video** button
4. User clicks button → button becomes disabled, spinner appears, status: "Downloading…"
5. Frontend polls `GET /api/videos/{video_id}/download` every 2 seconds
6. When status is `ready`, spinner disappears and `<video>` player renders with controls
7. User can seek, pause, and play freely

**Return visit (already downloaded):**
1. User selects a history item whose `download_status = 'ready'`
2. Video tab renders the player immediately — no download button shown

**Error path:**
1. yt-dlp fails (geo-block, private video, network error)
2. Status becomes `error`; spinner replaced with error message and **Try again** button
3. User clicks Try again → status resets to `pending`, polling resumes

**Deletion lifecycle:**
1. User deletes summary from history panel
2. Backend calls `soft_delete()` → file at `download_path` is deleted from disk, `download_status` and `download_path` set to NULL
3. If user restores the summary, the Video tab shows the download button again (no file, clean state)

### Edge Cases & Error States

| Scenario | Behaviour |
|---|---|
| Download triggered while status is `pending` | `POST /download` returns 409 Conflict — no second task spawned |
| Download triggered while status is `ready` | `POST /download` returns 200 with current status — no re-download |
| `DOWNLOAD_DIR` not writable | yt-dlp raises, status set to `error`, error message logged |
| File missing on disk but DB says `ready` | `GET /stream` returns 404; frontend shows error + retry button |
| Video unavailable on YouTube | yt-dlp raises, status set to `error` |
| Soft-delete with file deletion failure | Log warning, proceed with soft-delete; `download_path` still nulled |

---

## Modules

### New
| Module | Description | Tests |
|---|---|---|
| `backend/app/services/downloader.py` | yt-dlp wrapper — `download_video(video_id, url, output_dir) -> Path`. Deep module: all yt-dlp interaction behind a single function. | Unit tests with mocked yt-dlp |
| `frontend/src/components/VideoPlayer.vue` | Video tab — download button, polling loop, `<video>` player, retry button | — |

### Modified
| Module | Change | Tests |
|---|---|---|
| `backend/app/db.py` | Add `save_download_status()`, `clear_download()`; update `soft_delete()` to delete file + null columns | Integration tests |
| `backend/app/main.py` | Add `POST /download`, `GET /download`, `GET /stream` endpoints | FastAPI TestClient tests |
| `backend/app/models.py` | Add `DownloadStatusResponse` | — |
| `backend/app/config.py` | Add `download_dir: Path` setting | — |
| `frontend/src/services/api.ts` | Add `triggerDownload()`, `getDownloadStatus()`, `getStreamUrl()` | — |
| `frontend/src/types/index.ts` | Add `DownloadStatus` type | — |
| `docker-compose.yml` | Add `./downloads:/app/downloads` volume mount | — |

---

## Success Metrics

- **KPIs**: Download initiation rate (downloads / summarizations), player play-through rate, error rate per yt-dlp call
- **Acceptance Criteria**:
  - [ ] Video tab appears on all summary views
  - [ ] Download completes successfully for a public YouTube video
  - [ ] Player allows free seeking (range requests confirmed in browser network tab)
  - [ ] Polling stops and player renders within 2 seconds of download completing
  - [ ] Retry button triggers a fresh download attempt
  - [ ] Deleting from history removes the file from disk
  - [ ] Restoring a deleted summary shows the download button (not a broken player)
  - [ ] All three test suites pass

---

## Timeline & Milestones

| Milestone | Description | Target Date |
|---|---|---|
| Phase 1 | Backend service, DB migration, endpoints | TBD |
| Phase 2 | Frontend Video tab, polling, player | TBD |
| Phase 3 | Lifecycle cleanup + full test suite | TBD |

- **Dependencies**: `yt-dlp` availability on PyPI; no ffmpeg required

---

## Open Questions & Risks

| # | Question / Risk | Owner | Status |
|---|---|---|---|
| 1 | YouTube ToS prohibits downloading — feature is for personal/research use only; add a disclaimer? | josdijkstraco | Open |
| 2 | File at `download_path` missing but DB says `ready` — currently handled as 404 + retry; should we auto-heal by resetting status to NULL? | josdijkstraco | Open |
| 3 | Very large videos (2h+) may take >5 min to download — should there be a max-duration guard in `downloader.py`? | josdijkstraco | Open |

---

## Revision History

| Version | Date | Author | Summary of Changes |
|---|---|---|---|
| 1.0 | 2026-05-13 | Claude (grill-me session) | Initial draft |
