# Feature Specification: Summary Length Slider

**Feature Branch**: `002-summary-length-slider`
**Created**: 2026-02-07
**Status**: Draft
**Input**: User description: "I want to add a new feature where the user can use a slider to determine what percentage of the original transcript should remain after the summary."

## Clarifications

### Session 2026-02-07

- Q: How should "percentage of the original transcript" be measured? → A: Word count (summary words / transcript words).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Adjust Summary Length Before Submitting (Priority: P1)

As a user, I want to use a slider to choose how detailed the summary should be before I submit a YouTube URL, so that I can get a summary that matches my needs — brief for a quick overview, or longer for more detail.

The slider represents the approximate percentage of the original transcript's word count that the summary should retain. A lower percentage produces a more concise summary; a higher percentage produces a more detailed one.

**Why this priority**: This is the core feature. Without the slider control and the system's ability to use the selected percentage when generating the summary, the feature has no value.

**Independent Test**: Can be fully tested by adjusting the slider to different positions and submitting a YouTube URL, then verifying the resulting summary length roughly corresponds to the chosen percentage of the transcript.

**Acceptance Scenarios**:

1. **Given** the user is on the main page, **When** they view the input area, **Then** they see a slider control with a default value of 25% and a label showing the current percentage.
2. **Given** the user drags the slider to 10%, **When** they submit a YouTube URL, **Then** the returned summary is approximately 10% of the original transcript's word count.
3. **Given** the user moves the slider to 50%, **When** they submit a YouTube URL, **Then** the returned summary is approximately 50% of the original transcript's word count.
4. **Given** the user has not interacted with the slider, **When** they submit a YouTube URL, **Then** the summary is generated at the default 25% length.

---

### User Story 2 - See Live Percentage Feedback (Priority: P2)

As a user, I want to see the current percentage value update in real time as I move the slider, so that I know exactly what setting I'm choosing before I submit.

**Why this priority**: Visual feedback improves usability and confidence in the control, but the core functionality (US1) works without it.

**Independent Test**: Can be tested by moving the slider and confirming the displayed percentage label updates immediately as the slider moves.

**Acceptance Scenarios**:

1. **Given** the slider is at 25%, **When** the user drags it to 40%, **Then** the displayed percentage label updates to "40%" in real time as the slider moves.
2. **Given** the slider is at any position, **When** the user views the slider area, **Then** the current percentage is clearly visible next to or above the slider.

---

### User Story 3 - Preserve Slider Setting Across Submissions (Priority: P3)

As a user, I want the slider to retain its position after I submit a URL, so that I can summarize multiple videos at the same length without readjusting the slider each time.

**Why this priority**: Convenience improvement for repeat usage. The feature is fully functional without this.

**Independent Test**: Can be tested by setting the slider to a non-default value, submitting a URL, then submitting a second URL and verifying the slider remains at the previously chosen position.

**Acceptance Scenarios**:

1. **Given** the user sets the slider to 35% and submits a URL, **When** the summary is returned and the user enters a new URL, **Then** the slider remains at 35%.
2. **Given** the user has received a summary, **When** they look at the slider, **Then** it shows the same percentage they selected before submission.

---

### Edge Cases

- What happens when the transcript is very short (under 100 words)? The system should return the best summary it can; the percentage is a target, not a guarantee. For very short transcripts, the summary may be close to the full transcript length regardless of the slider setting.
- What happens at the minimum (10%) on a very long transcript? The summary should still be coherent and cover the main points, even if it must sacrifice detail to meet the length target.
- What happens at the maximum (50%) on a short transcript? The summary may end up being nearly as long as the original; this is acceptable since the user explicitly requested a detailed summary.
- How does the system handle the slider value during a loading state? The slider should be disabled while a summary is being generated, preventing changes mid-request.
- What if the AI produces a summary that doesn't match the target percentage? The percentage is approximate guidance. The system should instruct the AI to aim for the target, but exact adherence is not required. Variations of up to 20% from the target are acceptable (e.g., a 25% target may produce a summary between 20% and 30% of the original length).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display a slider control that allows the user to select a summary length percentage between 10% and 50%.
- **FR-002**: System MUST set the slider default value to 25% on initial page load.
- **FR-003**: System MUST display the currently selected percentage value as a label alongside the slider.
- **FR-004**: System MUST update the displayed percentage label in real time as the user moves the slider.
- **FR-005**: System MUST include the selected percentage in the summarization request sent to the backend.
- **FR-006**: System MUST use the provided percentage to guide the AI in generating a summary of approximately that proportion of the original transcript's word count.
- **FR-007**: System MUST accept percentage values in increments of 5% (10%, 15%, 20%, 25%, 30%, 35%, 40%, 45%, 50%).
- **FR-008**: System MUST disable the slider while a summarization request is in progress.
- **FR-009**: System MUST retain the slider position after a summary is returned, so the user can submit another URL at the same setting.
- **FR-010**: System MUST continue to work correctly if the percentage parameter is not provided, defaulting to 25%.

### Key Entities

- **Summary Length Preference**: A percentage value (10%–50%, in 5% increments) representing the user's desired ratio of summary word count to original transcript word count. Default is 25%. Sent as part of the summarization request and used as guidance for AI summary generation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can adjust the summary length slider and submit a URL within the same time it takes to submit without the slider (no more than 2 additional seconds of interaction).
- **SC-002**: Summaries generated at 10% are noticeably shorter than summaries generated at 50% for the same video — at least a 2x difference in word count.
- **SC-003**: The displayed percentage updates within 100 milliseconds of slider movement, providing immediate visual feedback.
- **SC-004**: The slider retains its position across consecutive submissions without resetting.
- **SC-005**: Existing functionality (submitting a URL without adjusting the slider) continues to work identically to the current behavior.

## Assumptions

- The percentage is measured by word count (summary words / transcript words). It is approximate guidance for the AI, not an exact word-count contract. The AI will be instructed to aim for the target but may vary.
- The slider range of 10%–50% is appropriate; below 10% produces summaries too brief to be useful, and above 50% is barely a summary.
- 5% increments provide sufficient granularity without overwhelming the user with too many choices.
- The default of 25% aligns with the current summarization behavior (roughly a quarter of the transcript).
- This feature extends the existing YouTube summarizer (feature 001) and does not require any new external services or API keys.
- The slider is a session-only control; there is no need to persist the user's preference across browser sessions.
