<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <div class="ft-card-title" style="font-size:11px;letter-spacing:0.12em">COMMAND CENTER</div>
        <div v-if="report.data" class="text-xs mt-0.5" style="color:#4a5568">
          {{ report.data.repo_url }} &mdash; {{ report.data.language }} &mdash; {{ report.data.scan_time_ms }}ms
        </div>
      </div>
      <div v-if="report.data" class="flex items-center gap-3">
        <span class="ft-tag">Job: {{ scan.jobId }}</span>
      </div>
    </div>

    <!-- No data -->
    <div v-if="!report.data" class="ft-card ft-card-body text-center py-16">
      <div class="mb-3" style="color:#4a5568">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" class="mx-auto">
          <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
        </svg>
      </div>
      <div class="text-sm mb-1" style="color:#8a96b0">No scan results loaded</div>
      <div class="text-xs" style="color:#4a5568">Enter a GitHub repository URL in the sidebar and click Scan</div>
    </div>

    <template v-else>
      <!-- Stat row -->
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <StatCard
          label="Total Issues"
          :value="report.issues.length"
          color="default"
          icon="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
        />
        <StatCard
          label="Critical"
          :value="report.criticalIssues.length"
          color="red"
          icon="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"
        />
        <StatCard
          label="Debt Score"
          :value="report.data.overall_debt_score ?? '—'"
          :sub="'Grade: ' + (report.data.overall_grade ?? '?')"
          :color="gradeToColor(report.data.overall_grade)"
          icon="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
        />
        <StatCard
          label="Modules"
          :value="report.modules.length"
          color="blue"
          icon="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
        />
        <StatCard
          label="Secrets"
          :value="report.data.secret_count ?? 0"
          color="red"
          icon="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
        />
        <StatCard
          label="Scan Time"
          :value="report.data.scan_time_ms ? (report.data.scan_time_ms / 1000).toFixed(1) + 's' : '—'"
          color="default"
          icon="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </div>

      <!-- Charts row -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="ft-card">
          <div class="ft-card-header">
            <span class="ft-card-title">Issues by Category</span>
          </div>
          <div class="ft-card-body">
            <apexchart
              v-if="categorySeries.length"
              type="donut"
              height="220"
              :options="categoryChartOpts"
              :series="categorySeries"
            />
            <div v-else class="text-center py-8 text-xs" style="color:#4a5568">No category data</div>
          </div>
        </div>

        <div class="ft-card">
          <div class="ft-card-header">
            <span class="ft-card-title">Top 5 Modules by Debt Score</span>
          </div>
          <div class="ft-card-body">
            <apexchart
              v-if="top5Modules.length"
              type="bar"
              height="220"
              :options="moduleChartOpts"
              :series="moduleSeries"
            />
            <div v-else class="text-center py-8 text-xs" style="color:#4a5568">No module data</div>
          </div>
        </div>
      </div>

      <!-- Executive summary -->
      <div class="ft-card">
        <div class="ft-card-header">
          <span class="ft-card-title">Executive Summary</span>
        </div>
        <div class="ft-card-body">
          <p class="text-sm leading-relaxed whitespace-pre-wrap" style="color:#dde3ef">
            {{ report.data.summary_narrative || 'No summary available.' }}
          </p>
        </div>
      </div>

      <!-- Top risks -->
      <div class="ft-card">
        <div class="ft-card-header">
          <span class="ft-card-title">Top Risks</span>
          <span class="ft-tag">{{ topCritical.length }} critical</span>
        </div>
        <div class="ft-card-body p-0">
          <div v-if="!topCritical.length" class="px-4 py-6 text-center text-xs" style="color:#4a5568">
            No critical issues found
          </div>
          <table v-else class="ft-table">
            <thead>
              <tr>
                <th>Severity</th>
                <th>Location</th>
                <th>Message</th>
                <th>Rule</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="issue in topCritical" :key="issue.id">
                <td><span class="sev sev-critical">Critical</span></td>
                <td class="font-mono text-xs" style="color:#8a96b0">{{ issue.file_path }}:{{ issue.line_start }}</td>
                <td style="color:#dde3ef;max-width:300px" class="truncate">{{ issue.message }}</td>
                <td class="ft-tag" style="color:#4a9ff5">{{ issue.rule_id }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useReportStore } from '../stores/report'
import { useScanStore } from '../stores/scan'
import StatCard from '../components/StatCard.vue'

const report = useReportStore()
const scan = useScanStore()

function gradeToColor(g: string): 'green' | 'blue' | 'yellow' | 'orange' | 'red' | 'default' {
  const map: Record<string, 'green' | 'blue' | 'yellow' | 'orange' | 'red'> = {
    A: 'green', B: 'blue', C: 'yellow', D: 'orange', F: 'red',
  }
  return map[g] ?? 'default'
}

const topCritical = computed(() => report.criticalIssues.slice(0, 5))

const top5Modules = computed(() =>
  [...report.modules].sort((a: any, b: any) => b.debt_score - a.debt_score).slice(0, 5)
)

const categoryChartOpts = computed(() => ({
  chart: { background: 'transparent', foreColor: '#8a96b0', toolbar: { show: false } },
  theme: { mode: 'dark' },
  labels: Object.keys(report.data?.issues_by_category || {}),
  colors: ['#f25555', '#f26d21', '#f5a623', '#3ecf8e', '#4a9ff5', '#a78bfa', '#26c6da'],
  legend: { position: 'bottom', fontSize: '11px', labels: { colors: '#8a96b0' } },
  dataLabels: { enabled: false },
  stroke: { width: 1, colors: ['#141d30'] },
  plotOptions: { pie: { donut: { size: '60%' } } },
  tooltip: { theme: 'dark' },
}))

const categorySeries = computed(() =>
  Object.values(report.data?.issues_by_category || {}) as number[]
)

const moduleChartOpts = computed(() => ({
  chart: { background: 'transparent', foreColor: '#8a96b0', toolbar: { show: false } },
  theme: { mode: 'dark' },
  xaxis: {
    categories: top5Modules.value.map((m: any) => m.path?.split('/').pop() ?? m.path),
    labels: { style: { colors: '#8a96b0', fontSize: '11px' } },
  },
  yaxis: { labels: { style: { colors: '#8a96b0', fontSize: '11px' } } },
  colors: ['#f26d21'],
  dataLabels: { enabled: false },
  plotOptions: { bar: { horizontal: true, borderRadius: 2, barHeight: '60%' } },
  grid: { borderColor: '#1e2d47' },
  tooltip: { theme: 'dark' },
}))

const moduleSeries = computed(() => [{
  name: 'Debt Score',
  data: top5Modules.value.map((m: any) => m.debt_score ?? 0),
}])
</script>
