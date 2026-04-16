<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AppIcon from '../components/AppIcon.vue'

interface KeyState { set: boolean; masked: string }
interface SettingsData {
  keys: { anthropic: KeyState; huggingface: KeyState; gemini: KeyState }
  scanner: { max_repo_size_mb: number; clone_timeout_s: number; llm_fix_batch_size: number; advisory_poll_hours: number }
  llm: { ollama_url: string; ollama_model: string; use_local_llm: boolean }
}

const tab = ref('api-keys')
const tabs = [
  { id: 'api-keys',  label: 'API Keys' },
  { id: 'models',    label: 'AI Models' },
  { id: 'scanner',   label: 'Scanner' },
]

const cfg    = ref<SettingsData | null>(null)
const models = ref<any>(null)
const saving = ref(false)
const msg    = ref('')
const msgOk  = ref(true)

const keys = ref({ anthropic_api_key: '', hf_api_token: '', gemini_api_key: '' })

async function load() {
  const [s, m] = await Promise.all([
    fetch('/api/settings').then(r => r.json()),
    fetch('/api/models').then(r => r.json()),
  ])
  cfg.value    = s
  models.value = m
}

async function saveKeys() {
  saving.value = true; msg.value = ''
  const payload: Record<string,string> = {}
  if (keys.value.anthropic_api_key) payload.anthropic_api_key = keys.value.anthropic_api_key
  if (keys.value.hf_api_token)      payload.hf_api_token      = keys.value.hf_api_token
  if (keys.value.gemini_api_key)    payload.gemini_api_key     = keys.value.gemini_api_key
  if (!Object.keys(payload).length) { msg.value = 'Enter at least one key to save'; msgOk.value = false; saving.value = false; return }
  const r = await fetch('/api/settings/keys', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const d = await r.json()
  msgOk.value = r.ok
  msg.value = r.ok ? `Keys applied for this session (${d.updated.join(', ')})` : 'Failed to apply keys'
  if (r.ok) { keys.value = { anthropic_api_key: '', hf_api_token: '', gemini_api_key: '' }; await load() }
  saving.value = false
}

onMounted(load)
</script>

<template>
  <div style="max-width:760px;margin:0 auto;">
    <h2 style="font-weight:400;margin-bottom:24px;">Settings</h2>

    <div class="gc-tabs" style="margin-bottom:24px;">
      <div v-for="t in tabs" :key="t.id" class="gc-tab" :class="{active: tab===t.id}" @click="tab=t.id">
        {{ t.label }}
      </div>
    </div>

    <!-- ─── API Keys ─── -->
    <div v-if="tab==='api-keys'">
      <!-- Status cards -->
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:24px;">
        <div class="gc-card" style="padding:16px;">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
            <span style="width:8px;height:8px;border-radius:50%;background:" :style="{background: cfg?.keys.anthropic.set ? '#1e8e3e' : '#d93025'}"></span>
            <span style="font-size:12px;font-weight:600;color:var(--gc-text-2);">Anthropic Claude</span>
          </div>
          <div v-if="cfg?.keys.anthropic.set" style="font-family:monospace;font-size:11px;color:var(--gc-text-3);">{{ cfg.keys.anthropic.masked }}</div>
          <div v-else style="font-size:11px;color:var(--gc-error);">No key set</div>
        </div>
        <div class="gc-card" style="padding:16px;">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
            <span style="width:8px;height:8px;border-radius:50%;" :style="{background: cfg?.keys.huggingface.set ? '#1e8e3e' : '#d93025'}"></span>
            <span style="font-size:12px;font-weight:600;color:var(--gc-text-2);">Hugging Face</span>
          </div>
          <div v-if="cfg?.keys.huggingface.set" style="font-family:monospace;font-size:11px;color:var(--gc-text-3);">{{ cfg.keys.huggingface.masked }}</div>
          <div v-else style="font-size:11px;color:var(--gc-error);">No token set</div>
        </div>
        <div class="gc-card" style="padding:16px;">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
            <span style="width:8px;height:8px;border-radius:50%;" :style="{background: cfg?.keys.gemini.set ? '#1e8e3e' : '#d93025'}"></span>
            <span style="font-size:12px;font-weight:600;color:var(--gc-text-2);">Google Gemini</span>
          </div>
          <div v-if="cfg?.keys.gemini.set" style="font-family:monospace;font-size:11px;color:var(--gc-text-3);">{{ cfg.keys.gemini.masked }}</div>
          <div v-else style="font-size:11px;color:var(--gc-error);">No key set</div>
        </div>
      </div>

      <!-- Key input form -->
      <div class="gc-card">
        <div class="gc-card-header">
          <h3 class="gc-card-title">Apply API Keys</h3>
          <span style="font-size:11px;color:var(--gc-text-3);">Session-only · restart clears them · or set in backend/.env for persistence</span>
        </div>
        <div class="gc-card-body">
          <div v-if="msg" class="gc-alert" :class="msgOk ? 'gc-alert-success' : 'gc-alert-error'" style="margin-bottom:16px;">
            {{ msg }}
          </div>

          <!-- Anthropic -->
          <div class="gc-form-group">
            <label class="gc-label">Anthropic API Key</label>
            <input v-model="keys.anthropic_api_key" class="gc-input" type="password"
              placeholder="sk-ant-api03-…" autocomplete="off" />
            <span class="gc-hint">
              Get from
              <a href="https://console.anthropic.com/settings/keys" target="_blank" style="color:var(--gc-primary);">console.anthropic.com</a>
              · Powers Claude Opus/Sonnet/Haiku
            </span>
          </div>

          <!-- Hugging Face -->
          <div class="gc-form-group">
            <label class="gc-label">Hugging Face Token</label>
            <input v-model="keys.hf_api_token" class="gc-input" type="password"
              placeholder="hf_…" autocomplete="off" />
            <span class="gc-hint">
              Get free token at
              <a href="https://huggingface.co/settings/tokens" target="_blank" style="color:var(--gc-primary);">huggingface.co/settings/tokens</a>
              · Must start with <code style="background:var(--gc-surface-2);padding:1px 4px;border-radius:3px;">hf_</code>
              · Free tier: Qwen2.5-Coder-32B, DeepSeek, Gemma and more
            </span>
          </div>

          <!-- Gemini -->
          <div class="gc-form-group">
            <label class="gc-label">Google Gemini API Key</label>
            <input v-model="keys.gemini_api_key" class="gc-input" type="password"
              placeholder="AIza…" autocomplete="off" />
            <span class="gc-hint">
              Get from
              <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:var(--gc-primary);">Google AI Studio</a>
              · Gemini 2.5 Flash free tier available · 1M token context
            </span>
          </div>

          <button class="gc-btn gc-btn-primary" :disabled="saving" @click="saveKeys">
            {{ saving ? 'Applying…' : 'Apply Keys' }}
          </button>

          <div style="margin-top:20px;padding:12px 14px;background:var(--gc-surface-2);border-radius:8px;border:1px solid var(--gc-border);">
            <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:var(--gc-text-3);margin-bottom:8px;">Persist to disk</div>
            <div style="font-size:12px;color:var(--gc-text-2);line-height:1.8;">
              Add to <code style="background:var(--gc-border);padding:1px 5px;border-radius:3px;font-size:11px;">backend/.env</code>:<br>
              <code style="font-size:11px;color:var(--gc-text);">ANTHROPIC_API_KEY=sk-ant-…</code><br>
              <code style="font-size:11px;color:var(--gc-text);">HF_API_TOKEN=hf_…</code><br>
              <code style="font-size:11px;color:var(--gc-text);">GEMINI_API_KEY=AIza…</code>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ─── AI Models ─── -->
    <div v-if="tab==='models' && models">
      <div v-for="(prov, key) in models.providers" :key="key" class="gc-card" style="margin-bottom:16px;">
        <div class="gc-card-header">
          <h3 class="gc-card-title">{{ prov.name }}</h3>
          <span class="gc-badge" :style="{background: prov.online ? 'var(--gc-success-bg)' : 'var(--gc-error-bg)', color: prov.online ? 'var(--gc-success)' : 'var(--gc-error)'}">
            {{ prov.online ? 'online' : 'not configured' }}
          </span>
        </div>
        <div class="gc-card-body" style="padding:0;">
          <table style="width:100%;border-collapse:collapse;">
            <thead>
              <tr style="border-bottom:1px solid var(--gc-border);">
                <th style="text-align:left;padding:8px 16px;font-size:11px;color:var(--gc-text-3);font-weight:600;text-transform:uppercase;">Model</th>
                <th style="text-align:left;padding:8px 16px;font-size:11px;color:var(--gc-text-3);font-weight:600;text-transform:uppercase;">Context</th>
                <th style="text-align:left;padding:8px 16px;font-size:11px;color:var(--gc-text-3);font-weight:600;text-transform:uppercase;">Tier</th>
                <th style="text-align:left;padding:8px 16px;font-size:11px;color:var(--gc-text-3);font-weight:600;text-transform:uppercase;">Note</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in prov.models" :key="m.id"
                style="border-bottom:1px solid var(--gc-divider);"
                :style="{opacity: prov.online ? 1 : 0.5}">
                <td style="padding:10px 16px;font-size:13px;color:var(--gc-text);font-weight:500;">{{ m.name }}</td>
                <td style="padding:10px 16px;font-size:12px;color:var(--gc-text-2);">{{ m.context || '—' }}</td>
                <td style="padding:10px 16px;font-size:12px;color:var(--gc-text-2);">{{ m.tier || '—' }}</td>
                <td style="padding:10px 16px;font-size:11px;color:var(--gc-text-3);">{{ m.note || m.size || '' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="gc-card" style="padding:16px;">
        <div style="font-size:12px;color:var(--gc-text-2);line-height:1.8;">
          <strong style="color:var(--gc-text);">Active model</strong> is shown in the pill at the top of the sidebar.<br>
          Click it to switch models at runtime.
          Model priority: <strong>Runtime override</strong> → Gemini key → HF token → Anthropic key → Ollama local.
        </div>
      </div>
    </div>

    <!-- ─── Scanner ─── -->
    <div v-if="tab==='scanner' && cfg">
      <div class="gc-card">
        <div class="gc-card-header"><h3 class="gc-card-title">Scanner Configuration</h3></div>
        <div class="gc-card-body" style="padding:0;">
          <table style="width:100%;border-collapse:collapse;">
            <tbody>
              <tr v-for="(val, key) in cfg.scanner" :key="key" style="border-bottom:1px solid var(--gc-divider);">
                <td style="padding:12px 16px;font-size:13px;color:var(--gc-text-2);width:60%;">{{ key.replace(/_/g,' ') }}</td>
                <td style="padding:12px 16px;font-family:monospace;font-size:13px;color:var(--gc-text);font-weight:500;">{{ val }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="gc-card" style="margin-top:16px;">
        <div class="gc-card-header"><h3 class="gc-card-title">Ollama (Local LLM)</h3></div>
        <div class="gc-card-body" style="padding:0;">
          <table style="width:100%;border-collapse:collapse;">
            <tbody>
              <tr style="border-bottom:1px solid var(--gc-divider);">
                <td style="padding:12px 16px;font-size:13px;color:var(--gc-text-2);width:60%;">URL</td>
                <td style="padding:12px 16px;font-family:monospace;font-size:13px;color:var(--gc-text);">{{ cfg.llm.ollama_url }}</td>
              </tr>
              <tr style="border-bottom:1px solid var(--gc-divider);">
                <td style="padding:12px 16px;font-size:13px;color:var(--gc-text-2);">Default model</td>
                <td style="padding:12px 16px;font-family:monospace;font-size:13px;color:var(--gc-text);">{{ cfg.llm.ollama_model }}</td>
              </tr>
              <tr>
                <td style="padding:12px 16px;font-size:13px;color:var(--gc-text-2);">Force local mode</td>
                <td style="padding:12px 16px;font-size:13px;color:var(--gc-text);">{{ cfg.llm.use_local_llm ? 'Yes' : 'No' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.gc-badge {
  padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600;
}
</style>
