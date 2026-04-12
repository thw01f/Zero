<template>
  <div class="app-shell">
    <!-- Top Header Bar -->
    <header class="app-header">
      <div class="header-left">
        <button class="icon-btn" @click="sidebarOpen = !sidebarOpen" title="Toggle sidebar">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        </button>
        <div class="logo-area">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="#f26d21" stroke-width="2.2" stroke-linejoin="round"/>
          </svg>
          <span class="logo-name">DARK<span class="logo-accent">LEAD</span></span>
          <span class="logo-badge">AI</span>
        </div>
        <div class="breadcrumb">
          <span class="breadcrumb-div">/</span>
          <span class="breadcrumb-page">{{ pageTitle }}</span>
        </div>
      </div>

      <div class="header-right">
        <div class="llm-pill" :title="`Backend: ${llmBackend} | Model: ${llmModel}`">
          <span class="status-dot status-ok" style="width:6px;height:6px"></span>
          <span>{{ llmLabel }}</span>
        </div>

        <div v-if="scan.status !== 'idle'" class="scan-pill" :class="`scan-${scan.status}`">
          <span class="status-dot" :class="scanDotClass"></span>
          <span>{{ scan.status }}</span>
          <span v-if="scan.status === 'running'" class="scan-pct">{{ scan.progress }}%</span>
        </div>

        <button class="icon-btn alert-btn" @click="alertsOpen = !alertsOpen">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
          <span v-if="alertsStore.unreadCount" class="badge-dot">{{ alertsStore.unreadCount }}</span>
        </button>

        <span class="clock">{{ clock }}</span>
        <div class="avatar">DL</div>
      </div>
    </header>

    <!-- Alerts Dropdown -->
    <transition name="fade">
      <div v-if="alertsOpen" class="alerts-overlay" @click="alertsOpen = false">
        <div class="alerts-panel" @click.stop>
          <div class="alerts-head">
            <span style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:#8a96b0">Alerts</span>
            <button class="ft-btn ft-btn-ghost" style="font-size:11px;padding:3px 8px" @click="alertsStore.markAllRead()">Mark all read</button>
          </div>
          <div v-if="!alertsStore.alerts.length" style="padding:20px;text-align:center;color:#4a5568;font-size:12px">No alerts</div>
          <div v-for="a in alertsStore.alerts.slice(0,15)" :key="a.id" class="alert-row" :class="{dimmed: a.read}" @click="alertsStore.markRead(a.id)">
            <span class="status-dot" style="flex-shrink:0" :class="a.type.includes('critical') ? 'status-critical' : 'status-warn'"></span>
            <div style="flex:1;overflow:hidden">
              <div style="font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ a.type.replace(/_/g,' ') }}</div>
              <div style="color:#4a5568;font-size:10px">{{ new Date(a.timestamp).toLocaleTimeString() }}</div>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <div class="app-body">
      <!-- Sidebar -->
      <aside class="sidebar" :class="{ 'sidebar-closed': !sidebarOpen }">
        <!-- Scan Form -->
        <div class="sidebar-scan">
          <ScanForm />
        </div>

        <!-- Nav -->
        <nav class="sidebar-nav">
          <div class="nav-section">
            <div class="nav-group-hdr">Dashboard</div>
            <router-link to="/" class="nav-item" exact active-class="active" exact>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
              Command Center
            </router-link>
            <router-link to="/heatmap" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="4" height="4"/><rect x="10" y="3" width="4" height="4"/><rect x="17" y="3" width="4" height="4"/><rect x="3" y="10" width="4" height="4"/><rect x="10" y="10" width="4" height="4"/><rect x="17" y="10" width="4" height="4"/><rect x="3" y="17" width="4" height="4"/><rect x="10" y="17" width="4" height="4"/><rect x="17" y="17" width="4" height="4"/></svg>
              Risk Heatmap
            </router-link>
          </div>

          <div class="nav-section">
            <div class="nav-group-hdr">Code Analysis</div>
            <router-link to="/issues" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              Issue Tracker
              <span v-if="report.issues.length" class="nav-cnt">{{ report.issues.length }}</span>
            </router-link>
            <router-link to="/code-analysis" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
              Code Analyzer
              <span class="nav-new">NEW</span>
            </router-link>
            <router-link to="/fixes" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
              Fix Studio
            </router-link>
          </div>

          <div class="nav-section">
            <div class="nav-group-hdr">Security</div>
            <router-link to="/security" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              Security Posture
            </router-link>
            <router-link to="/misconfig" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/></svg>
              Misconfig Radar
            </router-link>
            <router-link to="/compliance" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
              Compliance
            </router-link>
            <router-link to="/infra" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>
              Infra Posture
            </router-link>
          </div>

          <div class="nav-section">
            <div class="nav-group-hdr">Dependencies</div>
            <router-link to="/deps" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="5" r="3"/><path d="M12 8v13M5 16H3a2 2 0 0 0-2 2v1M19 16h2a2 2 0 0 1 2 2v1"/><circle cx="5" cy="20" r="1"/><circle cx="19" cy="20" r="1"/></svg>
              Dependency Intel
            </router-link>
            <router-link to="/updates" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-.08-3.02"/></svg>
              Update Center
              <span v-if="mandatoryCount" class="nav-cnt urgent">{{ mandatoryCount }}</span>
            </router-link>
            <router-link to="/advisories" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
              Advisory Feed
            </router-link>
          </div>

          <div class="nav-section">
            <div class="nav-group-hdr">Intelligence</div>
            <router-link to="/git" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M13 6h3a2 2 0 0 1 2 2v7"/><line x1="6" y1="9" x2="6" y2="21"/></svg>
              Git Intelligence
            </router-link>
            <router-link to="/trends" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>
              Trend Analysis
            </router-link>
            <router-link to="/ai" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              AI Assistant
            </router-link>
          </div>

          <div class="nav-section">
            <div class="nav-group-hdr">Platform</div>
            <router-link to="/self-health" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
              Self Health
            </router-link>
            <router-link to="/export" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              Export Reports
            </router-link>
          </div>
        </nav>
      </aside>

      <!-- Main -->
      <main class="app-main">
        <div v-if="scan.status === 'running'" class="scan-bar">
          <div class="scan-bar-fill" :style="{width: scan.progress + '%'}"></div>
        </div>
        <div class="content-area">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import ScanForm from './components/ScanForm.vue'
import { useReportStore } from './stores/report'
import { useScanStore } from './stores/scan'
import { useAlertsStore } from './stores/alerts'
import axios from 'axios'

const route = useRoute()
const report = useReportStore()
const scan = useScanStore()
const alertsStore = useAlertsStore()

const sidebarOpen = ref(true)
const alertsOpen = ref(false)
const clock = ref('')
const llmLabel = ref('Loading…')
const llmBackend = ref('')
const llmModel = ref('')

const PAGE_TITLES: Record<string, string> = {
  '/': 'Command Center', '/heatmap': 'Risk Heatmap', '/issues': 'Issue Tracker',
  '/code-analysis': 'Code Analyzer', '/fixes': 'Fix Studio', '/security': 'Security Posture',
  '/misconfig': 'Misconfig Radar', '/compliance': 'Compliance', '/infra': 'Infra Posture',
  '/deps': 'Dependency Intel', '/updates': 'Update Center', '/advisories': 'Advisory Feed',
  '/git': 'Git Intelligence', '/trends': 'Trend Analysis', '/ai': 'AI Assistant',
  '/self-health': 'Self Health', '/export': 'Export Reports',
}
const pageTitle = computed(() => PAGE_TITLES[route.path] ?? 'DarkLead')
const mandatoryCount = computed(() => report.depUpdates.filter((d: any) => d.classification === 'MANDATORY').length)
const scanDotClass = computed(() => ({
  'status-running': scan.status === 'running' || scan.status === 'queued',
  'status-ok': scan.status === 'complete',
  'status-critical': scan.status === 'failed',
  'status-warn': scan.status === 'queued',
}))

let clockTimer: ReturnType<typeof setInterval>
function tick() { clock.value = new Date().toLocaleTimeString('en-US', { hour12: false }) }

async function loadLlm() {
  try {
    const { data } = await axios.get('/api/analyze/models')
    llmBackend.value = data.active_backend
    llmModel.value = data.active_model
    const name = data.active_model.split(':')[0].replace('claude-', '')
    llmLabel.value = data.active_backend === 'ollama' ? `Ollama / ${name}` : `Claude / ${name}`
  } catch { llmLabel.value = 'LLM offline' }
}

onMounted(() => {
  tick()
  clockTimer = setInterval(tick, 1000)
  alertsStore.connectSSE()
  loadLlm()
  const jobId = new URLSearchParams(window.location.search).get('demo')
  if (jobId) {
    report.fetchReport(jobId)
    scan.jobId = jobId
    scan.status = 'complete'
  }
})
onUnmounted(() => {
  clearInterval(clockTimer)
  alertsStore.disconnect()
})
</script>

<style scoped>
.app-shell { display: flex; flex-direction: column; height: 100vh; overflow: hidden; }

/* ── Header ── */
.app-header {
  height: 44px; min-height: 44px;
  background: #0d1220; border-bottom: 1px solid #1e2d47;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 14px; z-index: 200; flex-shrink: 0;
  gap: 8px;
}
.header-left { display: flex; align-items: center; gap: 10px; min-width: 0; }
.header-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }

.icon-btn {
  width: 28px; height: 28px; display: flex; align-items: center; justify-content: center;
  background: transparent; border: none; color: #8a96b0; cursor: pointer; border-radius: 3px;
  flex-shrink: 0;
}
.icon-btn:hover { background: #1a2540; color: #dde3ef; }

.logo-area { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.logo-name { font-size: 14px; font-weight: 700; letter-spacing: 0.06em; color: #dde3ef; }
.logo-accent { color: #f26d21; }
.logo-badge {
  font-size: 9px; font-weight: 700; padding: 1px 5px; border-radius: 2px;
  background: rgba(242,109,33,0.2); border: 1px solid rgba(242,109,33,0.3); color: #f26d21;
}
.breadcrumb { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #4a5568; overflow: hidden; }
.breadcrumb-div { color: #263553; }
.breadcrumb-page { color: #8a96b0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.llm-pill {
  display: flex; align-items: center; gap: 5px;
  background: rgba(62,207,142,0.08); border: 1px solid rgba(62,207,142,0.2);
  border-radius: 3px; padding: 3px 8px; font-size: 10px; color: #3ecf8e; cursor: default;
  white-space: nowrap;
}

.scan-pill {
  display: flex; align-items: center; gap: 5px;
  border: 1px solid #1e2d47; border-radius: 3px;
  padding: 3px 8px; font-size: 11px; white-space: nowrap;
}
.scan-running { border-color: rgba(74,159,245,0.4); color: #4a9ff5; }
.scan-complete { border-color: rgba(62,207,142,0.4); color: #3ecf8e; }
.scan-failed   { border-color: rgba(242,85,85,0.4); color: #f25555; }
.scan-queued   { border-color: rgba(245,166,35,0.4); color: #f5a623; }
.scan-pct { font-size: 10px; opacity: 0.8; }

.alert-btn { position: relative; }
.badge-dot {
  position: absolute; top: 2px; right: 2px;
  min-width: 14px; height: 14px; border-radius: 7px;
  background: #f25555; color: #fff; font-size: 9px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; padding: 0 3px;
}

.clock { font-size: 11px; color: #4a5568; font-family: 'JetBrains Mono', monospace; white-space: nowrap; }
.avatar {
  width: 26px; height: 26px; border-radius: 50%;
  background: linear-gradient(135deg, #f26d21, #c45518);
  display: flex; align-items: center; justify-content: center;
  font-size: 9px; font-weight: 700; color: #fff; cursor: pointer; flex-shrink: 0;
}

/* ── Alerts ── */
.alerts-overlay {
  position: fixed; inset: 44px 0 0; z-index: 150;
  background: rgba(0,0,0,0.35);
}
.alerts-panel {
  position: absolute; top: 0; right: 0; width: 300px; height: 100%;
  background: #141d30; border-left: 1px solid #1e2d47;
  display: flex; flex-direction: column; overflow: hidden;
}
.alerts-head {
  padding: 12px 14px; border-bottom: 1px solid #1e2d47;
  display: flex; align-items: center; justify-content: space-between; flex-shrink: 0;
}
.alert-row {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 9px 14px; border-bottom: 1px solid #1a2540;
  font-size: 12px; color: #dde3ef; cursor: pointer;
  transition: background 0.1s;
}
.alert-row:hover { background: #1a2540; }
.alert-row.dimmed { opacity: 0.4; }

/* ── Body ── */
.app-body { flex: 1; display: flex; overflow: hidden; }

/* ── Sidebar ── */
.sidebar {
  width: 196px; min-width: 196px;
  background: #0d1220; border-right: 1px solid #1e2d47;
  display: flex; flex-direction: column;
  transition: width 0.2s ease, min-width 0.2s ease;
  overflow: hidden;
}
.sidebar-closed { width: 0 !important; min-width: 0 !important; }

.sidebar-scan {
  padding: 10px;
  border-bottom: 1px solid #1e2d47;
  flex-shrink: 0;
}
.sidebar-nav { flex: 1; overflow-y: auto; padding-bottom: 12px; }

.nav-section { margin-bottom: 2px; }
.nav-group-hdr {
  padding: 10px 12px 3px;
  font-size: 9px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.12em;
  color: #263553;
}
.nav-item {
  display: flex; align-items: center; gap: 8px;
  padding: 7px 12px; font-size: 12px; color: #8a96b0;
  cursor: pointer; transition: all 0.12s;
  border-left: 2px solid transparent;
  text-decoration: none; white-space: nowrap;
}
.nav-item:hover { background: #1a2540; color: #dde3ef; }
.nav-item.active {
  background: rgba(242,109,33,0.1);
  color: #f26d21;
  border-left-color: #f26d21;
  padding-left: 10px;
}
.nav-cnt {
  margin-left: auto; min-width: 18px; height: 15px;
  border-radius: 3px; padding: 0 4px;
  background: #1a2540; border: 1px solid #263553;
  font-size: 9px; font-weight: 600; color: #8a96b0;
  display: flex; align-items: center; justify-content: center;
}
.nav-cnt.urgent {
  background: rgba(242,85,85,0.15); border-color: rgba(242,85,85,0.3); color: #f25555;
}
.nav-new {
  margin-left: auto; padding: 1px 5px; border-radius: 2px;
  background: rgba(242,109,33,0.2); border: 1px solid rgba(242,109,33,0.3);
  font-size: 9px; font-weight: 700; color: #f26d21;
}

/* ── Main ── */
.app-main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.scan-bar { height: 3px; background: #1a2540; flex-shrink: 0; }
.scan-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #f26d21, #f5a623);
  transition: width 0.3s; border-radius: 0 2px 2px 0;
}
.content-area { flex: 1; overflow-y: auto; padding: 16px 20px; }

/* Transition */
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
