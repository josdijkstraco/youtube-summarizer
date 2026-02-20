# Implementation Plan: Fallacy Analysis

**Branch**: `003-fallacy-analysis` | **Date**: 2026-02-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-fallacy-analysis/spec.md`

## Summary

Extend the existing `/api/summarize` endpoint to automatically perform logical fallacy analysis on the transcript alongside summarization. The backend adds a new `analyze_fallacies()` service function that sends the transcript to OpenAI with the fallacy analysis prompt (from `fallacy.txt`) using JSON mode, parses the structured response, and returns it as an optional `fallacy_analysis` field in the existing `SummarizeResponse`. The frontend displays the fallacy results below the summary with color-coded severity indicators and a summary statistics panel.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI, Pydantic, OpenAI Python SDK (backend); Vue 3, Vite (frontend)
**Storage**: N/A — no persistence, on-demand analysis
**Testing**: pytest (backend), Vitest + @vue/test-utils (frontend)
**Target Platform**: Web application (localhost development)
**Project Type**: Web (backend + frontend)
**Performance Goals**: Fallacy analysis adds one additional OpenAI API call per request; total latency dominated by external AI calls
**Constraints**: OpenAI 30s timeout per call; response must not exceed 5MB; fallacy analysis failure must not block summary
**Scale/Scope**: Single-user development tool

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Code Quality — Single responsibility | PASS | New `fallacy_analyzer.py` service module, separate from `summarizer.py`. Display component separate from `SummaryDisplay.vue`. |
| I. Code Quality — Type annotations | PASS | All new Pydantic models and TypeScript interfaces will be fully typed. |
| I. Code Quality — Linting/formatting | PASS | Ruff (Python) + ESLint/Prettier (TS/Vue) enforced in polish phase. |
| I. Code Quality — No dead code | PASS | No removals needed; additive feature only. |
| I. Code Quality — Dependency justification | PASS | No new dependencies. Uses existing OpenAI SDK. |
| II. Testing — Integration test | PASS | Integration test for extended `/api/summarize` response with fallacy data. |
| II. Testing — Unit tests | PASS | Unit tests for `analyze_fallacies()`, Pydantic model parsing, frontend component. |
| II. Testing — Deterministic | PASS | All AI calls mocked in tests. |
| II. Testing — Descriptive names | PASS | Follow existing naming conventions. |
| II. Testing — Mock only external services | PASS | Only OpenAI is mocked. |
| III. UX — Actionable errors | PASS | Fallacy analysis failure shows message; summary still displays (FR-008). |
| III. UX — Consistent output format | PASS | Extended `SummarizeResponse` schema — backward compatible (new nullable field). |
| III. UX — Loading states | PASS | Existing loading indicator covers the combined operation (FR-007). |
| III. UX — Accessibility | PASS | Color coding supplemented with text labels (severity badge text). Keyboard-navigable cards. |
| IV. Performance — Timeouts | PASS | Reuses existing 30s timeout on OpenAI calls. |
| IV. Performance — Large payloads | PASS | Fallacy analysis response is small (JSON array); well under 5MB. |

All gates pass. No violations require justification.

## Project Structure

### Documentation (this feature)

```text
specs/003-fallacy-analysis/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── api.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models.py              # Extended: FallacyAnalysisResult, FallacySummary, Fallacy models
│   ├── main.py                # Extended: add fallacy analysis call to summarize_video()
│   └── services/
│       ├── summarizer.py      # Unchanged
│       └── fallacy_analyzer.py  # NEW: analyze_fallacies() function
└── tests/
    ├── unit/
    │   ├── test_models.py           # Extended: fallacy model tests
    │   └── test_fallacy_analyzer.py # NEW: unit tests for analyze_fallacies()
    └── integration/
        └── test_api.py              # Extended: fallacy analysis in summarize response

frontend/
├── src/
│   ├── types/index.ts                      # Extended: fallacy TypeScript interfaces
│   ├── App.vue                             # Extended: pass fallacy data to display
│   └── components/
│       ├── SummaryDisplay.vue              # Unchanged
│       ├── FallacyDisplay.vue              # NEW: fallacy list with severity cards
│       └── FallacySummaryPanel.vue         # NEW: statistics overview panel
└── tests/
    └── components/
        ├── FallacyDisplay.spec.ts          # NEW: fallacy display tests
        └── FallacySummaryPanel.spec.ts     # NEW: summary panel tests
```

**Structure Decision**: Extends existing web application structure. Backend gets a new service module (`fallacy_analyzer.py`) following the same pattern as `summarizer.py`. Frontend gets two new display components. No new directories needed beyond existing layout.
