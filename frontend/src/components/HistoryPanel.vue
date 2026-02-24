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

<style scoped>
.history-panel {
  max-height: calc(100vh - 4rem);
  overflow-y: auto;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 12px;
  background: #FFFFFF;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
}

.history-panel__heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.history-panel__heading h2 {
  font-family: 'Instrument Serif', serif;
  font-size: 1.15rem;
  font-weight: 400;
  color: #2C2C2C;
  margin: 0;
}

.history-panel__close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  padding: 0;
  background: none;
  border: none;
  border-radius: 6px;
  color: #8A8578;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.history-panel__close:hover {
  background: #F0EDE7;
  color: #2C2C2C;
}

.history-panel__status {
  padding: 1.5rem 1.25rem;
  font-size: 0.85rem;
  color: #8A8578;
  text-align: center;
}

.history-panel__status--error {
  color: #C45D3E;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.history-panel__retry {
  padding: 0.35rem 0.85rem;
  background: #C45D3E;
  color: #FFFFFF;
  border: none;
  border-radius: 100px;
  font-size: 0.75rem;
  font-family: 'DM Sans', sans-serif;
  cursor: pointer;
  transition: background 0.2s;
}

.history-panel__retry:hover {
  background: #A84D33;
}

.history-panel__list {
  list-style: none;
  margin: 0;
  padding: 0;
}

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
</style>
