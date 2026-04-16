<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div class="ft-card-title" style="font-size:11px;letter-spacing:0.12em">INFRASTRUCTURE POSTURE</div>
      <span class="ft-tag">{{ filtered.length }} findings</span>
    </div>

    <div v-if="!report.data" class="ft-card ft-card-body text-center py-12">
      <div class="text-sm mb-1" style="color:#8a96b0">No scan loaded</div>
      <div class="text-xs" style="color:#4a5568">Load a scan to see infrastructure findings</div>
    </div>

    <template v-else>
      <!-- Resource type filter -->
      <div class="ft-card ft-card-body">
        <div class="flex flex-wrap gap-2">
          <button
            v-for="rt in resourceTypes"
            :key="rt"
            class="ft-btn"
            :class="activeTab === rt ? 'ft-btn-primary' : 'ft-btn-secondary'"
            @click="activeTab = rt"
          >{{ rt }}</button>
        </div>
      </div>

      <!-- No infra findings -->
      <div v-if="!infraMisconfigs.length" class="ft-card ft-card-body text-center py-12">
        <div class="text-sm mb-1" style="color:#8a96b0">No infrastructure findings</div>
        <div class="text-xs" style="color:#4a5568">Scans Dockerfile, Terraform, K8s manifests, and .env files</div>
      </div>

      <template v-else>
        <!-- Summary by resource type -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div
            v-for="rt in INFRA_TYPES"
            :key="rt"
            class="ft-widget metric-tile cursor-pointer"
            @click="activeTab = rt"
          >
            <div class="metric-value text-lg" :style="{ color: countForType(rt) > 0 ? '#f26d21' : '#3ecf8e' }">
              {{ countForType(rt) }}
            </div>
            <div class="metric-label">{{ rt }}</div>
          </div>
        </div>

        <!-- Findings table -->
        <div class="ft-card" style="overflow:hidden">
          <div style="overflow-x:auto">
            <table class="ft-table">
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Resource</th>
                  <th>Check ID</th>
                  <th>Title</th>
                  <th>File</th>
                  <th>Remediation</th>
                </tr>
              </thead>
              <tbody>
                <template v-for="m in filtered" :key="m.id ?? m.check_id">
                  <tr @click="toggleExpand(m.id ?? m.check_id)" class="cursor-pointer">
                    <td><span class="sev" :class="'sev-' + m.severity">{{ m.severity }}</span></td>
                    <td><span class="cat-badge cat-misconfig">{{ m.resource_type }}</span></td>
                    <td style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#4a9ff5">{{ m.check_id }}</td>
                    <td style="max-width:240px" class="truncate">{{ m.title }}</td>
                    <td class="font-mono text-xs" style="color:#8a96b0">
                      {{ m.file_path }}{{ m.line_start ? ':' + m.line_start : '' }}
                    </td>
                    <td style="color:#4a5568;font-size:10px">{{ m.remediation ? '▼' : '—' }}</td>
                  </tr>
                  <tr v-if="m.remediation && expanded.has(m.id ?? m.check_id)" style="background:#0f1526">
                    <td colspan="6" class="px-3 py-3">
                      <div class="ft-card-title mb-1">Remediation</div>
                      <pre class="ft-code text-xs">{{ m.remediation }}</pre>
                    </td>
                  </tr>
                </template>
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useReportStore } from '../stores/report'

const report = useReportStore()
const activeTab = ref('ALL')
const expanded = ref(new Set<string>())

const INFRA_TYPES = ['Dockerfile', 'Terraform', 'K8s', 'EnvFile']

const infraMisconfigs = computed(() =>
  report.misconfigs.filter((m: any) => INFRA_TYPES.includes(m.resource_type))
)

const resourceTypes = computed(() => {
  const types = new Set(infraMisconfigs.value.map((m: any) => m.resource_type))
  return ['ALL', ...[...types].sort()]
})

const filtered = computed(() =>
  activeTab.value === 'ALL'
    ? infraMisconfigs.value
    : infraMisconfigs.value.filter((m: any) => m.resource_type === activeTab.value)
)

function countForType(rt: string) {
  return infraMisconfigs.value.filter((m: any) => m.resource_type === rt).length
}

function toggleExpand(id: string) {
  const s = new Set(expanded.value)
  s.has(id) ? s.delete(id) : s.add(id)
  expanded.value = s
}
</script>