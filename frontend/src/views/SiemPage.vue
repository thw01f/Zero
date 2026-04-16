<template>
  <div class="siem-root">
    <div class="siem-header">
      <div class="siem-header-left">
        <AppIcon name="eye" :size="18" class="siem-icon" />
        <span class="siem-title">SIEM — EveBox</span>
        <span class="siem-badge">Network Events</span>
      </div>
      <div class="siem-header-right">
        <span class="siem-url-label">EveBox URL</span>
        <input v-model="eveboxUrl" class="siem-url-input" placeholder="http://localhost:5636" @keyup.enter="reload" />
        <button class="siem-btn" @click="reload">Connect</button>
        <button class="siem-btn siem-btn-ghost" @click="openExternal" title="Open in new tab">
          <AppIcon name="upload" :size="14" />
        </button>
      </div>
    </div>

    <div class="siem-body">
      <!-- Error / offline state -->
      <div v-if="loadError" class="siem-offline">
        <AppIcon name="eye" :size="40" class="offline-icon" />
        <h3>EveBox not reachable</h3>
        <p>Could not load <code>{{ eveboxUrl }}</code></p>
        <p class="offline-hint">Start EveBox with:</p>
        <pre class="offline-cmd">evebox server --host 0.0.0.0 --port 5636</pre>
        <button class="siem-btn siem-btn-primary" @click="reload">Retry</button>
      </div>

      <!-- Loading -->
      <div v-else-if="loading" class="siem-loading">
        <span class="spin-char">◌</span>
        <span>Connecting to EveBox…</span>
      </div>

      <!-- EveBox iframe -->
      <iframe
        v-else
        :src="eveboxUrl"
        class="siem-frame"
        @load="onLoad"
        @error="onError"
        sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
        referrerpolicy="no-referrer"
        title="EveBox SIEM"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AppIcon from '../components/AppIcon.vue'

const STORAGE_KEY = 'dl_evebox_url'

const eveboxUrl = ref(localStorage.getItem(STORAGE_KEY) || 'http://localhost:5636')
const loading   = ref(true)
const loadError = ref(false)
let frameKey    = ref(0)

function saveUrl() {
  localStorage.setItem(STORAGE_KEY, eveboxUrl.value)
}

function reload() {
  saveUrl()
  loading.value   = true
  loadError.value = false
  frameKey.value++
  // Probe with a fetch first to give a quick error instead of a blank iframe
  probe()
}

async function probe() {
  try {
    await fetch(eveboxUrl.value, { mode: 'no-cors', signal: AbortSignal.timeout(5000) })
    // no-cors always succeeds if server responds, even with opaque response
    loading.value = false
  } catch {
    loading.value   = false
    loadError.value = true
  }
}

function onLoad() {
  loading.value   = false
  loadError.value = false
}

function onError() {
  loading.value   = false
  loadError.value = true
}

function openExternal() {
  window.open(eveboxUrl.value, '_blank', 'noopener')
}

onMounted(() => {
  probe()
})
</script>

<style scoped>
.siem-root {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background: var(--gc-bg);
}

.siem-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  border-bottom: 1px solid var(--gc-border);
  background: var(--gc-surface);
  flex-shrink: 0;
  gap: 12px;
  flex-wrap: wrap;
}

.siem-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.siem-icon { color: var(--gc-accent); }

.siem-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--gc-text-1);
}

.siem-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: #1a73e820;
  color: #1a73e8;
  font-weight: 500;
}

.siem-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.siem-url-label {
  font-size: 12px;
  color: var(--gc-text-3);
  white-space: nowrap;
}

.siem-url-input {
  background: var(--gc-bg);
  border: 1px solid var(--gc-border);
  border-radius: 6px;
  color: var(--gc-text-1);
  font-size: 13px;
  padding: 5px 10px;
  width: 240px;
  outline: none;
}
.siem-url-input:focus { border-color: var(--gc-accent); }

.siem-btn {
  background: var(--gc-accent);
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 5px 14px;
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: opacity .15s;
}
.siem-btn:hover { opacity: .85; }
.siem-btn-ghost {
  background: var(--gc-bg);
  color: var(--gc-text-2);
  border: 1px solid var(--gc-border);
  padding: 5px 8px;
}
.siem-btn-primary {
  background: var(--gc-accent);
  margin-top: 8px;
}

.siem-body {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.siem-frame {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
}

.siem-offline, .siem-loading {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--gc-text-2);
}

.offline-icon { color: var(--gc-text-3); opacity: .5; }

.siem-offline h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--gc-text-1);
  margin: 0;
}

.siem-offline p { margin: 0; font-size: 13px; }
.siem-offline code { color: var(--gc-accent); }
.offline-hint { color: var(--gc-text-3); font-size: 12px; }

.offline-cmd {
  background: var(--gc-surface);
  border: 1px solid var(--gc-border);
  border-radius: 6px;
  padding: 8px 16px;
  font-size: 13px;
  color: var(--gc-text-1);
  margin: 0;
}

.siem-loading {
  flex-direction: row;
  font-size: 14px;
  color: var(--gc-text-3);
}

.spin-char {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
