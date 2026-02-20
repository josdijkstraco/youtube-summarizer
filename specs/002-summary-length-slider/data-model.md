# Data Model: Summary Length Slider

**Feature Branch**: `002-summary-length-slider`
**Date**: 2026-02-07

## Overview

This feature adds one new field (`length_percent`) to the existing `SummarizeRequest` model. No new entities are introduced. No persistent storage changes.

## Changes to Existing Entities

### SummarizeRequest (modified)

| Field | Type | Constraints | Description | Change |
|-------|------|-------------|-------------|--------|
| url | string | Required, non-empty | YouTube video URL | Unchanged |
| length_percent | integer | Optional, 10–50, step 5, default 25 | Target summary length as percentage of transcript word count | **NEW** |

**Validation Rules** (new):
- MUST be an integer between 10 and 50 (inclusive)
- MUST be a multiple of 5 (i.e., one of: 10, 15, 20, 25, 30, 35, 40, 45, 50)
- MUST default to 25 when not provided
- Invalid values MUST produce a 422 validation error via standard Pydantic handling

### SummarizeResponse (unchanged)

No changes. The response already contains the summary text — a shorter or longer summary is still just a `summary` string.

### All Other Entities (unchanged)

VideoMetadata, ErrorResponse, Transcript, TranscriptSegment, Summary — no changes.

## Data Flow (updated)

```text
User Input (URL string + length_percent slider value)
    │
    ▼
SummarizeRequest (validated: url + length_percent)
    │
    ├──► YouTube URL Parser ──► video_id extraction
    │
    ├──► Transcript Service ──► Transcript (segments + full_text)
    │         │
    │         └──► Word count calculation (len(full_text.split()))
    │
    ├──► oEmbed Service ──► VideoMetadata (title, channel)
    │
    └──► Summarizer Service ──► Summary (text)
            │                      ▲
            │                      │
            │              length_percent + transcript_word_count
            │              → target_word_count = word_count * length_percent / 100
            │              → included in AI system prompt
            │
            ▼
    SummarizeResponse (summary + metadata)
            │
            ▼
    Frontend Display
```

## Relationships

- **SummarizeRequest.length_percent** → used by **Summarizer Service** to calculate target word count
- **Transcript.full_text** → word count computed, combined with length_percent to produce target
- All other relationships unchanged from feature 001
