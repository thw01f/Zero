<template>
  <RouterLink to="/self-health" class="flex items-center gap-2 text-xs">
    <span class="w-2 h-2 rounded-full" :class="statusColor" />
    <span class="text-slate-500">Platform {{ status }}</span>
  </RouterLink>
</template>
<script setup lang="ts">
// TODO: implement logic
</script>
