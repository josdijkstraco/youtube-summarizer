# Feature Specification: Fallacy Analysis

**Feature Branch**: `003-fallacy-analysis`
**Created**: 2026-02-07
**Status**: Draft
**Input**: User description: "I want to implement a feature that analyzes the transcript for logical fallacies. Use the prompt defined in fallacy.txt. Identify fallacies and show them on the screen with a highlighted color, along with the other information returned from the fallacy prompt."

## Clarifications

### Session 2026-02-07

- Q: Should fallacy analysis use a new endpoint, re-fetch the transcript, or extend the existing summarize endpoint? → A: Extend the existing `/api/summarize` endpoint to return fallacy analysis alongside the summary in one call.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Analyze Transcript for Fallacies (Priority: P1)

When a user submits a YouTube video URL for summarization, the system automatically performs both summarization and fallacy analysis in a single request. The response includes the summary (as before) plus a structured fallacy analysis with identified fallacies — each containing a quoted passage, fallacy name, category, severity rating, explanation, and a clearer illustrative example. The fallacy results are displayed below the summary, color-coded by severity.

**Why this priority**: This is the core feature — without fallacy detection, the entire feature has no value. It delivers the primary user need of identifying flawed reasoning in video content.

**Independent Test**: Submit a YouTube video URL. Verify the system returns both a summary and a structured fallacy analysis with at least the summary statistics and a list of identified fallacies (which may be empty for a fallacy-free transcript).

**Acceptance Scenarios**:

1. **Given** a user submits a valid YouTube URL, **When** the summarization completes, **Then** the response includes both the summary and a fallacy analysis with a summary section (total count, severity breakdown, primary tactics) and a list of individual fallacies.
2. **Given** the AI identifies fallacies in the transcript, **When** the results are displayed, **Then** each fallacy shows: the quoted passage, fallacy name, category, severity level, explanation, and a clearer example from a different context.
3. **Given** the transcript contains no logical fallacies, **When** the analysis completes, **Then** the system displays a message indicating no fallacies were found.

---

### User Story 2 - Color-Coded Severity Display (Priority: P2)

Each identified fallacy is visually distinguished by its severity level using color-coded highlighting. High-severity fallacies are shown in red, medium in amber/orange, and low in yellow/muted color. This allows the user to quickly scan and prioritize which fallacies are most concerning.

**Why this priority**: Color coding transforms the raw list into a scannable, actionable interface. Without it the feature works but is harder to use quickly.

**Independent Test**: Submit a YouTube video URL for a video known to contain arguments. Verify that each fallacy card displays a colored indicator or border that corresponds to its severity (high = red, medium = amber, low = yellow).

**Acceptance Scenarios**:

1. **Given** the analysis returns a high-severity fallacy, **When** it is displayed, **Then** it has a red color indicator (border, badge, or background accent).
2. **Given** the analysis returns a medium-severity fallacy, **When** it is displayed, **Then** it has an amber/orange color indicator.
3. **Given** the analysis returns a low-severity fallacy, **When** it is displayed, **Then** it has a yellow/muted color indicator.

---

### User Story 3 - Summary Statistics Overview (Priority: P3)

Before the individual fallacy list, the user sees a summary panel showing the total number of fallacies found, a breakdown by severity (high, medium, low counts), and the primary tactics used in the transcript. This gives a quick at-a-glance assessment.

**Why this priority**: Enhances usability by giving a quick overview before the user dives into details. The feature works without it, but this makes it more informative at a glance.

**Independent Test**: Submit a YouTube video URL and verify that a summary panel appears above the fallacy list showing total count, severity breakdown, and primary tactics.

**Acceptance Scenarios**:

1. **Given** the analysis has completed, **When** the results are displayed, **Then** a summary section shows the total number of fallacies, counts per severity level, and a list of primary fallacy tactics used.
2. **Given** zero fallacies are found, **When** the summary is displayed, **Then** it shows total: 0 with all severity counts at 0.

---

### Edge Cases

- What happens when the AI service is unavailable or returns an error during fallacy analysis? The summary is still returned successfully; the fallacy analysis field is null with an error indicator, and the user can see their summary without fallacy data.
- What happens when the transcript is extremely short (a few words)? The system still sends it for analysis; the AI may return zero fallacies.
- What happens when the AI returns malformed JSON for the fallacy analysis? The summary is still returned; the fallacy analysis is treated as unavailable with an appropriate message.
- What happens when the user submits a new video URL? Any previous summary and fallacy analysis results are cleared.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST perform fallacy analysis automatically as part of the existing summarization flow — no separate user action required.
- **FR-002**: System MUST send the transcript text to the AI with the fallacy analysis prompt defined in `fallacy.txt`, requesting a JSON-structured response.
- **FR-003**: System MUST parse the AI response into structured data: a summary object (total_fallacies, high/medium/low counts, primary_tactics) and an array of fallacy objects (timestamp, quote, fallacy_name, category, severity, explanation, clear_example).
- **FR-004**: System MUST display each identified fallacy with all returned fields: quoted passage, fallacy name, category, severity, explanation, and the illustrative example (scenario + why_wrong).
- **FR-005**: System MUST color-code each fallacy by severity: high = red, medium = amber/orange, low = yellow.
- **FR-006**: System MUST display a summary statistics panel showing total fallacies, breakdown by severity, and primary tactics.
- **FR-007**: System MUST show fallacy analysis results alongside the summary using the existing loading indicator for the combined operation.
- **FR-008**: System MUST handle fallacy analysis failures gracefully — a failed fallacy analysis MUST NOT prevent the summary from being displayed. The fallacy section shows an error message if analysis failed.
- **FR-009**: System MUST include fallacy analysis data in the existing summarization response structure (extended response schema).
- **FR-010**: System MUST clear any previous summary and fallacy analysis results when the user submits a new video URL.

### Key Entities

- **FallacySummary**: Aggregate statistics — total fallacy count, counts by severity level (high, medium, low), list of primary tactics identified.
- **Fallacy**: Individual fallacy — timestamp (optional), quoted passage, fallacy name, category (Relevance, Presumption, Ambiguity, Emotional Appeal, Statistical, Manipulation), severity (high/medium/low), explanation text, and a clear example containing a scenario and why_wrong explanation.
- **FallacyAnalysisResult**: Top-level container holding the summary and the list of individual fallacies. Included as an optional field in the existing summarization response.

## Assumptions

- The fallacy analysis uses the same AI model and service already configured for summarization (currently gpt-4o-mini via OpenAI).
- The fallacy analysis operates on the same transcript text already retrieved during the summarization step — no additional YouTube API call is needed.
- The `fallacy.txt` prompt is embedded in the backend service code (not loaded at runtime from the file). The file serves as the design reference for the prompt content.
- Fallacy analysis runs automatically with every summarization request — both operations are performed in a single call to the existing endpoint.
- The JSON response schema from the AI is best-effort; the backend validates and handles malformed responses gracefully.
- The `length_percent` slider (feature 002) does not affect fallacy analysis — the full transcript is always analyzed.
- A fallacy analysis failure does not block the summary from being returned; the fallacy result is nullable in the response.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users receive both a summary and fallacy analysis from a single submission — no additional clicks or actions required.
- **SC-002**: Each identified fallacy displays all six pieces of information from the analysis prompt (quote, name, category, severity, explanation, example).
- **SC-003**: Users can visually distinguish high, medium, and low severity fallacies at a glance through color coding.
- **SC-004**: The system handles fallacy analysis errors gracefully without blocking the summary — users always see their summary even if fallacy analysis fails.
- **SC-005**: Fallacy analysis does not break existing summarization functionality — all prior features continue to work unchanged.
