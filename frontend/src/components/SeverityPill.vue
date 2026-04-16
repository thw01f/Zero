
<template>
  <span :class="['sev-pill', `sev-${sev}`]">{{ label }}</span>
</template>
<script setup lang="ts">
defineProps<{ sev: string }>()
const label = ({ critical:'CRIT', major:'MAJOR', minor:'MINOR', info:'INFO' } as Record<string,string>)[sev] ?? sev.toUpperCase()
</script>
<style scoped>
.sev-pill { display:inline-block; padding:1px 7px; border-radius:3px; font-size:11px; font-weight:700; letter-spacing:0.05em; }
.sev-critical { background:#f25555; color:#fff; }
.sev-major    { background:#f26d21; color:#fff; }
.sev-minor    { background:#f5a623; color:#0a0e1a; }
.sev-info     { background:#4a9ff5; color:#fff; }
</style>
