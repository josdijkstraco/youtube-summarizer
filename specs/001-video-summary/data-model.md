# Data Model: YouTube Video Summary

**Feature Branch**: `001-video-summary`
**Date**: 2026-02-06

## Overview

This feature has no persistent storage. All data exists transiently
within a single request lifecycle. The models below describe the
shapes of data as they flow through the system.

## Entities

### SummarizeRequest

The user's input to the system.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| url | string | Required, non-empty | YouTube video URL provided by the user |

**Validation Rules**:
- MUST be a non-empty string
- MUST match a recognized YouTube URL pattern (youtube.com/watch,
  youtu.be, youtube.com/shorts)
- MUST contain a valid 11-character video ID

### VideoMetadata

Information about the YouTube video, retrieved via oEmbed.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| video_id | string | 11 chars, alphanumeric + `-_` | Extracted YouTube video ID |
| title | string | Optional | Video title from oEmbed |
| channel_name | string | Optional | Channel/author name from oEmbed |
| duration_seconds | integer | Optional, >= 0 | Approximate duration derived from transcript |
| thumbnail_url | string | Optional, valid URL | Thumbnail image URL |

**Notes**:
- `title` and `channel_name` come from the YouTube oEmbed API
- `duration_seconds` is calculated from the last transcript segment's
  `start + duration` values
- All metadata fields are optional — the system MUST gracefully handle
  missing metadata per US3 acceptance scenario 2

### Transcript

The raw transcript data retrieved from YouTube.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| video_id | string | 11 chars | Associated video ID |
| segments | list[TranscriptSegment] | Non-empty | Ordered list of caption segments |
| language | string | ISO 639-1 code | Transcript language (e.g., "en") |
| is_generated | boolean | Required | Whether captions are auto-generated |
| full_text | string | Derived | Concatenation of all segment texts |

### TranscriptSegment

A single caption segment from the YouTube transcript.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| text | string | Non-empty | Caption text content |
| start | float | >= 0 | Start time in seconds |
| duration | float | > 0 | Duration of this segment in seconds |

### Summary

The AI-generated summary of the transcript.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| text | string | Non-empty | Generated summary text |
| model | string | Non-empty | Model used (e.g., "gpt-4o-mini") |

### SummarizeResponse

The complete response returned to the frontend.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| summary | string | Non-empty | Generated summary text |
| metadata | VideoMetadata | Optional | Video metadata if available |

### ErrorResponse

Standardized error format for all failure cases.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| error | string | Non-empty | Machine-readable error code |
| message | string | Non-empty | Human-readable, actionable error message |
| details | string | Optional | Additional context or suggestions |

**Error Codes**:
- `invalid_url`: Input is not a recognized YouTube URL
- `video_not_found`: YouTube video does not exist or was removed
- `transcript_unavailable`: Video exists but has no captions
- `playlist_not_supported`: URL points to a playlist, not a video
- `summarization_failed`: OpenAI API call failed
- `internal_error`: Unexpected server error

## Data Flow

```text
User Input (URL string)
    │
    ▼
SummarizeRequest (validated)
    │
    ├──► YouTube URL Parser ──► video_id extraction
    │
    ├──► Transcript Service ──► Transcript (segments + full_text)
    │
    ├──► oEmbed Service ──► VideoMetadata (title, channel)
    │
    └──► Summarizer Service ──► Summary (text)
            │
            ▼
    SummarizeResponse (summary + metadata)
            │
            ▼
    Frontend Display
```

## Relationships

- **SummarizeRequest** → produces one **VideoMetadata** (via URL parsing + oEmbed)
- **SummarizeRequest** → produces one **Transcript** (via youtube-transcript-api)
- **Transcript** → feeds into one **Summary** (via OpenAI)
- **VideoMetadata** + **Summary** → combined into **SummarizeResponse**
- Any step failure → produces **ErrorResponse** instead
