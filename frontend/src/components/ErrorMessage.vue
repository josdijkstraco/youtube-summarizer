<script setup lang="ts">
import type { ErrorResponse } from "@/types";

const props = defineProps<{
  error: ErrorResponse;
}>();

const emit = defineEmits<{
  retry: [];
}>();
</script>

<template>
  <div class="error-message">
    <p class="error-message__text">{{ props.error.message }}</p>
    <p v-if="props.error.details" class="error-message__details">
      {{ props.error.details }}
    </p>
    <button class="error-message__retry" @click="emit('retry')">
      Try again
    </button>
  </div>
</template>

<style scoped>
.error-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  max-width: 640px;
  padding: 1.25rem;
  background-color: #fff5f5;
  border: 1px solid #feb2b2;
  border-radius: 8px;
}

.error-message__text {
  margin: 0;
  color: #c53030;
  font-weight: 600;
  text-align: center;
}

.error-message__details {
  margin: 0;
  color: #718096;
  font-size: 0.875rem;
  text-align: center;
}

.error-message__retry {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #c53030;
  background: none;
  border: 1px solid #c53030;
  border-radius: 6px;
  cursor: pointer;
}

.error-message__retry:hover {
  background-color: #c53030;
  color: #fff;
}
</style>
