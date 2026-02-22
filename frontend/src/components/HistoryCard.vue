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
  <div class="history-card">
    <img
      v-if="item.thumbnail_url"
      :src="item.thumbnail_url"
      :alt="item.title ?? 'Video thumbnail'"
      class="history-card__thumb"
      width="80"
      height="45"
      @error="($event.target as HTMLImageElement).style.display = 'none'"
    />
    <div class="history-card__body">
      <a
        :href="`https://www.youtube.com/watch?v=${item.video_id}`"
        target="_blank"
        rel="noopener"
        class="history-card__title"
        >{{ item.title ?? item.video_id }}</a
      >
      <p class="history-card__summary">{{ item.summary }}</p>
      <div class="history-card__footer">
        <span class="history-card__date">{{
          formatDate(item.created_at)
        }}</span>
        <button
          class="history-card__view-btn"
          @click.stop="emit('select', item.video_id)"
        >
          View
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.history-card {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem;
  border-bottom: 1px solid #e2e8f0;
}

.history-card__thumb {
  flex-shrink: 0;
  width: 80px;
  height: 45px;
  object-fit: cover;
  border-radius: 4px;
}

.history-card__body {
  flex: 1;
  min-width: 0;
}

.history-card__title {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: #1a202c;
  text-decoration: none;
  margin-bottom: 0.25rem;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.history-card__title:hover {
  text-decoration: underline;
}

.history-card__summary {
  margin: 0;
  font-size: 0.8rem;
  color: #718096;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.history-card__footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.25rem;
}

.history-card__date {
  font-size: 0.7rem;
  color: #a0aec0;
}

.history-card__view-btn {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  background: #3182ce;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.history-card__view-btn:hover {
  background: #2c5282;
}
</style>
