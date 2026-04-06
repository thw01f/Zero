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
// TODO: implement logic
</script>
