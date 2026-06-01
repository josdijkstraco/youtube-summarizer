<script setup lang="ts">
import type { DownloadedItem } from "@/types";
import { formatRelativeTime } from "@/utils/relativeTime";

const props = defineProps<{ item: DownloadedItem }>();
const emit = defineEmits<{ play: [videoId: string] }>();

function activate() {
  emit("play", props.item.video_id);
}
</script>

<template>
  <div
    class="video-card"
    role="button"
    tabindex="0"
    :aria-label="`Play ${item.title ?? item.video_id}`"
    @click="activate"
    @keydown.enter.prevent="activate"
    @keydown.space.prevent="activate"
  >
    <div class="video-card__thumb-wrap">
      <img
        v-if="item.thumbnail_url"
        :src="item.thumbnail_url"
        :alt="item.title ?? 'Video thumbnail'"
        class="video-card__thumb"
        @error="($event.target as HTMLImageElement).style.display = 'none'"
      />
    </div>
    <div class="video-card__body">
      <p class="video-card__title">{{ item.title ?? item.video_id }}</p>
      <span class="video-card__date">
        Downloaded {{ formatRelativeTime(item.downloaded_at) }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.video-card {
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  transition:
    transform 0.15s,
    box-shadow 0.15s,
    border-color 0.15s;
}

.video-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.1);
  border-color: rgba(0, 0, 0, 0.12);
}

.video-card:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
}

.video-card__thumb-wrap {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #f3f4f6;
}

.video-card__thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.video-card__body {
  padding: 0.75rem 0.85rem 0.9rem;
}

.video-card__title {
  margin: 0 0 0.35rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #111827;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.video-card__date {
  font-size: 0.7rem;
  color: #9ca3af;
}
</style>
