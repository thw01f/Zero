<template>
  <span :class="['status-chip', `status-${status}`]">
    <span class="status-dot"></span>{{ label }}
  </span>
</template>
<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ status: string }>()
const LABELS: Record<string,string> = { queued:'Queued', running:'Scanning', completed:'Done', failed:'Failed', pending:'Pending' }
const label = computed(() => LABELS[props.status] ?? props.status)
</script>
<style scoped>
.status-chip { display:inline-flex; align-items:center; gap:5px; padding:2px 9px; border-radius:10px; font-size:11px; font-weight:600; }
.status-dot  { width:6px; height:6px; border-radius:50%; background:currentColor; }
.status-queued    { color:#8899aa; background:rgba(136,153,170,0.12); }
.status-running   { color:#4a9ff5; background:rgba(74,159,245,0.12); animation:pulse 1.5s infinite; }
.status-completed { color:#3ecf8e; background:rgba(62,207,142,0.12); }
.status-failed    { color:#f25555; background:rgba(242,85,85,0.12); }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
</style>
