# Research: Fallacy Analysis

**Feature**: 003-fallacy-analysis
**Date**: 2026-02-07

## Decision 1: JSON Response Strategy for Fallacy Analysis

**Decision**: Use OpenAI JSON mode (`response_format: {"type": "json_object"}`) with the fallacy prompt, then validate the parsed JSON against Pydantic models.

**Rationale**: gpt-4o-mini fully supports JSON mode, which guarantees syntactically valid JSON output. The fallacy prompt already specifies the exact JSON schema in its text. JSON mode ensures parseable output while the existing prompt provides structural guidance. Pydantic validation catches any schema mismatches (missing fields, wrong types) after parsing.

**Alternatives considered**:
- **Structured Outputs (`json_schema` with `strict: true`)**: Provides stronger schema guarantees but requires defining the schema in OpenAI's format and adds complexity. The fallacy response schema is relatively flat and the prompt already describes it clearly — JSON mode is sufficient.
- **Raw text parsing with regex**: Fragile, unreliable for complex nested JSON. Rejected.
- **No JSON mode (rely on prompt alone)**: Risk of malformed output, especially with "```json" wrappers. Rejected.

## Decision 2: Fallacy Analysis Service Architecture

**Decision**: Create a new `fallacy_analyzer.py` service module with a single `analyze_fallacies(transcript_text: str) -> FallacyAnalysisResult | None` function. Keep it separate from `summarizer.py`.

**Rationale**: Follows the single-responsibility principle (Constitution I). The summarizer and fallacy analyzer have different prompts, different response schemas, and different failure modes. Separation makes each independently testable and maintainable.

**Alternatives considered**:
- **Add to `summarizer.py`**: Violates single responsibility; the module already handles summarization + chunking logic. Rejected.
- **Generic "AI service" module**: Over-abstraction for two distinct operations with different prompts and schemas. Rejected.

## Decision 3: Graceful Degradation Pattern

**Decision**: In `main.py`, call `analyze_fallacies()` inside a try/except block after successful summarization. On failure, set `fallacy_analysis` to `None` and log a warning. The summary is always returned regardless of fallacy analysis outcome.

**Rationale**: Matches the existing pattern used for metadata retrieval (lines 120-127 in `main.py`). Fallacy analysis is supplementary — the user's primary goal (summary) must never be blocked by a secondary feature failure. This also means the endpoint's existing error responses (400, 404, 502) are unchanged.

**Alternatives considered**:
- **Fail the entire request if fallacy analysis fails**: Unacceptable — violates FR-008 and SC-004. Users lose their summary.
- **Return partial response with error field**: Adds complexity to the response schema for an edge case. The nullable `fallacy_analysis` field communicates absence clearly.

## Decision 4: Response Schema Extension

**Decision**: Add an optional `fallacy_analysis: FallacyAnalysisResult | None` field to the existing `SummarizeResponse` Pydantic model. This is backward-compatible — existing clients that don't consume the field are unaffected.

**Rationale**: The clarification decision was to extend the existing endpoint rather than create a new one. Adding a nullable field is the least disruptive approach. The frontend TypeScript interface is updated correspondingly.

**Alternatives considered**:
- **New endpoint**: Rejected during clarification — user chose Option C (extend existing).
- **Wrap in a new response envelope**: Breaks backward compatibility with existing frontend code. Rejected.

## Decision 5: Prompt Embedding Strategy

**Decision**: Embed the fallacy analysis prompt as a Python string constant in `fallacy_analyzer.py` (matching the pattern of `_SYSTEM_PROMPT` in `summarizer.py`). The `fallacy.txt` file serves as the design reference only, not a runtime dependency.

**Rationale**: Follows the existing codebase pattern. Runtime file loading adds failure modes (file not found, encoding issues) and deployment complexity for zero benefit in a single-developer project.

**Alternatives considered**:
- **Load `fallacy.txt` at runtime**: Adds file I/O error handling, makes deployment fragile. Rejected.
- **Environment variable for prompt**: Over-engineering for a fixed prompt. Rejected.

## Decision 6: Handling Malformed AI Responses

**Decision**: Parse the AI's JSON response with `json.loads()`, then validate against Pydantic models. If either step fails, catch the exception and return `None` (fallacy analysis unavailable). Log the error for debugging.

**Rationale**: JSON mode guarantees valid JSON syntax but not schema adherence. Pydantic provides the second layer of validation. The graceful degradation pattern (Decision 3) already handles `None` results.

**Alternatives considered**:
- **Retry on malformed response**: Adds latency and complexity. A single attempt with graceful degradation is simpler and acceptable for a supplementary feature.
- **Return partial data from malformed response**: Increases parsing complexity for minimal gain. Clean failure is better UX than partially correct data.
