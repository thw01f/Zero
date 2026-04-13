
<template>
  <div class="p-6">
    <div class="ft-card mb-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-bold text-white">Scan History</h2>
        <span class="text-sm text-gray-400">{{ jobs.length }} scans</span>
      </div>
      <div v-if="loading" class="text-gray-400 text-center py-8">Loading scan history...</div>
      <table v-else class="ft-table w-full">
        <thead><tr>
          <th>Repository</th><th>Grade</th><th>Score</th>
          <th>Issues</th><th>Status</th><th>Date</th><th></th>
        </tr></thead>
        <tbody>
          <tr v-for="job in jobs" :key="job.job_id" class="cursor-pointer hover:bg-ft-card/60"
              @click="$router.push(`/report/${job.job_id}`)">
            <td class="font-mono text-sm">{{ shortRepo(job.repo_url) }}</td>
            <td><span :class="`grade-${job.grade?.toLowerCase()}`" class="font-bold">{{ job.grade ?? '—' }}</span></td>
            <td>{{ job.debt_score ?? '—' }}</td>
            <td>{{ job.issue_count ?? 0 }}</td>
            <td><span :class="`status-${job.status}`">{{ job.status }}</span></td>
            <td class="text-gray-400 text-sm">{{ fmtDate(job.created_at) }}</td>
            <td><button class="ft-btn ft-btn-ghost text-xs">View →</button></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
const jobs = ref<any[]>([])
const loading = ref(true)
onMounted(async () => {
  try {
    const r = await fetch('/api/scan/jobs')
    const d = await r.json()
    jobs.value = d.jobs ?? d
  } finally { loading.value = false }
})
function shortRepo(url: string) { return url?.replace('https://github.com/', '') ?? url }
function fmtDate(d: string) { return d ? new Date(d).toLocaleDateString() : '—' }
</script>
