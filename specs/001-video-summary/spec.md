# Feature Specification: YouTube Video Summary

**Feature Branch**: `001-video-summary`
**Created**: 2026-02-06
**Status**: Draft
**Input**: User description: "I want to build an application that allows a user to supply a link to a YouTube video. The system will then retrieve the transcript of the video, create a summary of the transcript, and display the summary to the user."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Summarize a YouTube Video (Priority: P1)

A user visits the application and pastes a YouTube video URL into an
input field. They submit the URL, and the system retrieves the video's
transcript, generates a concise summary, and displays it on screen.
The user can read the summary to understand the video's key points
without watching the entire video.

**Why this priority**: This is the core value proposition of the
application. Without this flow, no other features have meaning. It
delivers immediate, standalone value to every user.

**Independent Test**: Can be fully tested by submitting any valid
YouTube URL that has a transcript available and verifying a readable
summary is returned and displayed.

**Acceptance Scenarios**:

1. **Given** a user is on the application home screen, **When** they
   paste a valid YouTube URL and submit it, **Then** the system
   displays a text summary of the video's content within a reasonable
   wait time.
2. **Given** a user submits a valid YouTube URL, **When** the
   transcript is being retrieved and summarized, **Then** the system
   displays a progress indicator so the user knows processing is
   underway.
3. **Given** a user submits a valid YouTube URL for a video that has
   a transcript, **When** the summary is generated, **Then** the
   summary accurately reflects the main topics and key points of the
   video.

---

### User Story 2 - Handle Invalid or Unsupported Videos (Priority: P2)

A user submits a URL that is not a valid YouTube link, points to a
video that does not exist, or references a video that has no
transcript available. The system detects the issue and provides a
clear, actionable error message explaining what went wrong and what
the user can do about it.

**Why this priority**: Error handling is essential for a usable
product. Users will inevitably submit bad URLs or encounter videos
without transcripts. Graceful handling prevents confusion and
frustration.

**Independent Test**: Can be tested by submitting various invalid
inputs (non-URLs, non-YouTube URLs, deleted video URLs, videos
without transcripts) and verifying appropriate error messages appear.

**Acceptance Scenarios**:

1. **Given** a user is on the application home screen, **When** they
   submit a string that is not a valid URL, **Then** the system
   displays an error message indicating the input is not a valid URL.
2. **Given** a user submits a valid YouTube URL, **When** the video
   does not exist or has been removed, **Then** the system displays
   an error message stating the video could not be found.
3. **Given** a user submits a valid YouTube URL, **When** the video
   has no transcript available (e.g., no captions), **Then** the
   system displays a message explaining that no transcript is
   available for this video and suggests trying a different video.

---

### User Story 3 - View Video Metadata Alongside Summary (Priority: P3)

When a summary is displayed, the user also sees basic metadata about
the video — such as the title, channel name, and duration — so they
can confirm they summarized the correct video and have context for the
summary.

**Why this priority**: Metadata provides context and confirmation but
is not essential for the core summarization feature. It enhances user
confidence and experience without being required for the MVP.

**Independent Test**: Can be tested by submitting a valid YouTube URL
and verifying that the video title, channel name, and duration are
displayed alongside the summary.

**Acceptance Scenarios**:

1. **Given** a user has submitted a valid YouTube URL, **When** the
   summary is displayed, **Then** the video title, channel name, and
   duration are shown alongside the summary.
2. **Given** a user has submitted a valid YouTube URL, **When** any
   metadata field is unavailable, **Then** the system gracefully
   omits that field rather than showing an error or blank placeholder.

---

### Edge Cases

- What happens when the video transcript is extremely long (e.g., a
  3+ hour lecture)? The system MUST still produce a summary within a
  reasonable time and not fail silently.
- What happens when the video has auto-generated captions only? The
  system MUST treat auto-generated captions the same as manual
  captions and attempt to summarize them.
- What happens when the user submits a YouTube playlist URL instead
  of a single video? The system MUST inform the user that only
  individual video URLs are supported.
- What happens when the user submits a YouTube Shorts URL? The system
  MUST handle Shorts URLs the same as regular video URLs.
- What happens when the transcript is in a non-English language? The
  system MUST still attempt to generate a summary. If the summary
  language differs from the user's expected language, this is
  acceptable for the initial version.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a YouTube video URL as user input
  via a text input field.
- **FR-002**: System MUST validate that the submitted input is a
  properly formatted YouTube URL (supporting youtube.com/watch,
  youtu.be, and YouTube Shorts formats).
- **FR-003**: System MUST retrieve the transcript (captions) for the
  specified YouTube video, including auto-generated captions.
- **FR-004**: System MUST generate a concise, readable summary from
  the retrieved transcript text.
- **FR-005**: System MUST display the generated summary to the user
  in a readable format on the same page.
- **FR-006**: System MUST display a progress indicator while the
  transcript is being retrieved and the summary is being generated.
- **FR-007**: System MUST display clear, actionable error messages
  when the URL is invalid, the video is not found, or no transcript
  is available.
- **FR-008**: System MUST handle videos with long transcripts (3+
  hours) without failing or timing out from the user's perspective.
- **FR-009**: System MUST display video metadata (title, channel
  name, duration) alongside the summary when available.
- **FR-010**: System MUST reject non-video YouTube URLs (playlists,
  channels) with an appropriate message.

### Key Entities

- **Video**: Represents a YouTube video identified by URL. Key
  attributes: URL, video ID, title, channel name, duration,
  transcript availability.
- **Transcript**: The text content of a video's captions. Key
  attributes: full text, language, source type (manual or
  auto-generated), associated video.
- **Summary**: A condensed version of a transcript's content. Key
  attributes: summary text, source transcript, generation timestamp.

### Assumptions

- The application is a single-user, session-based experience with no
  authentication required. Any visitor can use it without signing in.
- Summaries are generated on-demand and are not persisted between
  sessions. Each request produces a fresh summary.
- The application supports one video at a time. There is no queue or
  batch processing.
- The target audience is English-speaking users, but the system will
  not reject non-English transcripts.
- The application is web-based and accessed via a browser.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can submit a YouTube URL and receive a readable
  summary in under 30 seconds for videos up to 30 minutes long.
- **SC-002**: 95% of valid YouTube URLs with available transcripts
  produce a successful summary on the first attempt.
- **SC-003**: 100% of invalid inputs (bad URLs, missing videos, no
  transcript) produce a user-friendly error message rather than a
  blank screen or unhandled error.
- **SC-004**: Users can identify the correct video from displayed
  metadata (title, channel, duration) before reading the summary.
- **SC-005**: The summary captures the main topics of the video as
  judged by a user who has watched the video (qualitative validation
  during testing).
