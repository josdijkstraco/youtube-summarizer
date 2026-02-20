# Implementation Plan: Summary Length Slider

**Branch**: `002-summary-length-slider` | **Date**: 2026-02-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-summary-length-slider/spec.md`

## Summary

Add a slider control to the frontend that lets users choose what percentage (10%–50%, in 5% increments) of the original transcript's word count the summary should retain. The selected percentage is sent to the backend, which incorporates it into the AI prompt to guide summary length. Default is 25%. The feature is backward-compatible — omitting the parameter uses the default.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI, openai, youtube-transcript-api (backend); Vue 3, Vite (frontend) — no new dependencies
**Storage**: N/A (no persistence — percentage is sent per request, slider is session-only)
**Testing**: pytest + pytest-asyncio (backend), Vitest + Vue Test Utils (frontend)
**Target Platform**: Web browser (frontend), Linux/macOS server (backend)
**Project Type**: web (frontend + backend)
**Performance Goals**: No additional latency — the percentage is passed as a prompt parameter
**Constraints**: Percentage is approximate guidance; ±20% variance acceptable. Slider updates < 100ms.
**Scale/Scope**: Extends existing single-page app. Adds 1 new component, modifies 3 existing files (backend + frontend).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Code Quality | All public interfaces have type annotations | PASS — `length_percent` field typed as `int` with Pydantic validation |
| I. Code Quality | Automated linting/formatting configured | PASS — Ruff (Python), ESLint + Prettier (TS) already in place |
| I. Code Quality | Dependencies justified (< 50-line threshold) | PASS — No new dependencies added |
| II. Testing Standards | Integration test for each user-facing feature | PASS — Integration test for percentage parameter planned |
| II. Testing Standards | Unit tests for business logic | PASS — Prompt generation, validation, slider component tests planned |
| II. Testing Standards | Mocks only for external services | PASS — Only mock OpenAI |
| III. UX Consistency | Actionable error messages | PASS — Invalid percentage returns 422 via Pydantic validation |
| III. UX Consistency | Consistent output format (JSON envelope) | PASS — Same SummarizeResponse schema |
| III. UX Consistency | Progress indicator for > 500ms ops | PASS — Existing loading state; slider disabled during loading |
| III. UX Consistency | Accessibility: keyboard-navigable | PASS — Native `<input type="range">` is keyboard-accessible |
| IV. Performance | API p95 < 500ms excluding external calls | PASS — No additional processing; word count is O(n) split |
| IV. Performance | External API timeouts + retries | PASS — Existing 30s timeout unchanged |

**Result**: All gates pass. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/002-summary-length-slider/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── api.yaml         # Updated OpenAPI spec (SummarizeRequest changes)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py              # Update: pass length_percent to summarizer
│   ├── models.py            # Update: add length_percent to SummarizeRequest
│   └── services/
│       └── summarizer.py    # Update: accept length_percent, modify AI prompt
├── tests/
│   ├── unit/
│   │   ├── test_models.py       # Update: test length_percent validation
│   │   └── test_summarizer.py   # Update: test prompt includes word count target
│   └── integration/
│       └── test_api.py          # Update: test percentage in request/response

frontend/
├── src/
│   ├── App.vue                  # Update: add LengthSlider, pass percentage to API
│   ├── components/
│   │   └── LengthSlider.vue     # NEW: slider component with label
│   ├── services/
│   │   └── api.ts               # Update: include length_percent in request
│   └── types/
│       └── index.ts             # Update: add length_percent to SummarizeRequest
├── tests/
│   └── components/
│       └── LengthSlider.spec.ts # NEW: slider component tests
```

**Structure Decision**: Web application structure unchanged from feature 001. Only modifications to existing files + 2 new files (component + test).

## Complexity Tracking

> No violations detected. All constitution gates pass.
