
<template>
  <div v-if="job && job.status !== 'completed'" class="scan-progress-wrap ft-card p-4">
    <div class="flex items-center justify-between mb-3">
      <span class="font-semibold text-sm">Scanning: <code class="text-ft-accent">{{ shortRepo }}</code></span>
      <span class="text-xs text-gray-400">{{ job.status }}</span>
    </div>
    <div class="progress-track">
      <div class="progress-fill" :style="{width: pct + '%'}"></div>
    </div>
    <div class="mt-2 text-xs text-gray-400">{{ stepLabel }}</div>
  </div>
</template>
<script setup lang="ts">
import { computed } from 'vue'

const STEPS = ['clone','detect','loc','scan','triage','fixes','misconfig','modules','compliance','updates','summary','persist']

const props = defineProps<{ job: any }>()
const pct = computed(() => {
  const idx = STEPS.indexOf(props.job?.current_step ?? '')
  return idx >= 0 ? Math.round((idx / STEPS.length) * 100) : 5
})
const stepLabel = computed(() => `Step ${STEPS.indexOf(props.job?.current_step ?? '')+1}/13: ${props.job?.current_step ?? 'initializing'}`)
const shortRepo = computed(() => props.job?.repo_url?.replace('https://github.com/', '') ?? '')
</script>
<style scoped>
.progress-track { height:3px; background:#1e2d45; border-radius:2px; overflow:hidden; }
.progress-fill  { height:100%; background:linear-gradient(90deg,#f26d21,#f5a623); transition:width 0.5s ease; }
</style>
