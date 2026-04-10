<template>
  <div class="space-y-4">
    <div class="ft-card-title" style="font-size:11px;letter-spacing:0.12em">TREND ANALYSIS</div>

    <div v-if="!report.data" class="ft-card ft-card-body text-center py-12">
      <div class="text-sm mb-1" style="color:#8a96b0">No scan loaded</div>
      <div class="text-xs" style="color:#4a5568">Load a scan to see trend data</div>
    </div>

    <template v-else>
      <!-- Info banner -->
      <div class="ft-card ft-card-body" style="border-left:2px solid #4a9ff5">
        <div class="text-xs" style="color:#8a96b0">
          Trend tracking requires multiple scans of the same project. Showing current scan snapshot below.
          Register a project with auto-rescan to track changes over time.
        </div>
      </div>

      <!-- Current snapshot bar chart -->
      <div class="ft-card">
        <div class="ft-card-header"><span class="ft-card-title">Issue Severity Distribution — Current Scan</span></div>
        <div class="ft-card-body">
          <apexchart
            type="bar"
            height="240"
            :options="sevOpts"
            :series="sevSeries"
          />
        </div>
      </div>

      <!-- Category breakdown -->
      <div class="ft-card">
        <div class="ft-card-header"><span class="ft-card-title">Issues by Category</span></div>
        <div class="ft-card-body">
          <apexchart
            v-if="catSeries.length"
            type="bar"
            height="200"
            :options="catOpts"
            :series="[{ name: 'Issues', data: catCounts }]"
          />
          <div v-else class="text-center py-8 text-xs" style="color:#4a5568">No category data</div>
        </div>
      </div>

      <!-- Debt message -->
      <div class="ft-card">
        <div class="ft-card-header"><span class="ft-card-title">Debt Score Summary</span></div>
        <div class="ft-card-body">
          <div class="flex items-center gap-4">
            <div class="text-5xl font-bold" :class="'grade-' + (report.data.overall_grade ?? 'F')">
              {{ report.data.overall_grade ?? '?' }}
            </div>
            <div>
              <div class="text-2xl font-bold" style="color:#dde3ef">{{ report.data.overall_debt_score ?? '—' }}</div>
              <div class="text-xs" style="color:#8a96b0">Debt Score / 100</div>
              <div class="text-xs mt-1" style="color:#4a5568">
                {{ debtMessage }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
<script setup lang="ts">
import { computed } from 'vue'
import { useReportStore } from '../stores/report'

const report = useReportStore()

const sevOpts = computed(() => ({
  chart: { background: 'transparent', foreColor: '#8a96b0', toolbar: { show: false } },
  theme: { mode: 'dark' },
  xaxis: {
    categories: ['Critical', 'Major', 'Minor', 'Info'],
    labels: { style: { colors: '#8a96b0', fontSize: '11px' } },
  },
  yaxis: { labels: { style: { colors: '#8a96b0', fontSize: '11px' } } },
  colors: ['#f25555', '#f26d21', '#f5a623', '#4a9ff5'],
  dataLabels: { enabled: true, style: { fontSize: '11px', colors: ['#dde3ef'] } },
  plotOptions: { bar: { borderRadius: 2, distributed: true, columnWidth: '50%' } },
  legend: { show: false },
  grid: { borderColor: '#1e2d47' },
  tooltip: { theme: 'dark' },
}))

const sevSeries = computed(() => [{
  name: 'Issues',
  data: [
    report.data?.issues_by_severity?.critical ?? 0,
    report.data?.issues_by_severity?.major ?? 0,
    report.data?.issues_by_severity?.minor ?? 0,
    report.data?.issues_by_severity?.info ?? 0,
  ],
}])

const catEntries = computed(() =>
  Object.entries(report.data?.issues_by_category ?? {})
    .sort((a: any, b: any) => b[1] - a[1])
    .slice(0, 8)
)

const catSeries = computed(() => catEntries.value.map(e => e[0]))
const catCounts = computed(() => catEntries.value.map(e => e[1]))

const catOpts = computed(() => ({
  chart: { background: 'transparent', foreColor: '#8a96b0', toolbar: { show: false } },
  theme: { mode: 'dark' },
  xaxis: {
    categories: catSeries.value,
    labels: { style: { colors: '#8a96b0', fontSize: '11px' } },
  },
  yaxis: { labels: { style: { colors: '#8a96b0', fontSize: '11px' } } },
  colors: ['#f26d21'],
  dataLabels: { enabled: false },
  plotOptions: { bar: { borderRadius: 2, horizontal: true } },
  grid: { borderColor: '#1e2d47' },
  tooltip: { theme: 'dark' },
}))

const debtMessage = computed(() => {
  const score = report.data?.overall_debt_score ?? 0
  if (score >= 80) return 'High technical debt — immediate remediation recommended'
  if (score >= 60) return 'Moderate technical debt — schedule remediation in next sprint'
  if (score >= 40) return 'Manageable debt — address during routine maintenance'
  return 'Low technical debt — project is in good health'
})
</script>