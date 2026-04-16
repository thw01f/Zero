<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import AppIcon from './AppIcon.vue'

interface ModelInfo {
  id: string; name: string; provider: string
  size?: string; context?: string; tier?: string
}
interface Provider {
  name: string; online: boolean; models: ModelInfo[]
}

const wrap  = ref<HTMLElement | null>(null)
const open  = ref(false)
const loading = ref(false)
const providers = ref<Record<string, Provider>>({})
const current   = ref<{ provider: string; model: string }>({ provider: 'ollama', model: '' })

async function fetchModels() {
  try {
    const r = await fetch('/api/models')
    const d = await r.json()
    providers.value = d.providers ?? {}
    current.value   = d.current   ?? current.value
  } catch {}
}

async function select(provider: string, model: string) {
  loading.value = true
  try {
    await fetch('/api/models/select', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider, model }),
    })
    current.value = { provider, model }
  } finally {
    loading.value = false
    open.value = false
  }
}

const currentLabel = computed(() => {
  const m = current.value.model
  return m ? m.split(':')[0].replace(/claude-/, 'Claude ') : 'Select model'
})

const isLocal = computed(() => current.value.provider === 'ollama')

const ollamaProvider   = computed(() => providers.value['ollama'])
const anthropicProvider= computed(() => providers.value['anthropic'])

function outside(e: MouseEvent) {
  if (wrap.value && !wrap.value.contains(e.target as Node)) open.value = false
}
onMounted(() => { fetchModels(); document.addEventListener('click', outside) })
onBeforeUnmount(() => document.removeEventListener('click', outside))
</script>

<template>
  <div class="ms-wrap" ref="wrap">
    <button class="ms-pill" :class="{active: open}" @click="open = !open">
      <span class="ms-dot" :class="isLocal ? 'local' : 'cloud'"></span>
      <span class="ms-label">{{ currentLabel }}</span>
      <AppIcon name="chevron_d" :size="12" style="color:var(--gc-text-3)" />
    </button>

    <transition name="ms-drop">
      <div v-if="open" class="ms-dropdown">
        <!-- Ollama section -->
        <div class="ms-section">
          <div class="ms-section-hdr">
            <span class="ms-dot local" style="width:8px;height:8px;"></span>
            Ollama (Local)
            <span class="ms-badge" :class="ollamaProvider?.online ? 'online' : 'offline'">
              {{ ollamaProvider?.online ? 'online' : 'offline' }}
            </span>
          </div>
          <template v-if="ollamaProvider?.online">
            <div v-if="!ollamaProvider.models.length" class="ms-empty">No models pulled yet</div>
            <div v-for="m in ollamaProvider.models" :key="m.id"
              class="ms-option"
              :class="{selected: current.provider==='ollama' && current.model===m.id}"
              @click="select('ollama', m.id)">
              <div class="ms-opt-name">{{ m.name }}</div>
              <div class="ms-opt-meta">{{ m.size }} · local</div>
            </div>
          </template>
          <div v-else class="ms-empty">Ollama not running</div>
        </div>

        <div class="ms-divider"></div>

        <!-- Anthropic section -->
        <div class="ms-section">
          <div class="ms-section-hdr">
            <span class="ms-dot cloud" style="width:8px;height:8px;"></span>
            Anthropic Claude
            <span class="ms-badge" :class="anthropicProvider?.online ? 'online' : 'no-key'">
              {{ anthropicProvider?.online ? 'online' : 'no API key' }}
            </span>
          </div>
          <div v-for="m in anthropicProvider?.models ?? []" :key="m.id"
            class="ms-option"
            :class="{selected: current.provider==='anthropic' && current.model===m.id,
                     disabled: !anthropicProvider?.online}"
            @click="anthropicProvider?.online && select('anthropic', m.id)">
            <div class="ms-opt-name">{{ m.name }}</div>
            <div class="ms-opt-meta">{{ m.context }} · {{ m.tier }}</div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.ms-wrap { position: relative; }

.ms-pill {
  display: flex; align-items: center; gap: 6px;
  padding: 0 10px; height: 32px; border-radius: 16px;
  border: 1px solid var(--gc-border); background: var(--gc-surface-2);
  cursor: pointer; font-size: 12px; font-weight: 500; color: var(--gc-text);
  transition: border-color 0.15s, background 0.15s;
  white-space: nowrap;
}
.ms-pill:hover, .ms-pill.active {
  border-color: var(--gc-primary); background: var(--gc-primary-light);
}

.ms-dot {
  width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0;
}
.ms-dot.local { background: #34a853; box-shadow: 0 0 0 2px rgba(52,168,83,.25); }
.ms-dot.cloud { background: #4285f4; box-shadow: 0 0 0 2px rgba(66,133,244,.25); }

.ms-label { max-width: 120px; overflow: hidden; text-overflow: ellipsis; }

.ms-dropdown {
  position: absolute; top: calc(100% + 6px); left: 50%; transform: translateX(-50%);
  width: 280px; background: var(--gc-surface); border: 1px solid var(--gc-border);
  border-radius: 12px; box-shadow: var(--gc-shadow-lg); z-index: 1000;
  overflow: hidden;
}

.ms-section { padding: 8px 0; }
.ms-section-hdr {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 14px 4px; font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: .6px; color: var(--gc-text-3);
}

.ms-badge {
  margin-left: auto; padding: 1px 6px; border-radius: 10px; font-size: 10px; font-weight: 500;
}
.ms-badge.online  { background: var(--gc-success-bg); color: var(--gc-success); }
.ms-badge.offline, .ms-badge.no-key { background: var(--gc-error-bg); color: var(--gc-error); }

.ms-option {
  padding: 8px 14px; cursor: pointer; display: flex; justify-content: space-between;
  align-items: center; transition: background 0.1s;
}
.ms-option:hover     { background: var(--gc-surface-2); }
.ms-option.selected  { background: var(--gc-primary-light); }
.ms-option.disabled  { opacity: .45; cursor: not-allowed; }
.ms-opt-name { font-size: 13px; color: var(--gc-text); }
.ms-opt-meta { font-size: 11px; color: var(--gc-text-3); }

.ms-empty   { padding: 8px 14px; font-size: 12px; color: var(--gc-text-3); }
.ms-divider { border-top: 1px solid var(--gc-border); }

.ms-drop-enter-active, .ms-drop-leave-active { transition: opacity .15s, transform .15s; }
.ms-drop-enter-from, .ms-drop-leave-to       { opacity: 0; transform: translateX(-50%) translateY(-6px); }
</style>
