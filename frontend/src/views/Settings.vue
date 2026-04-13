
<template>
  <div class="p-6 max-w-2xl">
    <div class="ft-card mb-4">
      <h2 class="text-lg font-bold text-white mb-4">LLM Backend</h2>
      <div class="space-y-3">
        <div class="metric-tile">
          <div class="metric-label">Active Backend</div>
          <div class="metric-value text-ft-green">{{ models.active_backend ?? '—' }}</div>
        </div>
        <div class="metric-tile">
          <div class="metric-label">Active Model</div>
          <div class="metric-value font-mono text-sm">{{ models.active_model ?? '—' }}</div>
        </div>
      </div>
      <div class="mt-4">
        <h3 class="text-sm font-semibold text-gray-300 mb-2">Available Models</h3>
        <div v-for="m in models.models" :key="m.name" class="flex items-center gap-3 py-1.5 border-b border-white/5">
          <span class="backend-badge" :class="m.backend">{{ m.backend }}</span>
          <span class="font-mono text-sm">{{ m.name }}</span>
          <span class="text-gray-400 text-xs ml-auto">{{ formatSize(m.size) }}</span>
        </div>
      </div>
    </div>
    <div class="ft-card">
      <h2 class="text-lg font-bold text-white mb-4">Scanner Configuration</h2>
      <div class="space-y-2 text-sm text-gray-300">
        <div class="flex justify-between"><span>Max repo size</span><span class="font-mono">200 MB</span></div>
        <div class="flex justify-between"><span>Clone timeout</span><span class="font-mono">60 s</span></div>
        <div class="flex justify-between"><span>LLM fix batch</span><span class="font-mono">20 issues</span></div>
        <div class="flex justify-between"><span>Advisory poll</span><span class="font-mono">6 h</span></div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
const models = ref<any>({})
onMounted(async () => { const r = await fetch('/api/analyze/models'); models.value = await r.json() })
function formatSize(b?: number) { if (!b) return 'unknown'; const gb = b/1e9; return gb >= 1 ? `${gb.toFixed(1)} GB` : `${(b/1e6).toFixed(0)} MB` }
</script>
