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
    <div class="length-slider__header">
      <span class="length-slider__label">Summary length</span>
      <span class="length-slider__value">{{ modelValue }}%</span>
    </div>
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
    <div class="length-slider__ticks">
      <span>Concise</span>
      <span>Detailed</span>
    </div>
  </div>
</template>

<style scoped>
.length-slider {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  width: 100%;
  max-width: 360px;
}

.length-slider__header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.length-slider__label {
  font-size: 0.8rem;
  font-weight: 500;
  color: #8A8578;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

.length-slider__value {
  font-size: 0.85rem;
  font-weight: 600;
  color: #2C2C2C;
  font-variant-numeric: tabular-nums;
}

.length-slider__input {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 4px;
  background: #E8E5DE;
  border-radius: 2px;
  outline: none;
  cursor: pointer;
}

.length-slider__input::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  background: #2C2C2C;
  border-radius: 50%;
  border: 3px solid #FAF9F6;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
  cursor: pointer;
  transition: transform 0.15s ease;
}

.length-slider__input::-webkit-slider-thumb:hover {
  transform: scale(1.15);
}

.length-slider__input::-moz-range-thumb {
  width: 18px;
  height: 18px;
  background: #2C2C2C;
  border-radius: 50%;
  border: 3px solid #FAF9F6;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
  cursor: pointer;
}

.length-slider__input:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.length-slider__ticks {
  display: flex;
  justify-content: space-between;
  font-size: 0.7rem;
  color: #B8B2A6;
  letter-spacing: 0.02em;
}
</style>
