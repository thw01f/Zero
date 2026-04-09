<template>
  <div class="space-y-4">
    <div class="ft-card-title" style="font-size:11px;letter-spacing:0.12em">UPDATE CENTER</div>

    <div v-if="!report.data" class="ft-card ft-card-body text-center py-12">
      <div class="text-sm mb-1" style="color:#8a96b0">No scan loaded</div>
      <div class="text-xs" style="color:#4a5568">Load a scan to see update requirements</div>
    </div>

    <template v-else>
      <!-- Urgent banner -->
      <div
        v-if="mandatory.length"
        class="ft-card ft-card-body"
        style="border-left:3px solid #f25555;background:rgba(242,85,85,0.05)"
      >
        <div class="flex items-center gap-3">
          <span class="status-dot status-critical"></span>
          <span class="text-sm font-medium" style="color:#f25555">
            {{ mandatory.length }} MANDATORY update{{ mandatory.length > 1 ? 's' : '' }} require immediate action
          </span>
        </div>
      </div>

      <!-- Filter -->
      <div class="ft-card ft-card-body">
        <div class="flex flex-wrap gap-2">
          <button
            v-for="f in ['ALL', 'MANDATORY', 'SUGGESTED', 'OPTIONAL', 'INFORMATIONAL']"
            :key="f"
            class="ft-btn"
            :class="activeFilter === f ? 'ft-btn-primary' : 'ft-btn-secondary'"
            @click="activeFilter = f"
          >
            {{ f }}
            <span v-if="countFor(f) > 0" class="ft-tag" style="margin-left:4px;padding:0 4px">{{ countFor(f) }}</span>
          </button>
        </div>
      </div>

      <!-- Groups by classification -->
      <template v-for="group in groupedFiltered" :key="group.label">
        <div class="ft-card">
          <div class="ft-card-header">
            <div class="flex items-center gap-2">
              <span class="sev" :class="'upd-' + group.label" style="font-size:9px">{{ group.label }}</span>
              <span class="ft-card-title">{{ group.items.length }} packages</span>
            </div>
          </div>
          <div class="ft-card-body space-y-3">
            <div v-for="u in group.items" :key="u.id ?? u.package_name" class="border-b pb-3 last:border-b-0 last:pb-0" style="border-color:#1e2d47">
              <div class="flex items-center justify-between flex-wrap gap-2">
                <div class="flex items-center gap-3">
                  <span class="font-mono font-medium" style="color:#dde3ef">{{ u.package_name }}</span>
                  <span class="text-xs" style="color:#f25555">{{ u.current_version }}</span>
                  <span style="color:#4a5568">→</span>
                  <span class="text-xs" style="color:#3ecf8e">{{ u.latest_version }}</span>
                  <span class="ft-tag" style="font-size:10px">{{ u.ecosystem }}</span>
                </div>
                <button class="ft-btn ft-btn-secondary" style="font-size:11px" @click="copy(u.upgrade_command)">Copy Command</button>
              </div>
              <div v-if="u.cve_ids?.length" class="flex flex-wrap gap-1 mt-2">
                <span v-for="cve in u.cve_ids" :key="cve" class="ft-tag" style="color:#f25555;border-color:rgba(242,85,85,0.3)">{{ cve }}</span>
              </div>
              <div v-if="u.changelog_summary" class="text-xs mt-2" style="color:#8a96b0">{{ u.changelog_summary }}</div>
              <div class="ft-code text-xs mt-2">{{ u.upgrade_command }}</div>
            </div>
          </div>
        </div>
      </template>

      <div v-if="!report.depUpdates.length" class="ft-card ft-card-body text-center py-8">
        <div class="text-xs" style="color:#4a5568">No dependency updates found</div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useReportStore } from '../stores/report'

const report = useReportStore()
const activeFilter = ref('ALL')

const mandatory = computed(() => report.depUpdates.filter((u: any) => u.classification === 'MANDATORY'))

const CLASSIFICATIONS = ['MANDATORY', 'SUGGESTED', 'OPTIONAL', 'INFORMATIONAL']

function countFor(f: string) {
  if (f === 'ALL') return report.depUpdates.length
  return report.depUpdates.filter((u: any) => u.classification === f).length
}

const filteredItems = computed(() =>
  activeFilter.value === 'ALL'
    ? report.depUpdates
    : report.depUpdates.filter((u: any) => u.classification === activeFilter.value)
)

const groupedFiltered = computed(() => {
  const order = activeFilter.value === 'ALL' ? CLASSIFICATIONS : [activeFilter.value]
  return order
    .map(label => ({
      label,
      items: (filteredItems.value as any[]).filter(u => u.classification === label),
    }))
    .filter(g => g.items.length > 0)
})

function copy(cmd: string) {
  navigator.clipboard.writeText(cmd).catch(() => {})
}
</script>
