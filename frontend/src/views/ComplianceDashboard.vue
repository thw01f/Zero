<template>
  <div class="space-y-4">
    <div class="ft-card-title" style="font-size:11px;letter-spacing:0.12em">COMPLIANCE DASHBOARD</div>

    <div v-if="!report.data" class="ft-card ft-card-body text-center py-12">
      <div class="text-sm mb-1" style="color:#8a96b0">No scan loaded</div>
      <div class="text-xs" style="color:#4a5568">Load a scan to see compliance results</div>
    </div>

    <template v-else>
      <!-- Summary donut + stats -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="ft-card">
          <div class="ft-card-header"><span class="ft-card-title">Compliance Overview</span></div>
          <div class="ft-card-body">
            <apexchart
              v-if="report.compliance.length"
              type="donut"
              height="220"
              :options="donutOpts"
              :series="donutSeries"
            />
            <div v-else class="text-center py-8 text-xs" style="color:#4a5568">No compliance data</div>
          </div>
        </div>

        <div class="grid grid-cols-3 gap-3 content-start">
          <div class="ft-widget metric-tile">
            <div class="metric-value" style="color:#3ecf8e">{{ passCount }}</div>
            <div class="metric-label">Pass</div>
          </div>
          <div class="ft-widget metric-tile">
            <div class="metric-value" style="color:#f5a623">{{ partialCount }}</div>
            <div class="metric-label">Partial</div>
          </div>
          <div class="ft-widget metric-tile">
            <div class="metric-value" style="color:#f25555">{{ failCount }}</div>
            <div class="metric-label">Fail</div>
          </div>
        </div>
      </div>

      <!-- Compliance table -->
      <div class="ft-card">
        <div class="ft-card-header">
          <span class="ft-card-title">Control Results</span>
          <div class="flex gap-2">
            <button
              v-for="f in ['ALL', 'owasp', 'nist']"
              :key="f"
              class="ft-btn"
              :class="activeFilter === f ? 'ft-btn-primary' : 'ft-btn-secondary'"
              @click="activeFilter = f"
            >{{ f.toUpperCase() }}</button>
          </div>
        </div>
        <div style="overflow-x:auto">
          <table class="ft-table">
            <thead>
              <tr>
                <th>Standard</th>
                <th>Control ID</th>
                <th>Control</th>
                <th>Status</th>
                <th>Issues</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in filteredCompliance" :key="c.control_id">
                <td>
                  <span class="ft-tag" style="text-transform:uppercase">{{ c.framework }}</span>
                </td>
                <td style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#4a9ff5">{{ c.control_id }}</td>
                <td style="max-width:280px" class="truncate">{{ c.control_name }}</td>
                <td>
                  <div class="flex items-center gap-2">
                    <span class="status-dot" :class="statusDot(c.status)"></span>
                    <span class="text-xs" :style="{ color: statusColor(c.status) }">{{ c.status }}</span>
                  </div>
                </td>
                <td>
                  <span :style="{ color: c.issue_count > 0 ? '#f25555' : '#3ecf8e' }">{{ c.issue_count }}</span>
                </td>
              </tr>
              <tr v-if="!filteredCompliance.length">
                <td colspan="5" class="text-center py-8" style="color:#4a5568">No compliance data available</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useReportStore } from '../stores/report'

const report = useReportStore()
const activeFilter = ref('ALL')

const filteredCompliance = computed(() =>
  activeFilter.value === 'ALL'
    ? report.compliance
    : report.compliance.filter((c: any) => c.framework === activeFilter.value)
)

const passCount = computed(() => report.compliance.filter((c: any) => c.status === 'pass').length)
const partialCount = computed(() => report.compliance.filter((c: any) => c.status === 'partial').length)
const failCount = computed(() => report.compliance.filter((c: any) => c.status === 'fail').length)

const donutSeries = computed(() => [passCount.value, partialCount.value, failCount.value])
const donutOpts = computed(() => ({
  chart: { background: 'transparent', foreColor: '#8a96b0', toolbar: { show: false } },
  theme: { mode: 'dark' },
  labels: ['Pass', 'Partial', 'Fail'],
  colors: ['#3ecf8e', '#f5a623', '#f25555'],
  legend: { position: 'bottom', fontSize: '11px', labels: { colors: '#8a96b0' } },
  dataLabels: { enabled: false },
  stroke: { width: 1, colors: ['#141d30'] },
  plotOptions: { pie: { donut: { size: '60%' } } },
  tooltip: { theme: 'dark' },
}))

function statusDot(s: string) {
  return { pass: 'status-ok', partial: 'status-warn', fail: 'status-critical' }[s] ?? 'status-inactive'
}

function statusColor(s: string) {
  return { pass: '#3ecf8e', partial: '#f5a623', fail: '#f25555' }[s] ?? '#8a96b0'
}
</script>
