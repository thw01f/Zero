
<template>
  <div class="p-6">
    <div class="ft-card">
      <h2 class="text-lg font-bold text-white mb-4">Repository Comparison</h2>
      <p class="text-gray-400 text-sm mb-6">Compare security posture across two scanned repositories.</p>
      <div class="grid grid-cols-2 gap-4 mb-6">
        <div>
          <label class="block text-xs text-gray-400 mb-1">Baseline Scan</label>
          <select v-model="jobA" class="ft-select w-full">
            <option v-for="j in jobs" :key="j.job_id" :value="j.job_id">{{ shortRepo(j.repo_url) }} ({{ j.grade }})</option>
          </select>
        </div>
        <div>
          <label class="block text-xs text-gray-400 mb-1">Comparison Scan</label>
          <select v-model="jobB" class="ft-select w-full">
            <option v-for="j in jobs" :key="j.job_id" :value="j.job_id">{{ shortRepo(j.repo_url) }} ({{ j.grade }})</option>
          </select>
        </div>
      </div>
      <div v-if="jobA && jobB" class="grid grid-cols-2 gap-4">
        <div v-for="j in [dataA, dataB]" :key="j?.job_id" class="ft-widget p-4">
          <div class="font-mono text-sm text-gray-300 mb-2">{{ shortRepo(j?.report?.repo_url) }}</div>
          <div class="flex gap-4">
            <div class="metric-tile"><div class="metric-label">Grade</div><div class="metric-value text-2xl">{{ j?.report?.grade ?? '—' }}</div></div>
            <div class="metric-tile"><div class="metric-label">Score</div><div class="metric-value">{{ j?.report?.debt_score ?? '—' }}</div></div>
            <div class="metric-tile"><div class="metric-label">Issues</div><div class="metric-value">{{ j?.report?.issue_count ?? '—' }}</div></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
const jobs = ref<any[]>([])
const jobA = ref(''), jobB = ref('')
const dataA = ref<any>(null), dataB = ref<any>(null)
async function loadReport(id: string) { const r = await fetch(`/api/report/${id}`); return r.json() }
onMounted(async () => { const r = await fetch('/api/scan/jobs'); const d = await r.json(); jobs.value = d.jobs ?? d })
watch(jobA, async v => { if (v) dataA.value = await loadReport(v) })
watch(jobB, async v => { if (v) dataB.value = await loadReport(v) })
function shortRepo(url: string) { return url?.replace('https://github.com/', '') ?? '—' }
</script>
