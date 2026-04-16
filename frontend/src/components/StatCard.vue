<template>
  <div class="ft-widget metric-tile">
    <div class="flex items-start justify-between">
      <div class="flex-1">
        <div class="metric-value" :style="valueStyle">{{ value }}</div>
        <div class="metric-label">{{ label }}</div>
        <div v-if="sub" class="metric-sub">{{ sub }}</div>
      </div>
      <div v-if="icon" class="ml-2 opacity-40" style="color:#8a96b0">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path :d="icon" />
        </svg>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  label: string
  value: number | string
  sub?: string
  color?: 'green' | 'red' | 'orange' | 'blue' | 'yellow' | 'default'
  icon?: string
}>()

const colorMap: Record<string, string> = {
  green: '#3ecf8e',
  red: '#f25555',
  orange: '#f26d21',
  blue: '#4a9ff5',
  yellow: '#f5a623',
  default: '#dde3ef',
}

const valueStyle = computed(() => ({
  color: colorMap[props.color ?? 'default'] ?? colorMap.default,
}))
</script>