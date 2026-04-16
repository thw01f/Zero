
<template>
  <a v-if="cwe" :href="`https://cwe.mitre.org/data/definitions/${cweNum}.html`"
     target="_blank" rel="noopener" class="cwe-tag">CWE-{{ cweNum }}</a>
</template>
<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ cwe?: string }>()
const cweNum = computed(() => props.cwe?.replace(/[^0-9]/g, '') ?? '')
</script>
<style scoped>
.cwe-tag { background:#1e2d45; color:#4a9ff5; border:1px solid #2a3f60;
  padding:1px 6px; border-radius:3px; font-size:11px; text-decoration:none; }
.cwe-tag:hover { background:#2a3f60; }
</style>
