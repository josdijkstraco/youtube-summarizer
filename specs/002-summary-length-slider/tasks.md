# Tasks: Summary Length Slider

**Input**: Design documents from `/specs/002-summary-length-slider/`
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

**Purpose**: Model and type changes that all user stories depend on. Since this feature extends an existing codebase, no project setup is needed.

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T001 [P] Add `length_percent` field to `SummarizeRequest` in `backend/app/models.py`: optional integer, default 25, range 10–50, must be a multiple of 5; use Pydantic `Field(default=25, ge=10, le=50)` with a `field_validator` for the 5% increment check
- [x] T002 [P] Add `length_percent` unit tests to `backend/tests/unit/test_models.py` (extend): test default value is 25, test valid values (10, 25, 50), test rejection of out-of-range values (5, 55, 0), test rejection of non-multiples-of-5 (12, 23, 37)
- [x] T003 [P] Add `length_percent` to `SummarizeRequest` interface in `frontend/src/types/index.ts`: optional `length_percent?: number` field

**Checkpoint**: Backend model accepts and validates `length_percent`. Frontend type includes the field. Model tests pass.

---

## Phase 2: User Story 1 - Adjust Summary Length Before Submitting (Priority: P1) MVP

**Goal**: User selects a percentage on a slider, submits a URL, and receives a summary whose length corresponds to the chosen percentage of the transcript's word count.

**Independent Test**: Submit a YouTube URL with `length_percent=10` and `length_percent=50`, verify the 50% summary is at least 2x longer than the 10% summary.

### Tests for User Story 1

- [x] T004 [P] [US1] Unit test for length-aware summarization in `backend/tests/unit/test_summarizer.py` (extend): test `generate_summary()` includes target word count in system prompt when `transcript_word_count` and `length_percent` are provided; test default behavior (no length params) produces the original prompt without word count target
- [x] T005 [P] [US1] Integration test for length_percent in `backend/tests/integration/test_api.py` (extend): test POST /api/summarize with `length_percent=10` passes the value through to the summarizer; test POST /api/summarize without `length_percent` uses default 25; test POST /api/summarize with invalid `length_percent=7` returns 422

### Implementation for User Story 1

- [x] T006 [US1] Update `generate_summary()` in `backend/app/services/summarizer.py` to accept optional `transcript_word_count: int` and `length_percent: int` parameters; when provided, modify the system prompt to include "Your summary should be approximately {target_words} words (about {length_percent}% of the transcript)."; calculate `target_words = transcript_word_count * length_percent // 100`; for chunked summarization, divide target proportionally across chunks and include overall target in the combine step
- [x] T007 [US1] Update `POST /api/summarize` in `backend/app/main.py`: compute `transcript_word_count = len(full_text.split())` after retrieving the transcript; pass `transcript_word_count` and `request.length_percent` to `generate_summary()`
- [x] T008 [P] [US1] Update `summarizeVideo()` in `frontend/src/services/api.ts` to accept an optional `lengthPercent` parameter and include it as `length_percent` in the request body
- [x] T009 [P] [US1] Create `LengthSlider.vue` component in `frontend/src/components/LengthSlider.vue`: native `<input type="range">` with `min=10`, `max=50`, `step=5`; accept `modelValue` prop (number) and `disabled` prop (boolean); emit `update:modelValue` on input for v-model support; display a label showing "Summary length: {value}%"
- [x] T010 [US1] Integrate `LengthSlider` in `frontend/src/App.vue`: add `lengthPercent` ref with default 25; place `LengthSlider` between `UrlInput` and the submit area, bound via v-model to `lengthPercent`; pass `lengthPercent` to `summarizeVideo()` in the `handleSubmit` function; disable slider while `loading` is true

**Checkpoint**: User can adjust slider and submit a URL. Backend generates a length-guided summary. Default behavior (no slider interaction) is unchanged. All US1 tests pass.

---

## Phase 3: User Story 2 - See Live Percentage Feedback (Priority: P2)

**Goal**: The percentage label updates in real time as the user drags the slider.

**Independent Test**: Move the slider and verify the displayed label updates immediately at each position.

### Tests for User Story 2

- [x] T011 [P] [US2] Frontend component test for `LengthSlider.vue` in `frontend/tests/components/LengthSlider.spec.ts`: test renders with default value and shows "25%" label; test changing input value updates displayed percentage; test emits `update:modelValue` with correct value on input; test renders as disabled when `disabled` prop is true; test shows correct label at min (10%) and max (50%) positions

### Implementation for User Story 2

- [x] T012 [US2] Verify `LengthSlider.vue` label updates reactively on `@input` event (already wired if using v-model with `<input type="range">`); ensure the label text format is "{value}%" and updates on every input event (not just on change/release)

**Checkpoint**: Slider label updates in real time during drag. Component tests pass.

---

## Phase 4: User Story 3 - Preserve Slider Setting Across Submissions (Priority: P3)

**Goal**: The slider retains its position after a summary is returned, so the user can submit another URL at the same setting.

**Independent Test**: Set slider to 35%, submit a URL, then verify the slider is still at 35% after the summary appears.

### Implementation for User Story 3

- [x] T013 [US3] Verify `lengthPercent` ref in `frontend/src/App.vue` is NOT reset in the `handleSubmit` function or in the `finally` block; confirm the slider retains its value after submission completes (the ref should only be initialized to 25 on component mount, never reassigned during the submit flow)

**Checkpoint**: Slider retains position across submissions. Manual verification: set to 35%, submit, confirm still 35%.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Quality improvements that affect multiple user stories

- [x] T014 [P] Run Ruff on backend (`ruff check backend/ && ruff format --check backend/`) and fix any violations
- [x] T015 [P] Run ESLint + Prettier on frontend (`npm run lint` in `frontend/`) and fix any violations
- [x] T016 [P] Run type checks: `mypy backend/app/` for Python, `npx vue-tsc --noEmit` for TypeScript frontend
- [x] T017 Run all backend tests (`pytest backend/tests/`) and all frontend tests (`npm run test` in `frontend/`) — verify no regressions
- [x] T018 Run frontend build (`npm run build` in `frontend/`) to verify production build succeeds

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — can start immediately (project already set up from feature 001)
- **User Story 1 (Phase 2)**: Depends on Phase 1 completion
- **User Story 2 (Phase 3)**: Depends on Phase 2 completion (slider component must exist)
- **User Story 3 (Phase 4)**: Depends on Phase 2 completion (submit flow must exist)
- **Polish (Phase 5)**: Depends on Phases 2–4 completion

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 1 — no dependencies on other stories
- **US2 (P2)**: Depends on US1 (the slider component created in US1)
- **US3 (P3)**: Depends on US1 (the submit flow and slider ref created in US1)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Backend model changes before service changes
- Service changes before endpoint wiring
- Backend before frontend
- Components before integration (App.vue)

### Parallel Opportunities

- Phase 1: T001, T002, T003 in parallel (different files, no dependencies)
- Phase 2: T004, T005 in parallel (tests); T008, T009 in parallel (frontend work while backend completes)
- Phase 5: T014, T015, T016 in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Foundational (model + type changes)
2. Complete Phase 2: User Story 1 (backend prompt + frontend slider)
3. **STOP and VALIDATE**: Submit a URL at 10% and 50%, verify different summary lengths
4. Deploy/demo if ready

### Incremental Delivery

1. Complete Foundational → Model and types ready
2. Add User Story 1 → Full end-to-end slider + length-guided summaries (MVP!)
3. Add User Story 2 → Live percentage feedback (component tests)
4. Add User Story 3 → Slider persistence verification
5. Polish phase → Lint, type-check, full test suite

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- This feature modifies existing files from feature 001 — no new project setup needed
- All external services (YouTube, OpenAI) are mocked in tests
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
