<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <div class="ft-card-title" style="font-size:11px;letter-spacing:0.12em">TREND ANALYSIS</div>
        <div class="text-xs mt-0.5" style="color:#4a5568">Historical view across all scans</div>
      </div>
      <div class="flex gap-2">
        <button class="ft-btn ft-btn-secondary" @click="load">Refresh</button>
        <button class="ft-btn" style="background:#3d1a1a;color:#f25555;border:1px solid #6b2a2a" @click="clearAll">Clear History</button>
      </div>
    </div>

    <div v-if="loading" class="ft-card ft-card-body text-center py-8">
      <div class="flex items-center justify-center gap-2">
        <span class="status-dot status-running"></span>
        <span class="text-xs" style="color:#8a96b0">Loading trend data...</span>
      </div>
    </div>

    <div v-else-if="!history.length" class="ft-card ft-card-body text-center py-12">
      <div class="text-sm mb-1" style="color:#8a96b0">No scan history yet</div>
      <div class="text-xs" style="color:#4a5568">Run multiple scans to track trends over time</div>
    </div>

    <template v-else>
      <!-- Summary stat cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div class="ft-widget metric-tile">
          <div class="metric-value" style="color:#4a9ff5">{{ history.length }}</div>
          <div class="metric-label">Total Scans</div>
        </div>
        <div class="ft-widget metric-tile">
          <div class="metric-value" style="color:#f25555">{{ totalCritical }}</div>
          <div class="metric-label">Avg Critical / Scan</div>
        </div>
        <div class="ft-widget metric-tile">
          <div class="metric-value" :class="'grade-' + (latestGrade || 'f')">{{ latestGrade || '?' }}</div>
          <div class="metric-label">Latest Grade</div>
        </div>
        <div class="ft-widget metric-tile">
          <div class="metric-value" style="color:#dde3ef">{{ avgDebt }}</div>
          <div class="metric-label">Avg Debt Score</div>
        </div>
      </div>

      <!-- Issue count trend -->
      <div class="ft-card">
        <div class="ft-card-header">
          <span class="ft-card-title">Issues Over Time</span>
          <span class="ft-tag">{{ history.length }} scans</span>
        </div>
        <div class="ft-card-body">
          <apexchart
            type="line"
            height="240"
            :key="'trend-' + history.length"
            :options="trendOpts"
            :series="trendSeries"
          />
        </div>
      </div>

      <!-- Debt score trend -->
      <div class="ft-card">
        <div class="ft-card-header"><span class="ft-card-title">Debt Score Trend</span></div>
        <div class="ft-card-body">
          <apexchart
            type="area"
            height="180"
            :key="'debt-' + history.length"
            :options="debtOpts"
            :series="debtSeries"
          />
        </div>
      </div>

      <!-- Current scan breakdown (if report loaded) -->
      <template v-if="report.data">
        <div class="ft-card">
          <div class="ft-card-header"><span class="ft-card-title">Current Scan — Severity Distribution</span></div>
          <div class="ft-card-body">
            <apexchart
              type="bar"
              height="200"
              :options="sevOpts"
              :series="sevSeries"
            />
          </div>
        </div>

        <div class="ft-card">
          <div class="ft-card-header"><span class="ft-card-title">Current Scan — Debt Summary</span></div>
          <div class="ft-card-body">
            <div class="flex items-center gap-6">
              <div class="text-5xl font-bold" :class="'grade-' + (report.data.overall_grade ?? 'F')">
                {{ report.data.overall_grade ?? '?' }}
              </div>
              <div>
                <div class="text-2xl font-bold" style="color:#dde3ef">{{ report.data.overall_debt_score ?? '—' }}</div>
                <div class="text-xs" style="color:#8a96b0">Debt Score</div>
                <div class="text-xs mt-1" style="color:#4a5568">{{ debtMessage }}</div>
              </div>
              <div class="ml-auto text-right">
                <div class="text-xs" style="color:#4a5568">Repo</div>
                <div class="text-xs font-mono" style="color:#dde3ef">{{ shortRepo(report.data.repo_url) }}</div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Scan history table -->
      <div class="ft-card">
        <div class="ft-card-header"><span class="ft-card-title">All Scans</span></div>
        <div style="overflow-x:auto">
          <table class="ft-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Repository</th>
                <th>Grade</th>
                <th>Debt</th>
                <th>Issues</th>
                <th>Time</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="j in history" :key="j.job_id">
                <td style="font-size:11px;color:#4a5568;white-space:nowrap">{{ fmtDate(j.created_at) }}</td>
                <td class="font-mono text-xs" style="color:#8a96b0;max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
                  {{ shortRepo(j.repo_url) }}
                </td>
                <td>
                  <span class="font-bold" :class="'grade-' + (j.grade?.toLowerCase() || 'f')">{{ j.grade || '—' }}</span>
                </td>
                <td style="color:#dde3ef">{{ j.debt_score ?? '—' }}</td>
                <td :style="{ color: j.issue_count > 0 ? '#f25555' : '#3ecf8e', fontWeight: 600 }">{{ j.issue_count ?? 0 }}</td>
                <td style="font-size:11px;color:#4a5568">{{ j.scan_time_ms ? (j.scan_time_ms/1000).toFixed(1)+'s' : '—' }}</td>
                <td>
                  <button
                    title="Delete this scan"
                    style="background:none;border:none;cursor:pointer;color:#6b2a2a;font-size:14px;padding:2px 6px;border-radius:4px"
                    @mouseover="($event.target as HTMLElement).style.color='#f25555'"
                    @mouseleave="($event.target as HTMLElement).style.color='#6b2a2a'"
                    @click="deleteJob(j.job_id)"
                  >✕</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useReportStore } from '../stores/report'

const report = useReportStore()
const history = ref<any[]>([])
const loading = ref(false)

function authHeaders() {
  const token = localStorage.getItem('dl_token') || ''
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function load() {
  loading.value = true
  try {
    const r = await fetch('/api/scan/jobs?limit=50', { headers: authHeaders() })
    const d = await r.json()
    const all = (Array.isArray(d) ? d : (d.jobs ?? []))
    history.value = all.filter((j: any) => j.status === 'complete')
  } catch {
    history.value = []
  } finally {
    loading.value = false
  }
}

async function deleteJob(jobId: string) {
  if (!confirm('Delete this scan from history?')) return
  await fetch(`/api/scan/jobs/${jobId}`, { method: 'DELETE', headers: authHeaders() })
  history.value = history.value.filter((j: any) => j.job_id !== jobId)
}

async function clearAll() {
  if (!confirm('Delete ALL scan history? This cannot be undone.')) return
  await fetch('/api/scan/jobs', { method: 'DELETE', headers: authHeaders() })
  history.value = []
}

onMounted(load)

const totalCritical = computed(() => {
  if (!history.value.length) return 0
  // We don't have per-sev breakdown here; just show average total issues
  const avg = history.value.reduce((s: number, j: any) => s + (j.issue_count ?? 0), 0) / history.value.length
  return Math.round(avg)
})

const latestGrade = computed(() => history.value[0]?.grade ?? null)
const avgDebt = computed(() => {
  const vals = history.value.map((j: any) => j.debt_score).filter((v: any) => v != null)
  if (!vals.length) return '—'
  return (vals.reduce((a: number, b: number) => a + b, 0) / vals.length).toFixed(1)
})

const labels = computed(() => history.value.map((j: any) =>
  new Date(j.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
).reverse())

const trendSeries = computed(() => [{
  name: 'Issues',
  data: [...history.value].reverse().map((j: any) => j.issue_count ?? 0),
}])

const trendOpts = computed(() => ({
  chart: { background: 'transparent', foreColor: '#8a96b0', toolbar: { show: false }, zoom: { enabled: false } },
  theme: { mode: 'dark' },
  xaxis: { categories: labels.value, labels: { style: { colors: '#8a96b0', fontSize: '10px' } } },
  yaxis: { labels: { style: { colors: '#8a96b0', fontSize: '10px' } } },
  colors: ['#f25555'],
  stroke: { width: 2, curve: 'smooth' },
  markers: { size: 5 },
  grid: { borderColor: '#1e2d47' },
  tooltip: { theme: 'dark' },
  dataLabels: { enabled: false },
}))

const debtSeries = computed(() => [{
  name: 'Debt Score',
  data: [...history.value].reverse().map((j: any) => j.debt_score ?? 0),
}])

const debtOpts = computed(() => ({
  chart: { background: 'transparent', foreColor: '#8a96b0', toolbar: { show: false }, zoom: { enabled: false } },
  theme: { mode: 'dark' },
  xaxis: { categories: labels.value, labels: { style: { colors: '#8a96b0', fontSize: '10px' } } },
  yaxis: { min: 0, max: 100, labels: { style: { colors: '#8a96b0', fontSize: '10px' } } },
  colors: ['#f26d21'],
  stroke: { width: 2, curve: 'smooth' },
  fill: { type: 'gradient', gradient: { opacityFrom: 0.3, opacityTo: 0.05 } },
  grid: { borderColor: '#1e2d47' },
  tooltip: { theme: 'dark' },
  dataLabels: { enabled: false },
}))

// Current scan breakdown
const sevSeries = computed(() => [{
  name: 'Issues',
  data: [
    report.data?.issues_by_severity?.critical ?? 0,
    report.data?.issues_by_severity?.major ?? 0,
    report.data?.issues_by_severity?.minor ?? 0,
    report.data?.issues_by_severity?.info ?? 0,
  ],
}])

const sevOpts = computed(() => ({
  chart: { background: 'transparent', foreColor: '#8a96b0', toolbar: { show: false } },
  theme: { mode: 'dark' },
  xaxis: { categories: ['Critical', 'Major', 'Minor', 'Info'], labels: { style: { colors: '#8a96b0', fontSize: '11px' } } },
  yaxis: { labels: { style: { colors: '#8a96b0', fontSize: '11px' } } },
  colors: ['#f25555', '#f26d21', '#f5a623', '#4a9ff5'],
  dataLabels: { enabled: true, style: { fontSize: '11px', colors: ['#dde3ef'] } },
  plotOptions: { bar: { borderRadius: 2, distributed: true, columnWidth: '50%' } },
  legend: { show: false },
  grid: { borderColor: '#1e2d47' },
  tooltip: { theme: 'dark' },
}))

const debtMessage = computed(() => {
  const score = report.data?.overall_debt_score ?? 0
  if (score >= 80) return 'High technical debt — immediate remediation recommended'
  if (score >= 60) return 'Moderate technical debt — address in next sprint'
  if (score >= 40) return 'Manageable debt — address during routine maintenance'
  return 'Low technical debt — project is in good health'
})

function shortRepo(url: string) {
  if (!url) return '—'
  return url.replace('https://github.com/', '').replace('upload://', 'upload: ')
}

function fmtDate(d: string) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' })
}
</script>
