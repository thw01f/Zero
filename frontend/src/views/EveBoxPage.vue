<template>
  <div class="tool-page">
    <div class="tool-header">
      <div>
        <div class="ft-card-title" style="font-size:11px;letter-spacing:0.12em">EVEBOX — SURICATA EVENT VIEWER</div>
        <div class="text-xs mt-0.5" style="color:#4a5568">IDS/IPS alert browser · SQLite backend · port 5636</div>
      </div>
      <div class="flex items-center gap-2">
        <span :class="['status-dot', online ? 'online' : 'offline']"></span>
        <span class="ft-tag" style="font-size:10px">{{ online ? 'ONLINE' : 'OFFLINE' }}</span>
        <button class="ft-btn-sm" @click="reload">↺ Reload</button>
        <a href="/api/evebox" target="_blank" class="ft-btn-sm">↗ Open full</a>
      </div>
    </div>

    <div class="iframe-wrap">
      <div v-if="!online && !loading" class="offline-overlay">
        <div class="offline-box">
          <div class="offline-icon">🛡️</div>
          <h3>EveBox is not running</h3>
          <p>Start it with:</p>
          <code>{{ startCmd }}</code>
          <div class="mt-3">
            <button class="ft-btn" @click="startEvebox">▶ Auto-start EveBox</button>
          </div>
          <p class="hint">Or run <code>sudo bash setup_tools.sh</code> to install as a system service</p>
        </div>
      </div>
      <div v-if="loading" class="loading-overlay">
        <div class="spinner"></div>
        <span>Connecting to EveBox...</span>
      </div>
      <iframe
        v-show="online"
        ref="frame"
        src="/api/evebox/"
        frameborder="0"
        class="tool-iframe"
        @load="onLoad"
        @error="onError"
        allow="same-origin"
        sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const frame   = ref<HTMLIFrameElement | null>(null)
const online  = ref(false)
const loading = ref(true)

const startCmd = '/home/w01f/.local/bin/evebox server --sqlite --no-auth --port 5636'

async function checkOnline() {
  try {
    const r = await fetch('/api/evebox/', { method: 'HEAD', signal: AbortSignal.timeout(3000) })
    online.value = r.ok || r.status < 500
  } catch {
    online.value = false
  }
  loading.value = false
}

async function startEvebox() {
  loading.value = true
  try {
    await fetch('/api/evebox/start', { method: 'POST' })
  } catch {}
  await new Promise(r => setTimeout(r, 3000))
  await checkOnline()
  if (online.value && frame.value) frame.value.src = '/api/evebox/'
}

function reload() {
  loading.value = true
  online.value  = false
  checkOnline().then(() => {
    if (online.value && frame.value) frame.value.src = '/api/evebox/'
  })
}

function onLoad()  { loading.value = false; online.value = true  }
function onError() { loading.value = false; online.value = false }

let _timer: ReturnType<typeof setInterval>
onMounted(() => {
  checkOnline()
  _timer = setInterval(checkOnline, 15000)
})
onUnmounted(() => clearInterval(_timer))
</script>

<style scoped>
.tool-page { display: flex; flex-direction: column; height: calc(100vh - 56px); gap: 8px; }
.tool-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 4px; flex-shrink: 0;
}
.iframe-wrap {
  position: relative; flex: 1; border-radius: 8px; overflow: hidden;
  border: 1px solid #1e2d47; background: #0d1117;
}
.tool-iframe { width: 100%; height: 100%; display: block; background: #fff; }

.offline-overlay, .loading-overlay {
  position: absolute; inset: 0; display: flex; align-items: center;
  justify-content: center; background: #0d1117; z-index: 10;
}
.offline-box {
  text-align: center; max-width: 480px; padding: 32px;
}
.offline-icon { font-size: 48px; margin-bottom: 12px; }
.offline-box h3 { color: #dde3ef; margin-bottom: 8px; }
.offline-box p  { color: #8a96b0; font-size: 13px; margin-bottom: 8px; }
.offline-box code {
  display: inline-block; background: #1e2d47; color: #3ecf8e;
  padding: 6px 12px; border-radius: 4px; font-size: 12px;
}
.hint { font-size: 11px; color: #4a5568; margin-top: 12px; }

.loading-overlay { flex-direction: column; gap: 12px; color: #8a96b0; font-size: 13px; }
.spinner {
  width: 28px; height: 28px; border: 2px solid #1e2d47;
  border-top-color: #4a9ff5; border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.status-dot {
  width: 8px; height: 8px; border-radius: 50%;
}
.status-dot.online  { background: #3ecf8e; box-shadow: 0 0 6px #3ecf8e; }
.status-dot.offline { background: #f25555; }

.ft-btn-sm {
  background: #1e2d47; color: #8a96b0; border: none; border-radius: 4px;
  padding: 4px 10px; font-size: 11px; cursor: pointer; text-decoration: none;
  display: inline-block;
}
.ft-btn-sm:hover { color: #dde3ef; background: #253650; }
.ft-btn {
  background: #4a9ff5; color: #fff; border: none; border-radius: 6px;
  padding: 8px 20px; font-size: 13px; cursor: pointer; margin-top: 4px;
}
.ft-btn:hover { background: #3d8de0; }
</style>
