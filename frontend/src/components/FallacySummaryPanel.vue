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
  font-family: 'Instrument Serif', serif;
  font-size: 2rem;
  font-weight: 400;
  color: #2C2C2C;
  line-height: 1;
}

.fallacy-summary-panel__label {
  font-size: 0.85rem;
  color: #8A8578;
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
  color: #C45D3E;
  background: rgba(196, 93, 62, 0.1);
}

.fallacy-summary-panel__severity--medium {
  color: #D4913A;
  background: rgba(212, 145, 58, 0.1);
}

.fallacy-summary-panel__severity--low {
  color: #8A7A3A;
  background: rgba(184, 168, 78, 0.1);
}

.fallacy-summary-panel__tactics {
  font-size: 0.85rem;
  color: #3D3D3D;
  line-height: 1.5;
}

.fallacy-summary-panel__tactics-label {
  font-weight: 600;
  color: #8A8578;
}
</style>
