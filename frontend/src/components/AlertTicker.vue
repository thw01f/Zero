<template>
  <div class="bg-slate-800 border-b border-slate-700 px-4 py-1.5 flex items-center gap-3 text-xs overflow-hidden">
    <span class="text-violet-400 font-medium flex-shrink-0">⚡ LIVE</span>
    <div class="flex gap-6 overflow-hidden">
      <div v-for="alert in alertsStore.alerts.slice(0, 5)" :key="alert.id"
           class="flex-shrink-0 flex items-center gap-1.5"
           :class="alert.type === 'advisory' ? 'text-orange-400' : 'text-slate-400'">
        <span>{{ alertIcon(alert.type) }}</span>
        <span>{{ alertText(alert) }}</span>
      </div>
    </div>
    <button @click="alertsStore.markAllRead()" class="ml-auto flex-shrink-0 text-slate-500 hover:text-slate-300">
      ✕
    </button>
  </div>
</template>
<script setup lang="ts">
import { useAlertsStore } from '../stores/alerts'
const alertsStore = useAlertsStore()
const alertIcon = (type: string) => ({ advisory: '🔴', self_health_alert: '⚠️', scan_complete: '✅' }[type] || '📣')
const alertText = (a: any) => {
  if (a.type === 'advisory') return `New advisory: ${a.data?.advisory_id || 'CVE'}`
  if (a.type === 'scan_complete') return 'Scan completed'
  return a.type
}
</script>
