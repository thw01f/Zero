
<template>
  <svg :width="size" :height="size" class="grade-ring">
    <circle :cx="cx" :cy="cx" :r="r" fill="none"
      stroke="#1e2d45" :stroke-width="sw"/>
    <circle :cx="cx" :cy="cx" :r="r" fill="none"
      :stroke="gradeColor" :stroke-width="sw"
      :stroke-dasharray="circumference"
      :stroke-dashoffset="dashOffset"
      stroke-linecap="round"
      transform="rotate(-90, 60, 60)"/>
    <text :x="cx" :y="cx+6" text-anchor="middle"
      :fill="gradeColor" font-size="28" font-weight="bold"
      font-family="'JetBrains Mono', monospace">{{ grade }}</text>
    <text :x="cx" :y="cx+22" text-anchor="middle"
      fill="#8899aa" font-size="10">{{ score }}/100</text>
  </svg>
</template>

<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ grade: string; score: number; size?: number }>()
const size = props.size ?? 120
const cx = size / 2
const r = cx - 12
const sw = 10
const circumference = 2 * Math.PI * r
const dashOffset = computed(() => circumference * (1 - props.score / 100))
const gradeColor = computed(() => {
  const g = props.grade
  if (g === 'A') return '#3ecf8e'
  if (g === 'B') return '#4a9ff5'
  if (g === 'C') return '#f5a623'
  if (g === 'D') return '#f26d21'
  return '#f25555'
})
</script>
