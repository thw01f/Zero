<template>
  <div class="space-y-4">
    <div class="ft-card-title" style="font-size:11px;letter-spacing:0.12em">EXPORT REPORTS</div>

    <div v-if="!scan.jobId" class="ft-card ft-card-body text-center py-12">
      <div class="text-sm mb-1" style="color:#8a96b0">No scan loaded</div>
      <div class="text-xs" style="color:#4a5568">Run or load a scan to export reports</div>
    </div>

    <template v-else>
      <!-- Job info -->
      <div class="ft-card">
        <div class="ft-card-header"><span class="ft-card-title">Job Information</span></div>
        <div class="ft-card-body">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div class="metric-label">Job ID</div>
              <div class="font-mono text-sm" style="color:#4a9ff5">{{ scan.jobId }}</div>
            </div>
            <div v-if="report.data">
              <div class="metric-label">Repository</div>
              <div class="text-sm" style="color:#dde3ef">{{ report.data.repo_url }}</div>
            </div>
            <div v-if="report.data">
              <div class="metric-label">Language</div>
              <div class="text-sm" style="color:#dde3ef">{{ report.data.language }}</div>
            </div>
            <div v-if="report.data">
              <div class="metric-label">Grade</div>
              <div class="text-2xl font-bold" :class="'grade-' + report.data.overall_grade">{{ report.data.overall_grade }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Export formats -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <a
          :href="`/api/export/${scan.jobId}/json`"
          class="ft-card ft-card-body text-center cursor-pointer transition-all"
          style="text-decoration:none;display:block"
          :style="{ ':hover': { background: '#1a2540' } }"
          @mouseenter="hovered = 'json'"
          @mouseleave="hovered = ''"
        >
          <div
            class="rounded-full flex items-center justify-center mx-auto mb-3"
            style="width:48px;height:48px;background:rgba(74,159,245,0.15);color:#4a9ff5"
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/>
            </svg>
          </div>
          <div class="font-medium text-sm mb-1" style="color:#dde3ef">JSON Export</div>
          <div class="text-xs" style="color:#4a5568">Full machine-readable data</div>
        </a>

        <a
          :href="`/api/export/${scan.jobId}/pdf`"
          class="ft-card ft-card-body text-center cursor-pointer"
          style="text-decoration:none;display:block"
        >
          <div
            class="rounded-full flex items-center justify-center mx-auto mb-3"
            style="width:48px;height:48px;background:rgba(242,109,33,0.15);color:#f26d21"
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
            </svg>
          </div>
          <div class="font-medium text-sm mb-1" style="color:#dde3ef">PDF Report</div>
          <div class="text-xs" style="color:#4a5568">Executive + technical report</div>
        </a>

        <a
          :href="`/api/export/${scan.jobId}/csv`"
          class="ft-card ft-card-body text-center cursor-pointer"
          style="text-decoration:none;display:block"
        >
          <div
            class="rounded-full flex items-center justify-center mx-auto mb-3"
            style="width:48px;height:48px;background:rgba(62,207,142,0.15);color:#3ecf8e"
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M3 3h18v18H3z"/><path d="M3 9h18M3 15h18M9 3v18"/>
            </svg>
          </div>
          <div class="font-medium text-sm mb-1" style="color:#dde3ef">CSV Export</div>
          <div class="text-xs" style="color:#4a5568">Issues in spreadsheet format</div>
        </a>
      </div>

      <!-- Share link -->
      <div class="ft-card">
        <div class="ft-card-header"><span class="ft-card-title">Share Link</span></div>
        <div class="ft-card-body">
          <div class="flex items-center gap-2">
            <input
              :value="shareUrl"
              class="ft-input"
              readonly
              style="font-family:'JetBrains Mono',monospace;font-size:11px"
            />
            <button class="ft-btn ft-btn-primary" @click="copyLink">
              {{ copied ? 'Copied!' : 'Copy' }}
            </button>
          </div>
          <div class="text-xs mt-2" style="color:#4a5568">
            Share this URL to let others view the scan results without re-running
          </div>
        </div>
      </div>
    </template>
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useScanStore } from '../stores/scan'
import { useReportStore } from '../stores/report'

const scan = useScanStore()
const report = useReportStore()
const copied = ref(false)
const hovered = ref('')

const shareUrl = computed(() => `${window.location.origin}?demo=${scan.jobId}`)

function copyLink() {
  navigator.clipboard.writeText(shareUrl.value).catch(() => {})
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}
</script>