<template>
  <div class="space-y-4">
    <div class="ft-card-title" style="font-size:11px;letter-spacing:0.12em">GIT INTELLIGENCE</div>

    <div v-if="!report.data" class="ft-card ft-card-body text-center py-12">
      <div class="text-sm mb-1" style="color:#8a96b0">No scan loaded</div>
      <div class="text-xs" style="color:#4a5568">Load a scan to see git intelligence</div>
    </div>

    <template v-else>
      <!-- Top churned files chart -->
      <div class="ft-card">
        <div class="ft-card-header"><span class="ft-card-title">Top 10 Churned Files</span></div>
        <div class="ft-card-body">
          <apexchart
            v-if="top10.length"
            type="bar"
            height="260"
            :options="churnOpts"
            :series="churnSeries"
          />
          <div v-else class="text-center py-8 text-xs" style="color:#4a5568">No churn data available</div>
        </div>
      </div>

      <!-- Module table -->
      <div class="ft-card">
        <div class="ft-card-header">
          <span class="ft-card-title">Module Analysis</span>
          <span class="ft-tag">{{ sortedModules.length }} modules</span>
        </div>
        <div style="overflow-x:auto">
          <table class="ft-table">
            <thead>
              <tr>
                <th class="sortable" @click="sortField = 'path'">Module Path</th>
                <th class="sortable" @click="sortField = 'loc'">LOC</th>
                <th class="sortable" @click="sortField = 'churn_count'">Churn</th>
                <th class="sortable" @click="sortField = 'debt_score'">Debt Score</th>
                <th>Grade</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in sortedModules" :key="m.id ?? m.path">
                <td class="font-mono text-xs" style="color:#8a96b0">{{ m.path }}</td>
                <td style="color:#dde3ef">{{ m.loc ?? '—' }}</td>
                <td :style="{ color: (m.churn_count ?? 0) > 20 ? '#f25555' : '#dde3ef' }">
                  {{ m.churn_count ?? '—' }}
                </td>
                <td>
                  <div class="flex items-center gap-2">
                    <div class="ft-progress" style="width:60px">
                      <div
                        class="ft-progress-bar"
                        :style="{
                          width: (m.debt_score ?? 0) + '%',
                          background: debtColor(m.debt_score),
                        }"
                      ></div>
                    </div>
                    <span style="color:#dde3ef">{{ m.debt_score ?? '—' }}</span>
                  </div>
                </td>
                <td>
                  <span class="font-bold text-sm" :class="'grade-' + (m.grade ?? 'F')">{{ m.grade ?? '—' }}</span>
                </td>
              </tr>
              <tr v-if="!sortedModules.length">
                <td colspan="5" class="text-center py-8" style="color:#4a5568">No module data</td>
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
const sortField = ref<'churn_count' | 'debt_score' | 'loc' | 'path'>('churn_count')

const sortedModules = computed(() =>
  [...report.modules].sort((a: any, b: any) => {
    if (sortField.value === 'path') return (a.path || '').localeCompare(b.path || '')
    return (b[sortField.value] ?? 0) - (a[sortField.value] ?? 0)
  })
)

const top10 = computed(() =>
  [...report.modules]
    .sort((a: any, b: any) => (b.churn_count ?? 0) - (a.churn_count ?? 0))
    .slice(0, 10)
)

const churnOpts = computed(() => ({
  chart: { background: 'transparent', foreColor: '#8a96b0', toolbar: { show: false } },
  theme: { mode: 'dark' },
  xaxis: {
    categories: top10.value.map((m: any) => m.path?.split('/').pop() ?? m.path),
    labels: { style: { colors: '#8a96b0', fontSize: '10px' } },
  },
  yaxis: { labels: { style: { colors: '#8a96b0', fontSize: '10px' } } },
  colors: ['#f26d21'],
  dataLabels: { enabled: false },
  plotOptions: { bar: { borderRadius: 2, horizontal: false, columnWidth: '60%' } },
  grid: { borderColor: '#1e2d47' },
  tooltip: { theme: 'dark' },
}))

const churnSeries = computed(() => [{
  name: 'Churn Count',
  data: top10.value.map((m: any) => m.churn_count ?? 0),
}])

function debtColor(score: number) {
  if (score >= 70) return '#f25555'
  if (score >= 40) return '#f5a623'
  return '#3ecf8e'
}
</script>
