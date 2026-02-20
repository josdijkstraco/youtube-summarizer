<script setup lang="ts">
defineProps<{
  modelValue: number;
  disabled?: boolean;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: number];
}>();

function onInput(event: Event) {
  const target = event.target as HTMLInputElement;
  emit("update:modelValue", Number(target.value));
}
</script>

<template>
  <div class="length-slider">
    <label class="length-slider__label">
      Summary length:
      <span class="length-slider__value">{{ modelValue }}%</span>
    </label>
    <input
      type="range"
      :min="10"
      :max="50"
      :step="5"
      :value="modelValue"
      :disabled="disabled"
      class="length-slider__input"
      @input="onInput"
    />
  </div>
</template>

<style scoped>
.length-slider {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  max-width: 400px;
}

.length-slider__label {
  font-size: 0.95rem;
  color: #4a5568;
}

.length-slider__value {
  font-weight: 600;
  color: #2d3748;
}

.length-slider__input {
  width: 100%;
  cursor: pointer;
}

.length-slider__input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
