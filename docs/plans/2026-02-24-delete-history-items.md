# Delete Items from Recent Videos — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow users to soft-delete individual videos from the history panel with optimistic UI and undo toast.

**Architecture:** Soft delete via `deleted_at` column in Postgres. Backend exposes DELETE and restore endpoints. Frontend uses optimistic removal with a 5-second undo toast that can restore the record.

**Tech Stack:** Python/FastAPI/asyncpg (backend), Vue 3/TypeScript (frontend)

---

### Task 1: Add `deleted_at` column to database schema

**Files:**
- Modify: `backend/app/db.py:23-54` (create_table function)

**Step 1: Add `deleted_at` to CREATE TABLE**

In `backend/app/db.py`, update the `create_table` function. Add `deleted_at` to the CREATE TABLE statement and add a migration block for existing databases:

```python
async def create_table(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS youtube_summarizer.summaries (
            id               BIGSERIAL    PRIMARY KEY,
            video_id         TEXT         NOT NULL UNIQUE,
            title            TEXT,
            thumbnail_url    TEXT,
            summary          TEXT         NOT NULL,
            transcript       TEXT         NOT NULL,
            fallacy_analysis JSONB        DEFAULT NULL,
            created_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),
            deleted_at       TIMESTAMPTZ  DEFAULT NULL
        )
        """
    )
    # Add fallacy_analysis column to existing tables if it doesn't exist
    await conn.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'youtube_summarizer'
                AND table_name = 'summaries'
                AND column_name = 'fallacy_analysis'
            ) THEN
                ALTER TABLE youtube_summarizer.summaries
                ADD COLUMN fallacy_analysis JSONB DEFAULT NULL;
            END IF;
        END $$;
        """
    )
    # Add deleted_at column to existing tables if it doesn't exist
    await conn.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'youtube_summarizer'
                AND table_name = 'summaries'
                AND column_name = 'deleted_at'
            ) THEN
                ALTER TABLE youtube_summarizer.summaries
                ADD COLUMN deleted_at TIMESTAMPTZ DEFAULT NULL;
            END IF;
        END $$;
        """
    )
```

**Step 2: Verify the app starts without errors**

Run: `cd backend && python -c "from app.db import create_table; print('import ok')"`
Expected: `import ok`

**Step 3: Commit**

```bash
git add backend/app/db.py
git commit -m "feat: add deleted_at column to summaries table schema"
```

---

### Task 2: Add soft_delete and restore DB functions + filter deleted records

**Files:**
- Modify: `backend/app/db.py:80-96` (get_by_video_id, list_recent, get_full_record)

**Step 1: Add WHERE deleted_at IS NULL to existing queries**

Update `get_by_video_id` (line 80-86):

```python
async def get_by_video_id(
    conn: asyncpg.Connection, video_id: str
) -> VideoRecord | None:
    row = await conn.fetchrow(
        "SELECT * FROM youtube_summarizer.summaries WHERE video_id = $1 AND deleted_at IS NULL",
        video_id,
    )
    if row is None:
        return None
    return _parse_video_record(row)
```

Update `list_recent` (line 89-96):

```python
async def list_recent(conn: asyncpg.Connection, limit: int) -> list[HistoryItem]:
    rows = await conn.fetch(
        "SELECT video_id, title, thumbnail_url, summary, created_at, "
        "(fallacy_analysis IS NOT NULL) as has_fallacy_analysis "
        "FROM youtube_summarizer.summaries "
        "WHERE deleted_at IS NULL "
        "ORDER BY created_at DESC LIMIT $1",
        limit,
    )
    return [HistoryItem(**dict(row)) for row in rows]
```

Update `get_full_record` (line 99-105):

```python
async def get_full_record(
    conn: asyncpg.Connection, video_id: str
) -> VideoRecord | None:
    row = await conn.fetchrow(
        "SELECT * FROM youtube_summarizer.summaries WHERE video_id = $1 AND deleted_at IS NULL",
        video_id,
    )
    if row is None:
        return None
    return _parse_video_record(row)
```

**Step 2: Add soft_delete and restore functions**

Add at the end of `backend/app/db.py` (before `get_fallacy_analysis` or after `save_fallacy_analysis`):

```python
async def soft_delete(conn: asyncpg.Connection, video_id: str) -> bool:
    """Soft-delete a video record. Returns True if a record was deleted."""
    result = await conn.execute(
        "UPDATE youtube_summarizer.summaries SET deleted_at = now() "
        "WHERE video_id = $1 AND deleted_at IS NULL",
        video_id,
    )
    return result == "UPDATE 1"


async def restore(conn: asyncpg.Connection, video_id: str) -> HistoryItem | None:
    """Restore a soft-deleted video record. Returns the restored item or None."""
    row = await conn.fetchrow(
        "UPDATE youtube_summarizer.summaries SET deleted_at = NULL "
        "WHERE video_id = $1 AND deleted_at IS NOT NULL "
        "RETURNING video_id, title, thumbnail_url, summary, created_at, "
        "(fallacy_analysis IS NOT NULL) as has_fallacy_analysis",
        video_id,
    )
    if row is None:
        return None
    return HistoryItem(**dict(row))
```

**Step 3: Verify imports are clean**

Run: `cd backend && python -c "from app.db import soft_delete, restore; print('ok')"`
Expected: `ok`

**Step 4: Commit**

```bash
git add backend/app/db.py
git commit -m "feat: add soft_delete/restore DB functions and filter deleted records"
```

---

### Task 3: Add DELETE and restore API endpoints

**Files:**
- Modify: `backend/app/main.py:18-29` (imports), `backend/app/main.py:63-68` (CORS), and add new endpoints

**Step 1: Update imports in main.py**

Add `soft_delete` and `restore` to the db imports (line 18-29):

```python
from app.db import (
    close_pool,
    create_pool,
    create_table,
    get_by_video_id,
    get_db,
    get_fallacy_analysis,
    get_full_record,
    list_recent,
    restore,
    save_fallacy_analysis,
    save_record,
    soft_delete,
)
```

**Step 2: Update CORS to allow DELETE**

Change line 66 from:
```python
    allow_methods=["GET", "POST"],
```
to:
```python
    allow_methods=["GET", "POST", "DELETE"],
```

**Step 3: Add the DELETE endpoint**

Add after the `get_history_item` endpoint (after line 99):

```python
@app.delete("/api/history/{video_id}", status_code=204)
async def delete_history_item(
    video_id: str,
    conn: asyncpg.Connection = Depends(get_db),  # noqa: B008
) -> None:
    deleted = await soft_delete(conn, video_id)
    if not deleted:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="not_found",
                message=f"No record found for video_id: {video_id}",
            ).model_dump(),
        )
```

**Step 4: Add the restore endpoint**

Add after the delete endpoint:

```python
@app.post("/api/history/{video_id}/restore", response_model=None)
async def restore_history_item(
    video_id: str,
    conn: asyncpg.Connection = Depends(get_db),  # noqa: B008
) -> HistoryItem | JSONResponse:
    item = await restore(conn, video_id)
    if item is None:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="not_found",
                message=f"No deleted record found for video_id: {video_id}",
            ).model_dump(),
        )
    return item
```

Note: Add `HistoryItem` to the models import if not already there (line 30-40). Check — it's currently imported as part of `HistoryResponse` usage but not directly. Add it:

```python
from app.models import (
    ErrorResponse,
    FallacyAnalysisRequest,
    FallacyAnalysisResult,
    HistoryItem,
    HistoryResponse,
    SummarizeRequest,
    SummarizeResponse,
    SummaryStats,
    VideoMetadata,
    VideoRecord,
)
```

**Step 5: Verify the app can start**

Run: `cd backend && python -c "from app.main import app; print('ok')"`
Expected: `ok`

**Step 6: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: add DELETE and restore API endpoints for history items"
```

---

### Task 4: Add delete and restore functions to frontend API service

**Files:**
- Modify: `frontend/src/services/api.ts`

**Step 1: Add deleteHistoryItem function**

Add at the end of `frontend/src/services/api.ts`:

```typescript
export async function deleteHistoryItem(videoId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/history/${videoId}`, {
    method: "DELETE",
  });

  if (!response.ok && response.status !== 204) {
    let errorResponse: ErrorResponse;
    try {
      errorResponse = await response.json();
    } catch {
      errorResponse = {
        error: "internal_error",
        message: "Failed to delete video.",
        details: null,
      };
    }
    throw new ApiError(errorResponse);
  }
}

export async function restoreHistoryItem(
  videoId: string,
): Promise<HistoryItem> {
  const response = await fetch(`${API_BASE}/api/history/${videoId}/restore`, {
    method: "POST",
  });

  if (!response.ok) {
    let errorResponse: ErrorResponse;
    try {
      errorResponse = await response.json();
    } catch {
      errorResponse = {
        error: "internal_error",
        message: "Failed to restore video.",
        details: null,
      };
    }
    throw new ApiError(errorResponse);
  }

  return response.json();
}
```

**Step 2: Add HistoryItem to the type import**

Update the import at the top of `api.ts`:

```typescript
import type {
  SummarizeResponse,
  FallacyAnalysisResult,
  ErrorResponse,
  HistoryResponse,
  HistoryItem,
  VideoRecord,
} from "@/types";
```

**Step 3: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

**Step 4: Commit**

```bash
git add frontend/src/services/api.ts
git commit -m "feat: add deleteHistoryItem and restoreHistoryItem API functions"
```

---

### Task 5: Add delete button to HistoryCard

**Files:**
- Modify: `frontend/src/components/HistoryCard.vue`

**Step 1: Add delete emit and handler**

Replace the full `<script setup>` block:

```vue
<script setup lang="ts">
import type { HistoryItem } from "@/types";

defineProps<{ item: HistoryItem }>();
const emit = defineEmits<{
  select: [videoId: string];
  delete: [videoId: string];
}>();

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function handleDelete(event: Event, videoId: string) {
  event.stopPropagation();
  emit("delete", videoId);
}
</script>
```

**Step 2: Add delete button to template**

Replace the template with:

```vue
<template>
  <div class="history-card" @click="emit('select', item.video_id)">
    <img
      v-if="item.thumbnail_url"
      :src="item.thumbnail_url"
      :alt="item.title ?? 'Video thumbnail'"
      class="history-card__thumb"
      width="88"
      height="50"
      @error="($event.target as HTMLImageElement).style.display = 'none'"
    />
    <div class="history-card__body">
      <p class="history-card__title">{{ item.title ?? item.video_id }}</p>
      <p class="history-card__summary">{{ item.summary }}</p>
      <span class="history-card__date">{{ formatDate(item.created_at) }}</span>
    </div>
    <button
      class="history-card__delete"
      aria-label="Remove from history"
      @click="handleDelete($event, item.video_id)"
    >
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="18" y1="6" x2="6" y2="18" />
        <line x1="6" y1="6" x2="18" y2="18" />
      </svg>
    </button>
  </div>
</template>
```

**Step 3: Add styles for the delete button**

Add these styles inside the `<style scoped>` block:

```css
.history-card {
  position: relative;
}

.history-card__delete {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  padding: 0;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 4px;
  color: #B8B2A6;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s, color 0.15s, background 0.15s;
}

.history-card:hover .history-card__delete {
  opacity: 1;
}

.history-card__delete:hover {
  color: #C45D3E;
  background: #FFF5F3;
  border-color: rgba(196, 93, 62, 0.2);
}

/* Always show on touch devices */
@media (hover: none) {
  .history-card__delete {
    opacity: 1;
  }
}
```

**Step 4: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

**Step 5: Commit**

```bash
git add frontend/src/components/HistoryCard.vue
git commit -m "feat: add delete button to HistoryCard with hover reveal"
```

---

### Task 6: Add optimistic delete with undo toast to HistoryPanel

**Files:**
- Modify: `frontend/src/components/HistoryPanel.vue`

**Step 1: Replace the full script block**

```vue
<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import type { HistoryItem } from "@/types";
import { fetchHistory, deleteHistoryItem, restoreHistoryItem } from "@/services/api";
import HistoryCard from "./HistoryCard.vue";

const historyItems = ref<HistoryItem[]>([]);
const historyLoading = ref(false);
const historyError = ref<string | null>(null);

// Undo toast state
const undoToast = ref<{
  videoId: string;
  item: HistoryItem;
  index: number;
} | null>(null);
let undoTimer: ReturnType<typeof setTimeout> | null = null;

async function loadHistory(): Promise<void> {
  historyLoading.value = true;
  historyError.value = null;
  try {
    const data = await fetchHistory(50);
    historyItems.value = data.items;
  } catch {
    historyError.value = "Could not load history.";
  } finally {
    historyLoading.value = false;
  }
}

function commitPendingDelete() {
  if (undoTimer) {
    clearTimeout(undoTimer);
    undoTimer = null;
  }
  undoToast.value = null;
}

async function handleDelete(videoId: string) {
  // If there's a pending undo, commit it first
  commitPendingDelete();

  const index = historyItems.value.findIndex((i) => i.video_id === videoId);
  if (index === -1) return;

  const item = historyItems.value[index];

  // Optimistically remove
  historyItems.value.splice(index, 1);

  // Show undo toast
  undoToast.value = { videoId, item, index };

  // Fire API call in background
  try {
    await deleteHistoryItem(videoId);
  } catch {
    // Restore on failure
    historyItems.value.splice(index, 0, item);
    undoToast.value = null;
    historyError.value = "Failed to delete. Please try again.";
    return;
  }

  // Auto-dismiss after 5 seconds
  undoTimer = setTimeout(() => {
    undoToast.value = null;
  }, 5000);
}

async function handleUndo() {
  if (!undoToast.value) return;

  const { videoId, item, index } = undoToast.value;
  commitPendingDelete();

  try {
    await restoreHistoryItem(videoId);
    // Re-insert at original position (clamped to list length)
    const insertAt = Math.min(index, historyItems.value.length);
    historyItems.value.splice(insertAt, 0, item);
  } catch {
    historyError.value = "Failed to undo. Please reload.";
  }
}

onMounted(loadHistory);
onUnmounted(() => {
  if (undoTimer) clearTimeout(undoTimer);
});

defineExpose({ reload: loadHistory });
const emit = defineEmits<{ selectVideo: [videoId: string]; close: [] }>();
</script>
```

**Step 2: Update the template to include undo toast and delete event**

```vue
<template>
  <aside class="history-panel">
    <div class="history-panel__heading">
      <h2>Recent Videos</h2>
      <button class="history-panel__close" aria-label="Close history" @click="emit('close')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </div>

    <div v-if="historyLoading" class="history-panel__status">
      Loading history...
    </div>

    <div
      v-else-if="historyError"
      class="history-panel__status history-panel__status--error"
    >
      {{ historyError }}
      <button class="history-panel__retry" @click="loadHistory">Retry</button>
    </div>

    <div v-else-if="historyItems.length === 0 && !undoToast" class="history-panel__status">
      No summaries yet.
    </div>

    <ul v-else class="history-panel__list">
      <li v-for="item in historyItems" :key="item.video_id">
        <HistoryCard
          :item="item"
          @select="emit('selectVideo', $event)"
          @delete="handleDelete"
        />
      </li>
    </ul>

    <Transition name="toast">
      <div v-if="undoToast" class="history-panel__toast">
        <span>Video removed.</span>
        <button class="history-panel__undo" @click="handleUndo">Undo</button>
      </div>
    </Transition>
  </aside>
</template>
```

**Step 3: Add toast styles**

Add these styles to the `<style scoped>` block:

```css
.history-panel__toast {
  position: sticky;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1.25rem;
  background: #2C2C2C;
  color: #FFFFFF;
  font-size: 0.8rem;
  border-radius: 0 0 12px 12px;
}

.history-panel__undo {
  padding: 0.25rem 0.75rem;
  background: none;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 100px;
  color: #FFFFFF;
  font-size: 0.75rem;
  font-family: 'DM Sans', sans-serif;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.history-panel__undo:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.5);
}

.toast-enter-active {
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.toast-leave-active {
  transition: all 0.2s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.toast-leave-to {
  opacity: 0;
}
```

**Step 4: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

**Step 5: Commit**

```bash
git add frontend/src/components/HistoryPanel.vue frontend/src/components/HistoryCard.vue
git commit -m "feat: add optimistic delete with undo toast to history panel"
```

---

### Task 7: Manual smoke test

**Step 1: Start the backend**

Run: `cd backend && uvicorn app.main:app --reload`

**Step 2: Start the frontend**

Run: `cd frontend && npm run dev`

**Step 3: Verify the following in the browser**

1. Open History drawer — videos load normally
2. Hover over a card — X button appears in top-right
3. Click X — card disappears immediately, dark toast appears at bottom: "Video removed. Undo"
4. Click Undo within 5 seconds — card reappears at its original position
5. Delete a card and wait 5+ seconds — toast disappears, card stays gone
6. Reload the page — deleted card is still gone (soft-deleted in DB)
7. Re-summarize a previously deleted video — it generates a fresh summary (not cached)
8. Delete while another undo toast is showing — first delete commits, new toast appears

**Step 4: Final commit if any adjustments were needed**

```bash
git add -A
git commit -m "feat: complete delete-from-history feature"
```
