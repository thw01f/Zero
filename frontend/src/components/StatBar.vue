<template>
  <div class="stat-bar">
    <div class="stat-bar-label">{{ label }}</div>
    <div class="stat-bar-track">
      <div class="stat-bar-fill" :style="{width: pct + '%', background: color}" />
    </div>
    <div class="stat-bar-value">{{ value }}<span v-if="total" class="stat-bar-total">/{{ total }}</span></div>
  </div>
</template>
<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ label: string; value: number; total?: number; color?: string }>()
const pct = computed(() => props.total ? Math.min(100, (props.value / props.total) * 100) : Math.min(100, props.value))
</script>
<style scoped>
.stat-bar { display:flex; align-items:center; gap:10px; margin:4px 0; }
.stat-bar-label { width:100px; font-size:12px; color:#8899aa; flex-shrink:0; }
.stat-bar-track { flex:1; height:6px; background:#1e2d45; border-radius:3px; overflow:hidden; }
.stat-bar-fill  { height:100%; border-radius:3px; transition:width 0.4s ease; }
.stat-bar-value { width:50px; text-align:right; font-size:12px; font-weight:600; color:#d4dde8; }
.stat-bar-total { color:#8899aa; font-weight:400; }
</style>
