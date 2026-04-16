<template>
  <div class="fs-root">
    <!-- Header bar -->
    <div class="fs-header">
      <div class="fs-title">FIX STUDIO</div>
      <div class="fs-stats">
        <div class="fs-stat">
          <span class="fs-stat-val">{{ fixable.length }}</span>
          <span class="fs-stat-lbl">fixes available</span>
        </div>
        <div class="fs-stat-sep">·</div>
        <div class="fs-stat" style="color:#3ecf8e">
          <span class="fs-stat-val">{{ accepted }}</span>
          <span class="fs-stat-lbl">accepted</span>
        </div>
        <div class="fs-stat-sep">·</div>
        <div class="fs-stat" style="color:#f25555">
          <span class="fs-stat-val">{{ rejected }}</span>
          <span class="fs-stat-lbl">rejected</span>
        </div>
      </div>
      <div class="fs-progress-wrap" v-if="fixable.length">
        <div class="fs-progress-bar" :style="{ width: acceptRate + '%' }"></div>
        <span class="fs-progress-label">{{ acceptRate }}% accepted</span>
      </div>
      <div v-if="fixable.length" class="fs-bulk-btns">
        <button class="fs-btn fs-btn-success" @click="acceptAll">Accept All</button>
        <button class="fs-btn fs-btn-danger" @click="rejectAll">Reject All</button>
      </div>
    </div>

    <!-- Empty states -->
    <div v-if="!report.data" class="fs-empty">
      <div class="fs-empty-icon">🔧</div>
      <div class="fs-empty-title">No scan loaded</div>
      <div class="fs-empty-sub">Load a scan from Scan History to view AI-generated fixes</div>
    </div>

    <div v-else-if="!fixable.length" class="fs-empty">
      <div class="fs-empty-icon">✅</div>
      <div class="fs-empty-title">No fix diffs available</div>
      <div class="fs-empty-sub">Fixes are generated for critical and major issues during Phase 2 enrichment</div>
    </div>

    <!-- Fix list -->
    <div v-else class="fs-body">
      <!-- File group -->
      <div v-for="(group, file) in fileGroups" :key="file" class="fs-file-group">
        <div class="fs-file-hdr">
          <div class="fs-file-info">
            <svg viewBox="0 0 16 16" width="13" height="13" fill="currentColor" style="flex-shrink:0;color:#8a96b0">
              <path d="M2 2h7l3 3v9H2V2zm7 0v3h3"/>
            </svg>
            <span class="fs-file-path">{{ file }}</span>
            <span class="fs-file-count">{{ group.length }} fix{{ group.length > 1 ? 'es' : '' }}</span>
          </div>
          <div class="fs-file-actions">
            <button class="fs-btn fs-btn-sm fs-btn-success" @click="acceptFile(group)">Accept All</button>
            <button class="fs-btn fs-btn-sm fs-btn-ghost" @click="rejectFile(group)">Reject All</button>
          </div>
        </div>

        <!-- Each fix -->
        <div v-for="issue in group" :key="issue.id" class="fs-fix-card" :class="fixStatus(issue)">
          <div class="fs-fix-hdr">
            <div class="fs-fix-left">
              <span class="sev-chip" :class="'sev-' + issue.severity">{{ issue.severity }}</span>
              <span class="fs-rule">{{ issue.rule_id || 'unknown' }}</span>
              <span class="fs-line">line {{ issue.line_start }}</span>
              <span v-if="issue.cwe_id" class="fs-cwe">CWE-{{ issue.cwe_id }}</span>
            </div>
            <div class="fs-fix-actions">
              <button
                class="fs-btn fs-btn-sm"
                :class="issue.fix_accepted === 1 ? 'fs-btn-success' : 'fs-btn-outline-success'"
                @click="accept(issue.id, true)"
              >
                <svg viewBox="0 0 20 20" fill="currentColor" width="12" height="12">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"/>
                </svg>
                Accept
              </button>
              <button
                class="fs-btn fs-btn-sm"
                :class="issue.fix_accepted === -1 ? 'fs-btn-danger' : 'fs-btn-outline-danger'"
                @click="accept(issue.id, false)"
              >
                <svg viewBox="0 0 20 20" fill="currentColor" width="12" height="12">
                  <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"/>
                </svg>
                Reject
              </button>
              <button class="fs-btn fs-btn-sm fs-btn-ghost" @click="toggleExpand(issue.id)">
                {{ expanded.has(issue.id) ? '▲ Less' : '▼ Details' }}
              </button>
            </div>
          </div>

          <!-- Message -->
          <div class="fs-fix-msg">{{ issue.message }}</div>

          <!-- Expanded content -->
          <div v-if="expanded.has(issue.id)" class="fs-fix-body">
            <!-- LLM explanation -->
            <div v-if="issue.llm_explanation" class="fs-explain-block">
              <div class="fs-explain-label">AI EXPLANATION</div>
              <div class="fs-explain-text">{{ issue.llm_explanation }}</div>
            </div>

            <!-- OWASP tag -->
            <div v-if="issue.owasp_category" class="fs-owasp-tag">
              OWASP: {{ issue.owasp_category }}
            </div>

            <!-- Diff viewer -->
            <div v-if="issue.fix_diff" class="fs-diff-wrap">
              <div class="fs-diff-label">PROPOSED FIX</div>
              <div class="fs-diff" v-html="renderDiff(issue.fix_diff)"></div>
            </div>
          </div>

          <!-- Status bar -->
          <div v-if="issue.fix_accepted !== 0" class="fs-status-bar" :class="issue.fix_accepted === 1 ? 'accepted' : 'rejected'">
            {{ issue.fix_accepted === 1 ? '✓ Accepted' : '✗ Rejected' }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useReportStore } from '../stores/report'

const report = useReportStore()

const expanded = ref<Set<string>>(new Set())

const fixable = computed(() => report.issues.filter((i: any) => i.fix_diff))
const accepted = computed(() => fixable.value.filter((i: any) => i.fix_accepted === 1).length)
const rejected = computed(() => fixable.value.filter((i: any) => i.fix_accepted === -1).length)
const acceptRate = computed(() =>
  fixable.value.length ? Math.round((accepted.value / fixable.value.length) * 100) : 0
)

const fileGroups = computed(() => {
  const groups: Record<string, any[]> = {}
  for (const iss of fixable.value) {
    const fp = iss.file_path || 'unknown'
    ;(groups[fp] = groups[fp] ?? []).push(iss)
  }
  return groups
})

function fixStatus(issue: any) {
  if (issue.fix_accepted === 1) return 'status-accepted'
  if (issue.fix_accepted === -1) return 'status-rejected'
  return ''
}

function toggleExpand(id: string) {
  if (expanded.value.has(id)) expanded.value.delete(id)
  else expanded.value.add(id)
  expanded.value = new Set(expanded.value)
}

async function accept(id: string, val: boolean) {
  await report.acceptFix(id, val)
}

async function acceptAll() {
  for (const iss of fixable.value) await report.acceptFix(iss.id, true)
}

async function rejectAll() {
  for (const iss of fixable.value) await report.acceptFix(iss.id, false)
}

async function acceptFile(group: any[]) {
  for (const iss of group) await report.acceptFix(iss.id, true)
}

async function rejectFile(group: any[]) {
  for (const iss of group) await report.acceptFix(iss.id, false)
}

function escHtml(s: string) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function renderDiff(diff: string): string {
  const lines = diff.split('\n').map(line => {
    if (line.startsWith('+++') || line.startsWith('---'))
      return `<div class="dl-hdr">${escHtml(line)}</div>`
    if (line.startsWith('+'))
      return `<div class="dl-add">${escHtml(line)}</div>`
    if (line.startsWith('-'))
      return `<div class="dl-del">${escHtml(line)}</div>`
    if (line.startsWith('@@'))
      return `<div class="dl-rng">${escHtml(line)}</div>`
    return `<div class="dl-ctx">${escHtml(line)}</div>`
  })
  return `<div class="dl-wrap">${lines.join('')}</div>`
}
</script>

<style scoped>
.fs-root {
  display: flex; flex-direction: column;
  height: calc(100vh - 64px - 48px);
  background: var(--gc-bg); overflow: hidden;
}

/* Header */
.fs-header {
  display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
  padding: 10px 20px; border-bottom: 1px solid var(--gc-border);
  background: var(--gc-surface); flex-shrink: 0;
}
.fs-title { font-size: 11px; font-weight: 700; letter-spacing: 0.12em; color: var(--gc-text-2); }
.fs-stats { display: flex; align-items: center; gap: 8px; }
.fs-stat { display: flex; align-items: center; gap: 4px; font-size: 12px; }
.fs-stat-val { font-weight: 700; color: var(--gc-text); }
.fs-stat-lbl { color: var(--gc-text-3); }
.fs-stat-sep { color: var(--gc-divider); }
.fs-progress-wrap {
  height: 6px; width: 120px; background: var(--gc-border);
  border-radius: 3px; position: relative; overflow: hidden;
}
.fs-progress-bar { height: 100%; background: #3ecf8e; border-radius: 3px; transition: width 0.4s; }
.fs-progress-label { display: none; }
.fs-bulk-btns { display: flex; gap: 6px; margin-left: auto; }

/* Buttons */
.fs-btn {
  display: inline-flex; align-items: center; gap: 4px; border: none; cursor: pointer;
  padding: 5px 12px; border-radius: 5px; font-size: 12px; font-weight: 500; transition: all 0.15s;
}
.fs-btn-sm { padding: 3px 8px; font-size: 11px; }
.fs-btn-success { background: rgba(62,207,142,.2); color: #3ecf8e; border: 1px solid rgba(62,207,142,.3); }
.fs-btn-success:hover { background: rgba(62,207,142,.3); }
.fs-btn-danger  { background: rgba(242,85,85,.15);  color: #f25555; border: 1px solid rgba(242,85,85,.2); }
.fs-btn-danger:hover  { background: rgba(242,85,85,.25); }
.fs-btn-outline-success { background: transparent; color: var(--gc-text-3); border: 1px solid var(--gc-border); }
.fs-btn-outline-success:hover { color: #3ecf8e; border-color: #3ecf8e; }
.fs-btn-outline-danger { background: transparent; color: var(--gc-text-3); border: 1px solid var(--gc-border); }
.fs-btn-outline-danger:hover { color: #f25555; border-color: #f25555; }
.fs-btn-ghost { background: transparent; color: var(--gc-text-3); border: 1px solid var(--gc-border); }
.fs-btn-ghost:hover { color: var(--gc-text); background: var(--gc-surface-2); }

/* Empty state */
.fs-empty {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 10px;
}
.fs-empty-icon { font-size: 40px; }
.fs-empty-title { font-size: 15px; color: var(--gc-text); font-weight: 600; }
.fs-empty-sub { font-size: 12px; color: var(--gc-text-3); max-width: 280px; text-align: center; }

/* Body */
.fs-body { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 20px; }

/* File group */
.fs-file-group { display: flex; flex-direction: column; gap: 8px; }
.fs-file-hdr {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 8px 14px; background: var(--gc-surface-2);
  border: 1px solid var(--gc-border); border-radius: 8px 8px 0 0;
  border-bottom: none;
}
.fs-file-info { display: flex; align-items: center; gap: 8px; min-width: 0; }
.fs-file-path {
  font-family: 'JetBrains Mono', monospace; font-size: 11px;
  color: var(--gc-text-2); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.fs-file-count {
  font-size: 10px; padding: 1px 6px; border-radius: 4px;
  background: var(--gc-primary-light); color: var(--gc-primary);
  flex-shrink: 0; font-weight: 600;
}
.fs-file-actions { display: flex; gap: 6px; flex-shrink: 0; }

/* Fix card */
.fs-fix-card {
  border: 1px solid var(--gc-border); border-radius: 0 0 8px 8px;
  background: var(--gc-surface); overflow: hidden; transition: border-color 0.2s;
}
.fs-fix-card + .fs-fix-card { border-radius: 0; border-top: none; }
.fs-fix-card:last-child { border-radius: 0 0 8px 8px; }
.fs-fix-card.status-accepted { border-color: rgba(62,207,142,.4); }
.fs-fix-card.status-rejected { border-color: rgba(242,85,85,.3); opacity: 0.7; }

.fs-fix-hdr {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  padding: 10px 14px; background: var(--gc-surface-2);
}
.fs-fix-left { display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0; }
.fs-rule { font-size: 11px; font-family: monospace; color: var(--gc-primary); font-weight: 600; }
.fs-line { font-size: 10px; color: var(--gc-text-3); font-family: monospace; }
.fs-cwe  { font-size: 10px; color: var(--gc-text-3); background: var(--gc-surface); border: 1px solid var(--gc-border); padding: 1px 5px; border-radius: 3px; }
.fs-fix-actions { display: flex; gap: 6px; flex-shrink: 0; }

.fs-fix-msg {
  padding: 8px 14px; font-size: 12px; color: var(--gc-text-2);
  border-bottom: 1px solid var(--gc-border);
}

/* Expanded body */
.fs-fix-body { padding: 12px 14px; display: flex; flex-direction: column; gap: 10px; }
.fs-explain-block { background: var(--gc-surface-2); border-left: 3px solid var(--gc-primary); padding: 10px 12px; border-radius: 0 4px 4px 0; }
.fs-explain-label { font-size: 9px; font-weight: 700; letter-spacing: 0.1em; color: var(--gc-text-3); margin-bottom: 4px; }
.fs-explain-text  { font-size: 12px; color: var(--gc-text); line-height: 1.5; }
.fs-owasp-tag {
  display: inline-flex; font-size: 10px; color: #8b5cf6;
  background: rgba(139,92,246,.1); border: 1px solid rgba(139,92,246,.2);
  padding: 2px 8px; border-radius: 4px; font-weight: 600;
}
.fs-diff-label { font-size: 9px; font-weight: 700; letter-spacing: 0.1em; color: var(--gc-text-3); margin-bottom: 4px; }

/* Status bar */
.fs-status-bar {
  padding: 4px 14px; font-size: 11px; font-weight: 600; text-align: right;
}
.fs-status-bar.accepted { background: rgba(62,207,142,.08); color: #3ecf8e; }
.fs-status-bar.rejected { background: rgba(242,85,85,.05); color: #f25555; }

/* Severity chips */
.sev-chip { display: inline-flex; align-items: center; font-size: 9px; font-weight: 700; text-transform: uppercase; padding: 2px 6px; border-radius: 3px; flex-shrink: 0; }
.sev-critical { background: rgba(239,68,68,.15);  color: #ef4444; }
.sev-major    { background: rgba(249,115,22,.15); color: #f97316; }
.sev-minor    { background: rgba(234,179,8,.15);  color: #eab308; }
.sev-info     { background: rgba(96,165,250,.15); color: #60a5fa; }

/* Diff */
:deep(.dl-wrap) { background: #0a0e1a; border: 1px solid #1e2d47; border-radius: 4px; overflow-x: auto; }
:deep(.dl-add)  { color: #3ecf8e; background: rgba(62,207,142,.06); padding: 1px 8px; font-family: 'JetBrains Mono',monospace; font-size: 11px; }
:deep(.dl-del)  { color: #f25555; background: rgba(242,85,85,.06);  padding: 1px 8px; font-family: 'JetBrains Mono',monospace; font-size: 11px; }
:deep(.dl-hdr)  { color: #8a96b0; background: #0f1526; padding: 1px 8px; font-family: 'JetBrains Mono',monospace; font-size: 11px; }
:deep(.dl-rng)  { color: #4a9ff5; padding: 1px 8px; font-family: 'JetBrains Mono',monospace; font-size: 11px; }
:deep(.dl-ctx)  { color: #dde3ef; padding: 1px 8px; font-family: 'JetBrains Mono',monospace; font-size: 11px; }
</style>
