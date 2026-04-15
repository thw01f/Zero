<template>
  <div class="table-filter">
    <input v-model="q" type="text" class="ft-input flex-1" :placeholder="placeholder" />
    <select v-if="sevOptions" v-model="sev" class="ft-select w-32">
      <option value="">All severities</option>
      <option v-for="s in sevOptions" :key="s" :value="s">{{ s }}</option>
    </select>
    <button v-if="q || sev" class="ft-btn ft-btn-ghost text-xs" @click="clear">Clear</button>
  </div>
</template>
<script setup lang="ts">
import { ref } from 'vue'
const props = defineProps<{ placeholder?: string; sevOptions?: string[] }>()
const emit = defineEmits<{ filter: [{ q: string; sev: string }] }>()
const q = ref(''), sev = ref('')
import { watch } from 'vue'
watch([q, sev], () => emit('filter', { q: q.value, sev: sev.value }))
function clear() { q.value = ''; sev.value = '' }
</script>
<style scoped>
.table-filter { display:flex; gap:8px; align-items:center; margin-bottom:12px; }
</style>
