<template>
  <RouterLink :to="path" class="flex items-center gap-2 px-3 py-1.5 rounded-lg mx-1 text-sm transition-colors"
    :class="isActive ? 'bg-violet-900/40 text-violet-300' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'">
    <span class="text-base">{{ icon }}</span>
    <span>{{ label }}</span>
    <span v-if="badge" class="ml-auto bg-red-600 text-white text-xs px-1.5 rounded-full">{{ badge }}</span>
  </RouterLink>
</template>
<script setup lang="ts">
// TODO: implement logic
</script>
