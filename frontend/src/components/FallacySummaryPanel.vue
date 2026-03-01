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
  max-width: 720px;
  padding: 1.25rem 1.5rem;
  background: #FFFFFF;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.fallacy-summary-panel__total {
  display: flex;
  align-items: baseline;
  gap: 0.6rem;
}

.fallacy-summary-panel__count {
  font-family: 'Syne', sans-serif;
  font-size: 2rem;
  font-weight: 700;
  color: #111827;
  line-height: 1;
}

.fallacy-summary-panel__label {
  font-size: 0.85rem;
  color: #6B7280;
}

.fallacy-summary-panel__breakdown {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.fallacy-summary-panel__severity {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.2rem 0.65rem;
  border-radius: 100px;
}

.fallacy-summary-panel__severity--high {
  color: #DC2626;
  background: rgba(220, 38, 38, 0.1);
}

.fallacy-summary-panel__severity--medium {
  color: #D97706;
  background: rgba(217, 119, 6, 0.1);
}

.fallacy-summary-panel__severity--low {
  color: #65A30D;
  background: rgba(101, 163, 13, 0.1);
}

.fallacy-summary-panel__tactics {
  font-size: 0.85rem;
  color: #374151;
  line-height: 1.5;
}

.fallacy-summary-panel__tactics-label {
  font-weight: 600;
  color: #6B7280;
}
</style>
