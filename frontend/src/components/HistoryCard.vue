<script setup lang="ts">
import type { HistoryItem } from "@/types";

defineProps<{ item: HistoryItem }>();
const emit = defineEmits<{ select: [videoId: string] }>();

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}
</script>

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
  </div>
</template>

<style scoped>
.history-card {
  display: flex;
  gap: 0.85rem;
  padding: 0.85rem 1.25rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  cursor: pointer;
  transition: background 0.15s;
}

.history-card:hover {
  background: #FAF9F6;
}

.history-card:last-child {
  border-bottom: none;
}

.history-card__thumb {
  flex-shrink: 0;
  width: 88px;
  height: 50px;
  object-fit: cover;
  border-radius: 6px;
}

.history-card__body {
  flex: 1;
  min-width: 0;
}

.history-card__title {
  margin: 0 0 0.2rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: #2C2C2C;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  line-height: 1.3;
}

.history-card__summary {
  margin: 0;
  font-size: 0.775rem;
  color: #8A8578;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.45;
}

.history-card__date {
  font-size: 0.675rem;
  color: #B8B2A6;
  margin-top: 0.2rem;
  display: inline-block;
}
</style>
