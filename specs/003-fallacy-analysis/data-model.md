# Data Model: Fallacy Analysis

**Feature**: 003-fallacy-analysis
**Date**: 2026-02-07

## New Models

### ClearExample

Illustrative example of a fallacy pattern in a different context.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| scenario | string | yes | A simpler example of the same fallacy pattern |
| why_wrong | string | yes | Brief explanation of why it's wrong |

### Fallacy

A single identified logical fallacy in the transcript.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| timestamp | string or null | no | Timestamp in the transcript, null if unavailable |
| quote | string | yes | Exact passage from transcript containing the fallacy |
| fallacy_name | string | yes | Name of the logical fallacy |
| category | string | yes | One of: Relevance, Presumption, Ambiguity, Emotional Appeal, Statistical, Manipulation |
| severity | string | yes | One of: high, medium, low |
| explanation | string | yes | 2-3 sentence explanation of why this qualifies as a fallacy |
| clear_example | ClearExample | yes | Illustrative example in a different context |

### FallacySummary

Aggregate statistics for the fallacy analysis.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| total_fallacies | integer | yes | Total number of fallacies identified |
| high_severity | integer | yes | Count of high-severity fallacies |
| medium_severity | integer | yes | Count of medium-severity fallacies |
| low_severity | integer | yes | Count of low-severity fallacies |
| primary_tactics | list of strings | yes | Most common fallacy types used in the transcript |

### FallacyAnalysisResult

Top-level container for the full fallacy analysis.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| summary | FallacySummary | yes | Aggregate statistics |
| fallacies | list of Fallacy | yes | Individual fallacies (may be empty) |

## Modified Models

### SummarizeResponse (extended)

Added one new optional field to the existing response.

| Field | Type | Required | Change |
|-------|------|----------|--------|
| summary | string | yes | Unchanged |
| metadata | VideoMetadata or null | no | Unchanged |
| fallacy_analysis | FallacyAnalysisResult or null | no | **NEW** — null when analysis fails or is unavailable |

## Validation Rules

- `category` must be one of the six defined categories (Relevance, Presumption, Ambiguity, Emotional Appeal, Statistical, Manipulation)
- `severity` must be one of: high, medium, low
- `total_fallacies` must equal the length of the `fallacies` array
- `high_severity + medium_severity + low_severity` must equal `total_fallacies`
- `primary_tactics` must be a non-empty list when `total_fallacies > 0`, empty list when `total_fallacies == 0`

## Relationships

```text
SummarizeResponse
├── summary: str
├── metadata: VideoMetadata | None
└── fallacy_analysis: FallacyAnalysisResult | None
    ├── summary: FallacySummary
    │   ├── total_fallacies: int
    │   ├── high_severity: int
    │   ├── medium_severity: int
    │   ├── low_severity: int
    │   └── primary_tactics: list[str]
    └── fallacies: list[Fallacy]
        ├── timestamp: str | None
        ├── quote: str
        ├── fallacy_name: str
        ├── category: str
        ├── severity: str
        ├── explanation: str
        └── clear_example: ClearExample
            ├── scenario: str
            └── why_wrong: str
```
