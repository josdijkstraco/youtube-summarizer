# Feature Specification: Postgres Video Storage

**Feature Branch**: `004-postgres-video-storage`
**Created**: 2026-02-21
**Status**: Draft
**Input**: User description: "Help me implement a system that stores the thumbnail, the link, the summary and transcript of the video into Postgres. I have a postgres instance in AWS you can use."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Past Video Summaries (Priority: P1)

A user who has previously summarized a YouTube video wants to revisit the result without reprocessing the video. They open the application and can see a history of previously processed videos, including the thumbnail, link, and summary for each entry.

**Why this priority**: Persistence is the core value of this feature — without it, all other stories are moot. This is the primary user benefit: not having to wait for re-processing.

**Independent Test**: Can be fully tested by submitting a video URL, verifying it appears in a history list with thumbnail, link, and summary, and confirming it survives a page refresh.

**Acceptance Scenarios**:

1. **Given** a video has been summarized previously, **When** the user views the history list, **Then** the video's thumbnail, link, and summary are displayed.
2. **Given** the history list is shown, **When** the user refreshes the page, **Then** previously stored entries are still visible.
3. **Given** no videos have been processed yet, **When** the user views the history list, **Then** an empty state message is shown.

---

### User Story 2 - Avoid Duplicate Processing (Priority: P2)

A user submits a YouTube URL that has already been processed and stored. The system recognizes the existing record and returns the stored summary and transcript immediately without re-fetching or re-summarizing.

**Why this priority**: Saves time and cost by preventing redundant API calls for videos already in the database.

**Independent Test**: Can be tested by submitting the same URL twice and verifying the second submission returns instantly with the stored result, rather than re-running the full summarization pipeline.

**Acceptance Scenarios**:

1. **Given** a video URL already exists in storage, **When** the user submits that URL again, **Then** the stored summary is returned without re-processing.
2. **Given** a URL is looked up in storage, **When** a match is found, **Then** the response time is significantly faster than a full summarization.

---

### User Story 3 - Access Full Transcript of Stored Video (Priority: P3)

A user wants to read the full transcript of a previously processed video. They can retrieve the raw transcript alongside the summary from the stored record.

**Why this priority**: Provides additional value beyond the summary for users who want verbatim content, but is secondary to the core persistence story.

**Independent Test**: Can be tested by retrieving a stored record and verifying the full transcript text is present and matches the original video content.

**Acceptance Scenarios**:

1. **Given** a video has been stored with its transcript, **When** the user requests the full record, **Then** the complete transcript text is returned.
2. **Given** a video was processed but no transcript was available, **When** the user views the record, **Then** the transcript field indicates it is unavailable.

---

### Edge Cases

- What happens when a video URL is submitted but the thumbnail cannot be fetched?
- How does the system handle a duplicate URL submitted concurrently by two users at the same time?
- What happens if storage fails mid-process (summary is generated but save fails)?
- How does the system handle very long transcripts that exceed typical field size limits?
- What happens when a previously stored video is deleted from YouTube (thumbnail link breaks)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST persist the video URL, thumbnail URL, generated summary, and full transcript for each processed video.
- **FR-002**: System MUST check storage before processing a submitted video URL and return the existing record if a match is found.
- **FR-003**: System MUST store the video record in a remote Postgres database hosted on AWS.
- **FR-004**: System MUST display a history of stored video records including thumbnail, link, and summary.
- **FR-005**: System MUST store the timestamp of when the video was first processed.
- **FR-006**: System MUST handle storage failures gracefully, still returning the generated result to the user even if persistence fails, and surfacing an error indicator.
- **FR-007**: System MUST support retrieval of the full transcript for any stored video record.
- **FR-008**: System MUST use a secure, credential-based connection to the AWS Postgres instance, with all credentials (host, port, database name, username, password) supplied via environment variables.

### Key Entities

- **VideoRecord**: Represents a processed YouTube video. Key attributes: unique video identifier (derived from URL), video URL, thumbnail URL, generated summary text, full transcript text, created-at timestamp.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Previously processed videos are retrievable from storage within 1 second on subsequent requests.
- **SC-002**: 100% of successfully processed videos are persisted to the database (no silent data loss).
- **SC-003**: Duplicate video submissions are served from storage at least 5× faster than a fresh summarization.
- **SC-004**: The history list displays up to the 50 most recent stored videos without perceptible delay.
- **SC-005**: Database connection failures do not prevent the user from receiving their summary — a fallback response is always returned.

## Assumptions

- The AWS Postgres instance is already provisioned and accessible from the application's host environment.
- Thumbnail URLs are sourced from YouTube's standard thumbnail CDN and are assumed to be stable — only the URL is stored, not the image data.
- A video is uniquely identified by its YouTube video ID extracted from the URL.
- The summary and transcript generated at processing time are stored as-is; no editing or versioning of stored records is needed.
- The connection to Postgres uses standard SSL/TLS encryption in transit.
- No user authentication is required for this feature — all stored records are accessible to any user of the application.
