<script setup lang="ts">
import type { FallacySummary } from "@/types";

defineProps<{
  summary: FallacySummary | null;
}>();
</script>

<template>
  <div v-if="summary" class="fallacy-summary-panel">
    <div class="fallacy-summary-panel__total">
      <span class="fallacy-summary-panel__count">{{
        summary.total_fallacies
      }}</span>
      <span class="fallacy-summary-panel__label">Fallacies Found</span>
    </div>
    <div class="fallacy-summary-panel__breakdown">
      <span
        class="fallacy-summary-panel__severity fallacy-summary-panel__severity--high"
      >
        High: {{ summary.high_severity }}
      </span>
      <span
        class="fallacy-summary-panel__severity fallacy-summary-panel__severity--medium"
      >
        Medium: {{ summary.medium_severity }}
      </span>
      <span
        class="fallacy-summary-panel__severity fallacy-summary-panel__severity--low"
      >
        Low: {{ summary.low_severity }}
      </span>
    </div>
    <div
      v-if="summary.primary_tactics.length > 0"
      class="fallacy-summary-panel__tactics"
    >
      <span class="fallacy-summary-panel__tactics-label">Primary tactics:</span>
      {{ summary.primary_tactics.join(", ") }}
    </div>
  </div>
</template>

<style scoped>
.fallacy-summary-panel {
  width: 100%;
  max-width: 960px;
  padding: 1rem 1.25rem;
  background-color: #f7fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.fallacy-summary-panel__total {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}

.fallacy-summary-panel__count {
  font-size: 1.75rem;
  font-weight: 700;
  color: #1a202c;
}

.fallacy-summary-panel__label {
  font-size: 0.875rem;
  color: #718096;
}

.fallacy-summary-panel__breakdown {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.fallacy-summary-panel__severity {
  font-size: 0.8rem;
  font-weight: 600;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
}

.fallacy-summary-panel__severity--high {
  color: #c53030;
  background-color: #fed7d7;
}

.fallacy-summary-panel__severity--medium {
  color: #c05621;
  background-color: #feebc8;
}

.fallacy-summary-panel__severity--low {
  color: #975a16;
  background-color: #fefcbf;
}

.fallacy-summary-panel__tactics {
  font-size: 0.875rem;
  color: #4a5568;
}

.fallacy-summary-panel__tactics-label {
  font-weight: 600;
  color: #718096;
}
</style>
