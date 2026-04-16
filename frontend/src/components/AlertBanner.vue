<template>
  <div v-if="show" :class="['alert-banner', `alert-${level}`]" role="alert">
    <span class="alert-icon">{{ icons[level] }}</span>
    <span class="alert-msg"><slot /></span>
    <button class="alert-close" @click="show=false">✕</button>
  </div>
</template>
<script setup lang="ts">
import { ref } from 'vue'
defineProps<{ level?: 'info'|'success'|'warning'|'error' }>()
const show = ref(true)
const icons = { info:'ℹ️', success:'✅', warning:'⚠️', error:'🚨' }
</script>
<style scoped>
.alert-banner { display:flex; align-items:center; gap:8px; padding:10px 16px; border-radius:4px; margin:8px 0; font-size:13px; }
.alert-info    { background:rgba(74,159,245,0.12); border-left:3px solid #4a9ff5; color:#4a9ff5; }
.alert-success { background:rgba(62,207,142,0.12); border-left:3px solid #3ecf8e; color:#3ecf8e; }
.alert-warning { background:rgba(245,166,35,0.12); border-left:3px solid #f5a623; color:#f5a623; }
.alert-error   { background:rgba(242,85,85,0.12);  border-left:3px solid #f25555; color:#f25555; }
.alert-msg { flex:1; }
.alert-close { background:none; border:none; cursor:pointer; color:inherit; opacity:0.7; }
</style>
