<script setup lang="ts">
import { ref } from "vue";
import type { VideoMetadata } from "@/types";

defineProps<{
  summary: string;
  transcript: string;
  metadata?: VideoMetadata | null;
}>();

const activeTab = ref<"summary" | "transcript">("summary");

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
      <div class="summary-display__meta-text">
        <h2 v-if="metadata.title" class="summary-display__title">
          {{ metadata.title }}
        </h2>
        <div class="summary-display__meta-row">
          <span v-if="metadata.channel_name" class="summary-display__channel">
            {{ metadata.channel_name }}
          </span>
          <span
            v-if="metadata.duration_seconds != null"
            class="summary-display__duration"
          >
            {{ formatDuration(metadata.duration_seconds) }}
          </span>
        </div>
      </div>
    </div>
    <div class="summary-display__tabs">
      <button
        :class="[
          'summary-display__tab',
          { 'is-active': activeTab === 'summary' },
        ]"
        @click="activeTab = 'summary'"
      >
        Summary
      </button>
      <button
        :class="[
          'summary-display__tab',
          { 'is-active': activeTab === 'transcript' },
        ]"
        @click="activeTab = 'transcript'"
      >
        Transcript
      </button>
    </div>
    <div class="summary-display__content">
      <template v-if="activeTab === 'summary'">
        <p
          v-for="(paragraph, index) in summary.split('\n\n')"
          :key="index"
          class="summary-display__paragraph"
        >
          {{ paragraph }}
        </p>
      </template>
      <p v-else class="summary-display__transcript">{{ transcript }}</p>
    </div>
  </div>
</template>

<style scoped>
.summary-display {
  width: 100%;
  max-width: 720px;
  background: #FFFFFF;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03), 0 6px 24px rgba(0, 0, 0, 0.02);
}

.summary-display__meta {
  display: flex;
  gap: 1rem;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  align-items: center;
}

.summary-display__thumbnail {
  width: 120px;
  height: 68px;
  object-fit: cover;
  border-radius: 8px;
  flex-shrink: 0;
}

.summary-display__meta-text {
  flex: 1;
  min-width: 0;
}

.summary-display__title {
  margin: 0 0 0.3rem;
  font-size: 1rem;
  font-weight: 600;
  color: #2C2C2C;
  line-height: 1.35;
}

.summary-display__meta-row {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.summary-display__channel {
  font-size: 0.8rem;
  color: #8A8578;
}

.summary-display__duration {
  font-size: 0.8rem;
  color: #B8B2A6;
  font-variant-numeric: tabular-nums;
}

.summary-display__tabs {
  display: flex;
  gap: 0;
  padding: 0 1.5rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.summary-display__tab {
  padding: 0.75rem 0;
  margin-right: 1.5rem;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  font-size: 0.85rem;
  font-weight: 500;
  font-family: 'DM Sans', sans-serif;
  color: #B8B2A6;
  cursor: pointer;
  transition: color 0.2s, border-color 0.2s;
}

.summary-display__tab:hover {
  color: #2C2C2C;
}

.summary-display__tab.is-active {
  color: #2C2C2C;
  border-bottom-color: #C45D3E;
}

.summary-display__content {
  padding: 1.5rem;
  line-height: 1.75;
  color: #3D3D3D;
  font-size: 0.95rem;
}

.summary-display__paragraph {
  margin: 0 0 1rem;
  white-space: pre-wrap;
}

.summary-display__paragraph:last-child {
  margin-bottom: 0;
}

.summary-display__transcript {
  margin: 0;
  white-space: pre-wrap;
  font-size: 0.875rem;
  line-height: 1.75;
  color: #5A5A5A;
}
</style>
