<template>
  <RouterLink to="/self-health" class="flex items-center gap-2 text-xs">
    <span class="w-2 h-2 rounded-full" :class="statusColor" />
    <span class="text-slate-500">Platform {{ status }}</span>
  </RouterLink>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import axios from 'axios'
const status = ref('checking')
const statusColor = ref('bg-slate-500')
onMounted(async () => {
  try {
    const { data } = await axios.get('/api/self-health')
    status.value = data.status
    statusColor.value = data.status === 'healthy' ? 'bg-green-400' : data.status === 'degraded' ? 'bg-yellow-400' : 'bg-red-400'
  } catch { status.value = 'offline'; statusColor.value = 'bg-red-400' }
})
</script>