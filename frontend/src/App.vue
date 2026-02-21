<script setup lang="ts">
import { ref } from "vue";
import type {
  SummarizeResponse,
  ErrorResponse,
  VideoMetadata,
  FallacyAnalysisResult,
} from "@/types";
import { summarizeVideo, analyzeFallacies, ApiError } from "@/services/api";
import UrlInput from "@/components/UrlInput.vue";
import LengthSlider from "@/components/LengthSlider.vue";
import LoadingState from "@/components/LoadingState.vue";
import SummaryDisplay from "@/components/SummaryDisplay.vue";
import FallacyDisplay from "@/components/FallacyDisplay.vue";
import FallacySummaryPanel from "@/components/FallacySummaryPanel.vue";
import ErrorMessage from "@/components/ErrorMessage.vue";

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
</script>

<template>
  <div id="app">
    <h1>YouTube Summarizer</h1>
    <UrlInput :loading="loading" @submit="handleSubmit" />
    <LengthSlider v-model="lengthPercent" :disabled="loading" />
    <LoadingState v-if="loading" />
    <ErrorMessage v-if="error" :error="error" @retry="handleRetry" />
    <SummaryDisplay v-if="summary" :summary="summary" :transcript="transcript ?? ''" :metadata="metadata" />
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
      @retry="() => { fallacyError = null; }"
    />
    <FallacySummaryPanel
      v-if="fallacyAnalysis"
      :summary="fallacyAnalysis.summary"
    />
    <FallacyDisplay
      v-if="fallacyAnalysis"
      :fallacies="fallacyAnalysis.fallacies"
    />
  </div>
</template>

<style scoped>
#app {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  padding: 2rem 1rem;
  min-height: 100vh;
  font-family:
    system-ui,
    -apple-system,
    sans-serif;
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
