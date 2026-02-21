<script setup lang="ts">
import { ref } from "vue";
import type {
  SummarizeResponse,
  ErrorResponse,
  VideoMetadata,
  FallacyAnalysisResult,
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

const loading = ref(false);
const lengthPercent = ref(25);
const summary = ref<string | null>(null);
const transcript = ref<string | null>(null);
const metadata = ref<VideoMetadata | null>(null);
const fallacyAnalysis = ref<FallacyAnalysisResult | null>(null);
const error = ref<ErrorResponse | null>(null);
const fallacyLoading = ref(false);
const submittedUrl = ref<string | null>(null);
const fallacyError = ref<ErrorResponse | null>(null);
const historyPanelRef = ref<InstanceType<typeof HistoryPanel> | null>(null);

async function handleSubmit(url: string) {
  loading.value = true;
  summary.value = null;
  transcript.value = null;
  metadata.value = null;
  fallacyAnalysis.value = null;
  error.value = null;
  fallacyError.value = null;
  submittedUrl.value = null;

  try {
    const response: SummarizeResponse = await summarizeVideo(
      url,
      lengthPercent.value,
    );
    summary.value = response.summary;
    transcript.value = response.transcript;
    metadata.value = response.metadata ?? null;
    submittedUrl.value = url;
    historyPanelRef.value?.reload();
  } catch (e) {
    if (e instanceof ApiError) {
      error.value = e.errorResponse;
    } else {
      error.value = {
        error: "internal_error",
        message: "An unexpected error occurred. Please try again.",
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
      fallacyError.value = {
        error: "internal_error",
        message: "An unexpected error occurred. Please try again.",
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

async function handleSelectVideo(videoId: string) {
  loading.value = true;
  summary.value = null;
  transcript.value = null;
  metadata.value = null;
  fallacyAnalysis.value = null;
  error.value = null;
  fallacyError.value = null;
  submittedUrl.value = `https://www.youtube.com/watch?v=${videoId}`;

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
  } catch (e) {
    if (e instanceof ApiError) {
      error.value = e.errorResponse;
    } else {
      error.value = {
        error: "internal_error",
        message: "An unexpected error occurred. Please try again.",
        details: null,
      };
    }
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div id="app">
    <HistoryPanel ref="historyPanelRef" @select-video="handleSelectVideo" />
    <main class="app-main">
      <h1>YouTube Summarizer</h1>
      <UrlInput :loading="loading" @submit="handleSubmit" />
      <LengthSlider v-model="lengthPercent" :disabled="loading" />
      <LoadingState v-if="loading" />
      <ErrorMessage v-if="error" :error="error" @retry="handleRetry" />
      <SummaryDisplay
        v-if="summary"
        :summary="summary"
        :transcript="transcript ?? ''"
        :metadata="metadata"
      />
      <button
        v-if="summary && !fallacyAnalysis && !fallacyLoading"
        class="analyze-button"
        @click="handleAnalyzeFallacies"
      >
        Analyze for Logical Fallacies
      </button>
      <LoadingState v-if="fallacyLoading" />
      <ErrorMessage
        v-if="fallacyError"
        :error="fallacyError"
        @retry="
          () => {
            fallacyError = null;
          }
        "
      />
      <FallacySummaryPanel
        v-if="fallacyAnalysis"
        :summary="fallacyAnalysis.summary"
      />
      <FallacyDisplay
        v-if="fallacyAnalysis"
        :fallacies="fallacyAnalysis.fallacies"
      />
    </main>
  </div>
</template>

<style scoped>
#app {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 1.5rem;
  padding: 2rem 1rem;
  min-height: 100vh;
  font-family:
    system-ui,
    -apple-system,
    sans-serif;
  align-items: start;
}

@media (max-width: 768px) {
  #app {
    grid-template-columns: 1fr;
  }
}

.app-main {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
}

h1 {
  font-size: 2rem;
  font-weight: 700;
  color: #1a202c;
  margin: 0;
}

.analyze-button {
  padding: 0.75rem 1.5rem;
  background-color: #e53e3e;
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}

.analyze-button:hover {
  background-color: #c53030;
}
</style>
