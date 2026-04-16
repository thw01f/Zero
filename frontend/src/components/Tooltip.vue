
<template>
  <div class="tooltip-host" @mouseenter="show=true" @mouseleave="show=false">
    <slot />
    <div v-show="show" :class="['tooltip-box', placement]">{{ text }}</div>
  </div>
</template>
<script setup lang="ts">
import { ref } from 'vue'
defineProps<{ text: string; placement?: 'top'|'bottom'|'left'|'right' }>()
const show = ref(false)
</script>
<style scoped>
.tooltip-host { position:relative; display:inline-flex; }
.tooltip-box { position:absolute; z-index:9999; background:#263553; color:#d4dde8;
  border:1px solid #2a3f60; padding:4px 10px; border-radius:4px; font-size:12px;
  white-space:nowrap; pointer-events:none; }
.tooltip-box.top    { bottom:calc(100% + 6px); left:50%; transform:translateX(-50%); }
.tooltip-box.bottom { top:calc(100% + 6px);    left:50%; transform:translateX(-50%); }
.tooltip-box.left   { right:calc(100% + 6px);  top:50%;  transform:translateY(-50%); }
.tooltip-box.right  { left:calc(100% + 6px);   top:50%;  transform:translateY(-50%); }
</style>
