<script setup lang="ts">
import { ref, watch, onUnmounted } from "vue";
import type { DownloadStatusResponse } from "@/types";
import { triggerDownload, getDownloadStatus, getStreamUrl } from "@/services/api";

const props = defineProps<{
  videoId: string;
  initialStatus?: DownloadStatusResponse | null;
}>();

type PlayerState = "idle" | "polling" | "ready" | "error";

const state = ref<PlayerState>("idle");
const errorMessage = ref<string | null>(null);
let pollTimer: ReturnType<typeof setInterval> | null = null;

function resolveInitialState() {
  const s = props.initialStatus?.status ?? null;
  if (s === "ready") return "ready" as PlayerState;
  if (s === "pending") return "polling" as PlayerState;
  if (s === "error") return "error" as PlayerState;
  return "idle" as PlayerState;
}

state.value = resolveInitialState();
if (state.value === "polling") startPolling();

watch(
  () => [props.videoId, props.initialStatus] as const,
  () => {
    stopPolling();
    errorMessage.value = null;
    state.value = resolveInitialState();
    if (state.value === "polling") startPolling();
  },
);

async function handleDownload() {
  errorMessage.value = null;
  try {
    await triggerDownload(props.videoId);
  } catch {
    // 409 (already in progress) is handled by status polling, not an error
  }
  state.value = "polling";
  startPolling();
}

async function handleRetry() {
  errorMessage.value = null;
  state.value = "polling";
  try {
    await triggerDownload(props.videoId);
  } catch {
    // continue polling regardless
  }
  startPolling();
}

function startPolling() {
  stopPolling();
  pollTimer = setInterval(async () => {
    try {
      const res = await getDownloadStatus(props.videoId);
      if (res.status === "ready") {
        stopPolling();
        state.value = "ready";
      } else if (res.status === "error") {
        stopPolling();
        errorMessage.value = "Download failed. Please try again.";
        state.value = "error";
      }
    } catch {
      // transient error — keep polling
    }
  }, 2000);
}

function stopPolling() {
  if (pollTimer !== null) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

onUnmounted(stopPolling);
</script>

<template>
  <div class="video-player">
    <!-- Ready: show player -->
    <template v-if="state === 'ready'">
      <video
        class="video-player__video"
        controls
        preload="metadata"
        :src="getStreamUrl(videoId)"
      />
    </template>

    <!-- Polling: show spinner -->
    <template v-else-if="state === 'polling'">
      <div class="video-player__status">
        <span class="video-player__spinner" aria-hidden="true" />
        <span class="video-player__status-text">Downloading…</span>
      </div>
    </template>

    <!-- Error: show message + retry -->
    <template v-else-if="state === 'error'">
      <div class="video-player__status video-player__status--error">
        <p class="video-player__error-msg">{{ errorMessage ?? "Download failed." }}</p>
        <button class="video-player__btn" @click="handleRetry">Try again</button>
      </div>
    </template>

    <!-- Idle: show download button -->
    <template v-else>
      <div class="video-player__status">
        <p class="video-player__hint">No video downloaded yet.</p>
        <button class="video-player__btn video-player__btn--primary" @click="handleDownload">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          Download video
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.video-player {
  width: 100%;
  padding: 1.5rem;
}

.video-player__video {
  width: 100%;
  border-radius: 8px;
  background: #000;
  display: block;
}

.video-player__status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 2.5rem 1rem;
  text-align: center;
}

.video-player__status--error {
  gap: 0.75rem;
}

.video-player__hint {
  margin: 0;
  font-size: 0.9rem;
  color: #6B7280;
}

.video-player__error-msg {
  margin: 0;
  font-size: 0.9rem;
  color: #B91C1C;
}

.video-player__status-text {
  font-size: 0.875rem;
  color: #6B7280;
  font-family: 'Manrope', sans-serif;
}

.video-player__btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 1.25rem;
  background: transparent;
  color: #2563EB;
  border: 1.5px solid #2563EB;
  border-radius: 100px;
  font-size: 0.875rem;
  font-weight: 500;
  font-family: 'Manrope', sans-serif;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.video-player__btn:hover {
  background: #2563EB;
  color: #fff;
}

.video-player__btn--primary {
  padding: 0.6rem 1.5rem;
}

/* Spinner */
.video-player__spinner {
  display: inline-block;
  width: 28px;
  height: 28px;
  border: 3px solid rgba(37, 99, 235, 0.2);
  border-top-color: #2563EB;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
