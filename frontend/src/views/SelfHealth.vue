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
<script setup lang="ts">
// TODO: implement logic
</script>
