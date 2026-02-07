<script setup lang="ts"></script>

<template>
  <div class="loading-state">
    <div class="loading-state__spinner"></div>
    <p class="loading-state__text">Generating summary...</p>
  </div>
</template>

<style scoped>
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 2rem;
}

.loading-state__spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e2e8f0;
  border-top-color: #e53e3e;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-state__text {
  font-size: 1rem;
  color: #718096;
}
</style>
