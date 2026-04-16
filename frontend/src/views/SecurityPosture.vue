<template>
  <div class="space-y-4">
    <div class="ft-card-title" style="font-size:11px;letter-spacing:0.12em">SECURITY POSTURE</div>

    <div v-if="!report.data" class="ft-card ft-card-body text-center py-12">
      <div class="text-sm mb-1" style="color:#8a96b0">No scan loaded</div>
      <div class="text-xs" style="color:#4a5568">Load a scan to see security posture</div>
    </div>

    <template v-else>
      <!-- Score gauge + OWASP -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="ft-card">
          <div class="ft-card-header"><span class="ft-card-title">Security Score</span></div>
          <div class="ft-card-body">
            <apexchart
              type="radialBar"
              height="220"
              :options="gaugeOpts"
              :series="[securityScore]"
            />
            <div class="text-center text-xs" style="color:#8a96b0">
              {{ report.criticalIssues.length }} critical &mdash;
              {{ secrets.length }} secrets &mdash;
              {{ securityIssues.length }} security findings
            </div>
          </div>
        </div>

        <div class="ft-card">
          <div class="ft-card-header"><span class="ft-card-title">CWE Distribution</span></div>
          <div class="ft-card-body">
            <apexchart
              v-if="cweSeries.length"
              type="bar"
              height="220"
              :options="cweOpts"
              :series="[{ name: 'Count', data: cweCounts }]"
            />
            <div v-else class="text-center py-8 text-xs" style="color:#4a5568">No CWE data</div>
          </div>
        </div>
      </div>

      <!-- OWASP Top 10 -->
      <div class="ft-card">
        <div class="ft-card-header"><span class="ft-card-title">OWASP Top 10 Coverage</span></div>
        <div style="overflow-x:auto">
          <table class="ft-table">
            <thead>
              <tr>
                <th>Category</th>
                <th>Findings</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in owaspRows" :key="row.cat">
                <td style="color:#dde3ef">{{ row.cat }}</td>
                <td>
                  <span :style="{ color: row.count > 0 ? '#f25555' : '#3ecf8e' }">{{ row.count }}</span>
                </td>
                <td>
                  <span class="status-dot" :class="row.count > 0 ? 'status-critical' : 'status-ok'"></span>
                  <span class="ml-2 text-xs" :style="{ color: row.count > 0 ? '#f25555' : '#3ecf8e' }">
                    {{ row.count > 0 ? 'Findings' : 'Clean' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Secrets -->
      <div class="ft-card">
        <div class="ft-card-header">
          <span class="ft-card-title">Secrets Found</span>
          <span class="ft-tag" :style="{ color: secrets.length ? '#f25555' : '#3ecf8e' }">{{ secrets.length }}</span>
        </div>
        <div v-if="!secrets.length" class="ft-card-body text-xs" style="color:#4a5568">No secrets detected</div>
        <div v-else style="overflow-x:auto">
          <table class="ft-table">
            <thead>
              <tr>
                <th>Severity</th>
                <th>File:Line</th>
                <th>Message</th>
                <th>Tool</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in secrets" :key="s.id">
                <td><span class="sev sev-critical">critical</span></td>
                <td class="font-mono text-xs" style="color:#8a96b0">{{ s.file_path }}:{{ s.line_start }}</td>
                <td style="max-width:300px" class="truncate">{{ s.message }}</td>
                <td style="font-size:11px;color:#4a5568">{{ s.tool }}</td>
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

const report = useReportStore()

const secrets = computed(() => report.issues.filter((i: any) => i.category === 'secret'))
const securityIssues = computed(() => report.issues.filter((i: any) => i.category === 'security'))

const securityScore = computed(() => {
  if (!report.data) return 0
  const c = report.criticalIssues.length
  const s = secrets.value.length
  const score = Math.max(0, 100 - c * 10 - s * 15 - securityIssues.value.length * 2)
  return Math.min(100, score)
})

const gaugeOpts = computed(() => ({
  chart: { background: 'transparent', foreColor: '#8a96b0', toolbar: { show: false } },
  theme: { mode: 'dark' },
  plotOptions: {
    radialBar: {
      startAngle: -135,
      endAngle: 135,
      hollow: { size: '55%' },
      track: { background: '#1e2d47' },
      dataLabels: {
        name: { show: true, color: '#8a96b0', fontSize: '11px', offsetY: 20 },
        value: {
          color: securityScore.value >= 70 ? '#3ecf8e' : securityScore.value >= 40 ? '#f5a623' : '#f25555',
          fontSize: '28px',
          fontWeight: 700,
          offsetY: -10,
          formatter: (v: number) => v + '',
        },
      },
    },
  },
  fill: {
    type: 'gradient',
    gradient: {
      shade: 'dark',
      type: 'horizontal',
      colorStops: [
        { offset: 0, color: '#f25555' },
        { offset: 50, color: '#f5a623' },
        { offset: 100, color: '#3ecf8e' },
      ],
    },
  },
  labels: ['Security Score'],
  tooltip: { enabled: false },
}))

const OWASP_CATS = [
  'A01 Broken Access Control',
  'A02 Cryptographic Failures',
  'A03 Injection',
  'A04 Insecure Design',
  'A05 Security Misconfiguration',
  'A06 Vulnerable Components',
  'A07 Auth Failures',
  'A08 Data Integrity Failures',
  'A09 Logging Failures',
  'A10 SSRF',
]

const owaspRows = computed(() =>
  OWASP_CATS.map(cat => {
    const count = report.issues.filter((i: any) =>
      (i.owasp_category || '').includes(cat.split(' ')[0])
    ).length
    return { cat, count }
  })
)

const cweMap = computed(() => {
  const m: Record<string, number> = {}
  report.issues.forEach((i: any) => {
    if (i.cwe_id) m[i.cwe_id] = (m[i.cwe_id] || 0) + 1
  })
  return m
})

const cweSeries = computed(() =>
  Object.entries(cweMap.value)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
)

const cweCounts = computed(() => cweSeries.value.map(e => e[1]))

const cweOpts = computed(() => ({
  chart: { background: 'transparent', foreColor: '#8a96b0', toolbar: { show: false } },
  theme: { mode: 'dark' },
  xaxis: {
    categories: cweSeries.value.map(e => e[0]),
    labels: { style: { colors: '#8a96b0', fontSize: '10px' } },
  },
  yaxis: { labels: { style: { colors: '#8a96b0', fontSize: '10px' } } },
  colors: ['#f25555'],
  dataLabels: { enabled: false },
  plotOptions: { bar: { borderRadius: 2, horizontal: false } },
  grid: { borderColor: '#1e2d47' },
  tooltip: { theme: 'dark' },
}))
</script>
