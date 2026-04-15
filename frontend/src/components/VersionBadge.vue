<template>
  <span class="version-badge">v{{ version }}</span>
</template>
<script setup lang="ts">
defineProps<{ version: string }>()
</script>
<style scoped>
.version-badge { font-size:10px; color:#8899aa; background:#1e2d45; padding:1px 5px; border-radius:3px; }
</style>
