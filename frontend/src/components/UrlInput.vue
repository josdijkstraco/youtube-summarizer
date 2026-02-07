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
      Summarize
    </button>
  </form>
</template>

<style scoped>
.url-input {
  display: flex;
  gap: 0.5rem;
  width: 100%;
  max-width: 640px;
}

.url-input__field {
  flex: 1;
  padding: 0.75rem 1rem;
  font-size: 1rem;
  border: 1px solid #ccc;
  border-radius: 6px;
}

.url-input__field:disabled {
  opacity: 0.6;
}

.url-input__button {
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  color: #fff;
  background-color: #e53e3e;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.url-input__button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.url-input__button:not(:disabled):hover {
  background-color: #c53030;
}
</style>
