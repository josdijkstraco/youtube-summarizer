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
      <div class="fallacy-card__badges">
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
      </div>
      <p class="fallacy-card__explanation">{{ fallacy.explanation }}</p>
      <div class="fallacy-card__example">
        <p class="fallacy-card__example-label">Example</p>
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
  max-width: 720px;
}

.fallacy-display__heading {
  margin: 0 0 1.25rem;
  font-family: 'Syne', sans-serif;
  font-size: 1.5rem;
  font-weight: 700;
  color: #111827;
}

.fallacy-display__empty {
  color: #6B7280;
  font-style: italic;
  font-size: 0.9rem;
}

.fallacy-card {
  padding: 1.25rem 1.5rem;
  margin-bottom: 1rem;
  background: #FFFFFF;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-left: 3px solid #E8E5DE;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.fallacy-card--high {
  border-left-color: #DC2626;
}

.fallacy-card--medium {
  border-left-color: #D97706;
}

.fallacy-card--low {
  border-left-color: #65A30D;
}

.fallacy-card__quote {
  margin: 0 0 0.75rem;
  padding: 0.6rem 0.85rem;
  border-left: 2px solid #E5E7EB;
  color: #4B5563;
  font-style: italic;
  font-size: 0.9rem;
  line-height: 1.5;
  background: rgba(0, 0, 0, 0.015);
  border-radius: 0 6px 6px 0;
}

.fallacy-card__name {
  margin: 0 0 0.5rem;
  font-size: 0.95rem;
  font-weight: 600;
  color: #111827;
}

.fallacy-card__badges {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.fallacy-card__category {
  display: inline-block;
  padding: 0.15rem 0.6rem;
  font-size: 0.7rem;
  font-weight: 500;
  color: #6B7280;
  background: #F3F4F6;
  border-radius: 100px;
  letter-spacing: 0.02em;
}

.fallacy-card__severity {
  display: inline-block;
  padding: 0.15rem 0.6rem;
  font-size: 0.7rem;
  font-weight: 600;
  border-radius: 100px;
}

.fallacy-card__severity--high {
  color: #DC2626;
  background: rgba(220, 38, 38, 0.1);
}

.fallacy-card__severity--medium {
  color: #D97706;
  background: rgba(217, 119, 6, 0.1);
}

.fallacy-card__severity--low {
  color: #65A30D;
  background: rgba(101, 163, 13, 0.1);
}

.fallacy-card__explanation {
  margin: 0 0 0.75rem;
  color: #374151;
  line-height: 1.65;
  font-size: 0.9rem;
}

.fallacy-card__example {
  padding: 0.75rem 1rem;
  background: #F9FAFB;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.04);
}

.fallacy-card__example-label {
  margin: 0 0 0.35rem;
  font-size: 0.7rem;
  font-weight: 600;
  color: #9CA3AF;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.fallacy-card__example-scenario {
  margin: 0 0 0.25rem;
  color: #374151;
  font-size: 0.85rem;
  line-height: 1.5;
}

.fallacy-card__example-why {
  margin: 0;
  color: #6B7280;
  font-size: 0.825rem;
  line-height: 1.5;
}
</style>
