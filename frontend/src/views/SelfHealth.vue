<template>
  <div class="space-y-4">
    <div class="ft-card-title" style="font-size:11px;letter-spacing:0.12em">SELF-HEALTH MONITOR</div>

    <div v-if="loading" class="ft-card ft-card-body text-center py-8">
      <div class="flex items-center justify-center gap-2">
        <span class="status-dot status-running"></span>
        <span class="text-xs" style="color:#8a96b0">Loading health data...</span>
      </div>
    </div>

    <template v-else>
      <!-- Platform status tiles -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div v-for="svc in platformServices" :key="svc.name" class="ft-widget metric-tile">
          <div class="flex items-center gap-2 mb-1">
            <span class="status-dot" :class="svc.dot"></span>
            <span class="metric-label" style="margin:0">{{ svc.name }}</span>
          </div>
          <div class="metric-value text-sm" :style="{ color: svc.color }">{{ svc.status }}</div>
          <div v-if="svc.detail" class="metric-sub">{{ svc.detail }}</div>
        </div>
      </div>

      <!-- Scanner availability -->
      <div class="ft-card">
        <div class="ft-card-header"><span class="ft-card-title">Scanner Availability</span></div>
        <div class="ft-card-body">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
            <div
              v-for="(ver, name) in scannerVersions"
              :key="name"
              class="flex items-center justify-between p-2 rounded"
              style="background:#0f1526;border:1px solid #1e2d47"
            >
              <span class="font-mono text-xs" style="color:#dde3ef">{{ name }}</span>
              <div class="flex items-center gap-1">
                <span class="status-dot" :class="scannerDot(ver)"></span>
                <span class="text-xs" :style="{ color: scannerColor(ver) }">
                  {{ ver === 'missing' ? 'missing' : ver === 'error' ? 'error' : 'ok' }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- LLM models -->
      <div v-if="models.length" class="ft-card">
        <div class="ft-card-header"><span class="ft-card-title">LLM Models</span></div>
        <div style="overflow-x:auto">
          <table class="ft-table">
            <thead>
              <tr>
                <th>Model ID</th>
                <th>Type</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in models" :key="m.id ?? m.name">
                <td class="font-mono text-xs" style="color:#4a9ff5">{{ m.id || m.name }}</td>
                <td style="color:#8a96b0">{{ m.type || m.object || '—' }}</td>
                <td>
                  <span class="status-dot status-ok"></span>
                  <span class="ml-2 text-xs" style="color:#3ecf8e">available</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Raw health data -->
      <div v-if="health" class="ft-card">
        <div class="ft-card-header">
          <span class="ft-card-title">System Metrics</span>
          <span class="ft-tag">{{ formatDate(health.captured_at) }}</span>
        </div>
        <div class="ft-card-body">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div class="metric-label">Own CVEs</div>
              <div class="metric-value text-lg" :style="{ color: (health.own_cve_count ?? 0) > 0 ? '#f25555' : '#3ecf8e' }">
                {{ health.own_cve_count ?? 0 }}
              </div>
            </div>
            <div>
              <div class="metric-label">Disk Free</div>
              <div class="metric-value text-lg">{{ health.disk_free_gb ?? '—' }} <span class="text-sm" style="color:#8a96b0">GB</span></div>
            </div>
            <div>
              <div class="metric-label">Queue Depth</div>
              <div class="metric-value text-lg">{{ health.redis_queue_depth ?? '—' }}</div>
            </div>
            <div>
              <div class="metric-label">Status</div>
              <div class="metric-value text-lg capitalize" :style="{ color: statusColor(health.status) }">{{ health.status }}</div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const health = ref<any>(null)
const models = ref<any[]>([])
const loading = ref(true)

const SCANNERS = ['bandit', 'ruff', 'lizard', 'gitleaks', 'trivy', 'hadolint', 'checkov']

const scannerVersions = computed(() => {
  if (!health.value?.scanner_versions) {
    return Object.fromEntries(SCANNERS.map(s => [s, 'unknown']))
  }
  return health.value.scanner_versions
})

const platformServices = computed(() => {
  const h = health.value
  return [
    {
      name: 'API',
      status: h ? 'Online' : 'Unknown',
      dot: h ? 'status-ok' : 'status-inactive',
      color: h ? '#3ecf8e' : '#8a96b0',
      detail: null,
    },
    {
      name: 'Database',
      status: h?.db_ok === false ? 'Degraded' : h ? 'Online' : 'Unknown',
      dot: h?.db_ok === false ? 'status-warn' : h ? 'status-ok' : 'status-inactive',
      color: h?.db_ok === false ? '#f5a623' : '#3ecf8e',
      detail: null,
    },
    {
      name: 'Redis',
      status: h?.redis_ok === false ? 'Degraded' : h ? 'Online' : 'Unknown',
      dot: h?.redis_ok === false ? 'status-warn' : h ? 'status-ok' : 'status-inactive',
      color: h?.redis_ok === false ? '#f5a623' : '#3ecf8e',
      detail: h?.redis_queue_depth != null ? `Queue: ${h.redis_queue_depth}` : null,
    },
    {
      name: 'LLM Backend',
      status: models.value.length ? 'Online' : h ? 'Unknown' : 'Unknown',
      dot: models.value.length ? 'status-ok' : 'status-inactive',
      color: models.value.length ? '#3ecf8e' : '#8a96b0',
      detail: models.value.length ? `${models.value.length} model(s)` : null,
    },
  ]
})

function scannerDot(ver: string) {
  if (ver === 'missing') return 'status-critical'
  if (ver === 'error') return 'status-warn'
  return 'status-ok'
}

function scannerColor(ver: string) {
  if (ver === 'missing') return '#f25555'
  if (ver === 'error') return '#f5a623'
  return '#3ecf8e'
}

function statusColor(s: string) {
  return { healthy: '#3ecf8e', degraded: '#f5a623', critical: '#f25555' }[s] ?? '#8a96b0'
}

function formatDate(d: string) {
  if (!d) return '—'
  return new Date(d).toLocaleString()
}

onMounted(async () => {
  loading.value = true
  try {
    const [healthRes, modelsRes] = await Promise.allSettled([
      axios.get('/api/health'),
      axios.get('/api/analyze/models'),
    ])
    if (healthRes.status === 'fulfilled') health.value = healthRes.value.data
    if (modelsRes.status === 'fulfilled') {
      const d = modelsRes.value.data
      models.value = Array.isArray(d) ? d : (d.data ?? d.models ?? [])
    }
  } finally {
    loading.value = false
  }
})
</script>
