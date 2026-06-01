# Implementation Tasks

## T001
**Phase**: Phase 1 - Backend Model
**Module**: backend/app/models.py
**Task**: Add `download_status` field to `HistoryItem` Pydantic model
**Done when**: `HistoryItem` includes `download_status: str | None` as a field
**Depends on**: None

---

## T002
**Phase**: Phase 1 - Backend Query
**Module**: backend/app/db.py
**Task**: Update `list_recent()` to SELECT `download_status` from database and include it in the result
**Done when**: `list_recent()` query includes `download_status` in SELECT clause and returns it via `HistoryItem`
**Depends on**: T001

---

## T003
**Phase**: Phase 2 - Frontend Types
**Module**: frontend/src/types/index.ts
**Task**: Add `download_status` field to `HistoryItem` TypeScript interface
**Done when**: `HistoryItem` interface includes `download_status: string | null`
**Depends on**: T001

---

## T004
**Phase**: Phase 2 - Frontend Component
**Module**: frontend/src/components/HistoryCard.vue
**Task**: Add CSS styles for the 8px green dot indicator with white border
**Done when**: `.history-card__download-indicator` CSS class exists with correct size, color, position, and border
**Depends on**: T003

---

## T005
**Phase**: Phase 2 - Frontend Component
**Module**: frontend/src/components/HistoryCard.vue
**Task**: Add conditional rendering of download indicator dot based on `item.download_status === 'ready'`
**Done when**: Dot appears on thumbnail when status is 'ready', hidden otherwise
**Depends on**: T003, T004

---

## T006
**Phase**: Phase 2 - Frontend Component
**Module**: frontend/src/components/HistoryCard.vue
**Task**: Ensure indicator and delete button coexist without visual overlap
**Done when**: Delete button hover state and indicator are both visible and don't interfere
**Depends on**: T005

---

## T007
**Phase**: Phase 3 - Integration Test
**Module**: Manual QA
**Task**: Verify indicator appears on downloaded videos in history sidebar
**Done when**: Green dot is visible on thumbnails with `download_status = 'ready'` in both desktop and mobile viewports
**Depends on**: T001, T002, T003, T004, T005, T006

---

## T008
**Phase**: Phase 3 - Edge Case
**Module**: Manual QA
**Task**: Verify indicator does NOT appear for non-downloaded videos (null/pending/error status)
**Done when**: No dot appears on thumbnails when `download_status` is not 'ready'
**Depends on**: T001, T002, T003, T005

---

## T009
**Phase**: Phase 3 - Regression
**Module**: Manual QA
**Task**: Verify existing history functionality (click to load, delete, restore) continues to work
**Done when**: All existing history panel interactions function correctly after changes
**Depends on**: T001, T002, T003, T004, T005, T006

---

## T010
**Phase**: Phase 3 - Edge Case
**Module**: Manual QA
**Task**: Verify indicator renders even when thumbnail image fails to load
**Done when**: Green dot is visible on thumbnail placeholder/error state when image fails to load
**Depends on**: T005

---

## T011
**Phase**: Phase 3 - Edge Case
**Module**: Manual QA
**Task**: Verify indicator scales appropriately on mobile viewports (small thumbnails)
**Done when**: Dot maintains 8px size and proper positioning on thumbnails ≤88px wide
**Depends on**: T005

---

## T012
**Phase**: Phase 3 - Accessibility
**Module**: Manual QA
**Task**: Verify indicator has sufficient contrast against various thumbnail backgrounds
**Done when**: Green dot with white border is distinguishable on light, dark, and busy thumbnails
**Depends on**: T005

---

## T013
**Phase**: Phase 3 - Integration
**Module**: Manual QA
**Task**: Verify full data pipeline: database `download_status` → API response → frontend rendering
**Done when**: Changing `download_status` in database triggers indicator appearance/disappearance in UI
**Depends on**: T001, T002, T003, T005