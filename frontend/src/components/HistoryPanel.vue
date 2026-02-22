<script setup lang="ts">
import { ref, onMounted } from "vue";
import type { HistoryItem } from "@/types";
import { fetchHistory } from "@/services/api";
import HistoryCard from "./HistoryCard.vue";

const historyItems = ref<HistoryItem[]>([]);
const historyLoading = ref(false);
const historyError = ref<string | null>(null);

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

onMounted(loadHistory);

defineExpose({ reload: loadHistory });
const emit = defineEmits<{ selectVideo: [videoId: string]; close: [] }>();
</script>

<template>
  <aside class="history-panel">
    <div class="history-panel__heading">
      <h2>Recent Videos</h2>
      <button class="history-panel__close" aria-label="Close history" @click="emit('close')">✕</button>
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

    <div v-else-if="historyItems.length === 0" class="history-panel__status">
      No summaries yet.
    </div>

    <ul v-else class="history-panel__list">
      <li v-for="item in historyItems" :key="item.video_id">
        <HistoryCard :item="item" @select="emit('selectVideo', $event)" />
      </li>
    </ul>
  </aside>
</template>

<style scoped>
.history-panel {
  max-height: calc(100vh - 4rem);
  overflow-y: auto;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
}

.history-panel__heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e2e8f0;
  background: #fff;
}

.history-panel__heading h2 {
  font-size: 1rem;
  font-weight: 700;
  color: #1a202c;
  margin: 0;
}

.history-panel__close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.75rem;
  height: 1.75rem;
  padding: 0;
  background: none;
  border: none;
  border-radius: 4px;
  font-size: 0.9rem;
  color: #718096;
  cursor: pointer;
  line-height: 1;
}

.history-panel__close:hover {
  background: #edf2f7;
  color: #1a202c;
}

.history-panel__status {
  padding: 1rem;
  font-size: 0.875rem;
  color: #718096;
  text-align: center;
}

.history-panel__status--error {
  color: #e53e3e;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.history-panel__retry {
  padding: 0.25rem 0.75rem;
  background: #e53e3e;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 0.8rem;
  cursor: pointer;
}

.history-panel__retry:hover {
  background: #c53030;
}

.history-panel__list {
  list-style: none;
  margin: 0;
  padding: 0;
}
</style>
