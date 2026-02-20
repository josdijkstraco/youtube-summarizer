<script setup lang="ts">
import type { Fallacy } from "@/types";

defineProps<{
  fallacies: Fallacy[];
}>();
</script>

<template>
  <div class="fallacy-display">
    <h2 class="fallacy-display__heading">Fallacy Analysis</h2>
    <p v-if="fallacies.length === 0" class="fallacy-display__empty">
      No fallacies found in this transcript.
    </p>
    <div
      v-for="(fallacy, index) in fallacies"
      :key="index"
      :class="['fallacy-card', `fallacy-card--${fallacy.severity}`]"
    >
      <blockquote class="fallacy-card__quote">{{ fallacy.quote }}</blockquote>
      <h3 class="fallacy-card__name">{{ fallacy.fallacy_name }}</h3>
      <span class="fallacy-card__category">{{ fallacy.category }}</span>
      <span
        :class="[
          'fallacy-card__severity',
          `fallacy-card__severity--${fallacy.severity}`,
        ]"
      >
        {{
          fallacy.severity.charAt(0).toUpperCase() + fallacy.severity.slice(1)
        }}
      </span>
      <p class="fallacy-card__explanation">{{ fallacy.explanation }}</p>
      <div class="fallacy-card__example">
        <p class="fallacy-card__example-label">Example:</p>
        <p class="fallacy-card__example-scenario">
          {{ fallacy.clear_example.scenario }}
        </p>
        <p class="fallacy-card__example-why">
          {{ fallacy.clear_example.why_wrong }}
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fallacy-display {
  width: 100%;
  max-width: 960px;
}

.fallacy-display__heading {
  margin: 0 0 1rem;
  font-size: 1.25rem;
  font-weight: 600;
  color: #2d3748;
}

.fallacy-display__empty {
  color: #718096;
  font-style: italic;
}

.fallacy-card {
  padding: 1rem 1.25rem;
  margin-bottom: 1rem;
  border: 1px solid #e2e8f0;
  border-left: 4px solid #e2e8f0;
  border-radius: 6px;
  background-color: #fff;
}

.fallacy-card--high {
  border-left-color: #e53e3e;
  background-color: #fff5f5;
}

.fallacy-card--medium {
  border-left-color: #dd6b20;
  background-color: #fffaf0;
}

.fallacy-card--low {
  border-left-color: #d69e2e;
  background-color: #fffff0;
}

.fallacy-card__quote {
  margin: 0 0 0.75rem;
  padding: 0.5rem 0.75rem;
  border-left: 3px solid #cbd5e0;
  color: #4a5568;
  font-style: italic;
  background-color: #f7fafc;
  border-radius: 2px;
}

.fallacy-card__name {
  margin: 0 0 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  color: #1a202c;
}

.fallacy-card__category {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  margin-right: 0.5rem;
  font-size: 0.75rem;
  font-weight: 500;
  color: #4a5568;
  background-color: #edf2f7;
  border-radius: 9999px;
}

.fallacy-card__severity {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 9999px;
}

.fallacy-card__severity--high {
  color: #c53030;
  background-color: #fed7d7;
}

.fallacy-card__severity--medium {
  color: #c05621;
  background-color: #feebc8;
}

.fallacy-card__severity--low {
  color: #975a16;
  background-color: #fefcbf;
}

.fallacy-card__explanation {
  margin: 0.75rem 0;
  color: #4a5568;
  line-height: 1.6;
}

.fallacy-card__example {
  padding: 0.75rem;
  background-color: #f7fafc;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
}

.fallacy-card__example-label {
  margin: 0 0 0.25rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: #718096;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.fallacy-card__example-scenario {
  margin: 0 0 0.25rem;
  color: #4a5568;
}

.fallacy-card__example-why {
  margin: 0;
  color: #718096;
  font-size: 0.875rem;
}
</style>
