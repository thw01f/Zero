<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div class="ft-card-title" style="font-size:11px;letter-spacing:0.12em">DEPENDENCY INTELLIGENCE</div>
      <span class="ft-tag">{{ filtered.length }} packages</span>
    </div>

    <div v-if="!report.data" class="ft-card ft-card-body text-center py-12">
      <div class="text-sm mb-1" style="color:#8a96b0">No scan loaded</div>
      <div class="text-xs" style="color:#4a5568">Load a scan to see dependency updates</div>
    </div>

    <template v-else>
      <!-- Filter -->
      <div class="ft-card ft-card-body">
        <div class="flex flex-wrap gap-2">
          <button
            v-for="f in ['ALL', 'MANDATORY', 'SUGGESTED', 'OPTIONAL', 'INFORMATIONAL']"
            :key="f"
            class="ft-btn"
            :class="filter === f ? 'ft-btn-primary' : 'ft-btn-secondary'"
            @click="filter = f"
          >{{ f }}</button>
        </div>
      </div>

      <!-- Table -->
      <div class="ft-card" style="overflow:hidden">
        <div style="overflow-x:auto">
          <table class="ft-table">
            <thead>
              <tr>
                <th>Classification</th>
                <th>Ecosystem</th>
                <th>Package</th>
                <th>Current</th>
                <th>Latest</th>
                <th>CVEs</th>
                <th>Upgrade Command</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in filtered" :key="u.id ?? u.package_name">
                <td>
                  <span class="sev" :class="'upd-' + u.classification" style="font-size:9px">{{ u.classification }}</span>
                </td>
                <td style="color:#8a96b0;font-size:11px">{{ u.ecosystem }}</td>
                <td style="font-family:'JetBrains Mono',monospace;font-size:12px;color:#dde3ef">{{ u.package_name }}</td>
                <td style="font-size:11px;color:#f25555">{{ u.current_version }}</td>
                <td style="font-size:11px;color:#3ecf8e">{{ u.latest_version }}</td>
                <td>
                  <div class="flex flex-wrap gap-1">
                    <span
                      v-for="cve in (u.cve_ids || [])"
                      :key="cve"
                      class="ft-tag"
                      style="color:#f25555;border-color:rgba(242,85,85,0.3)"
                    >{{ cve }}</span>
                    <span v-if="!u.cve_ids?.length" style="color:#4a5568;font-size:11px">—</span>
                  </div>
                </td>
                <td>
                  <div class="flex items-center gap-2">
                    <code class="ft-tag font-mono" style="font-size:10px;color:#3ecf8e">{{ u.upgrade_command }}</code>
                    <button class="ft-btn ft-btn-ghost" style="padding:2px 6px;font-size:10px" @click="copy(u.upgrade_command)">Copy</button>
                  </div>
                </td>
              </tr>
              <tr v-if="!filtered.length">
                <td colspan="7" class="text-center py-8" style="color:#4a5568">No dependency updates found</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useReportStore } from '../stores/report'

const report = useReportStore()
const filter = ref('ALL')

const filtered = computed(() =>
  filter.value === 'ALL'
    ? report.depUpdates
    : report.depUpdates.filter((u: any) => u.classification === filter.value)
)

function copy(cmd: string) {
  navigator.clipboard.writeText(cmd).catch(() => {})
}
</script>