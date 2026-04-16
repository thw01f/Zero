
<template>
  <span :class="['metric-delta', positive ? 'up' : 'down']">
    {{ positive ? '▲' : '▼' }} {{ Math.abs(value) }}{{ unit }}
  </span>
</template>
<script setup lang="ts">
const props = defineProps<{ value: number; unit?: string; higherIsBetter?: boolean }>()
const positive = props.higherIsBetter ? props.value > 0 : props.value < 0
</script>
<style scoped>
.metric-delta { font-size:11px; font-weight:600; padding:1px 5px; border-radius:3px; }
.up   { color:#3ecf8e; background:rgba(62,207,142,0.12); }
.down { color:#f25555; background:rgba(242,85,85,0.12); }
</style>
