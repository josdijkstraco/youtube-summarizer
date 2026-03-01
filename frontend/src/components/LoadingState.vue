<script setup lang="ts">
withDefaults(defineProps<{ message?: string }>(), {
  message: 'Generating summary...',
});
</script>

<template>
  <div class="loading-state">
    <div class="loading-state__bar">
      <div class="loading-state__fill"></div>
    </div>
    <p class="loading-state__text">{{ message }}</p>
  </div>
</template>

<style scoped>
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 1.5rem;
  width: 100%;
  max-width: 400px;
}

.loading-state__bar {
  width: 100%;
  height: 3px;
  background: #E5E7EB;
  border-radius: 2px;
  overflow: hidden;
}

.loading-state__fill {
  width: 40%;
  height: 100%;
  background: #2563EB;
  border-radius: 2px;
  animation: slide 1.4s ease-in-out infinite;
}

@keyframes slide {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(350%); }
}

.loading-state__text {
  font-size: 0.85rem;
  color: #6B7280;
  letter-spacing: 0.02em;
}
</style>
