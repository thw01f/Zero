
<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <div class="ft-card-title" style="font-size:11px;letter-spacing:0.12em">SCAN HISTORY</div>
        <div class="text-xs mt-0.5" style="color:#4a5568">{{ jobs.length }} scans recorded</div>
      </div>
      <button class="ft-btn ft-btn-secondary" @click="fetchJobs">Refresh</button>
    </div>

    <div v-if="loading" class="ft-card ft-card-body text-center py-8">
      <div class="flex items-center justify-center gap-2">
        <span class="status-dot status-running"></span>
        <span class="text-xs" style="color:#8a96b0">Loading scan history...</span>
      </div>
    </div>

    <div v-else-if="!jobs.length" class="ft-card ft-card-body text-center py-12">
      <div class="text-sm mb-1" style="color:#8a96b0">No scans yet</div>
      <div class="text-xs" style="color:#4a5568">Submit a GitHub URL or zip file to start</div>
    </div>

    <div v-else class="ft-card" style="overflow:hidden">
      <div style="overflow-x:auto">
        <table class="ft-table">
          <thead>
            <tr>
              <th>Repository</th>
              <th>Language</th>
              <th>Grade</th>
              <th>Debt</th>
              <th>Issues</th>
              <th>Status</th>
              <th>Date</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="job in jobs"
              :key="job.job_id"
              class="cursor-pointer"
              :style="{ opacity: job.status === 'running' ? 0.7 : 1 }"
              @click="loadJob(job)"
            >
              <td>
                <div class="font-mono text-xs" style="color:#dde3ef;max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
                  {{ shortRepo(job.repo_url) }}
                </div>
                <div class="text-xs mt-0.5" style="color:#4a5568">{{ job.job_id.slice(0,8) }}…</div>
              </td>
              <td style="color:#8a96b0;font-size:11px">{{ job.language || '—' }}</td>
              <td>
                <span v-if="job.grade" class="font-bold text-base" :class="'grade-' + job.grade.toLowerCase()">
                  {{ job.grade }}
                </span>
                <span v-else style="color:#4a5568">—</span>
              </td>
              <td style="color:#dde3ef;font-size:12px">{{ job.debt_score ?? '—' }}</td>
              <td>
                <span :style="{ color: job.issue_count > 0 ? '#f25555' : '#3ecf8e', fontWeight: 600 }">
                  {{ job.issue_count ?? 0 }}
                </span>
              </td>
              <td>
                <div class="flex items-center gap-1.5">
                  <span class="status-dot" :class="statusDot(job.status)"></span>
                  <span class="text-xs" :style="{ color: statusColor(job.status) }">{{ job.status }}</span>
                  <span v-if="job.status === 'running'" class="text-xs" style="color:#4a5568">({{ job.progress }}%)</span>
                </div>
              </td>
              <td style="font-size:11px;color:#4a5568;white-space:nowrap">{{ fmtDate(job.created_at) }}</td>
              <td>
                <button
                  class="ft-btn ft-btn-secondary"
                  style="font-size:11px;padding:3px 10px"
                  :disabled="job.status !== 'complete'"
                  @click.stop="loadJob(job)"
                >
                  {{ loadingJobId === job.job_id ? '…' : 'Load →' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Success toast -->
    <div v-if="toast" class="ft-card ft-card-body" style="border-left:2px solid #3ecf8e;padding:8px 12px">
      <span class="text-xs" style="color:#3ecf8e">{{ toast }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useScanStore } from '../stores/scan'
import { useReportStore } from '../stores/report'

const router = useRouter()
const scan   = useScanStore()
const report = useReportStore()

const jobs         = ref<any[]>([])
const loading      = ref(true)
const loadingJobId = ref<string | null>(null)
const toast        = ref('')

async function fetchJobs() {
  loading.value = true
  try {
    const token = localStorage.getItem('dl_token') || ''
    const r = await fetch('/api/scan/jobs?limit=50', {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    const d = await r.json()
    jobs.value = Array.isArray(d) ? d : (d.jobs ?? [])
  } catch {
    jobs.value = []
  } finally {
    loading.value = false
  }
}

async function loadJob(job: any) {
  if (job.status !== 'complete') return
  loadingJobId.value = job.job_id
  try {
    scan.jobId    = job.job_id
    scan.status   = 'complete'
    scan.progress = 100
    await report.fetchReport(job.job_id)
    showToast(`Loaded: ${shortRepo(job.repo_url)}`)
    router.push('/')
  } finally {
    loadingJobId.value = null
  }
}

function showToast(msg: string) {
  toast.value = msg
  setTimeout(() => { toast.value = '' }, 3000)
}

function shortRepo(url: string) {
  if (!url) return '—'
  return url.replace('https://github.com/', '').replace('upload://', 'upload: ')
}

function fmtDate(d: string) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function statusDot(s: string) {
  return { complete: 'status-ok', running: 'status-running', failed: 'status-critical', pending: 'status-inactive' }[s] ?? 'status-inactive'
}

function statusColor(s: string) {
  return { complete: '#3ecf8e', running: '#4a9ff5', failed: '#f25555', pending: '#8a96b0' }[s] ?? '#8a96b0'
}

onMounted(fetchJobs)
</script>
