<template>
  <RouterLink :to="path" class="flex items-center gap-2 px-3 py-1.5 rounded-lg mx-1 text-sm transition-colors"
    :class="isActive ? 'bg-violet-900/40 text-violet-300' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'">
    <span class="text-base">{{ icon }}</span>
    <span>{{ label }}</span>
    <span v-if="badge" class="ml-auto bg-red-600 text-white text-xs px-1.5 rounded-full">{{ badge }}</span>
  </RouterLink>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
const props = defineProps<{ path: string; icon: string; label: string; badge?: number }>()
const route = useRoute()
const isActive = computed(() => route.path === props.path)
</script>