<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div class="ft-card-title" style="font-size:11px;letter-spacing:0.12em">FIX STUDIO</div>
      <div class="flex items-center gap-3">
        <span class="ft-tag">{{ accepted }} / {{ fixable.length }} accepted</span>
        <div class="ft-progress" style="width:120px">
          <div class="ft-progress-bar" :style="{ width: acceptRate + '%', background: '#3ecf8e' }"></div>
        </div>
      </div>
    </div>

    <div v-if="!report.data" class="ft-card ft-card-body text-center py-12">
      <div class="text-sm mb-1" style="color:#8a96b0">No scan loaded</div>
      <div class="text-xs" style="color:#4a5568">Load a scan to see fix suggestions</div>
    </div>

    <div v-else-if="!fixable.length" class="ft-card ft-card-body text-center py-12">
      <div class="text-sm mb-1" style="color:#8a96b0">No fix diffs available</div>
      <div class="text-xs" style="color:#4a5568">Fixes are generated for critical and major security issues</div>
    </div>

    <div v-for="issue in fixable" :key="issue.id" class="ft-card">
      <div class="ft-card-header">
        <div class="flex items-center gap-2">
          <span class="sev" :class="'sev-' + issue.severity">{{ issue.severity }}</span>
          <span class="font-mono text-xs" style="color:#8a96b0">{{ issue.file_path }}:{{ issue.line_start }}</span>
          <span style="color:#4a9ff5;font-size:11px">{{ issue.rule_id }}</span>
        </div>
        <div class="flex gap-2">
          <button
            class="ft-btn"
            :class="issue.fix_accepted === 1 ? 'ft-btn-primary' : 'ft-btn-secondary'"
            @click="accept(issue.id, true)"
          >Accept</button>
          <button
            class="ft-btn"
            :class="issue.fix_accepted === -1 ? 'ft-btn-danger' : 'ft-btn-secondary'"
            @click="accept(issue.id, false)"
          >Reject</button>
        </div>
      </div>
      <div class="ft-card-body space-y-3">
        <p v-if="issue.llm_explanation" class="text-xs leading-relaxed" style="color:#8a96b0">
          {{ issue.llm_explanation }}
        </p>
        <div v-if="issue.fix_diff" class="d2h-wrapper" v-html="renderDiff(issue.fix_diff)"></div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { useReportStore } from '../stores/report'

const report = useReportStore()

const fixable = computed(() => report.issues.filter((i: any) => i.fix_diff))
const accepted = computed(() => fixable.value.filter((i: any) => i.fix_accepted === 1).length)
const acceptRate = computed(() =>
  fixable.value.length ? Math.round((accepted.value / fixable.value.length) * 100) : 0
)

async function accept(id: string, val: boolean) {
  await report.acceptFix(id, val)
}

function escHtml(s: string) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function renderDiff(diff: string): string {
  const lines = diff.split('\n').map(line => {
    if (line.startsWith('+++') || line.startsWith('---')) {
      return `<div style="color:#8a96b0;padding:2px 8px;background:#0f1526;font-family:'JetBrains Mono',monospace;font-size:11px">${escHtml(line)}</div>`
    }
    if (line.startsWith('+')) {
      return `<div style="background:rgba(62,207,142,0.08);color:#3ecf8e;padding:2px 8px;font-family:'JetBrains Mono',monospace;font-size:11px">${escHtml(line)}</div>`
    }
    if (line.startsWith('-')) {
      return `<div style="background:rgba(242,85,85,0.08);color:#f25555;padding:2px 8px;font-family:'JetBrains Mono',monospace;font-size:11px">${escHtml(line)}</div>`
    }
    if (line.startsWith('@@')) {
      return `<div style="color:#4a9ff5;padding:2px 8px;background:#0f1526;font-family:'JetBrains Mono',monospace;font-size:11px">${escHtml(line)}</div>`
    }
    return `<div style="color:#dde3ef;padding:2px 8px;font-family:'JetBrains Mono',monospace;font-size:11px">${escHtml(line)}</div>`
  })
  return `<div style="background:#0a0e1a;border:1px solid #1e2d47;border-radius:3px;overflow-x:auto">${lines.join('')}</div>`
}
</script>