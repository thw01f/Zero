<template>
  <div>
    <div class="flex justify-between text-xs text-slate-400 mb-1">
      <span>{{ scanStore.currentStage || 'Scanning...' }}</span>
      <span>{{ scanStore.progress }}%</span>
    </div>
    <div class="h-1.5 bg-slate-700 rounded-full overflow-hidden">
      <div class="h-full bg-violet-500 rounded-full transition-all duration-300"
           :style="{ width: scanStore.progress + '%' }" />
    </div>
    <div v-if="scanStore.scannerEvents.length" class="mt-1.5 space-y-0.5">
      <div v-for="e in scanStore.scannerEvents.slice(-3)" :key="e.scanner"
           class="text-xs text-slate-500 flex justify-between">
        <span>✓ {{ e.scanner }}</span>
        <span>{{ e.count }} findings</span>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { useScanStore } from '../stores/scan'
const scanStore = useScanStore()
</script>
