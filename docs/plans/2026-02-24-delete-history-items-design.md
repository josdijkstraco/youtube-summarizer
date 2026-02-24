# Delete Items from Recent Videos List — Design

## Summary

Add the ability to soft-delete individual videos from the history panel. Deletion is optimistic (card disappears instantly) with a 5-second undo toast. Data is retained in Postgres via a `deleted_at` timestamp column.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Delete type | Soft delete (`deleted_at` column) | Enables undo, data retention |
| UI trigger | X button on each HistoryCard | Discoverable, consistent with existing patterns |
| Confirmation | Instant with undo toast (5s) | Low-friction for a low-stakes action |
| Scope | Individual items only | Keep scope small; bulk delete can come later |
| UI pattern | Optimistic UI | Best UX; soft delete makes rollback trivial |

## Database Changes

Add `deleted_at TIMESTAMPTZ DEFAULT NULL` to `youtube_summarizer.summaries`.

- Update `CREATE TABLE IF NOT EXISTS` in `db.py` to include the new column.
- Add `ALTER TABLE youtube_summarizer.summaries ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL` for existing databases.
- All listing queries (`list_recent`) filter with `WHERE deleted_at IS NULL`.
- Cache lookup (`get_by_video_id`) also excludes soft-deleted records so re-summarizing generates fresh results.

New DB functions:
- `soft_delete(conn, video_id)` — sets `deleted_at = now()`
- `restore(conn, video_id)` — sets `deleted_at = NULL`

## API Changes

| Method | Endpoint | Behavior | Response |
|--------|----------|----------|----------|
| `DELETE` | `/api/history/{video_id}` | Soft-deletes the record | `204 No Content` |
| `POST` | `/api/history/{video_id}/restore` | Clears `deleted_at` | `200` with restored `HistoryItem` |

Update CORS config to allow `DELETE` method.

## Frontend: HistoryCard

- Add a small X button in the top-right corner, visible on hover (always visible on touch devices via CSS).
- Click on X emits `delete(videoId)` and stops event propagation (prevents card selection).

## Frontend: HistoryPanel

- On `delete` event: immediately remove item from local list, call `deleteHistoryItem(videoId)`, show undo toast.
- Undo toast appears at the bottom of the history panel for 5 seconds: "Video removed. Undo".
- On undo click: call `restoreHistoryItem(videoId)`, re-insert item at its original position, dismiss toast.
- On API failure: restore the card, show error toast.
- Only one undo toast at a time — deleting another item while a toast is showing commits the previous delete.

## Frontend: api.ts

- `deleteHistoryItem(videoId: string)` — `DELETE /api/history/{videoId}`
- `restoreHistoryItem(videoId: string)` — `POST /api/history/{videoId}/restore`
