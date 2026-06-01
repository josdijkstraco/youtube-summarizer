<script setup lang="ts">
import { ref, onMounted } from "vue";
import type {
  SummarizeResponse,
  SummaryStats,
  ErrorResponse,
  VideoMetadata,
  FallacyAnalysisResult,
  Highlight,
  QaMessage,
} from "@/types";
import {
  summarizeVideo,
  analyzeFallacies,
  fetchHistoryItem,
  ApiError,
} from "@/services/api";
import UrlInput from "@/components/UrlInput.vue";
import LengthSlider from "@/components/LengthSlider.vue";
import LoadingState from "@/components/LoadingState.vue";
import SummaryDisplay from "@/components/SummaryDisplay.vue";
import FallacyDisplay from "@/components/FallacyDisplay.vue";
import FallacySummaryPanel from "@/components/FallacySummaryPanel.vue";
import ErrorMessage from "@/components/ErrorMessage.vue";
import HistoryPanel from "@/components/HistoryPanel.vue";
import LibraryView from "@/components/LibraryView.vue";

const view = ref<"summarize" | "library" | "player">("summarize");
const loading = ref(false);
const lengthPercent = ref(25);
const summary = ref<string | null>(null);
const transcript = ref<string | null>(null);
const metadata = ref<VideoMetadata | null>(null);
const fallacyAnalysis = ref<FallacyAnalysisResult | null>(null);
const error = ref<ErrorResponse | null>(null);
const stats = ref<SummaryStats | null>(null);
const fallacyLoading = ref(false);
const submittedUrl = ref<string | null>(null);
const fallacyError = ref<ErrorResponse | null>(null);
const historyPanelRef = ref<InstanceType<typeof HistoryPanel> | null>(null);
const drawerOpen = ref(false);
const currentVideoId = ref<string | null>(null);
const currentHighlights = ref<Highlight[]>([]);
const currentQaHistory = ref<QaMessage[]>([]);
const currentNotes = ref<string | null>(null);

async function handleSubmit(url: string) {
  loading.value = true;
  summary.value = null;
  transcript.value = null;
  metadata.value = null;
  fallacyAnalysis.value = null;
  stats.value = null;
  error.value = null;
  fallacyError.value = null;
  submittedUrl.value = null;
  currentVideoId.value = null;
  currentHighlights.value = [];
  currentQaHistory.value = [];
  currentNotes.value = null;

  try {
    const response: SummarizeResponse = await summarizeVideo(
      url,
      lengthPercent.value,
    );
    summary.value = response.summary;
    transcript.value = response.transcript;
    metadata.value = response.metadata ?? null;
    stats.value = response.stats ?? null;
    submittedUrl.value = url;
    currentVideoId.value = response.metadata?.video_id ?? null;
    currentHighlights.value = response.highlights ?? [];
    currentNotes.value = response.notes ?? null;
    historyPanelRef.value?.reload();
  } catch (e) {
    if (e instanceof ApiError) {
      error.value = e.errorResponse;
    } else {
      const msg = e instanceof Error ? e.message : String(e);
      error.value = {
        error: "internal_error",
        message:
          msg === "Failed to fetch"
            ? "Could not reach the server. Check that the backend is running."
            : `Unexpected error: ${msg}`,
        details: null,
      };
    }
  } finally {
    loading.value = false;
  }
}

async function handleAnalyzeFallacies() {
  if (!submittedUrl.value) return;
  fallacyLoading.value = true;
  fallacyError.value = null;
  try {
    fallacyAnalysis.value = await analyzeFallacies(submittedUrl.value);
  } catch (e) {
    if (e instanceof ApiError) {
      fallacyError.value = e.errorResponse;
    } else {
      const msg = e instanceof Error ? e.message : String(e);
      fallacyError.value = {
        error: "internal_error",
        message:
          msg === "Failed to fetch"
            ? "Could not reach the server. Check that the backend is running."
            : `Unexpected error: ${msg}`,
        details: null,
      };
    }
  } finally {
    fallacyLoading.value = false;
  }
}

function handleRetry() {
  error.value = null;
}

function goTo(v: "summarize" | "library" | "player") {
  if (view.value === "player" && v !== "player") {
    window.history.replaceState({}, "", "/");
  }
  view.value = v;
}

async function handleSelectVideo(videoId: string) {
  drawerOpen.value = false;
  loading.value = true;
  summary.value = null;
  transcript.value = null;
  metadata.value = null;
  fallacyAnalysis.value = null;
  stats.value = null;
  error.value = null;
  fallacyError.value = null;
  submittedUrl.value = `https://www.youtube.com/watch?v=${videoId}`;
  currentVideoId.value = null;
  currentHighlights.value = [];
  currentQaHistory.value = [];
  currentNotes.value = null;

  try {
    const record = await fetchHistoryItem(videoId);
    summary.value = record.summary;
    transcript.value = record.transcript;
    metadata.value = {
      video_id: record.video_id,
      title: record.title,
      thumbnail_url: record.thumbnail_url,
      channel_name: null,
      duration_seconds: null,
    };
    currentVideoId.value = record.video_id;
    currentHighlights.value = record.highlights ?? [];
    currentQaHistory.value = record.qa_history ?? [];
    currentNotes.value = record.notes ?? null;
    if (record.fallacy_analysis) {
      fallacyAnalysis.value = record.fallacy_analysis;
    }
  } catch (e) {
    if (e instanceof ApiError) {
      error.value = e.errorResponse;
    } else {
      const msg = e instanceof Error ? e.message : String(e);
      error.value = {
        error: "internal_error",
        message:
          msg === "Failed to fetch"
            ? "Could not reach the server. Check that the backend is running."
            : `Unexpected error: ${msg}`,
        details: null,
      };
    }
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  const watch = new URLSearchParams(window.location.search).get("watch");
  if (watch) {
    view.value = "player";
    handleSelectVideo(watch);
  }
});
</script>

<template>
  <div id="app">
    <nav class="app-nav">
      <span class="app-nav__brand">YouTube Summarizer</span>
      <div class="app-nav__links">
        <button
          type="button"
          class="app-nav__link"
          :class="{ 'is-active': view === 'summarize' }"
          @click="goTo('summarize')"
        >
          Summarize
        </button>
        <button
          type="button"
          class="app-nav__link"
          :class="{ 'is-active': view === 'library' }"
          @click="goTo('library')"
        >
          Library
        </button>
      </div>
    </nav>

    <template v-if="view === 'summarize'">
      <div
        class="drawer-overlay"
        :class="{ 'drawer-overlay--visible': drawerOpen }"
        @click="drawerOpen = false"
      ></div>
      <div class="drawer" :class="{ 'drawer--open': drawerOpen }">
        <button
          v-show="!drawerOpen"
          aria-label="Open history"
          class="drawer-tab"
          @click="drawerOpen = true"
        >
          <svg
            class="drawer-tab__icon"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <polyline points="9 18 15 12 9 6" />
          </svg>
          <span class="drawer-tab__label">History</span>
        </button>
        <div class="drawer__scroll">
          <HistoryPanel
            ref="historyPanelRef"
            @select-video="handleSelectVideo"
            @close="drawerOpen = false"
          />
        </div>
      </div>
      <main class="app-main">
        <header class="app-header">
          <h1 class="app-title">
            YouTube<br /><span class="app-title__accent">Summarizer</span>
          </h1>
          <p class="app-subtitle">Paste a link. Get the essence.</p>
        </header>
        <div class="app-controls">
          <UrlInput :loading="loading" @submit="handleSubmit" />
          <LengthSlider v-model="lengthPercent" :disabled="loading" />
        </div>
        <LoadingState v-if="loading" />
        <ErrorMessage v-if="error" :error="error" @retry="handleRetry" />
        <Transition name="fade-up">
          <SummaryDisplay
            v-if="summary"
            :summary="summary"
            :transcript="transcript ?? ''"
            :metadata="metadata"
            :stats="stats"
            :video-id="currentVideoId"
            :initial-highlights="currentHighlights"
            :initial-qa-history="currentQaHistory"
            :initial-notes="currentNotes"
          />
        </Transition>
        <Transition name="fade-up">
          <button
            v-if="summary && !fallacyAnalysis && !fallacyLoading"
            class="analyze-button"
            @click="handleAnalyzeFallacies"
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            Analyze for Logical Fallacies
          </button>
        </Transition>
        <LoadingState
          v-if="fallacyLoading"
          message="Analyzing for fallacies..."
        />
        <ErrorMessage
          v-if="fallacyError"
          :error="fallacyError"
          @retry="
            () => {
              fallacyError = null;
            }
          "
        />
        <Transition name="fade-up">
          <FallacySummaryPanel
            v-if="fallacyAnalysis"
            :summary="fallacyAnalysis.summary"
          />
        </Transition>
        <Transition name="fade-up">
          <FallacyDisplay
            v-if="fallacyAnalysis"
            :fallacies="fallacyAnalysis.fallacies"
          />
        </Transition>
      </main>
    </template>

    <main v-else-if="view === 'library'" class="app-main app-main--library">
      <LibraryView />
    </main>

    <main v-else-if="view === 'player'" class="app-main">
      <LoadingState v-if="loading" />
      <ErrorMessage v-if="error" :error="error" @retry="handleRetry" />
      <SummaryDisplay
        v-if="summary"
        :summary="summary"
        :transcript="transcript ?? ''"
        :metadata="metadata"
        :stats="stats"
        :video-id="currentVideoId"
        :initial-highlights="currentHighlights"
        :initial-qa-history="currentQaHistory"
        :initial-notes="currentNotes"
        :initial-tab="'video'"
      />
    </main>
  </div>
</template>

<style scoped>
#app {
  display: grid;
  grid-template-columns: 1fr;
  min-height: 100vh;
  align-items: start;
}

/* ---- Nav ---- */
.app-nav {
  position: sticky;
  top: 0;
  z-index: 1100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.85rem 1.5rem;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.07);
}

.app-nav__brand {
  font-family: "Syne", sans-serif;
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: #111827;
}

.app-nav__links {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.app-nav__link {
  padding: 0.4rem 0.9rem;
  background: transparent;
  border: none;
  border-radius: 100px;
  font-family: "Manrope", sans-serif;
  font-size: 0.85rem;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  transition:
    color 0.2s,
    background 0.2s;
}

.app-nav__link:hover {
  color: #111827;
  background: #f3f4f6;
}

.app-nav__link.is-active {
  color: #2563eb;
  font-weight: 600;
}

/* ---- Drawer ---- */
.drawer-tab {
  position: absolute;
  right: -2.75rem;
  top: 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  width: 2.75rem;
  padding: 0.7rem 0.5rem;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-left: none;
  border-radius: 0 10px 10px 0;
  cursor: pointer;
  box-shadow: 2px 2px 12px rgba(0, 0, 0, 0.04);
  transition:
    background 0.2s,
    box-shadow 0.2s;
}

.drawer-tab:hover {
  background: #f3f4f6;
  box-shadow: 2px 2px 16px rgba(0, 0, 0, 0.07);
}

.drawer-tab__icon {
  color: #6b7280;
}

.drawer-tab__label {
  font-size: 0.6rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #6b7280;
  writing-mode: vertical-rl;
  font-family: "Manrope", sans-serif;
}

.drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.25);
  backdrop-filter: blur(2px);
  z-index: 999;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s;
}

.drawer-overlay--visible {
  opacity: 1;
  pointer-events: auto;
}

.drawer {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 520px;
  z-index: 1000;
  transform: translateX(-100%);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: visible;
}

.drawer--open {
  transform: translateX(0);
}

.drawer__scroll {
  height: 100%;
  overflow-y: auto;
  padding: 1rem;
}

/* ---- Main Content ---- */
.app-main {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
  padding: 4rem 1.5rem 6rem;
  max-width: 720px;
  margin: 0 auto;
  width: 100%;
}

.app-main--library {
  max-width: 1100px;
  padding-top: 2rem;
}

.app-header {
  text-align: center;
  animation: fadeIn 0.6s ease-out;
}

.app-title {
  font-family: "Syne", sans-serif;
  font-size: 3.25rem;
  font-weight: 700;
  line-height: 1.1;
  color: #111827;
  letter-spacing: -0.02em;
}

.app-title__accent {
  color: #2563eb;
}

.app-subtitle {
  margin-top: 0.75rem;
  font-size: 1.05rem;
  font-weight: 300;
  color: #6b7280;
  letter-spacing: 0.02em;
}

.app-controls {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.25rem;
  width: 100%;
}

/* ---- Analyze Button ---- */
.analyze-button {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.75rem;
  background: transparent;
  color: #2563eb;
  border: 1.5px solid #2563eb;
  border-radius: 100px;
  font-size: 0.9rem;
  font-weight: 500;
  font-family: "Manrope", sans-serif;
  cursor: pointer;
  transition: all 0.25s ease;
  letter-spacing: 0.01em;
}

.analyze-button:hover {
  background: #2563eb;
  color: #ffffff;
}

/* ---- Transitions ---- */
.fade-up-enter-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.fade-up-leave-active {
  transition: all 0.2s ease;
}

.fade-up-enter-from {
  opacity: 0;
  transform: translateY(12px);
}

.fade-up-leave-to {
  opacity: 0;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 600px) {
  .app-title {
    font-size: 2.5rem;
  }

  .app-main {
    padding: 2.5rem 1rem 4rem;
  }
}
</style>
