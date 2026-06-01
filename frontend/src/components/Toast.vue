<script setup lang="ts">
import { ref, watch, onUnmounted } from "vue";

const props = withDefaults(
  defineProps<{
    message: string;
    type?: "success" | "error" | "info";
    duration?: number;
  }>(),
  {
    type: "success",
    duration: 3000,
  },
);

const emit = defineEmits<{ dismiss: [] }>();

const visible = ref(true);
let timer: ReturnType<typeof setTimeout> | null = null;

function startTimer() {
  if (timer !== null) clearTimeout(timer);
  timer = setTimeout(() => {
    visible.value = false;
  }, props.duration);
}

function onAfterLeave() {
  emit("dismiss");
}

watch(
  () => props.message,
  () => {
    visible.value = true;
    startTimer();
  },
  { immediate: true },
);

onUnmounted(() => {
  if (timer !== null) clearTimeout(timer);
});
</script>

<template>
  <Transition name="toast" @after-leave="onAfterLeave">
    <div
      v-if="visible"
      :class="['toast', `toast--${type}`]"
      role="status"
      aria-live="polite"
    >
      {{ message }}
    </div>
  </Transition>
</template>

<style scoped>
.toast {
  position: fixed;
  bottom: 1.5rem;
  left: 50%;
  transform: translateX(-50%);
  padding: 0.65rem 1.25rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  font-family: "Manrope", sans-serif;
  color: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 9999;
  white-space: nowrap;
  pointer-events: none;
}

.toast--success {
  background: #16a34a;
}

.toast--error {
  background: #dc2626;
}

.toast--info {
  background: #2563eb;
}

.toast-enter-active,
.toast-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(0.5rem);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(0.5rem);
}
</style>
