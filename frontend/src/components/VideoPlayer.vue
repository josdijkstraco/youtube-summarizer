<script setup lang="ts">
import { ref, watch, onUnmounted } from "vue";
import type { DownloadStatus } from "@/types";
import { triggerDownload, getDownloadStatus, getStreamUrl } from "@/services/api";

const props = defineProps<{
  videoId: string;
}>();

type LocalStatus = "idle" | "pending" | "ready" | "error";

const status = ref<LocalStatus>("idle");
const errorMessage = ref<string | null>(null);
const isTriggering = ref(false);
let pollTimer: ReturnType<typeof setInterval> | null = null;

function stopPolling() {
  if (pollTimer !== null) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

function applyStatus(ds: DownloadStatus) {
  if (ds.status === "ready") {
    status.value = "ready";
    stopPolling();
  } else if (ds.status === "error") {
    status.value = "error";
    errorMessage.value = ds.error_message ?? "Download failed.";
    stopPolling();
  } else if (ds.status === "pending") {
    status.value = "pending";
  } else {
    status.value = "idle";
  }
}

async function checkInitialStatus() {
  try {
    const ds = await getDownloadStatus(props.videoId);
    applyStatus(ds);
    if (ds.status === "pending") startPolling();
  } catch {
    // No record yet — stay idle
  }
}

function startPolling() {
  stopPolling();
  pollTimer = setInterval(async () => {
    try {
      const ds = await getDownloadStatus(props.videoId);
      applyStatus(ds);
    } catch {
      stopPolling();
    }
  }, 2000);
}

async function handleDownload() {
  if (isTriggering.value) return;
  isTriggering.value = true;
  errorMessage.value = null;
  try {
    const ds = await triggerDownload(props.videoId);
    applyStatus(ds);
    if (ds.status === "pending") startPolling();
  } catch (err) {
    status.value = "error";
    errorMessage.value = err instanceof Error ? err.message : "Could not start download.";
  } finally {
    isTriggering.value = false;
  }
}

async function handleRetry() {
  status.value = "idle";
  errorMessage.value = null;
  await handleDownload();
}

// Re-check whenever videoId changes (different history item selected)
watch(
  () => props.videoId,
  () => {
    stopPolling();
    status.value = "idle";
    errorMessage.value = null;
    checkInitialStatus();
  },
  { immediate: true },
);

onUnmounted(stopPolling);
</script>

<template>
  <div class="video-player">
    <!-- Idle: no download yet -->
    <div v-if="status === 'idle'" class="video-player__idle">
      <p class="video-player__message">No video downloaded yet.</p>
      <p class="video-player__disclaimer">For personal / research use only.</p>
      <button
        class="video-player__btn video-player__btn--primary"
        :disabled="isTriggering"
        @click="handleDownload"
      >
        Download video
      </button>
    </div>

    <!-- Pending: download in progress -->
    <div v-else-if="status === 'pending'" class="video-player__pending">
      <div class="video-player__spinner" aria-label="Downloading…" />
      <p class="video-player__message">Downloading…</p>
    </div>

    <!-- Ready: video player -->
    <div v-else-if="status === 'ready'" class="video-player__ready">
      <video
        controls
        class="video-player__video"
        :src="getStreamUrl(videoId)"
      />
    </div>

    <!-- Error: message + retry -->
    <div v-else-if="status === 'error'" class="video-player__error">
      <p class="video-player__error-text">
        {{ errorMessage ?? "Download failed." }}
      </p>
      <button
        class="video-player__btn video-player__btn--primary"
        :disabled="isTriggering"
        @click="handleRetry"
      >
        Try again
      </button>
    </div>
  </div>
</template>

<style scoped>
.video-player {
  padding: 1.5rem;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.video-player__idle,
.video-player__pending,
.video-player__error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  text-align: center;
}

.video-player__message {
  margin: 0;
  font-size: 0.95rem;
  color: #6B7280;
}

.video-player__disclaimer {
  margin: 0;
  font-size: 0.75rem;
  color: #9CA3AF;
}

.video-player__error-text {
  margin: 0;
  font-size: 0.875rem;
  color: #B91C1C;
  max-width: 420px;
}

.video-player__btn {
  padding: 0.5rem 1.25rem;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  font-family: 'Manrope', sans-serif;
  cursor: pointer;
  transition: background 0.15s, opacity 0.15s;
}

.video-player__btn--primary {
  background: #2563EB;
  color: #fff;
}

.video-player__btn--primary:hover:not(:disabled) {
  background: #1D4ED8;
}

.video-player__btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Spinner */
.video-player__spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(37, 99, 235, 0.2);
  border-top-color: #2563EB;
  border-radius: 50%;
  animation: vp-spin 0.8s linear infinite;
}

@keyframes vp-spin {
  to { transform: rotate(360deg); }
}

/* Video element */
.video-player__ready {
  width: 100%;
}

.video-player__video {
  width: 100%;
  border-radius: 8px;
  background: #000;
  display: block;
}
</style>
