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
  padding: 1.25rem 1.5rem;
  background: #FDF6F3;
  border: 1px solid rgba(196, 93, 62, 0.15);
  border-radius: 12px;
}

.error-message__text {
  margin: 0;
  color: #C45D3E;
  font-weight: 500;
  font-size: 0.9rem;
  text-align: center;
}

.error-message__details {
  margin: 0;
  color: #8A8578;
  font-size: 0.825rem;
  text-align: center;
}

.error-message__retry {
  padding: 0.45rem 1.25rem;
  font-size: 0.825rem;
  font-weight: 500;
  font-family: 'DM Sans', sans-serif;
  color: #C45D3E;
  background: none;
  border: 1px solid #C45D3E;
  border-radius: 100px;
  cursor: pointer;
  transition: all 0.2s;
}

.error-message__retry:hover {
  background: #C45D3E;
  color: #FFFFFF;
}
</style>
