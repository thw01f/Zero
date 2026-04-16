<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import AppIcon from './AppIcon.vue'

interface ModelInfo {
  id: string; name: string; provider: string
  size?: string; context?: string; tier?: string; note?: string
}
interface Provider {
  name: string; online: boolean; models: ModelInfo[]
  upgrades?: { tag: string; name: string; size: string; note: string }[]
}

const wrap     = ref<HTMLElement | null>(null)
const open     = ref(false)
const loading  = ref(false)
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
  const m = current.value.model ?? ''
  if (!m) return 'Select model'
  // HF: "Qwen/Qwen2.5-Coder-32B-Instruct" → "Qwen2.5-Coder 32B"
  if (m.includes('/')) return m.split('/')[1].replace(/-Instruct$/i, '').replace(/-/g, ' ').slice(0, 22)
  // Gemini: "gemini-2.5-flash" → "Gemini 2.5 Flash"
  if (m.startsWith('gemini-')) return m.replace('gemini-', 'Gemini ').replace(/-/g, ' ')
  return m.split(':')[0]
})

const providerDot = computed(() => {
  const p = current.value.provider
  if (p === 'ollama')       return 'local'
  if (p === 'huggingface')  return 'hf'
  if (p === 'gemini')       return 'gemini'
  return 'cloud'
})

const ollamaP    = computed(() => providers.value['ollama'])
const hfP        = computed(() => providers.value['huggingface'])
const anthropicP = computed(() => providers.value['anthropic'])
const geminiP    = computed(() => providers.value['gemini'])

function outside(e: MouseEvent) {
  if (wrap.value && !wrap.value.contains(e.target as Node)) open.value = false
}
onMounted(() => { fetchModels(); document.addEventListener('click', outside) })
onBeforeUnmount(() => document.removeEventListener('click', outside))
</script>

<template>
  <div class="ms-wrap" ref="wrap">
    <button class="ms-pill" :class="{active: open}" @click="open = !open">
      <span class="ms-dot" :class="providerDot"></span>
      <span class="ms-label">{{ currentLabel }}</span>
      <AppIcon name="chevron_d" :size="11" style="color:var(--gc-text-3);flex-shrink:0;" />
    </button>

    <transition name="ms-drop">
      <div v-if="open" class="ms-dropdown">

        <!-- ── Ollama local ── -->
        <div class="ms-section">
          <div class="ms-section-hdr">
            <span class="ms-dot local"></span>
            Ollama (Local)
            <span class="ms-badge" :class="ollamaP?.online ? 'online' : 'offline'">
              {{ ollamaP?.online ? 'running' : 'offline' }}
            </span>
          </div>
          <template v-if="ollamaP?.online">
            <div v-if="!ollamaP.models.length" class="ms-empty">
              No models pulled yet.<br>
              <code style="font-size:10px;">ollama pull qwen2.5-coder:14b</code>
            </div>
            <div v-for="m in ollamaP.models" :key="m.id"
              class="ms-option"
              :class="{selected: current.provider==='ollama' && current.model===m.id}"
              @click="select('ollama', m.id)">
              <div class="ms-opt-name">{{ m.name }}</div>
              <div class="ms-opt-meta">{{ m.size }} · local</div>
            </div>
          </template>
          <div v-else class="ms-empty">Ollama not running</div>

          <!-- Upgrade suggestions -->
          <div v-if="ollamaP?.upgrades?.length" class="ms-upgrades">
            <div class="ms-upgrades-lbl">Better models to pull:</div>
            <div v-for="u in ollamaP.upgrades" :key="u.tag" class="ms-upgrade-row">
              <code class="ms-upgrade-tag">{{ u.tag }}</code>
              <span class="ms-upgrade-meta">{{ u.size }} — {{ u.note }}</span>
            </div>
          </div>
        </div>

        <div class="ms-divider"></div>

        <!-- ── Hugging Face ── -->
        <div class="ms-section">
          <div class="ms-section-hdr">
            <span class="ms-dot hf"></span>
            Hugging Face
            <span class="ms-badge" :class="hfP?.online ? 'online' : 'no-key'">
              {{ hfP?.online ? 'API key set' : 'no token' }}
            </span>
          </div>
          <div v-if="!hfP?.online" class="ms-hint">
            Set <code>HF_API_TOKEN=hf_…</code> in <code>backend/.env</code>
            to unlock 6 top code models (free tier available).
          </div>
          <div v-for="m in hfP?.models ?? []" :key="m.id"
            class="ms-option"
            :class="{selected: current.provider==='huggingface' && current.model===m.id,
                     disabled: !hfP?.online}"
            @click="hfP?.online && select('huggingface', m.id)">
            <div class="ms-opt-name">{{ m.name }}</div>
            <div class="ms-opt-meta">{{ m.note }}</div>
          </div>
        </div>

        <div class="ms-divider"></div>

        <!-- ── Anthropic ── -->
        <div class="ms-section">
          <div class="ms-section-hdr">
            <span class="ms-dot cloud"></span>
            Anthropic Claude
            <span class="ms-badge" :class="anthropicP?.online ? 'online' : 'no-key'">
              {{ anthropicP?.online ? 'online' : 'no API key' }}
            </span>
          </div>
          <div v-if="!anthropicP?.online" class="ms-hint">
            Set <code>ANTHROPIC_API_KEY=sk-ant-…</code> in <code>backend/.env</code>
          </div>
          <div v-for="m in anthropicP?.models ?? []" :key="m.id"
            class="ms-option"
            :class="{selected: current.provider==='anthropic' && current.model===m.id,
                     disabled: !anthropicP?.online}"
            @click="anthropicP?.online && select('anthropic', m.id)">
            <div class="ms-opt-name">{{ m.name }}</div>
            <div class="ms-opt-meta">{{ m.context }} · {{ m.tier }}</div>
          </div>
        </div>

        <div class="ms-divider"></div>

        <!-- ── Google Gemini ── -->
        <div class="ms-section">
          <div class="ms-section-hdr">
            <span class="ms-dot gemini"></span>
            Google Gemini
            <span class="ms-badge" :class="geminiP?.online ? 'online' : 'no-key'">
              {{ geminiP?.online ? 'online' : 'no API key' }}
            </span>
          </div>
          <div v-if="!geminiP?.online" class="ms-hint">
            Set <code>GEMINI_API_KEY=AIza…</code> in <code>backend/.env</code>
            or apply via Settings · 1M token context · free tier
          </div>
          <div v-for="m in geminiP?.models ?? []" :key="m.id"
            class="ms-option"
            :class="{selected: current.provider==='gemini' && current.model===m.id,
                     disabled: !geminiP?.online}"
            @click="geminiP?.online && select('gemini', m.id)">
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
  padding: 0 10px; height: 30px; border-radius: 15px;
  border: 1px solid var(--gc-border); background: var(--gc-surface-2);
  cursor: pointer; font-size: 12px; font-weight: 500; color: var(--gc-text);
  transition: border-color .15s, background .15s; white-space: nowrap;
}
.ms-pill:hover, .ms-pill.active {
  border-color: var(--gc-primary); background: var(--gc-primary-light);
}

.ms-dot {
  width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0;
}
.ms-dot.local   { background: #34a853; box-shadow: 0 0 0 2px rgba(52,168,83,.25); }
.ms-dot.cloud   { background: #4285f4; box-shadow: 0 0 0 2px rgba(66,133,244,.25); }
.ms-dot.hf      { background: #ff6f00; box-shadow: 0 0 0 2px rgba(255,111,0,.25); }
.ms-dot.gemini  { background: #1a73e8; box-shadow: 0 0 0 2px rgba(26,115,232,.25); }

.ms-label { max-width: 130px; overflow: hidden; text-overflow: ellipsis; }

.ms-dropdown {
  position: absolute; top: calc(100% + 6px); left: 50%; transform: translateX(-50%);
  width: 310px; background: var(--gc-surface); border: 1px solid var(--gc-border);
  border-radius: 12px; box-shadow: var(--gc-shadow-lg); z-index: 1000; overflow: hidden;
  max-height: 520px; overflow-y: auto;
}
.ms-dropdown::-webkit-scrollbar { width: 4px; }
.ms-dropdown::-webkit-scrollbar-thumb { background: var(--gc-border); border-radius: 2px; }

.ms-section { padding: 8px 0; }
.ms-section-hdr {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 14px 4px; font-size: 11px; font-weight: 700;
  text-transform: uppercase; letter-spacing: .6px; color: var(--gc-text-3);
}
.ms-badge {
  margin-left: auto; padding: 1px 6px; border-radius: 10px; font-size: 10px; font-weight: 600;
}
.ms-badge.online  { background: var(--gc-success-bg); color: var(--gc-success); }
.ms-badge.offline, .ms-badge.no-key { background: var(--gc-error-bg); color: var(--gc-error); }

.ms-option {
  padding: 7px 14px; cursor: pointer; display: flex; justify-content: space-between;
  align-items: center; gap: 8px; transition: background .1s;
}
.ms-option:hover    { background: var(--gc-surface-2); }
.ms-option.selected { background: var(--gc-primary-light); }
.ms-option.disabled { opacity: .45; cursor: not-allowed; }
.ms-opt-name { font-size: 13px; color: var(--gc-text); font-weight: 500; }
.ms-opt-meta { font-size: 11px; color: var(--gc-text-3); text-align: right; max-width: 140px; }

.ms-empty {
  padding: 8px 14px; font-size: 12px; color: var(--gc-text-3); line-height: 1.5;
}
.ms-hint {
  padding: 6px 14px 8px; font-size: 11px; color: var(--gc-text-3); line-height: 1.6;
  background: var(--gc-surface-2); border-top: 1px solid var(--gc-divider);
  border-bottom: 1px solid var(--gc-divider);
}
.ms-hint code { background: var(--gc-border); padding: 1px 4px; border-radius: 3px; font-size: 10px; }

/* Upgrades box */
.ms-upgrades {
  margin: 4px 10px 6px; padding: 8px 10px; border-radius: 8px;
  background: var(--gc-surface-2); border: 1px solid var(--gc-border);
}
.ms-upgrades-lbl { font-size: 10px; font-weight: 700; color: var(--gc-text-3); text-transform: uppercase; letter-spacing: .5px; margin-bottom: 6px; }
.ms-upgrade-row  { display: flex; align-items: baseline; gap: 8px; padding: 2px 0; }
.ms-upgrade-tag  { font-size: 11px; background: var(--gc-border); padding: 1px 5px; border-radius: 3px; color: var(--gc-text); flex-shrink: 0; }
.ms-upgrade-meta { font-size: 11px; color: var(--gc-text-3); }

.ms-divider { border-top: 1px solid var(--gc-border); }

.ms-drop-enter-active, .ms-drop-leave-active { transition: opacity .15s, transform .15s; }
.ms-drop-enter-from, .ms-drop-leave-to       { opacity: 0; transform: translateX(-50%) translateY(-6px); }
</style>
