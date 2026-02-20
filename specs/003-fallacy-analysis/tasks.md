# Tasks: Fallacy Analysis

**Input**: Design documents from `/specs/003-fallacy-analysis/`
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

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Backend models, TypeScript types, and service module that all user stories depend on. Since this feature extends an existing codebase, no project setup is needed.

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T001 [P] Add fallacy analysis Pydantic models to `backend/app/models.py`: `ClearExample` (scenario: str, why_wrong: str), `Fallacy` (timestamp: str | None, quote: str, fallacy_name: str, category: str, severity: str, explanation: str, clear_example: ClearExample), `FallacySummary` (total_fallacies: int, high_severity: int, medium_severity: int, low_severity: int, primary_tactics: list[str]), `FallacyAnalysisResult` (summary: FallacySummary, fallacies: list[Fallacy]); add `fallacy_analysis: FallacyAnalysisResult | None = None` field to `SummarizeResponse`
- [X] T002 [P] Add fallacy model unit tests to `backend/tests/unit/test_models.py` (extend): test `ClearExample` requires scenario and why_wrong; test `Fallacy` with all fields; test `Fallacy` with null timestamp; test `FallacySummary` with all fields; test `FallacyAnalysisResult` with summary and fallacies list; test `SummarizeResponse` includes optional `fallacy_analysis` field defaulting to None; test `SummarizeResponse` with populated `fallacy_analysis`
- [X] T003 [P] Add fallacy TypeScript interfaces to `frontend/src/types/index.ts`: `ClearExample` (scenario: string, why_wrong: string), `Fallacy` (timestamp: string | null, quote: string, fallacy_name: string, category: string, severity: string, explanation: string, clear_example: ClearExample), `FallacySummary` (total_fallacies: number, high_severity: number, medium_severity: number, low_severity: number, primary_tactics: string[]), `FallacyAnalysisResult` (summary: FallacySummary, fallacies: Fallacy[]); add `fallacy_analysis: FallacyAnalysisResult | null` to `SummarizeResponse`

**Checkpoint**: Backend models validate correctly. Frontend types include all fallacy interfaces. SummarizeResponse has nullable fallacy_analysis field. Model tests pass.

---

## Phase 2: User Story 1 - Analyze Transcript for Fallacies (Priority: P1) MVP

**Goal**: When a user submits a YouTube URL, the system performs both summarization and fallacy analysis automatically. The response includes structured fallacy data alongside the summary. Fallacy results are displayed below the summary.

**Independent Test**: Submit a YouTube URL. Verify the response includes a `fallacy_analysis` field with summary statistics and a list of identified fallacies. Verify the frontend displays fallacy cards with all six data fields.

### Tests for User Story 1

- [X] T004 [P] [US1] Unit tests for `analyze_fallacies()` in `backend/tests/unit/test_fallacy_analyzer.py` (new): test returns `FallacyAnalysisResult` when OpenAI returns valid JSON; test system prompt contains fallacy analysis instructions; test transcript is passed as user message; test uses JSON mode (`response_format`); test returns `None` when OpenAI returns malformed JSON; test returns `None` when OpenAI raises an API error; test uses 30s timeout
- [X] T005 [P] [US1] Integration tests for fallacy analysis in `backend/tests/integration/test_api.py` (extend): test POST /api/summarize returns `fallacy_analysis` field in response; test `fallacy_analysis` is null when fallacy analysis fails (OpenAI error on second call); test existing summary, metadata, and error responses are unchanged

### Implementation for User Story 1

- [X] T006 [US1] Create `analyze_fallacies()` function in `backend/app/services/fallacy_analyzer.py` (new): embed the fallacy analysis prompt from `fallacy.txt` as `_FALLACY_SYSTEM_PROMPT` constant; accept `transcript_text: str` parameter; call OpenAI with `response_format={"type": "json_object"}`, model `gpt-4o-mini`, timeout 30s; parse JSON response with `json.loads()`; validate against `FallacyAnalysisResult` Pydantic model; return `FallacyAnalysisResult` on success, `None` on any failure (log warning); reuse existing `_MODEL` and `_TIMEOUT` constants pattern from `summarizer.py`
- [X] T007 [US1] Update `summarize_video()` in `backend/app/main.py`: import `analyze_fallacies` from `app.services.fallacy_analyzer`; after successful summarization and before metadata fetch, call `analyze_fallacies(full_text)` inside a try/except block (matching the metadata pattern); on failure, set `fallacy_analysis = None` and log warning; pass `fallacy_analysis` to `SummarizeResponse` constructor
- [X] T008 [P] [US1] Create `FallacyDisplay.vue` component in `frontend/src/components/FallacyDisplay.vue`: accept `fallacies` prop (array of Fallacy objects); render each fallacy as a card showing: quoted passage (blockquote), fallacy name (heading), category (badge), severity (text label), explanation (paragraph), and clear example (scenario + why_wrong in a sub-section); show "No fallacies found" message when array is empty
- [X] T009 [US1] Integrate fallacy display in `frontend/src/App.vue`: add `fallacyAnalysis` ref typed as `FallacyAnalysisResult | null`; store `response.fallacy_analysis ?? null` after successful API call; clear `fallacyAnalysis` in `handleSubmit` reset block; render `FallacyDisplay` below `SummaryDisplay` when `fallacyAnalysis` is not null, passing `fallacyAnalysis.fallacies`

**Checkpoint**: User can submit a URL and see both summary and fallacy analysis. Backend returns structured fallacy data. Frontend displays fallacy cards with all fields. Fallacy analysis failure does not break summary display. All US1 tests pass.

---

## Phase 3: User Story 2 - Color-Coded Severity Display (Priority: P2)

**Goal**: Each fallacy card is visually distinguished by its severity level using color-coded indicators — high = red, medium = amber/orange, low = yellow.

**Independent Test**: Submit a URL and verify fallacy cards have different colored indicators (border or badge) based on their severity level.

### Tests for User Story 2

- [X] T010 [P] [US2] Frontend component tests for `FallacyDisplay.vue` in `frontend/tests/components/FallacyDisplay.spec.ts` (new): test renders fallacy cards with all fields (quote, name, category, severity, explanation, example); test high-severity fallacy has CSS class `fallacy-card--high`; test medium-severity fallacy has CSS class `fallacy-card--medium`; test low-severity fallacy has CSS class `fallacy-card--low`; test shows "No fallacies found" message when fallacies array is empty; test renders multiple fallacies

### Implementation for User Story 2

- [X] T011 [US2] Update `FallacyDisplay.vue` to add severity-based CSS classes: add dynamic class binding `fallacy-card--{severity}` to each card element; define CSS styles: `.fallacy-card--high` with red left border and light red background accent, `.fallacy-card--medium` with amber/orange left border and light amber background accent, `.fallacy-card--low` with yellow left border and light yellow background accent; add a severity badge element showing the severity text ("High", "Medium", "Low") with matching background color

**Checkpoint**: Fallacy cards are visually color-coded by severity. Component tests verify CSS class assignment. Users can distinguish severity at a glance.

---

## Phase 4: User Story 3 - Summary Statistics Overview (Priority: P3)

**Goal**: A summary statistics panel appears above the fallacy list showing total count, severity breakdown, and primary tactics used.

**Independent Test**: Submit a URL and verify a statistics panel appears above the fallacy list with total count, severity counts, and primary tactics.

### Tests for User Story 3

- [X] T012 [P] [US3] Frontend component tests for `FallacySummaryPanel.vue` in `frontend/tests/components/FallacySummaryPanel.spec.ts` (new): test renders total fallacy count; test renders high/medium/low severity counts; test renders primary tactics as a comma-separated list; test renders zero-state correctly (total: 0, all counts 0, no tactics); test does not render when summary is null

### Implementation for User Story 3

- [X] T013 [P] [US3] Create `FallacySummaryPanel.vue` component in `frontend/src/components/FallacySummaryPanel.vue`: accept `summary` prop (FallacySummary object); display total fallacy count prominently; show severity breakdown as labeled counts (e.g., "High: 2, Medium: 3, Low: 1"); show primary tactics as a comma-separated inline list; use consistent styling with existing components
- [X] T014 [US3] Integrate `FallacySummaryPanel` in `frontend/src/App.vue`: render `FallacySummaryPanel` above `FallacyDisplay` when `fallacyAnalysis` is not null, passing `fallacyAnalysis.summary`

**Checkpoint**: Statistics panel shows above fallacy list with total, severity breakdown, and tactics. Zero-state displays correctly. Component tests pass.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Quality improvements that affect multiple user stories

- [X] T015 [P] Run Ruff on backend (`ruff check app/ tests/ && ruff format --check app/ tests/` in `backend/`) and fix any violations
- [X] T016 [P] Run ESLint + Prettier on frontend (`npm run lint` in `frontend/`) and fix any violations
- [X] T017 [P] Run type checks: `mypy app/` in `backend/` for Python, `vue-tsc --noEmit` in `frontend/` for TypeScript
- [X] T018 Run all backend tests (`pytest tests/` in `backend/`) and all frontend tests (`npm run test` in `frontend/`) — verify no regressions
- [X] T019 Run frontend build (`npm run build` in `frontend/`) to verify production build succeeds

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — can start immediately (project already set up from features 001/002)
- **User Story 1 (Phase 2)**: Depends on Phase 1 completion
- **User Story 2 (Phase 3)**: Depends on Phase 2 completion (FallacyDisplay component must exist)
- **User Story 3 (Phase 4)**: Depends on Phase 2 completion (fallacyAnalysis ref and App.vue integration must exist)
- **Polish (Phase 5)**: Depends on Phases 2–4 completion

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 1 — no dependencies on other stories
- **US2 (P2)**: Depends on US1 (the FallacyDisplay component created in US1)
- **US3 (P3)**: Depends on US1 (the fallacyAnalysis ref and App.vue integration from US1)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Backend model changes before service changes
- Service changes before endpoint wiring
- Backend before frontend
- Components before integration (App.vue)

### Parallel Opportunities

- Phase 1: T001, T002, T003 in parallel (different files, no dependencies)
- Phase 2: T004, T005 in parallel (tests); T008 in parallel with T006/T007 (frontend while backend completes)
- Phase 3: T010 in parallel with other test tasks
- Phase 4: T012, T013 in parallel (test + component in different files)
- Phase 5: T015, T016, T017 in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Foundational (models + types)
2. Complete Phase 2: User Story 1 (backend service + frontend display)
3. **STOP and VALIDATE**: Submit a URL, verify fallacy analysis appears below summary
4. Deploy/demo if ready

### Incremental Delivery

1. Complete Foundational → Models and types ready
2. Add User Story 1 → Full end-to-end fallacy analysis with basic display (MVP!)
3. Add User Story 2 → Color-coded severity indicators
4. Add User Story 3 → Summary statistics panel
5. Polish phase → Lint, type-check, full test suite

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- This feature modifies existing files from features 001/002 — no new project setup needed
- All external services (YouTube, OpenAI) are mocked in tests
- The fallacy prompt from `fallacy.txt` is embedded as a Python string constant (not loaded at runtime)
- OpenAI JSON mode (`response_format: {"type": "json_object"}`) is used for reliable JSON output
- Fallacy analysis failure never blocks the summary — graceful degradation pattern
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
