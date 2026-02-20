# Research: Summary Length Slider

**Feature Branch**: `002-summary-length-slider`
**Date**: 2026-02-07

## Research Summary

This feature extends the existing YouTube summarizer to accept a user-controlled summary length parameter. No new external services, dependencies, or architectural changes are needed. The research below documents key decisions.

## Decisions

### 1. How to communicate length preference to the AI

**Decision**: Include transcript word count and target word count directly in the system prompt.

**Rationale**: The most reliable way to influence LLM output length is to state the target explicitly in the prompt. By computing the transcript word count on the backend and calculating the target word count (transcript_words * length_percent / 100), we give the AI a concrete number to aim for rather than an abstract percentage.

**Alternatives considered**:
- `max_tokens` parameter: Too blunt — token count doesn't map cleanly to word count, and truncation can produce incomplete sentences.
- Post-processing (truncate/pad): Unnatural results — cutting a summary mid-thought or padding with filler defeats the purpose.
- Multiple API calls with length feedback: Too slow and expensive for a simple length preference.

### 2. Prompt engineering approach

**Decision**: Modify the system prompt to include: "Your summary should be approximately {target_words} words (about {length_percent}% of the transcript)."

**Rationale**: GPT-4o-mini responds well to explicit word count targets in prompts. This approach:
- Gives the AI both the absolute target (word count) and relative context (percentage)
- Allows natural variation (the AI won't hit the exact count, but will be in the right ballpark)
- Works with the existing chunked summarization flow (each chunk prompt can include per-chunk targets)

**Alternatives considered**:
- Percentage-only in prompt ("summarize to 25%"): Less effective — the AI doesn't know the absolute transcript length.
- Separate length-control prompt after initial summary: Adds latency and cost for a second API call.

### 3. Backend validation strategy

**Decision**: Use Pydantic's `Field` with `ge=10, le=50` constraints and a custom validator ensuring 5% increments. Default to 25 when not provided.

**Rationale**: Pydantic validation keeps the constraint definition co-located with the model and produces clear 422 errors automatically. The 5% increment check is a simple modulo operation.

**Alternatives considered**:
- Enum of allowed values: More rigid but less readable; Pydantic Field with range + modulo check is cleaner.
- Manual validation in endpoint: Violates the pattern established in feature 001 where Pydantic handles all request validation.

### 4. Frontend slider implementation

**Decision**: Use a native HTML `<input type="range">` with `min=10`, `max=50`, `step=5`.

**Rationale**: The native range input:
- Is keyboard-accessible out of the box (arrow keys adjust the value)
- Supports all required constraints natively (min, max, step)
- Requires no additional dependencies
- Can be styled with CSS for visual consistency

**Alternatives considered**:
- Third-party slider library (e.g., vue-slider-component): Violates the constitution's dependency justification rule — a native input handles this in under 50 lines.
- Custom-built slider with drag events: Unnecessary complexity for a simple range selection.

### 5. Word count calculation

**Decision**: Count words using Python's `str.split()` on the transcript text (already available as `full_text`).

**Rationale**: Simple whitespace splitting is sufficient for an approximate word count. The transcript text is already concatenated from segments in `get_transcript()`. No additional processing needed.

**Alternatives considered**:
- Token count (tiktoken): Over-engineered — users think in words, not tokens. Word count is the specified measurement unit.
- Character count: Less intuitive for users and less accurate as a proxy for content density.

### 6. Chunked summarization with length parameter

**Decision**: For long transcripts that require chunking, divide the target word count proportionally across chunks, then combine with a final pass that also includes the overall target.

**Rationale**: If a transcript is split into 3 chunks with a 25% target, each chunk summary should aim for ~25% of its chunk's word count. The final combining step then has an overall target to ensure the final output matches the user's intent.

**Alternatives considered**:
- Apply target only to final combine step: Chunk summaries would be uncontrolled in length, making the combine step harder.
- Ignore chunking (single-pass with full transcript): Not possible for transcripts exceeding the context window.
