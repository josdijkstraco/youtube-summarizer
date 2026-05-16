<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from "vue";
import type { DownloadStatus } from "@/types";
import { triggerDownload, getDownloadStatus, getStreamUrl, deleteDownload } from "@/services/api";
import Toast from "@/components/Toast.vue";

const props = defineProps<{
  videoId: string;
}>();

type LocalStatus = "idle" | "pending" | "ready" | "error";

const status = ref<LocalStatus>("idle");
const errorMessage = ref<string | null>(null);
const isTriggering = ref(false);
const isDeleting = ref(false);
const showDeleteModal = ref(false);
const showToast = ref(false);
const toastMessage = ref("");
const toastType = ref<"success" | "error" | "info">("success");
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

async function handleDelete() {
  isDeleting.value = true;
  errorMessage.value = null;
  try {
    await deleteDownload(props.videoId);
    showDeleteModal.value = false;
    isDeleting.value = false;
    status.value = "idle";
    toastMessage.value = "Video deleted successfully";
    toastType.value = "success";
    showToast.value = true;
  } catch (err) {
    isDeleting.value = false;
    showDeleteModal.value = false;
    toastMessage.value = err instanceof Error ? err.message : "Failed to delete video.";
    toastType.value = "error";
    showToast.value = true;
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === "Escape" && showDeleteModal.value && !isDeleting.value) {
    showDeleteModal.value = false;
  }
}

onMounted(() => document.addEventListener("keydown", onKeydown));

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

onUnmounted(() => {
  stopPolling();
  document.removeEventListener("keydown", onKeydown);
});
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
      <div class="video-player__ready-actions">
        <button
          class="video-player__btn video-player__btn--destructive"
          @click="showDeleteModal = true"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
          Delete video
        </button>
      </div>
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

  <!-- Toast notification -->
  <Toast
    v-if="showToast"
    :message="toastMessage"
    :type="toastType"
    @dismiss="showToast = false"
  />

  <!-- Confirmation modal -->
  <Teleport to="body">
    <div
      v-if="showDeleteModal"
      class="vp-modal-overlay"
      @click.self="!isDeleting && (showDeleteModal = false)"
    >
      <div class="vp-modal" role="dialog" aria-modal="true" aria-labelledby="vp-modal-title">
        <h3 id="vp-modal-title" class="vp-modal__title">Delete video</h3>
        <p class="vp-modal__message">
          Are you sure you want to delete this downloaded video? You can re-download it later.
        </p>
        <div class="vp-modal__actions">
          <button
            class="video-player__btn vp-modal__btn--cancel"
            :disabled="isDeleting"
            @click="showDeleteModal = false"
          >
            Cancel
          </button>
          <button
            class="video-player__btn video-player__btn--destructive"
            :disabled="isDeleting"
            @click="handleDelete"
          >
            <span v-if="isDeleting" class="vp-modal__btn-spinner" aria-hidden="true" />
            <span>{{ isDeleting ? "Deleting…" : "Delete" }}</span>
          </button>
        </div>
      </div>
    </div>
  </Teleport>
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

.video-player__btn--destructive {
  background: #DC2626;
  color: #fff;
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
}

.video-player__btn--destructive:hover:not(:disabled) {
  background: #B91C1C;
}

.video-player__btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.video-player__ready-actions {
  display: flex;
  justify-content: flex-start;
  margin-top: 0.75rem;
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

/* Inline button spinner */
.vp-modal__btn-spinner {
  display: inline-block;
  width: 13px;
  height: 13px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: #fff;
  border-radius: 50%;
  animation: vp-spin 0.7s linear infinite;
  vertical-align: middle;
  margin-right: 6px;
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

/* Confirmation modal */
.vp-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.vp-modal {
  background: #fff;
  border-radius: 12px;
  padding: 1.5rem;
  width: min(420px, 90vw);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.vp-modal__title {
  margin: 0 0 0.75rem;
  font-size: 1.1rem;
  font-weight: 700;
  color: #111827;
  font-family: 'Manrope', sans-serif;
}

.vp-modal__message {
  margin: 0 0 1.25rem;
  font-size: 0.875rem;
  color: #6B7280;
  line-height: 1.5;
}

.vp-modal__actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.vp-modal__btn--cancel {
  background: #F3F4F6;
  color: #374151;
}

.vp-modal__btn--cancel:hover:not(:disabled) {
  background: #E5E7EB;
}
</style>
