# Product Requirements Document (PRD)

## Overview & Context

- **Product/Feature Summary**: Add a subtle visual indicator (green dot) to the history sidebar showing when a video has been downloaded and is available locally.
- **Problem Statement**: Users cannot easily identify which videos in their history are available for local playback without clicking into each one. This creates unnecessary network requests and confusion when offline.
- **Business Objectives**: Improve user experience by providing clear visual feedback about local video availability, reducing unnecessary API calls and improving perceived performance.
- **Success Metrics**: Users can quickly identify downloaded videos in the history panel; indicator is visible but unobtrusive.

---

## Scope

- **In Scope**: 
  - Backend: Expose `download_status` field via `HistoryItem` model and `list_recent()` query
  - Frontend: Update TypeScript types, add dot indicator to `HistoryCard.vue` component
  - Visual design: 8px green dot (#10B981) with 2px white border, positioned top-right corner of thumbnail
- **Out of Scope**: 
  - Download/un-download functionality (already exists)
  - Other history panel modifications
  - Different indicator colors for different states
- **Release Phases / Milestones**: Single release combining backend and frontend changes

---

## Stakeholders

- **Target Users / Personas**: Users who download videos for offline viewing or faster playback
- **Internal Stakeholders**: Product owner, frontend team
- **Owners**: Implementation team

---

## Requirements

### Functional Requirements

- **FR-1**: Backend must include `download_status` field in `HistoryItem` response
- **FR-2**: Backend `list_recent()` must query `download_status` from database and return it in history response
- **FR-3**: Frontend must update `HistoryItem` interface to include `download_status: string | null`
- **FR-4**: `HistoryCard.vue` must render an 8px green dot on the thumbnail when `download_status === 'ready'`
- **FR-5**: Dot must not render for states: `pending`, `error`, or `null`

### Non-Functional Requirements

- **Performance**: No measurable performance impact on history panel load time
- **Visual Design**: Indicator must be subtle and not interfere with thumbnail visibility or delete button functionality
- **Accessibility**: Dot should have sufficient contrast against thumbnail backgrounds (achieved via white border)

### Technical Constraints

- Database schema already includes `download_status` column (added in previous migration)
- Must maintain backward compatibility with existing API consumers
- No new dependencies added

---

## User Experience

- **User Flow**: 
  1. User opens history sidebar
  2. Each downloaded video shows a small green dot in top-right corner of thumbnail
  3. Non-downloaded videos show no indicator
  4. Delete button (top-right, hover-only) and indicator coexist without overlap issues

- **Edge Cases**:
  - Thumbnail fails to load: dot still renders in same position
  - Very small thumbnails (mobile): dot scales appropriately with CSS
  - Deleted video: dot disappears after soft-delete

---

## Success Metrics

- **KPIs**: 
  - Indicator appears on all cards with `download_status = 'ready'`
  - No visual regression in thumbnail display or delete button
  - Zero user-reported confusion about indicator meaning
- **Acceptance Criteria**:
  - Backend returns `download_status` in history API response
  - Frontend renders 8px green dot (#10B981) with 2px white border at top-right of thumbnail
  - Dot only shows when `download_status === 'ready'`
  - All existing history functionality continues to work

---

## Timeline & Milestones

| Milestone | Description | Target Date |
|-----------|-------------|-------------|
| Implementation Complete | Backend and frontend changes merged | Same day |
| QA | Manual verification in browser | Same day |
| Launch | Production release | Same day |

- **Dependencies**: None (uses existing database schema)

---

## Open Questions & Risks

| # | Question / Risk | Owner | Status |
|---|-----------------|-------|--------|
| 1 | Should indicator show hover tooltip (e.g., "Available offline")? | Product | Deferred |

---

## Revision History

| Version | Date | Author | Summary of Changes |
|---------|------|--------|--------------------|
| 1.0 | 2026-05-16 | Claude Code | Initial PRD from discussion |