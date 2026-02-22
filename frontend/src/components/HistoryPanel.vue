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
</style>
