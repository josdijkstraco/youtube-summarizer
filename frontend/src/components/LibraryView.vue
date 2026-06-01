<script setup lang="ts">
import { ref, onMounted } from "vue";
import type { DownloadedItem } from "@/types";
import { fetchDownloaded } from "@/services/api";
import VideoCard from "./VideoCard.vue";

const items = ref<DownloadedItem[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

async function load(): Promise<void> {
  loading.value = true;
  error.value = null;
  try {
    const data = await fetchDownloaded();
    items.value = data.items;
  } catch {
    error.value = "Could not load your library.";
  } finally {
    loading.value = false;
  }
}

onMounted(load);

function openPlayer(videoId: string) {
  window.open("/?watch=" + encodeURIComponent(videoId), "_blank", "noopener");
}
</script>

<template>
  <section class="library">
    <div class="library__inner">
      <h2 class="library__heading">Your Library</h2>

      <div v-if="loading" class="library__status">Loading your library…</div>

      <div v-else-if="error" class="library__status library__status--error">
        {{ error }}
        <button class="library__retry" @click="load">Retry</button>
      </div>

      <div v-else-if="items.length === 0" class="library__status">
        No downloaded videos yet — download a video from its summary to see it
        here.
      </div>

      <div v-else class="library__grid">
        <VideoCard
          v-for="item in items"
          :key="item.video_id"
          :item="item"
          @play="openPlayer"
        />
      </div>
    </div>
  </section>
</template>

<style scoped>
.library {
  padding: 1.5rem 1.25rem 2.5rem;
}

.library__inner {
  max-width: 1100px;
  margin: 0 auto;
}

.library__heading {
  font-family: "Syne", sans-serif;
  font-size: 1.5rem;
  font-weight: 600;
  color: #111827;
  margin: 0 0 1.25rem;
}

.library__status {
  padding: 1.5rem 0;
  font-size: 0.9rem;
  color: #6b7280;
  text-align: center;
}

.library__status--error {
  color: #dc2626;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.library__retry {
  padding: 0.35rem 0.85rem;
  background: #2563eb;
  color: #ffffff;
  border: none;
  border-radius: 100px;
  font-size: 0.75rem;
  font-family: "Manrope", sans-serif;
  cursor: pointer;
  transition: background 0.2s;
}

.library__retry:hover {
  background: #1d4ed8;
}

.library__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1.25rem;
}
</style>
