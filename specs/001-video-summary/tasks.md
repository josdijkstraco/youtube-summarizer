# Tasks: YouTube Video Summary

**Input**: Design documents from `/specs/001-video-summary/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included per constitution Principle II (Testing Standards).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/app/`, `frontend/src/`
- Backend tests: `backend/tests/`
- Frontend tests: `frontend/tests/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependency installation, and tooling configuration

- [x] T001 Create backend project structure: `backend/app/__init__.py`, `backend/app/services/__init__.py`, `backend/tests/unit/`, `backend/tests/integration/`
- [x] T002 Create `backend/pyproject.toml` with Python 3.11+ target, and `backend/requirements.txt` with FastAPI, uvicorn, youtube-transcript-api, openai, httpx, pydantic-settings dependencies
- [x] T003 [P] Configure Ruff linting and formatting in `backend/pyproject.toml` (ruff check + ruff format sections)
- [x] T004 [P] Create `backend/.env.example` with `OPENAI_API_KEY=your-key-here` placeholder
- [x] T005 Scaffold Vue 3 + Vite + TypeScript frontend project in `frontend/` using `npm create vue@latest` with TypeScript enabled
- [x] T006 [P] Configure ESLint + Prettier for frontend in `frontend/.eslintrc.cjs` and `frontend/.prettierrc`
- [x] T007 [P] Add Vitest and `@vue/test-utils` as dev dependencies in `frontend/package.json`
- [x] T008 [P] Configure pytest and pytest-asyncio in `backend/pyproject.toml` (pytest section with asyncio_mode = "auto")

**Checkpoint**: Both projects build and run with empty shells. `ruff check .` passes on backend, `npm run lint` passes on frontend, `pytest` discovers no tests, `npm run test` discovers no tests.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared models, configuration, API skeleton, and TypeScript types that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T009 Implement settings/config in `backend/app/config.py` using pydantic-settings: load `OPENAI_API_KEY` from environment, define `BACKEND_CORS_ORIGINS` list
- [x] T010 Define Pydantic models in `backend/app/models.py`: `SummarizeRequest(url: str)`, `VideoMetadata(video_id, title, channel_name, duration_seconds, thumbnail_url)`, `SummarizeResponse(summary: str, metadata: VideoMetadata | None)`, `ErrorResponse(error: str, message: str, details: str | None)` per data-model.md
- [x] T011 Create FastAPI app skeleton in `backend/app/main.py`: app instance, CORS middleware (allow localhost:5173), health check endpoint at `GET /api/health`, and `POST /api/summarize` stub returning 501
- [x] T012 [P] Define TypeScript interfaces in `frontend/src/types/index.ts`: `SummarizeRequest`, `SummarizeResponse`, `VideoMetadata`, `ErrorResponse` matching the OpenAPI contract
- [x] T013 [P] Implement API client in `frontend/src/services/api.ts`: `summarizeVideo(url: string): Promise<SummarizeResponse>` using native fetch with error handling that parses `ErrorResponse` JSON on non-200 status codes
- [x] T014 [P] Create unit test for Pydantic models in `backend/tests/unit/test_models.py`: validate `SummarizeRequest` rejects empty string, `ErrorResponse` requires error + message fields, `VideoMetadata` allows nullable fields

**Checkpoint**: Backend starts with `uvicorn app.main:app`, CORS configured, health endpoint returns `{"status": "ok"}`, summarize endpoint returns 501 stub. Frontend builds and TypeScript compiles. Model tests pass.

---

## Phase 3: User Story 1 - Summarize a YouTube Video (Priority: P1) MVP

**Goal**: User pastes a YouTube URL, receives a text summary of the video's transcript

**Independent Test**: Submit a valid YouTube URL with available transcript and verify a readable summary is returned and displayed in the browser

### Tests for User Story 1

- [x] T015 [P] [US1] Unit test for YouTube URL parsing in `backend/tests/unit/test_youtube.py`: test `extract_video_id()` with youtube.com/watch, youtu.be, youtube.com/shorts, m.youtube.com formats; test rejection of non-YouTube URLs, playlist URLs, empty strings
- [x] T016 [P] [US1] Unit test for transcript service in `backend/tests/unit/test_transcript.py`: test `get_transcript()` returns concatenated text from mocked youtube-transcript-api segments; test that transcript segments are joined with spaces
- [x] T017 [P] [US1] Unit test for summarizer service in `backend/tests/unit/test_summarizer.py`: test `generate_summary()` calls OpenAI with correct model ID `gpt-4o-mini` and system prompt; test chunked summarization for long transcripts (mock openai client)
- [x] T018 [US1] Integration test for POST /api/summarize in `backend/tests/integration/test_api.py`: test happy path with mocked youtube-transcript-api and mocked OpenAI client; verify response matches `SummarizeResponse` schema

### Implementation for User Story 1

- [x] T019 [US1] Implement YouTube URL parsing and validation in `backend/app/services/youtube.py`: `extract_video_id(url: str) -> str` using regex, `is_playlist_url(url: str) -> bool`, raise `ValueError` with descriptive message on invalid input
- [x] T020 [US1] Implement transcript retrieval in `backend/app/services/transcript.py`: `get_transcript(video_id: str) -> tuple[str, list[dict]]` using `YouTubeTranscriptApi.fetch()`, concatenate segment texts into full transcript string, return both full text and raw segments; handle `TranscriptsDisabled`, `NoTranscriptFound`, `VideoUnavailable` exceptions
- [x] T021 [US1] Implement summarization in `backend/app/services/summarizer.py`: `generate_summary(transcript_text: str) -> str` using OpenAI `gpt-4o-mini` with a system prompt for concise video summarization; implement chunked summarization for transcripts exceeding 100K tokens; set timeout of 30s on API call
- [x] T022 [US1] Wire up `POST /api/summarize` endpoint in `backend/app/main.py`: accept `SummarizeRequest`, call `extract_video_id()`, `get_transcript()`, `generate_summary()`, return `SummarizeResponse` with summary text (metadata=None for now)
- [x] T023 [P] [US1] Create `UrlInput.vue` component in `frontend/src/components/UrlInput.vue`: text input with placeholder "Paste a YouTube URL...", submit button labeled "Summarize", emit `submit` event with URL string, disable button while loading
- [x] T024 [P] [US1] Create `LoadingState.vue` component in `frontend/src/components/LoadingState.vue`: display a spinner/pulse animation with "Generating summary..." text, shown via `v-if` prop
- [x] T025 [P] [US1] Create `SummaryDisplay.vue` component in `frontend/src/components/SummaryDisplay.vue`: receive summary string as prop, render in readable paragraph format with proper whitespace handling
- [x] T026 [US1] Integrate components in `frontend/src/App.vue`: compose UrlInput, LoadingState, and SummaryDisplay; manage reactive state (`loading`, `summary`, `error`) using Composition API refs; call `api.summarizeVideo()` on submit, toggle loading/summary/error states

**Checkpoint**: User can paste a YouTube URL, click Summarize, see a loading indicator, and receive a text summary. Backend processes the full pipeline (URL parse → transcript fetch → AI summarization). Run `pytest backend/tests/` — all US1 tests pass.

---

## Phase 4: User Story 2 - Handle Invalid or Unsupported Videos (Priority: P2)

**Goal**: System displays clear, actionable error messages for invalid URLs, missing videos, and unavailable transcripts

**Independent Test**: Submit various invalid inputs (non-URLs, non-YouTube URLs, deleted video URLs, playlist URLs, videos without transcripts) and verify appropriate error messages appear

### Tests for User Story 2

- [x] T027 [P] [US2] Unit test for error mapping in `backend/tests/unit/test_youtube.py` (extend): test that `extract_video_id()` raises `ValueError` with specific messages for non-URL strings, non-YouTube URLs, and playlist URLs
- [x] T028 [US2] Integration test for error responses in `backend/tests/integration/test_api.py` (extend): test POST /api/summarize returns 400 with `invalid_url` error for bad URLs, 400 with `playlist_not_supported` for playlist URLs, 404 with `video_not_found` for non-existent videos, 404 with `transcript_unavailable` for videos without captions; verify all responses match `ErrorResponse` schema

### Implementation for User Story 2

- [x] T029 [US2] Add structured error handling to `POST /api/summarize` in `backend/app/main.py`: catch `ValueError` from URL parsing (return 400 `invalid_url` or `playlist_not_supported`), catch `VideoUnavailable` from transcript service (return 404 `video_not_found`), catch `TranscriptsDisabled`/`NoTranscriptFound` (return 404 `transcript_unavailable`), catch OpenAI errors (return 502 `summarization_failed`), catch all unhandled exceptions (return 500 `internal_error`); all error responses use `ErrorResponse` model with actionable messages per contracts/api.yaml
- [x] T030 [P] [US2] Create `ErrorMessage.vue` component in `frontend/src/components/ErrorMessage.vue`: receive `ErrorResponse` object as prop, display error message prominently with a suggestion/details section if `details` field is present, include a "Try again" action to clear the error state
- [x] T031 [US2] Update `frontend/src/App.vue` to handle error states: parse `ErrorResponse` from failed API calls in `api.ts`, display `ErrorMessage` component when error state is set, clear error on new submission
- [x] T032 [US2] Update `frontend/src/services/api.ts` to parse error responses: on non-200 status, read response body as `ErrorResponse` JSON, throw typed error with error code and message so `App.vue` can display it

**Checkpoint**: Invalid URLs show "not a valid YouTube URL" message. Playlist URLs show "not supported" message. Non-existent videos show "could not be found" message. Videos without transcripts show "no transcript available" message with suggestion. Run `pytest backend/tests/` — all US1 and US2 tests pass.

---

## Phase 5: User Story 3 - View Video Metadata Alongside Summary (Priority: P3)

**Goal**: Display video title, channel name, and duration alongside the summary

**Independent Test**: Submit a valid YouTube URL and verify that title, channel name, and duration appear alongside the summary

### Tests for User Story 3

- [x] T033 [P] [US3] Unit test for metadata service in `backend/tests/unit/test_youtube.py` (extend): test `get_video_metadata()` parses oEmbed JSON response correctly (title, author_name → channel_name, thumbnail_url); test graceful handling when oEmbed returns error or partial data
- [x] T034 [P] [US3] Unit test for duration calculation in `backend/tests/unit/test_transcript.py` (extend): test `calculate_duration(segments)` returns last segment's `start + duration` as integer seconds; test empty segments returns None

### Implementation for User Story 3

- [x] T035 [US3] Implement metadata retrieval in `backend/app/services/youtube.py` (extend): add `get_video_metadata(video_id: str) -> VideoMetadata` that calls YouTube oEmbed endpoint `https://www.youtube.com/oembed?url=...&format=json`, maps `title`, `author_name` → `channel_name`, `thumbnail_url`; handle HTTP errors gracefully returning partial metadata
- [x] T036 [US3] Add duration calculation to `backend/app/services/transcript.py` (extend): add `calculate_duration(segments: list[dict]) -> int | None` that computes duration from last segment's `start + duration`; return None if segments is empty
- [x] T037 [US3] Update `POST /api/summarize` in `backend/app/main.py` to include metadata: call `get_video_metadata()` and `calculate_duration()` alongside transcript retrieval, populate `SummarizeResponse.metadata` field; metadata retrieval failures MUST NOT block the summary response (return summary with metadata=None)
- [x] T038 [US3] Update `SummaryDisplay.vue` in `frontend/src/components/SummaryDisplay.vue` to display metadata: show video title as heading, channel name as subtitle, formatted duration (e.g., "12:34"), and thumbnail image above the summary text; conditionally hide missing fields using `v-if`
- [x] T039 [US3] Update `frontend/src/App.vue` to pass metadata to `SummaryDisplay`: pass full `SummarizeResponse` object (summary + metadata) to `SummaryDisplay` component

**Checkpoint**: Summary now displays with video title, channel name, and duration. Missing metadata fields are gracefully omitted. Run `pytest backend/tests/` — all US1, US2, and US3 tests pass.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Quality improvements that affect multiple user stories

- [x] T040 [P] Add frontend component tests in `frontend/tests/components/UrlInput.spec.ts`: test input binding, submit event emission, button disabled state during loading
- [x] T041 [P] Add frontend component tests in `frontend/tests/components/SummaryDisplay.spec.ts`: test rendering summary text, rendering metadata fields, hiding missing metadata
- [x] T042 Run Ruff on entire backend codebase (`ruff check backend/ && ruff format --check backend/`) and fix any violations
- [x] T043 [P] Run ESLint + Prettier on frontend (`npm run lint` in `frontend/`) and fix any violations
- [x] T044 [P] Run type checks: `mypy backend/app/` for Python, `npx vue-tsc --noEmit` for TypeScript frontend
- [x] T045 Validate quickstart.md end-to-end: follow every step in `specs/001-video-summary/quickstart.md` from scratch, verify both servers start and a real YouTube URL produces a summary

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 completion
- **User Story 2 (Phase 4)**: Depends on Phase 2 completion; builds on Phase 3 error paths
- **User Story 3 (Phase 5)**: Depends on Phase 2 completion; extends Phase 3 response
- **Polish (Phase 6)**: Depends on Phases 3-5 completion

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **US2 (P2)**: Can start after Phase 2 — extends error handling from US1 endpoint but is independently testable
- **US3 (P3)**: Can start after Phase 2 — extends metadata for US1 response but is independently testable

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Services before endpoint wiring
- Backend before frontend
- Components before integration (App.vue)

### Parallel Opportunities

- Phase 1: T003, T004 in parallel; T006, T007, T008 in parallel
- Phase 2: T012, T013, T014 in parallel (frontend work while backend models are done)
- Phase 3: T015, T016, T017 in parallel (all unit tests); T023, T024, T025 in parallel (all Vue components)
- Phase 4: T027, T028 in parallel (tests); T030 in parallel with T029 (frontend/backend)
- Phase 5: T033, T034 in parallel (tests)
- Phase 6: T040, T041, T043, T044 in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all unit tests for US1 together:
Task: "Unit test for YouTube URL parsing in backend/tests/unit/test_youtube.py"
Task: "Unit test for transcript service in backend/tests/unit/test_transcript.py"
Task: "Unit test for summarizer service in backend/tests/unit/test_summarizer.py"

# Launch all Vue components for US1 together:
Task: "Create UrlInput.vue in frontend/src/components/UrlInput.vue"
Task: "Create LoadingState.vue in frontend/src/components/LoadingState.vue"
Task: "Create SummaryDisplay.vue in frontend/src/components/SummaryDisplay.vue"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test by submitting a real YouTube URL and verifying summary displays
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test error cases → Deploy/Demo
4. Add User Story 3 → Test metadata display → Deploy/Demo
5. Polish phase → Run all linters, type checks, quickstart validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Backend uses `backend/app/` paths, frontend uses `frontend/src/` paths
- All external services (YouTube, OpenAI) are mocked in tests
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
