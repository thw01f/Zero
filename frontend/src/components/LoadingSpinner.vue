
<template>
  <div :class="['spinner-wrap', size]">
    <svg class="spinner" viewBox="0 0 50 50">
      <circle cx="25" cy="25" r="20" fill="none"
        :stroke="color ?? '#f26d21'" stroke-width="4"
        stroke-linecap="round" stroke-dasharray="80" stroke-dashoffset="60"/>
    </svg>
    <span v-if="label" class="spinner-label">{{ label }}</span>
  </div>
</template>
<script setup lang="ts">
defineProps<{ size?: 'sm'|'md'|'lg'; color?: string; label?: string }>()
</script>
<style scoped>
.spinner-wrap { display:flex; flex-direction:column; align-items:center; gap:8px; }
.spinner { animation: spin 0.8s linear infinite; }
.spinner-wrap.sm .spinner { width:20px; height:20px; }
.spinner-wrap.md .spinner { width:36px; height:36px; }
.spinner-wrap.lg .spinner { width:56px; height:56px; }
.spinner-label { font-size:12px; color:#8899aa; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
