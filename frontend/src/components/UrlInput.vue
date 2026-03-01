<script setup lang="ts">
import { ref } from "vue";

const props = defineProps<{
  loading: boolean;
}>();

const emit = defineEmits<{
  submit: [url: string];
}>();

const url = ref("");

function handleSubmit() {
  const trimmed = url.value.trim();
  if (trimmed) {
    emit("submit", trimmed);
  }
}
</script>

<template>
  <form class="url-input" @submit.prevent="handleSubmit">
    <div class="url-input__wrapper">
      <svg class="url-input__icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
        <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
      </svg>
      <input
        v-model="url"
        type="text"
        placeholder="Paste a YouTube URL..."
        :disabled="props.loading"
        class="url-input__field"
      />
      <button
        type="submit"
        :disabled="props.loading || !url.trim()"
        class="url-input__button"
      >
        <span v-if="!props.loading">Summarize</span>
        <span v-else class="url-input__loading-dots">
          <span></span><span></span><span></span>
        </span>
      </button>
    </div>
  </form>
</template>

<style scoped>
.url-input {
  width: 100%;
  max-width: 640px;
}

.url-input__wrapper {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.5rem 0.5rem 1.25rem;
  background: #FFFFFF;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 100px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 16px rgba(0, 0, 0, 0.02);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.url-input__wrapper:focus-within {
  border-color: rgba(37, 99, 235, 0.35);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 16px rgba(37, 99, 235, 0.08);
}

.url-input__icon {
  flex-shrink: 0;
  color: #9CA3AF;
}

.url-input__field {
  flex: 1;
  padding: 0.6rem 0;
  font-size: 0.95rem;
  font-family: 'Manrope', sans-serif;
  color: #111827;
  border: none;
  outline: none;
  background: transparent;
}

.url-input__field::placeholder {
  color: #9CA3AF;
}

.url-input__field:disabled {
  opacity: 0.5;
}

.url-input__button {
  flex-shrink: 0;
  padding: 0.65rem 1.5rem;
  font-size: 0.9rem;
  font-weight: 500;
  font-family: 'Manrope', sans-serif;
  color: #FFFFFF;
  background: #111827;
  border: none;
  border-radius: 100px;
  cursor: pointer;
  transition: background 0.2s;
  min-width: 110px;
}

.url-input__button:not(:disabled):hover {
  background: #030712;
}

.url-input__button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.url-input__loading-dots {
  display: inline-flex;
  gap: 3px;
  align-items: center;
  justify-content: center;
}

.url-input__loading-dots span {
  width: 5px;
  height: 5px;
  background: #FFFFFF;
  border-radius: 50%;
  animation: dotPulse 1.2s ease-in-out infinite;
}

.url-input__loading-dots span:nth-child(2) {
  animation-delay: 0.15s;
}

.url-input__loading-dots span:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes dotPulse {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}
</style>
