
<template>
  <div class="empty-state">
    <div class="empty-icon">{{ icon }}</div>
    <div class="empty-title">{{ title }}</div>
    <div class="empty-sub">{{ subtitle }}</div>
    <slot />
  </div>
</template>
<script setup lang="ts">
defineProps<{ icon?: string; title: string; subtitle?: string }>()
</script>
<style scoped>
.empty-state { display:flex; flex-direction:column; align-items:center; justify-content:center;
  padding:48px 24px; text-align:center; }
.empty-icon { font-size:48px; margin-bottom:16px; opacity:0.5; }
.empty-title { font-size:16px; font-weight:600; color:#d4dde8; margin-bottom:8px; }
.empty-sub { font-size:13px; color:#8899aa; }
</style>
