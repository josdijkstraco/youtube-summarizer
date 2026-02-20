<!--
  Sync Impact Report
  ==================
  Version change: (none) → 1.0.0
  Modified principles: N/A (initial creation)
  Added sections:
    - Core Principles (4 principles)
    - Performance & Reliability Standards
    - Development Workflow
    - Governance
  Removed sections: N/A
  Templates requiring updates:
    - .specify/templates/plan-template.md ✅ no changes needed (Constitution Check section is generic)
    - .specify/templates/spec-template.md ✅ no changes needed (user stories + acceptance criteria align)
    - .specify/templates/tasks-template.md ✅ no changes needed (test-first workflow compatible)
    - .specify/templates/checklist-template.md ✅ no changes needed (generic structure)
    - .specify/templates/agent-file-template.md ✅ no changes needed (generic structure)
  Follow-up TODOs: None
-->

# YouTube Summarizer Constitution

## Core Principles

### I. Code Quality

All code committed to this project MUST meet the following standards:

- Every module MUST have a single, clear responsibility. Functions
  exceeding 40 lines MUST be decomposed.
- All public interfaces MUST include type annotations. Dynamic typing
  is permitted only in private helpers where types are obvious from
  context.
- No code MUST be merged without passing automated linting and
  formatting checks. The project MUST enforce a consistent style via
  tooling (formatter + linter), not manual review alone.
- Dead code, unused imports, and commented-out blocks MUST be removed
  before merge. TODOs MUST reference a tracked issue.
- Dependencies MUST be justified. Every new dependency MUST solve a
  problem that cannot be addressed with fewer than 50 lines of
  project code.

### II. Testing Standards

Testing is mandatory and MUST follow a structured discipline:

- Every user-facing feature MUST have at least one integration test
  that exercises the full flow from input to output.
- Unit tests MUST cover all business logic functions. Edge cases
  identified in specs MUST have corresponding test cases.
- Tests MUST be deterministic. Flaky tests MUST be quarantined and
  fixed within one development cycle or deleted.
- Test names MUST describe the scenario and expected outcome, not the
  implementation (e.g., `test_returns_summary_for_valid_url` not
  `test_function_a`).
- Mocks MUST only replace external services (APIs, databases,
  filesystem). Internal module interactions MUST NOT be mocked.

### III. User Experience Consistency

All user-facing behavior MUST deliver a coherent, predictable
experience:

- Error messages MUST be actionable. Every user-visible error MUST
  explain what went wrong and suggest a resolution or next step.
- Output formats MUST be consistent across all features. If JSON is
  returned in one endpoint, all endpoints MUST use the same envelope
  structure.
- Loading states, progress indicators, and feedback mechanisms MUST
  be present for any operation exceeding 500ms perceived latency.
- Breaking changes to user-facing interfaces MUST be versioned and
  documented. Users MUST receive deprecation warnings at least one
  release before removal.
- Accessibility MUST be considered for any UI component. Text MUST
  meet minimum contrast ratios and interactive elements MUST be
  keyboard-navigable.

### IV. Performance Requirements

Performance MUST be treated as a feature, not an afterthought:

- API responses MUST complete within 500ms at the 95th percentile
  under normal load, excluding external service latency.
- Memory usage MUST remain stable under sustained load. Unbounded
  growth (memory leaks) MUST be treated as P0 bugs.
- Large payloads (video transcripts, batch results) MUST use
  streaming or pagination. No single response MUST exceed 5MB
  without explicit user opt-in.
- External API calls MUST implement timeouts (max 30s), retries with
  exponential backoff, and circuit-breaker patterns for repeated
  failures.
- Performance-critical paths MUST be profiled before optimization.
  Premature optimization without measurement data is prohibited.

## Performance & Reliability Standards

These quantitative targets apply across the project:

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| API p95 latency | < 500ms (excluding external calls) | Load test or APM |
| Error rate | < 1% of requests under normal load | Error tracking |
| Test suite runtime | < 60s for unit tests, < 5min total | CI pipeline |
| Test coverage | > 80% line coverage on business logic | Coverage tool |
| Startup time | < 3s to ready state | Manual or automated |

Targets MUST be validated in CI when tooling is available. Regressions
against these targets MUST block merge.

## Development Workflow

All contributors MUST follow this workflow:

1. **Spec First**: Features MUST have a written specification
   (spec.md) approved before implementation begins.
2. **Plan Before Code**: Non-trivial changes MUST have an
   implementation plan (plan.md) reviewed against this constitution.
3. **Branch Per Feature**: Each feature MUST be developed on a
   dedicated branch. Direct commits to main are prohibited.
4. **Tests Accompany Code**: New functionality MUST include tests in
   the same PR. Test-only PRs for existing untested code are
   encouraged.
5. **Review Required**: All PRs MUST receive at least one review
   (human or automated) verifying compliance with this constitution
   before merge.
6. **Commit Discipline**: Commits MUST be atomic and descriptive.
   Each commit MUST represent a single logical change.

## Governance

This constitution is the authoritative source of project standards.
In case of conflict between this document and other guidance, this
constitution takes precedence.

**Amendment Procedure**:
1. Propose changes via PR with rationale for each modification.
2. Changes MUST be reviewed and approved before merge.
3. Version MUST be incremented per semantic versioning:
   - MAJOR: Principle removal, redefinition, or backward-incompatible
     governance change.
   - MINOR: New principle or section added, or material expansion of
     existing guidance.
   - PATCH: Clarifications, wording fixes, non-semantic refinements.
4. All dependent templates MUST be checked for consistency after
   amendment (see Sync Impact Report).

**Compliance Review**:
- Every plan.md MUST include a Constitution Check section verifying
  alignment with active principles.
- PR reviews MUST verify adherence to applicable principles.
- Quarterly review of this document is recommended to ensure
  principles remain relevant.

**Version**: 1.0.0 | **Ratified**: 2026-02-06 | **Last Amended**: 2026-02-06
