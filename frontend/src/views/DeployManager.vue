<script setup lang="ts">
import { ref } from 'vue'

const activeEnv = ref('production')
const envs = ['development', 'staging', 'production']

const containers = [
  { name: 'api-service', image: 'darklead/api:v1.4.2', status: 'running', cpu: '12%', mem: '248 MB', uptime: '6d 14h', ports: '8080:8080' },
  { name: 'auth-service', image: 'darklead/auth:v1.2.0', status: 'running', cpu: '4%', mem: '112 MB', uptime: '6d 14h', ports: '8081:8081' },
  { name: 'redis', image: 'redis:7-alpine', status: 'running', cpu: '1%', mem: '32 MB', uptime: '12d 2h', ports: '6379:6379' },
  { name: 'postgres', image: 'postgres:16', status: 'running', cpu: '3%', mem: '184 MB', uptime: '12d 2h', ports: '5432:5432' },
  { name: 'worker', image: 'darklead/worker:v1.4.2', status: 'stopped', cpu: '0%', mem: '0 MB', uptime: '—', ports: '' },
  { name: 'nginx', image: 'nginx:1.25-alpine', status: 'running', cpu: '0%', mem: '18 MB', uptime: '6d 14h', ports: '443:443' },
]

const pipelines = [
  { name: 'Docker Build & Push', provider: 'GitHub Actions', branch: 'main', last: '2m ago', duration: '3m 12s', status: 'success' },
  { name: 'K8s Rolling Deploy', provider: 'GitHub Actions', branch: 'main', last: '2m ago', duration: '1m 44s', status: 'success' },
  { name: 'Terraform Plan', provider: 'Terraform Cloud', branch: 'infra/patch-12', last: '1h ago', duration: '22s', status: 'pending' },
  { name: 'Staging Deploy', provider: 'GitLab CI', branch: 'dev', last: '4h ago', duration: '5m 01s', status: 'failed' },
  { name: 'Smoke Tests', provider: 'GitHub Actions', branch: 'main', last: '2m ago', duration: '48s', status: 'success' },
]

const mcpTools = [
  { name: 'kubectl', icon: '⎈', desc: 'Kubernetes cluster management', version: 'v1.29.2', connected: true },
  { name: 'docker', icon: '◻', desc: 'Container build & orchestration', version: '26.0.0', connected: true },
  { name: 'terraform', icon: '◈', desc: 'Infrastructure as Code provisioning', version: 'v1.8.0', connected: false },
  { name: 'helm', icon: '⎗', desc: 'Kubernetes package manager', version: 'v3.14.4', connected: true },
  { name: 'ansible', icon: '⟁', desc: 'Configuration management & deploy', version: '2.16.5', connected: false },
  { name: 'ArgoCD', icon: '⎉', desc: 'GitOps continuous delivery', version: 'v2.10.4', connected: false },
]

const toast = ref('')
function doAction(label: string) {
  toast.value = `${label} — coming soon`
  setTimeout(() => toast.value = '', 3000)
}
</script>

<template>
  <div class="dm-root">
    <!-- Header -->
    <div class="dm-header">
      <div class="dm-header-left">
        <div class="dm-icon">⬡</div>
        <div>
          <div class="dm-title">Deploy Manager</div>
          <div class="dm-sub">Container orchestration, CI/CD pipelines &amp; infrastructure provisioning</div>
        </div>
      </div>
      <div class="dm-env-tabs">
        <button v-for="e in envs" :key="e" :class="['dm-env-btn', activeEnv===e && 'active']" @click="activeEnv=e">
          {{ e }}
        </button>
      </div>
    </div>

    <!-- Status strip -->
    <div class="dm-kpis">
      <div class="dm-kpi">
        <div class="dm-kpi-dot" style="background:#34a853"></div>
        <div>
          <div class="dm-kpi-val">5 / 6</div>
          <div class="dm-kpi-lbl">Containers Running</div>
        </div>
      </div>
      <div class="dm-kpi">
        <div class="dm-kpi-dot" style="background:var(--gc-primary)"></div>
        <div>
          <div class="dm-kpi-val">v1.4.2</div>
          <div class="dm-kpi-lbl">Deployed Version</div>
        </div>
      </div>
      <div class="dm-kpi">
        <div class="dm-kpi-dot" style="background:#34a853"></div>
        <div>
          <div class="dm-kpi-val">99.7%</div>
          <div class="dm-kpi-lbl">Uptime (30d)</div>
        </div>
      </div>
      <div class="dm-kpi">
        <div class="dm-kpi-dot" style="background:var(--gc-warning)"></div>
        <div>
          <div class="dm-kpi-val">1 pending</div>
          <div class="dm-kpi-lbl">Terraform Plan</div>
        </div>
      </div>
    </div>

    <div class="dm-grid">
      <!-- Containers -->
      <div class="ft-card dm-card-wide">
        <div class="ft-card-header">
          <span class="ft-card-title">Containers — {{ activeEnv }}</span>
          <div style="display:flex;gap:8px">
            <button class="ft-btn ft-btn-secondary ft-btn-sm" @click="doAction('Compose pull')">Pull Images</button>
            <button class="ft-btn ft-btn-primary ft-btn-sm" @click="doAction('docker compose up')">Deploy All</button>
          </div>
        </div>
        <div class="ft-card-body" style="padding:0">
          <table class="ft-table">
            <thead>
              <tr><th>Container</th><th>Image</th><th>Status</th><th>CPU</th><th>Mem</th><th>Uptime</th><th>Ports</th><th></th></tr>
            </thead>
            <tbody>
              <tr v-for="c in containers" :key="c.name">
                <td style="font-weight:500">{{ c.name }}</td>
                <td class="dm-mono">{{ c.image }}</td>
                <td>
                  <span class="dm-status-badge" :class="c.status === 'running' ? 'dm-ok' : 'dm-stopped'">
                    <span class="status-dot" :class="c.status === 'running' ? 'status-ok' : 'status-inactive'"></span>
                    {{ c.status }}
                  </span>
                </td>
                <td class="dm-mono">{{ c.cpu }}</td>
                <td class="dm-mono">{{ c.mem }}</td>
                <td class="dm-mono" style="color:var(--gc-text-2)">{{ c.uptime }}</td>
                <td class="dm-mono" style="color:var(--gc-text-2);font-size:11px">{{ c.ports }}</td>
                <td>
                  <button v-if="c.status==='running'" class="ft-btn ft-btn-danger ft-btn-sm" @click="doAction('Stop '+c.name)">Stop</button>
                  <button v-else class="ft-btn ft-btn-primary ft-btn-sm" @click="doAction('Start '+c.name)">Start</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Pipelines -->
      <div class="ft-card">
        <div class="ft-card-header">
          <span class="ft-card-title">CI/CD Pipelines</span>
          <button class="ft-btn ft-btn-secondary ft-btn-sm" @click="doAction('Trigger pipeline')">Run Pipeline</button>
        </div>
        <div class="ft-card-body" style="padding:0">
          <table class="ft-table">
            <thead>
              <tr><th>Pipeline</th><th>Provider</th><th>Branch</th><th>Last Run</th><th>Duration</th><th>Status</th></tr>
            </thead>
            <tbody>
              <tr v-for="p in pipelines" :key="p.name">
                <td style="font-weight:500;font-size:13px">{{ p.name }}</td>
                <td style="font-size:12px;color:var(--gc-text-2)">{{ p.provider }}</td>
                <td class="dm-mono">{{ p.branch }}</td>
                <td style="font-size:12px;color:var(--gc-text-2)">{{ p.last }}</td>
                <td class="dm-mono">{{ p.duration }}</td>
                <td>
                  <span :class="['dm-pipe-badge',
                    p.status==='success' ? 'dm-pipe-ok' :
                    p.status==='failed'  ? 'dm-pipe-fail' : 'dm-pipe-pending']">
                    {{ p.status }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- MCP Tools -->
      <div class="ft-card">
        <div class="ft-card-header">
          <span class="ft-card-title">MCP / Infra Tools</span>
          <span class="ft-tag">3 connected</span>
        </div>
        <div class="ft-card-body">
          <div class="dm-tools">
            <div v-for="t in mcpTools" :key="t.name" class="dm-tool-card">
              <div class="dm-tool-icon">{{ t.icon }}</div>
              <div class="dm-tool-body">
                <div class="dm-tool-name">{{ t.name }} <span class="dm-mono" style="font-size:11px;color:var(--gc-text-3)">{{ t.version }}</span></div>
                <div class="dm-tool-desc">{{ t.desc }}</div>
              </div>
              <div :class="['dm-tool-dot', t.connected ? 'dm-tool-conn' : 'dm-tool-disc']"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <transition name="toast">
      <div v-if="toast" class="dm-toast">{{ toast }}</div>
    </transition>
  </div>
</template>

<style scoped>
.dm-root { display:flex; flex-direction:column; gap:18px; max-width:1300px; }

.dm-header { display:flex; align-items:center; justify-content:space-between; gap:16px; flex-wrap:wrap; }
.dm-header-left { display:flex; align-items:center; gap:14px; }
.dm-icon { font-size:26px; width:44px; height:44px; border-radius:10px; background:var(--gc-primary-light); display:flex; align-items:center; justify-content:center; color:var(--gc-primary); }
.dm-title { font-size:20px; font-weight:600; color:var(--gc-text); }
.dm-sub   { font-size:13px; color:var(--gc-text-2); margin-top:2px; }

.dm-env-tabs { display:flex; background:var(--gc-surface); border:1px solid var(--gc-border); border-radius:8px; overflow:hidden; }
.dm-env-btn { padding:7px 18px; font-size:13px; font-weight:500; color:var(--gc-text-2); background:transparent; border:none; cursor:pointer; transition:all .15s; }
.dm-env-btn.active { background:var(--gc-primary); color:#fff; }
.dm-env-btn:hover:not(.active) { background:var(--gc-surface-2); color:var(--gc-text); }

.dm-kpis { display:flex; gap:12px; flex-wrap:wrap; }
.dm-kpi { flex:1; min-width:150px; background:var(--gc-surface); border:1px solid var(--gc-border); border-radius:10px; padding:14px 18px; display:flex; align-items:center; gap:14px; }
.dm-kpi-dot { width:10px; height:10px; border-radius:50%; flex-shrink:0; }
.dm-kpi-val { font-size:18px; font-weight:600; color:var(--gc-text); }
.dm-kpi-lbl { font-size:11px; color:var(--gc-text-2); margin-top:2px; text-transform:uppercase; letter-spacing:.04em; }

.dm-grid { display:flex; flex-direction:column; gap:16px; }
.dm-card-wide {}

.dm-mono { font-family:var(--font-mono); font-size:12px; }

.dm-status-badge { display:inline-flex; align-items:center; gap:5px; font-size:12px; font-weight:500; padding:2px 8px; border-radius:4px; }
.dm-ok      { background:rgba(52,168,83,.12); color:#34a853; }
.dm-stopped { background:var(--gc-surface-2); color:var(--gc-text-3); }

.dm-pipe-badge { font-size:11px; font-weight:600; padding:2px 8px; border-radius:4px; text-transform:uppercase; }
.dm-pipe-ok      { background:rgba(52,168,83,.15); color:#34a853; }
.dm-pipe-fail    { background:rgba(234,67,53,.15); color:var(--gc-error); }
.dm-pipe-pending { background:rgba(251,188,4,.15); color:var(--gc-warning); }

.dm-tools { display:flex; flex-direction:column; gap:10px; }
.dm-tool-card { display:flex; align-items:center; gap:12px; padding:10px 14px; background:var(--gc-surface-2); border-radius:8px; border:1px solid var(--gc-border); }
.dm-tool-icon { font-size:20px; width:36px; height:36px; display:flex; align-items:center; justify-content:center; border-radius:8px; background:var(--gc-surface); flex-shrink:0; }
.dm-tool-body { flex:1; }
.dm-tool-name { font-size:13px; font-weight:500; color:var(--gc-text); }
.dm-tool-desc { font-size:12px; color:var(--gc-text-2); margin-top:2px; }
.dm-tool-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
.dm-tool-conn { background:#34a853; box-shadow:0 0 6px #34a85366; }
.dm-tool-disc { background:var(--gc-text-3); }

.dm-toast { position:fixed; bottom:24px; right:24px; background:var(--gc-surface); border:1px solid var(--gc-border); border-radius:8px; padding:12px 20px; font-size:13px; color:var(--gc-text); box-shadow:var(--gc-shadow-lg); z-index:9999; }
.toast-enter-active,.toast-leave-active { transition:all .2s; }
.toast-enter-from,.toast-leave-to { opacity:0; transform:translateY(8px); }
</style>
