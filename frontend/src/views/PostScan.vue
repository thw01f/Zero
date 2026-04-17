<script setup lang="ts">
import { ref } from 'vue'

const activeTab = ref('remediation')
const selectedJob = ref('a3f9c21b — github.com/org/api-service')

const jobs = [
  'a3f9c21b — github.com/org/api-service',
  '7b2e441a — github.com/org/auth-service',
  '0d9f3312 — github.com/org/frontend',
]

const remediationItems = [
  { id: 1, file: 'src/auth/login.py', severity: 'critical', rule: 'B602', message: 'Shell injection via subprocess', assignee: 'unassigned', status: 'open', cwe: 'CWE-78' },
  { id: 2, file: 'src/api/users.py', severity: 'critical', rule: 'B608', message: 'SQL query built with string concat', assignee: 'alice', status: 'in-progress', cwe: 'CWE-89' },
  { id: 3, file: 'config/settings.py', severity: 'major', rule: 'B105', message: 'Hardcoded password string', assignee: 'bob', status: 'open', cwe: 'CWE-798' },
  { id: 4, file: 'src/utils/crypto.py', severity: 'major', rule: 'B303', message: 'Use of MD5 for hashing', assignee: 'alice', status: 'resolved', cwe: 'CWE-327' },
  { id: 5, file: 'src/middleware/cors.py', severity: 'minor', rule: 'B201', message: 'Flask debug mode enabled', assignee: 'unassigned', status: 'open', cwe: 'CWE-489' },
]

const workflows = [
  { id: 1, name: 'Auto-generate fix PRs', icon: '⬡', desc: 'Create GitHub PRs with AI-generated patches for accepted fixes', status: 'ready', action: 'Run' },
  { id: 2, name: 'Create Jira Tickets', icon: '◈', desc: 'Push critical & major findings to Jira as sprint backlog items', status: 'ready', action: 'Run' },
  { id: 3, name: 'Notify Slack Channel', icon: '◉', desc: 'Send scan summary digest to #security-alerts channel', status: 'ready', action: 'Run' },
  { id: 4, name: 'CI/CD Gate Check', icon: '⬢', desc: 'Block deployments if critical issues remain unresolved', status: 'active', action: 'Configure' },
  { id: 5, name: 'Schedule Re-scan', icon: '◷', desc: 'Auto re-scan on every push to main branch', status: 'active', action: 'Configure' },
  { id: 6, name: 'Email Executive Report', icon: '✉', desc: 'Send PDF summary to engineering leadership', status: 'ready', action: 'Send' },
]

const history = [
  { ts: '2026-04-17 09:14', action: 'PR #441 created', detail: 'Fix: SQL injection in users.py', by: 'DarkLead Bot', status: 'success' },
  { ts: '2026-04-17 09:13', action: 'Jira ticket DL-204', detail: 'CWE-78 shell injection — sprint backlog', by: 'DarkLead Bot', status: 'success' },
  { ts: '2026-04-16 18:00', action: 'Re-scan triggered', detail: 'Push to main by alice', by: 'GitHub Webhook', status: 'success' },
  { ts: '2026-04-16 14:22', action: 'CI gate BLOCKED', detail: '3 critical issues unresolved', by: 'GitHub Actions', status: 'blocked' },
  { ts: '2026-04-15 11:05', action: 'Slack notification', detail: 'Weekly digest sent to #security-alerts', by: 'Scheduler', status: 'success' },
]

const assignees = ['unassigned', 'alice', 'bob', 'charlie', 'diana']
const statusOpts = ['open', 'in-progress', 'resolved', 'wontfix']

const toast = ref('')
function runWorkflow(w: any) {
  toast.value = `${w.name} — queued (coming soon)`
  setTimeout(() => toast.value = '', 3000)
}
</script>

<template>
  <div class="ps-root">
    <!-- Header -->
    <div class="ps-header">
      <div class="ps-header-left">
        <div class="ps-icon">⟳</div>
        <div>
          <div class="ps-title">Post-Scan Actions</div>
          <div class="ps-sub">Remediation workflows, ticket creation, notifications &amp; CI gates</div>
        </div>
      </div>
      <select v-model="selectedJob" class="ft-select ps-job-sel">
        <option v-for="j in jobs" :key="j">{{ j }}</option>
      </select>
    </div>

    <!-- KPI strip -->
    <div class="ps-kpis">
      <div class="ps-kpi">
        <div class="ps-kpi-val" style="color:var(--gc-error)">3</div>
        <div class="ps-kpi-lbl">Critical Open</div>
      </div>
      <div class="ps-kpi">
        <div class="ps-kpi-val" style="color:var(--gc-warning)">1</div>
        <div class="ps-kpi-lbl">In Progress</div>
      </div>
      <div class="ps-kpi">
        <div class="ps-kpi-val" style="color:var(--gc-success)">1</div>
        <div class="ps-kpi-lbl">Resolved</div>
      </div>
      <div class="ps-kpi">
        <div class="ps-kpi-val">40%</div>
        <div class="ps-kpi-lbl">Remediation Rate</div>
      </div>
      <div class="ps-kpi">
        <div class="ps-kpi-val" style="color:var(--gc-error)">CI BLOCKED</div>
        <div class="ps-kpi-lbl">Pipeline Gate</div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="ps-tabs">
      <button :class="['ps-tab', activeTab==='remediation' && 'active']" @click="activeTab='remediation'">Remediation Board</button>
      <button :class="['ps-tab', activeTab==='workflows' && 'active']" @click="activeTab='workflows'">Automation Workflows</button>
      <button :class="['ps-tab', activeTab==='history' && 'active']" @click="activeTab='history'">Action History</button>
    </div>

    <!-- Remediation Board -->
    <div v-if="activeTab==='remediation'" class="ft-card">
      <div class="ft-card-header">
        <span class="ft-card-title">Remediation Board</span>
        <div style="display:flex;gap:8px">
          <button class="ft-btn ft-btn-secondary ft-btn-sm">Export CSV</button>
          <button class="ft-btn ft-btn-primary ft-btn-sm">+ Assign All</button>
        </div>
      </div>
      <div class="ft-card-body" style="padding:0">
        <table class="ft-table">
          <thead>
            <tr>
              <th>Severity</th><th>File</th><th>Finding</th><th>CWE</th>
              <th>Assignee</th><th>Status</th><th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in remediationItems" :key="item.id">
              <td><span :class="['sev', `sev-${item.severity}`]">{{ item.severity }}</span></td>
              <td class="ps-mono">{{ item.file }}</td>
              <td style="max-width:220px;white-space:normal;font-size:12px">{{ item.message }}</td>
              <td><span class="ps-cwe">{{ item.cwe }}</span></td>
              <td>
                <select :value="item.assignee" class="ft-select" style="height:26px;padding:0 8px;font-size:12px">
                  <option v-for="a in assignees" :key="a">{{ a }}</option>
                </select>
              </td>
              <td>
                <select :value="item.status" class="ft-select" style="height:26px;padding:0 8px;font-size:12px">
                  <option v-for="s in statusOpts" :key="s">{{ s }}</option>
                </select>
              </td>
              <td>
                <button class="ft-btn ft-btn-ghost ft-btn-sm">View Fix</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Automation Workflows -->
    <div v-if="activeTab==='workflows'" class="ps-workflows">
      <div v-for="w in workflows" :key="w.id" class="ft-card ps-wf-card">
        <div class="ps-wf-icon">{{ w.icon }}</div>
        <div class="ps-wf-body">
          <div class="ps-wf-name">{{ w.name }}</div>
          <div class="ps-wf-desc">{{ w.desc }}</div>
        </div>
        <div class="ps-wf-right">
          <span :class="['ps-wf-status', w.status === 'active' ? 'ps-wf-active' : 'ps-wf-ready']">
            {{ w.status }}
          </span>
          <button class="ft-btn ft-btn-primary ft-btn-sm" @click="runWorkflow(w)">
            {{ w.action }}
          </button>
        </div>
      </div>
    </div>

    <!-- Action History -->
    <div v-if="activeTab==='history'" class="ft-card">
      <div class="ft-card-header">
        <span class="ft-card-title">Action History</span>
      </div>
      <div class="ft-card-body" style="padding:0">
        <table class="ft-table">
          <thead>
            <tr><th>Time</th><th>Action</th><th>Detail</th><th>Triggered By</th><th>Status</th></tr>
          </thead>
          <tbody>
            <tr v-for="h in history" :key="h.ts">
              <td class="ps-mono" style="color:var(--gc-text-2);font-size:12px">{{ h.ts }}</td>
              <td style="font-weight:500;font-size:13px">{{ h.action }}</td>
              <td style="font-size:12px;color:var(--gc-text-2)">{{ h.detail }}</td>
              <td style="font-size:12px">{{ h.by }}</td>
              <td>
                <span :class="['ps-hist-badge', h.status === 'success' ? 'ps-hist-ok' : 'ps-hist-block']">
                  {{ h.status }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Toast -->
    <transition name="toast">
      <div v-if="toast" class="ps-toast">{{ toast }}</div>
    </transition>
  </div>
</template>

<style scoped>
.ps-root { display:flex; flex-direction:column; gap:18px; max-width:1200px; }

.ps-header { display:flex; align-items:center; justify-content:space-between; gap:16px; flex-wrap:wrap; }
.ps-header-left { display:flex; align-items:center; gap:14px; }
.ps-icon { font-size:28px; width:44px; height:44px; border-radius:10px; background:var(--gc-primary-light); display:flex; align-items:center; justify-content:center; color:var(--gc-primary); }
.ps-title { font-size:20px; font-weight:600; color:var(--gc-text); }
.ps-sub   { font-size:13px; color:var(--gc-text-2); margin-top:2px; }
.ps-job-sel { min-width:280px; }

.ps-kpis { display:flex; gap:12px; flex-wrap:wrap; }
.ps-kpi { flex:1; min-width:130px; background:var(--gc-surface); border:1px solid var(--gc-border); border-radius:10px; padding:14px 18px; }
.ps-kpi-val { font-size:22px; font-weight:600; color:var(--gc-text); }
.ps-kpi-lbl { font-size:11px; color:var(--gc-text-2); margin-top:4px; text-transform:uppercase; letter-spacing:.04em; }

.ps-tabs { display:flex; gap:4px; border-bottom:1px solid var(--gc-border); padding-bottom:0; }
.ps-tab { padding:8px 18px; font-size:13px; font-weight:500; color:var(--gc-text-2); background:transparent; border:none; cursor:pointer; border-bottom:2px solid transparent; transition:all .15s; }
.ps-tab:hover { color:var(--gc-text); }
.ps-tab.active { color:var(--gc-primary); border-bottom-color:var(--gc-primary); }

.ps-mono { font-family:var(--font-mono); font-size:12px; color:var(--gc-text-2); }
.ps-cwe  { font-size:11px; font-family:var(--font-mono); background:var(--gc-surface-2); border:1px solid var(--gc-border); padding:2px 6px; border-radius:4px; color:var(--gc-text-2); }

.ps-workflows { display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:14px; }
.ps-wf-card { flex-direction:row; align-items:center; gap:16px; padding:18px; }
.ps-wf-icon { font-size:24px; width:44px; height:44px; border-radius:10px; background:var(--gc-surface-2); display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.ps-wf-body { flex:1; }
.ps-wf-name { font-size:14px; font-weight:500; color:var(--gc-text); }
.ps-wf-desc { font-size:12px; color:var(--gc-text-2); margin-top:3px; line-height:1.4; }
.ps-wf-right { display:flex; flex-direction:column; align-items:flex-end; gap:8px; flex-shrink:0; }
.ps-wf-status { font-size:11px; font-weight:600; padding:2px 8px; border-radius:4px; text-transform:uppercase; }
.ps-wf-active { background:rgba(52,168,83,.15); color:#34a853; }
.ps-wf-ready  { background:var(--gc-surface-2); color:var(--gc-text-3); }

.ps-hist-badge { font-size:11px; font-weight:600; padding:2px 8px; border-radius:4px; text-transform:uppercase; }
.ps-hist-ok    { background:rgba(52,168,83,.15); color:#34a853; }
.ps-hist-block { background:rgba(234,67,53,.15); color:var(--gc-error); }

.ps-toast { position:fixed; bottom:24px; right:24px; background:var(--gc-surface); border:1px solid var(--gc-border); border-radius:8px; padding:12px 20px; font-size:13px; color:var(--gc-text); box-shadow:var(--gc-shadow-lg); z-index:9999; }
.toast-enter-active,.toast-leave-active { transition:all .2s; }
.toast-enter-from,.toast-leave-to { opacity:0; transform:translateY(8px); }
</style>
