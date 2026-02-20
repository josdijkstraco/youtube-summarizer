<script setup lang="ts">
import { ref } from "vue";
import type {
  SummarizeResponse,
  ErrorResponse,
  VideoMetadata,
  FallacyAnalysisResult,
} from "@/types";
import { summarizeVideo, ApiError } from "@/services/api";
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
const metadata = ref<VideoMetadata | null>(null);
const fallacyAnalysis = ref<FallacyAnalysisResult | null>(null);
const error = ref<ErrorResponse | null>(null);

async function handleSubmit(url: string) {
  loading.value = true;
  summary.value = null;
  metadata.value = null;
  fallacyAnalysis.value = null;
  error.value = null;

  try {
    const response: SummarizeResponse = await summarizeVideo(
      url,
      lengthPercent.value,
    );
    summary.value = response.summary;
    metadata.value = response.metadata ?? null;
    fallacyAnalysis.value = response.fallacy_analysis ?? null;
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
    <SummaryDisplay v-if="summary" :summary="summary" :metadata="metadata" />
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
</style>
