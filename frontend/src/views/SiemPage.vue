<template>
  <div class="logs-root">
    <!-- Header -->
    <div class="logs-header">
      <div class="logs-header-left">
        <AppIcon name="eye" :size="16" class="logs-icon" />
        <span class="logs-title">Live Log Monitor</span>
        <span class="logs-badge">{{ connectedJobs.length }} active</span>
      </div>
      <div class="logs-header-right">
        <button class="logs-btn logs-btn-ghost" @click="clearLogs" title="Clear logs">
          <AppIcon name="close" :size="13" />
          Clear
        </button>
        <button class="logs-btn" :class="paused ? 'logs-btn-warn' : ''" @click="paused = !paused">
          {{ paused ? '▶ Resume' : '⏸ Pause' }}
        </button>
        <label class="logs-filter-label">
          <input v-model="filterText" class="logs-filter" placeholder="Filter logs…" />
        </label>
      </div>
    </div>

    <!-- Job tabs -->
    <div class="logs-tabs" v-if="jobTabs.length">
      <button
        v-for="tab in jobTabs" :key="tab.id"
        class="logs-tab" :class="{active: activeJob === tab.id}"
        @click="activeJob = tab.id"
      >
        <span class="tab-dot" :class="tab.status"></span>
        <span>{{ tab.label }}</span>
        <span class="tab-progress" v-if="tab.progress < 100">{{ tab.progress }}%</span>
      </button>
      <button class="logs-tab logs-tab-all" :class="{active: activeJob === 'all'}" @click="activeJob = 'all'">
        All
      </button>
    </div>

    <!-- Terminal -->
    <div class="logs-terminal" ref="termRef">
      <div v-if="!filteredLogs.length" class="logs-empty">
        <AppIcon name="eye" :size="36" style="opacity:.2" />
        <p>Waiting for events… Start a scan to see live logs here.</p>
      </div>
      <div
        v-for="(log, i) in filteredLogs"
        :key="i"
        class="log-line"
        :class="'lvl-' + log.level"
      >
        <span class="log-time">{{ log.time }}</span>
        <span class="log-job" v-if="activeJob === 'all' && log.jobShort">{{ log.jobShort }}</span>
        <span class="log-stage" v-if="log.stage">{{ log.stage }}</span>
        <span class="log-msg">{{ log.msg }}</span>
        <span class="log-pct" v-if="log.progress !== undefined">{{ log.progress }}%</span>
      </div>
    </div>

    <!-- Stats bar -->
    <div class="logs-statsbar">
      <span class="stat">
        <span class="stat-dot lvl-error"></span>
        {{ counts.error }} errors
      </span>
      <span class="stat">
        <span class="stat-dot lvl-warn"></span>
        {{ counts.warn }} warnings
      </span>
      <span class="stat">
        <span class="stat-dot lvl-ok"></span>
        {{ counts.ok }} completed
      </span>
      <span class="stat stat-total">{{ logs.length }} total lines</span>
      <span class="stat stat-right">
        <span :class="sseOk ? 'conn-ok' : 'conn-err'">●</span>
        {{ sseOk ? 'SSE connected' : 'SSE disconnected' }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useAuthStore } from '../stores/auth'
import AppIcon from '../components/AppIcon.vue'

interface LogLine {
  time: string
  jobId?: string
  jobShort?: string
  stage?: string
  msg: string
  level: 'info' | 'ok' | 'warn' | 'error' | 'llm' | 'sys'
  progress?: number
}

interface JobTab {
  id: string
  label: string
  status: 'running' | 'done' | 'error'
  progress: number
}

const auth      = useAuthStore()
const termRef   = ref<HTMLElement | null>(null)
const logs      = ref<LogLine[]>([])
const paused    = ref(false)
const filterText= ref('')
const activeJob = ref<string>('all')
const sseOk     = ref(false)

const jobTabs   = ref<JobTab[]>([])
const connectedJobs = ref<string[]>([])
const wsMap     = new Map<string, WebSocket>()

// ── filtered view ──────────────────────────────────────────
const filteredLogs = computed(() => {
  let list = logs.value
  if (activeJob.value !== 'all') list = list.filter(l => l.jobId === activeJob.value)
  if (filterText.value) {
    const q = filterText.value.toLowerCase()
    list = list.filter(l => l.msg.toLowerCase().includes(q) || l.stage?.toLowerCase().includes(q))
  }
  return list
})

const counts = computed(() => ({
  error: logs.value.filter(l => l.level === 'error').length,
  warn:  logs.value.filter(l => l.level === 'warn').length,
  ok:    logs.value.filter(l => l.level === 'ok').length,
}))

// ── helpers ────────────────────────────────────────────────
function ts() {
  return new Date().toTimeString().slice(0, 8)
}

function push(line: LogLine) {
  if (paused.value) return
  logs.value.push(line)
  if (logs.value.length > 2000) logs.value.splice(0, 200)
  nextTick(() => {
    if (termRef.value) termRef.value.scrollTop = termRef.value.scrollHeight
  })
}

function clearLogs() { logs.value = [] }

// ── SSE system alerts ──────────────────────────────────────
let sseSource: EventSource | null = null

function connectSSE() {
  sseSource?.close()
  sseSource = new EventSource('/api/sse/alerts')
  sseSource.onopen = () => { sseOk.value = true }
  sseSource.onmessage = (e) => {
    try {
      const d = JSON.parse(e.data)
      if (d.type === 'heartbeat') return
      push({
        time: ts(), msg: d.message || d.title || JSON.stringify(d),
        level: d.level === 'error' ? 'error' : d.level === 'warning' ? 'warn' : 'sys',
        stage: 'ALERT',
      })
    } catch {}
  }
  sseSource.onerror = () => {
    sseOk.value = false
    setTimeout(connectSSE, 5000)
  }
}

// ── Job WebSocket ──────────────────────────────────────────
const STAGE_LABELS: Record<string, string> = {
  cloning: 'CLONE', cloned: 'CLONE', analyzing: 'SCAN', scan_complete: 'SCAN',
  triage: 'TRIAGE', fixes: 'FIX', misconfigs: 'MISCONFIG', debt_scored: 'DEBT',
  compliance: 'COMPLY', persisted: 'PERSIST', summary: 'SUMMARY',
}

function connectJob(jobId: string) {
  if (wsMap.has(jobId)) return
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const ws = new WebSocket(`${proto}//${location.host}/api/ws/${jobId}`)
  wsMap.set(jobId, ws)
  connectedJobs.value = [...connectedJobs.value, jobId]

  // Ensure tab exists
  if (!jobTabs.value.find(t => t.id === jobId)) {
    jobTabs.value.push({ id: jobId, label: jobId.slice(0, 8), status: 'running', progress: 0 })
  }

  push({ time: ts(), jobId, jobShort: jobId.slice(0, 8), msg: `WebSocket connected for job ${jobId.slice(0, 8)}`, level: 'info', stage: 'WS' })

  ws.onmessage = (e) => {
    try {
      const d = JSON.parse(e.data)
      const stage = STAGE_LABELS[d.stage] || d.stage || ''
      let level: LogLine['level'] = 'info'
      let msg = ''

      if (d.event === 'complete') {
        level = 'ok'
        msg = `Scan complete in ${(d.scan_time_ms / 1000).toFixed(1)}s`
        updateTab(jobId, 'done', 100)
        disconnectJob(jobId)
      } else if (d.event === 'error') {
        level = 'error'
        msg = d.message || 'Scan failed'
        updateTab(jobId, 'error', -1)
        disconnectJob(jobId)
      } else if (d.event === 'llm_start') {
        level = 'llm'
        msg = `LLM ${stage} started…`
      } else if (d.event === 'llm_done') {
        level = 'llm'
        msg = `LLM ${stage} done`
      } else {
        msg = `${stage || d.event || 'progress'}`
        if (d.progress) updateTab(jobId, 'running', d.progress)
      }

      push({ time: ts(), jobId, jobShort: jobId.slice(0, 8), msg, level, stage, progress: d.progress })
    } catch {}
  }

  ws.onerror = () => push({ time: ts(), jobId, jobShort: jobId.slice(0, 8), msg: 'WebSocket error', level: 'error' })
  ws.onclose = () => {
    wsMap.delete(jobId)
    connectedJobs.value = connectedJobs.value.filter(j => j !== jobId)
  }
}

function disconnectJob(jobId: string) {
  const ws = wsMap.get(jobId)
  if (ws) { ws.close(); wsMap.delete(jobId) }
  connectedJobs.value = connectedJobs.value.filter(j => j !== jobId)
}

function updateTab(jobId: string, status: JobTab['status'], progress: number) {
  const tab = jobTabs.value.find(t => t.id === jobId)
  if (tab) { tab.status = status; if (progress >= 0) tab.progress = progress }
}

// ── Poll for running jobs every 5 s ───────────────────────
let pollTimer: ReturnType<typeof setInterval> | null = null

async function pollJobs() {
  try {
    const r = await fetch('/api/scan/jobs?limit=10', { headers: auth.authHeaders() })
    if (!r.ok) return
    const jobs: any[] = await r.json()
    for (const j of jobs) {
      if (j.status === 'running' && !wsMap.has(j.job_id)) {
        connectJob(j.job_id)
      }
    }
  } catch {}
}

// ── Lifecycle ──────────────────────────────────────────────
onMounted(() => {
  connectSSE()
  pollJobs()
  pollTimer = setInterval(pollJobs, 5000)
  push({ time: ts(), msg: 'Live log monitor started', level: 'sys', stage: 'SYSTEM' })
})

onBeforeUnmount(() => {
  sseSource?.close()
  wsMap.forEach(ws => ws.close())
  wsMap.clear()
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.logs-root {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background: var(--gc-bg);
  font-family: 'Roboto Mono', 'Menlo', monospace;
}

/* Header */
.logs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  border-bottom: 1px solid var(--gc-border);
  background: var(--gc-surface);
  flex-shrink: 0;
  flex-wrap: wrap;
  gap: 8px;
}
.logs-header-left { display: flex; align-items: center; gap: 10px; }
.logs-header-right { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.logs-icon { color: #34a853; }
.logs-title { font-size: 14px; font-weight: 600; color: var(--gc-text-1); font-family: var(--font-sans); }
.logs-badge {
  font-size: 11px; padding: 2px 8px; border-radius: 10px;
  background: #34a85320; color: #34a853; font-weight: 500;
}

.logs-btn {
  display: flex; align-items: center; gap: 4px;
  background: var(--gc-accent, #1a73e8); color: #fff;
  border: none; border-radius: 6px; padding: 4px 12px;
  font-size: 12px; cursor: pointer; font-family: var(--font-sans);
}
.logs-btn-ghost {
  background: transparent; color: var(--gc-text-2);
  border: 1px solid var(--gc-border);
}
.logs-btn-ghost:hover { background: var(--gc-surface-2); }
.logs-btn-warn { background: #f9ab00; color: #000; }

.logs-filter {
  background: var(--gc-bg); border: 1px solid var(--gc-border);
  border-radius: 6px; color: var(--gc-text-1); font-size: 12px;
  padding: 4px 10px; outline: none; width: 160px;
}
.logs-filter:focus { border-color: var(--gc-accent, #1a73e8); }

/* Job tabs */
.logs-tabs {
  display: flex; gap: 2px; padding: 4px 12px;
  background: var(--gc-surface); border-bottom: 1px solid var(--gc-border);
  overflow-x: auto; flex-shrink: 0;
}
.logs-tabs::-webkit-scrollbar { height: 3px; }
.logs-tab {
  display: flex; align-items: center; gap: 5px;
  padding: 4px 10px; border-radius: 6px; border: none;
  background: transparent; color: var(--gc-text-2);
  font-size: 12px; cursor: pointer; white-space: nowrap;
  font-family: 'Roboto Mono', monospace;
}
.logs-tab:hover { background: var(--gc-surface-2); }
.logs-tab.active { background: var(--gc-primary-light); color: var(--gc-primary); font-weight: 600; }
.logs-tab-all { margin-left: auto; color: var(--gc-text-3); }

.tab-dot {
  width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0;
}
.tab-dot.running { background: #f9ab00; animation: pulse 1.2s ease-in-out infinite; }
.tab-dot.done    { background: #34a853; }
.tab-dot.error   { background: #ea4335; }

@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }

.tab-progress { font-size: 10px; color: var(--gc-text-3); }

/* Terminal area */
.logs-terminal {
  flex: 1; overflow-y: auto; overflow-x: hidden;
  background: #0d1117;
  padding: 8px 0;
  font-size: 12.5px;
  line-height: 1.6;
}
.logs-terminal::-webkit-scrollbar { width: 6px; }
.logs-terminal::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }

.logs-empty {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  height: 100%; gap: 14px; color: #484f58;
}
.logs-empty p { font-size: 13px; font-family: var(--font-sans); }

.log-line {
  display: flex; align-items: baseline; gap: 8px;
  padding: 1px 16px;
  border-left: 2px solid transparent;
}
.log-line:hover { background: #161b22; }

.log-time  { color: #484f58; flex-shrink: 0; font-size: 11.5px; }
.log-job   { color: #58a6ff; flex-shrink: 0; font-size: 10.5px; background: #1f2937; padding: 0 5px; border-radius: 3px; }
.log-stage { flex-shrink: 0; font-size: 10px; font-weight: 700; letter-spacing: .4px; min-width: 60px; text-align: right; }
.log-msg   { flex: 1; color: #c9d1d9; }
.log-pct   { flex-shrink: 0; color: #484f58; font-size: 11px; }

/* Level colors */
.lvl-info  { border-left-color: transparent; }
.lvl-info  .log-stage { color: #58a6ff; }

.lvl-ok    { border-left-color: #34a853; }
.lvl-ok    .log-stage { color: #34a853; }
.lvl-ok    .log-msg   { color: #7ee787; }

.lvl-warn  { border-left-color: #f9ab00; }
.lvl-warn  .log-stage { color: #f9ab00; }
.lvl-warn  .log-msg   { color: #e3b341; }

.lvl-error { border-left-color: #ea4335; }
.lvl-error .log-stage { color: #ea4335; }
.lvl-error .log-msg   { color: #ffa198; }

.lvl-llm   { border-left-color: #a371f7; }
.lvl-llm   .log-stage { color: #a371f7; }
.lvl-llm   .log-msg   { color: #d2a8ff; }

.lvl-sys   { }
.lvl-sys   .log-stage { color: #8b949e; }
.lvl-sys   .log-msg   { color: #8b949e; font-style: italic; }

/* Stats bar */
.logs-statsbar {
  display: flex; align-items: center; gap: 16px;
  padding: 5px 16px;
  background: #161b22; border-top: 1px solid #30363d;
  font-size: 11.5px; color: #8b949e; flex-shrink: 0;
  flex-wrap: wrap;
}
.stat { display: flex; align-items: center; gap: 5px; }
.stat-dot { width: 8px; height: 8px; border-radius: 50%; }
.stat-right { margin-left: auto; }
.conn-ok  { color: #34a853; }
.conn-err { color: #ea4335; }
</style>
