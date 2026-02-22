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
  font-family: 'Instrument Serif', serif;
  font-size: 1.5rem;
  font-weight: 400;
  color: #2C2C2C;
}

.fallacy-display__empty {
  color: #8A8578;
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
  border-left-color: #C45D3E;
}

.fallacy-card--medium {
  border-left-color: #D4913A;
}

.fallacy-card--low {
  border-left-color: #B8A84E;
}

.fallacy-card__quote {
  margin: 0 0 0.75rem;
  padding: 0.6rem 0.85rem;
  border-left: 2px solid #E8E5DE;
  color: #5A5A5A;
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
  color: #2C2C2C;
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
  color: #8A8578;
  background: #F0EDE7;
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
  color: #C45D3E;
  background: rgba(196, 93, 62, 0.1);
}

.fallacy-card__severity--medium {
  color: #D4913A;
  background: rgba(212, 145, 58, 0.1);
}

.fallacy-card__severity--low {
  color: #8A7A3A;
  background: rgba(184, 168, 78, 0.1);
}

.fallacy-card__explanation {
  margin: 0 0 0.75rem;
  color: #3D3D3D;
  line-height: 1.65;
  font-size: 0.9rem;
}

.fallacy-card__example {
  padding: 0.75rem 1rem;
  background: #FAF9F6;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.04);
}

.fallacy-card__example-label {
  margin: 0 0 0.35rem;
  font-size: 0.7rem;
  font-weight: 600;
  color: #B8B2A6;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.fallacy-card__example-scenario {
  margin: 0 0 0.25rem;
  color: #3D3D3D;
  font-size: 0.85rem;
  line-height: 1.5;
}

.fallacy-card__example-why {
  margin: 0;
  color: #8A8578;
  font-size: 0.825rem;
  line-height: 1.5;
}
</style>
