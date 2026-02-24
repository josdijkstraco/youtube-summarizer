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

<style scoped>
.history-card {
  position: relative;
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
</style>
