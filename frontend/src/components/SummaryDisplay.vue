<script setup lang="ts">
import type { VideoMetadata } from "@/types";

defineProps<{
  summary: string;
  metadata?: VideoMetadata | null;
}>();

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  const pad = (n: number) => String(n).padStart(2, "0");
  return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${m}:${pad(s)}`;
}
</script>

<template>
  <div class="summary-display">
    <div v-if="metadata" class="summary-display__meta">
      <img
        v-if="metadata.thumbnail_url"
        :src="metadata.thumbnail_url"
        :alt="metadata.title ?? 'Video thumbnail'"
        class="summary-display__thumbnail"
      />
      <h2 v-if="metadata.title" class="summary-display__title">
        {{ metadata.title }}
      </h2>
      <p v-if="metadata.channel_name" class="summary-display__channel">
        {{ metadata.channel_name }}
      </p>
      <p
        v-if="metadata.duration_seconds != null"
        class="summary-display__duration"
      >
        {{ formatDuration(metadata.duration_seconds) }}
      </p>
    </div>
    <h2 class="summary-display__heading">Summary</h2>
    <div class="summary-display__content">
      <p
        v-for="(paragraph, index) in summary.split('\n\n')"
        :key="index"
        class="summary-display__paragraph"
      >
        {{ paragraph }}
      </p>
    </div>
  </div>
</template>

<style scoped>
.summary-display {
  width: 100%;
  max-width: 640px;
  padding: 1.5rem;
  background-color: #f7fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.summary-display__meta {
  margin-bottom: 1.25rem;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid #e2e8f0;
}

.summary-display__thumbnail {
  width: 100%;
  border-radius: 6px;
  margin-bottom: 0.75rem;
}

.summary-display__title {
  margin: 0 0 0.25rem;
  font-size: 1.125rem;
  font-weight: 600;
  color: #1a202c;
}

.summary-display__channel {
  margin: 0 0 0.25rem;
  font-size: 0.875rem;
  color: #718096;
}

.summary-display__duration {
  margin: 0;
  font-size: 0.875rem;
  color: #a0aec0;
}

.summary-display__heading {
  margin: 0 0 1rem;
  font-size: 1.25rem;
  font-weight: 600;
  color: #2d3748;
}

.summary-display__content {
  line-height: 1.7;
  color: #4a5568;
}

.summary-display__paragraph {
  margin: 0 0 1rem;
  white-space: pre-wrap;
}

.summary-display__paragraph:last-child {
  margin-bottom: 0;
}
</style>
