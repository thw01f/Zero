<template>
  <div class="ai-root">
    <div v-if="!scan.jobId" class="ai-empty">
      <div class="ai-empty-icon">🤖</div>
      <div class="ai-empty-title">No scan loaded</div>
      <div class="ai-empty-sub">Run a scan first to enable AI analysis</div>
    </div>

    <template v-else>
      <!-- Left: Vulnerability Browser -->
      <div class="ai-sidebar">
        <div class="ai-sidebar-hdr">
          <span class="ai-sidebar-title">TOP VULNERABILITIES</span>
          <span class="ai-badge-count">{{ topIssues.length }}</span>
        </div>
        <div class="ai-filter-row">
          <button
            v-for="s in ['all','critical','major','minor']" :key="s"
            class="ai-filter-btn" :class="{ active: issueFilter === s }"
            @click="issueFilter = s"
          >{{ s }}</button>
        </div>
        <div class="ai-issue-list">
          <div
            v-for="iss in filteredIssues" :key="iss.id"
            class="ai-issue-item"
            :class="{ selected: selectedIssue?.id === iss.id }"
            @click="selectIssue(iss)"
          >
            <div class="ai-issue-top">
              <span class="sev-chip" :class="'sev-' + iss.severity">{{ iss.severity }}</span>
              <span class="ai-issue-rule">{{ iss.rule_id || 'rule' }}</span>
            </div>
            <div class="ai-issue-msg">{{ truncate(iss.message, 72) }}</div>
            <div class="ai-issue-file">{{ shortPath(iss.file_path) }}:{{ iss.line_start }}</div>
          </div>
          <div v-if="!filteredIssues.length" class="ai-no-issues">No {{ issueFilter !== 'all' ? issueFilter : '' }} issues</div>
        </div>
      </div>

      <!-- Divider -->
      <div class="ai-divider"></div>

      <!-- Right: Chat + Explain panel -->
      <div class="ai-main">
        <!-- Issue detail drawer (shown when issue selected) -->
        <transition name="slide-down">
          <div v-if="selectedIssue && explainData" class="ai-explain-card">
            <!-- Header -->
            <div class="ai-explain-hdr">
              <span class="sev-chip" :class="'sev-' + selectedIssue.severity">{{ selectedIssue.severity }}</span>
              <span class="ai-explain-rule">{{ selectedIssue.rule_id }}</span>
              <span class="ai-explain-path">{{ shortPath(selectedIssue.file_path) }}:{{ selectedIssue.line_start }}</span>
              <!-- Tab switcher -->
              <div class="ai-explain-tabs">
                <button :class="['ai-etab', explainTab==='analysis' && 'active']" @click="explainTab='analysis'">Analysis</button>
                <button :class="['ai-etab', explainTab==='codefix' && 'active']" @click="explainTab='codefix'; ensureFix()">
                  Code Fix
                  <span v-if="fixPatched" class="ai-etab-dot"></span>
                </button>
              </div>
              <button class="ai-close-btn" @click="clearExplain">✕</button>
            </div>

            <div v-if="explainLoading" class="ai-explain-loading">
              <span class="spin-dot"></span> Analyzing vulnerability…
            </div>

            <!-- Analysis tab -->
            <div v-else-if="explainTab==='analysis'" class="ai-explain-body">
              <div class="ai-explain-section">
                <div class="ai-explain-label">WHY IT HAPPENS</div>
                <div class="ai-explain-text">{{ explainData.why }}</div>
              </div>
              <div class="ai-explain-section">
                <div class="ai-explain-label">RISK</div>
                <div class="ai-explain-text" style="color:#f97316">{{ explainData.risk }}</div>
              </div>
              <div class="ai-explain-section">
                <div class="ai-explain-label">FIX SUMMARY</div>
                <pre class="ai-explain-code">{{ explainData.fix }}</pre>
              </div>
              <div v-if="explainData.example_attack" class="ai-explain-section">
                <div class="ai-explain-label">ATTACK EXAMPLE</div>
                <div class="ai-explain-text" style="color:#ef4444;font-size:11px">{{ explainData.example_attack }}</div>
              </div>
              <div v-if="explainData.references?.length" class="ai-explain-section">
                <div class="ai-explain-label">REFERENCES</div>
                <div class="ai-refs">
                  <span v-for="r in explainData.references" :key="r" class="ft-tag">{{ r }}</span>
                </div>
              </div>
              <div style="padding-bottom:4px">
                <button class="ft-btn ft-btn-secondary ft-btn-sm" @click="explainTab='codefix'; ensureFix()">
                  View Code Fix →
                </button>
              </div>
            </div>

            <!-- Code Fix tab -->
            <div v-else-if="explainTab==='codefix'" class="ai-codefix-panel">
              <div v-if="fixLoading" class="ai-explain-loading">
                <span class="spin-dot"></span> Generating patch…
              </div>
              <div v-else class="ai-codefix-body">
                <!-- Before / After toggle -->
                <div class="ai-codefix-toolbar">
                  <div class="ai-codefix-toggle">
                    <button :class="['ai-toggle-btn', fixView==='split' && 'active']" @click="fixView='split'">Split</button>
                    <button :class="['ai-toggle-btn', fixView==='diff' && 'active']"  @click="fixView='diff'">Diff</button>
                    <button :class="['ai-toggle-btn', fixView==='fixed' && 'active']" @click="fixView='fixed'">Fixed only</button>
                  </div>
                  <div style="display:flex;gap:6px;margin-left:auto">
                    <button class="ft-btn ft-btn-secondary ft-btn-sm" @click="copyFix" :title="copied ? 'Copied!' : 'Copy fixed code'">
                      {{ copied ? '✓ Copied' : 'Copy Fix' }}
                    </button>
                    <button class="ft-btn ft-btn-secondary ft-btn-sm" @click="sendFixToChat">Ask AI</button>
                    <button class="ft-btn ft-btn-primary ft-btn-sm" @click="acceptFix" :disabled="selectedIssue.fix_accepted===1">
                      {{ selectedIssue.fix_accepted===1 ? '✓ Accepted' : 'Accept Fix' }}
                    </button>
                  </div>
                </div>

                <!-- Split view -->
                <div v-if="fixView==='split'" class="ai-codefix-split">
                  <div class="ai-codefix-pane">
                    <div class="ai-codefix-pane-hdr ai-pane-bad">
                      <span>⚠ Vulnerable</span>
                      <span class="ai-pane-file">{{ shortPath(selectedIssue.file_path) }}:{{ selectedIssue.line_start }}</span>
                    </div>
                    <div class="ai-code-editor">
                      <div v-for="(line, idx) in vulnerableLines" :key="idx"
                        :class="['ai-code-line', idx+1 === selectedIssue.line_start && 'ai-code-line-hl']">
                        <span class="ai-lineno">{{ idx + 1 }}</span>
                        <span class="ai-linetext">{{ line }}</span>
                      </div>
                      <div v-if="!vulnerableLines.length" class="ai-code-placeholder">
                        <span>Paste vulnerable code below to compare</span>
                      </div>
                    </div>
                    <textarea v-model="userCodeInput" class="ai-code-paste"
                      placeholder="Paste the vulnerable code snippet here…"
                      rows="3" @input="parseUserCode"></textarea>
                  </div>
                  <div class="ai-codefix-pane">
                    <div class="ai-codefix-pane-hdr ai-pane-good">
                      <span>✓ Fixed</span>
                      <span class="ai-pane-file">AI suggested patch</span>
                    </div>
                    <div class="ai-code-editor">
                      <div v-for="(line, idx) in fixedLines" :key="idx" class="ai-code-line ai-code-line-fix">
                        <span class="ai-lineno">{{ idx + 1 }}</span>
                        <span class="ai-linetext">{{ line }}</span>
                      </div>
                      <div v-if="!fixedLines.length" class="ai-code-placeholder">No fix generated yet</div>
                    </div>
                  </div>
                </div>

                <!-- Diff view -->
                <div v-if="fixView==='diff'" class="ai-codefix-diff-wrap">
                  <div v-if="selectedIssue.fix_diff" v-html="renderDiff(selectedIssue.fix_diff)" class="ai-diff-inner"></div>
                  <div v-else-if="generatedDiff" v-html="renderDiff(generatedDiff)" class="ai-diff-inner"></div>
                  <div v-else class="ai-code-placeholder" style="padding:20px">
                    No diff available — paste vulnerable code in Split view to generate one.
                  </div>
                </div>

                <!-- Fixed only -->
                <div v-if="fixView==='fixed'" class="ai-code-editor ai-fixed-only">
                  <div v-for="(line, idx) in fixedLines" :key="idx" class="ai-code-line ai-code-line-fix">
                    <span class="ai-lineno">{{ idx + 1 }}</span>
                    <span class="ai-linetext">{{ line }}</span>
                  </div>
                  <div v-if="!fixedLines.length" class="ai-code-placeholder">No fix available</div>
                </div>

                <!-- Patch notes -->
                <div v-if="fixNotes" class="ai-fix-notes">
                  <div class="ai-explain-label" style="margin-bottom:6px">PATCH NOTES</div>
                  <div class="ai-explain-text">{{ fixNotes }}</div>
                </div>
              </div>
            </div>
          </div>
        </transition>

        <!-- Chat header -->
        <div class="ai-chat-hdr">
          <span class="ai-chat-title">AI ASSISTANT</span>
          <div class="ai-chat-model">{{ modelName }}</div>
          <button v-if="messages.length" class="ai-clear-btn" @click="clearChat">Clear</button>
        </div>

        <!-- Messages -->
        <div ref="messagesEl" class="ai-messages">
          <div v-if="!messages.length" class="ai-suggestions">
            <div class="ai-suggest-title">Ask about your scan results</div>
            <div class="ai-suggest-grid">
              <button
                v-for="q in suggestions" :key="q"
                class="ai-suggest-btn" @click="sendQuestion(q)"
              >{{ q }}</button>
            </div>
          </div>

          <div v-for="(msg, i) in messages" :key="i" class="ai-msg-row" :class="msg.role">
            <div class="ai-msg-bubble" :class="msg.role">
              <pre class="ai-msg-text">{{ msg.content }}</pre>
            </div>
          </div>

          <div v-if="loading" class="ai-msg-row assistant">
            <div class="ai-msg-bubble assistant ai-typing">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>

        <!-- Quick suggestions when chatting -->
        <div v-if="messages.length && !loading" class="ai-quick-row">
          <button
            v-for="q in quickSugg" :key="q"
            class="ai-quick-btn" @click="sendQuestion(q)"
          >{{ q }}</button>
        </div>

        <!-- Input -->
        <div class="ai-input-row">
          <textarea
            v-model="input"
            @keydown.enter.exact.prevent="send"
            @keydown.enter.shift.exact="input += '\n'"
            placeholder="Ask about vulnerabilities, code quality, security posture… (Enter to send)"
            class="ai-textarea"
            rows="2"
          ></textarea>
          <button class="ai-send-btn" :disabled="loading || !input.trim()" @click="send">
            <svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
              <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z"/>
            </svg>
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import axios from 'axios'
import { useScanStore } from '../stores/scan'
import { useReportStore } from '../stores/report'

const scan   = useScanStore()
const report = useReportStore()

const messages      = ref<{ role: string; content: string }[]>([])
const input         = ref('')
const loading       = ref(false)
const messagesEl    = ref<HTMLElement | null>(null)
const issueFilter   = ref('all')
const selectedIssue = ref<any>(null)
const explainData   = ref<any>(null)
const explainLoading = ref(false)
const modelName     = ref('AI')

// Code Fix state
const explainTab    = ref<'analysis'|'codefix'>('analysis')
const fixView       = ref<'split'|'diff'|'fixed'>('split')
const fixLoading    = ref(false)
const fixPatched    = ref(false)
const fixNotes      = ref('')
const userCodeInput = ref('')
const vulnerableLines = ref<string[]>([])
const fixedLines    = ref<string[]>([])
const generatedDiff = ref('')
const copied        = ref(false)

const suggestions = [
  'What are the top 3 critical fixes?',
  'Is this project safe to deploy?',
  'Summarize all injection risks',
  'Which files need immediate attention?',
  'What OWASP categories are present?',
  'Explain the worst vulnerability',
]

const quickSugg = [
  'How to fix critical issues?',
  'What is the overall risk score?',
  'Show me the worst file',
]

const topIssues = computed(() => {
  const sevOrder: Record<string, number> = { critical: 0, major: 1, minor: 2, info: 3 }
  return [...(report.issues || [])]
    .sort((a, b) => (sevOrder[a.severity] ?? 4) - (sevOrder[b.severity] ?? 4))
    .slice(0, 40)
})

const filteredIssues = computed(() => {
  if (issueFilter.value === 'all') return topIssues.value
  return topIssues.value.filter(i => i.severity === issueFilter.value)
})

function truncate(s: string, n: number) {
  return s && s.length > n ? s.slice(0, n) + '…' : s
}

function shortPath(fp: string) {
  const parts = (fp || '').replace(/\\/g, '/').split('/')
  return parts.length > 2 ? '…/' + parts.slice(-2).join('/') : fp
}

async function scrollToBottom() {
  await nextTick()
  if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
}

onMounted(async () => {
  if (!scan.jobId) return
  try {
    const { data } = await axios.get(`/api/analyze/models`)
    modelName.value = data.active_model?.split('-').slice(0, 2).join('-') || 'AI'
  } catch {}
  try {
    const { data } = await axios.get(`/api/chat/${scan.jobId}/history`)
    if (data.messages?.length) {
      messages.value = data.messages.map((m: any) => ({ role: m.role, content: m.content }))
      await scrollToBottom()
    }
  } catch {}
})

async function selectIssue(iss: any) {
  selectedIssue.value = iss
  explainData.value = null
  explainLoading.value = true

  // Fetch AI explanation
  try {
    const { data } = await axios.post('/api/analyze/explain', {
      file_path: iss.file_path,
      line: iss.line_start,
      severity: iss.severity,
      rule_id: iss.rule_id,
      message: iss.message,
      language: report.data?.language || 'unknown',
      cwe_id: iss.cwe_id,
      owasp_category: iss.owasp_category,
    })
    explainData.value = data
  } catch {
    explainData.value = {
      why: iss.llm_explanation || iss.message,
      risk: 'See message above.',
      fix: 'Review and remediate the identified issue.',
      example_attack: '',
      references: [],
    }
  } finally {
    explainLoading.value = false
  }
}

function clearExplain() {
  selectedIssue.value = null
  explainData.value   = null
  explainTab.value    = 'analysis'
  fixView.value       = 'split'
  fixPatched.value    = false
  fixNotes.value      = ''
  userCodeInput.value = ''
  vulnerableLines.value = []
  fixedLines.value    = []
  generatedDiff.value = ''
}

async function ensureFix() {
  if (fixPatched.value || !selectedIssue.value || !explainData.value) return
  fixLoading.value = true
  try {
    // Build a richer patch request asking for full before/after code blocks
    const { data } = await axios.post('/api/analyze/explain', {
      file_path: selectedIssue.value.file_path,
      line: selectedIssue.value.line_start,
      severity: selectedIssue.value.severity,
      rule_id: selectedIssue.value.rule_id,
      message: `Generate a complete before/after code patch to fix: ${selectedIssue.value.message}`,
      code_context: selectedIssue.value.llm_explanation || selectedIssue.value.message,
      language: report.data?.language || 'unknown',
      cwe_id: selectedIssue.value.cwe_id,
      owasp_category: selectedIssue.value.owasp_category,
    })
    // Parse fix field — split on --- / +++ markers or treat as fixed snippet
    const rawFix: string = data.fix || explainData.value?.fix || ''
    fixedLines.value = rawFix.split('\n')
    fixNotes.value = data.why || explainData.value?.why || ''
    // Use stored diff if available
    if (selectedIssue.value.fix_diff) {
      generatedDiff.value = selectedIssue.value.fix_diff
    }
    fixPatched.value = true
  } catch {
    // Fallback to already-fetched fix
    const raw = explainData.value?.fix || ''
    fixedLines.value = raw.split('\n')
    fixNotes.value   = explainData.value?.why || ''
    fixPatched.value = true
  } finally {
    fixLoading.value = false
  }
}

function parseUserCode() {
  vulnerableLines.value = userCodeInput.value.split('\n')
  // Auto-generate a simple diff when user pastes code
  if (fixedLines.value.length && vulnerableLines.value.length) {
    const orig = vulnerableLines.value.map(l => '- ' + l).join('\n')
    const fixed = fixedLines.value.map(l => '+ ' + l).join('\n')
    generatedDiff.value = `--- a/${selectedIssue.value?.file_path || 'file'}\n+++ b/${selectedIssue.value?.file_path || 'file'}\n@@ -${selectedIssue.value?.line_start || 1} @@\n${orig}\n${fixed}`
  }
}

async function copyFix() {
  const text = fixedLines.value.join('\n')
  await navigator.clipboard.writeText(text).catch(() => {})
  copied.value = true
  setTimeout(() => copied.value = false, 2000)
}

function sendFixToChat() {
  const fix = fixedLines.value.join('\n')
  const q = `Here is the AI-suggested fix for ${selectedIssue.value?.rule_id} in ${selectedIssue.value?.file_path}:\n\`\`\`\n${fix}\n\`\`\`\nIs this fix correct and complete? Are there any edge cases I should handle?`
  input.value = q
  // scroll to input
}

async function acceptFix() {
  if (!selectedIssue.value) return
  try {
    await axios.post(`/api/fixes/${selectedIssue.value.id}/accept`, { accepted: true })
    selectedIssue.value.fix_accepted = 1
  } catch {}
}

function clearChat() {
  messages.value = []
}

async function send() {
  if (!input.value.trim() || !scan.jobId) return
  await sendQuestion(input.value.trim())
  input.value = ''
}

async function sendQuestion(q: string) {
  if (!scan.jobId) return
  messages.value.push({ role: 'user', content: q })
  input.value = ''
  loading.value = true
  await scrollToBottom()
  try {
    const { data } = await axios.post(`/api/chat/${scan.jobId}`, { message: q })
    messages.value.push({ role: 'assistant', content: data.response })
  } catch (e: any) {
    messages.value.push({ role: 'assistant', content: 'Error: ' + (e.response?.data?.detail || e.message || 'unknown') })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

function escHtml(s: string) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function renderDiff(diff: string): string {
  const lines = diff.split('\n').map(line => {
    if (line.startsWith('+++') || line.startsWith('---'))
      return `<div class="diff-hdr">${escHtml(line)}</div>`
    if (line.startsWith('+'))
      return `<div class="diff-add">${escHtml(line)}</div>`
    if (line.startsWith('-'))
      return `<div class="diff-del">${escHtml(line)}</div>`
    if (line.startsWith('@@'))
      return `<div class="diff-range">${escHtml(line)}</div>`
    return `<div class="diff-ctx">${escHtml(line)}</div>`
  })
  return `<div class="diff-block">${lines.join('')}</div>`
}
</script>

<style scoped>
.ai-root {
  display: flex;
  height: calc(100vh - 64px - 48px);
  background: var(--gc-bg);
  overflow: hidden;
}

/* Empty state */
.ai-empty {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 10px;
}
.ai-empty-icon { font-size: 40px; }
.ai-empty-title { font-size: 15px; color: var(--gc-text); font-weight: 600; }
.ai-empty-sub { font-size: 12px; color: var(--gc-text-3); }

/* Sidebar */
.ai-sidebar {
  width: 280px; flex-shrink: 0;
  display: flex; flex-direction: column;
  border-right: 1px solid var(--gc-border);
  background: var(--gc-surface);
  overflow: hidden;
}
.ai-sidebar-hdr {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 14px; border-bottom: 1px solid var(--gc-border);
}
.ai-sidebar-title {
  font-size: 10px; font-weight: 700; letter-spacing: 0.1em; color: var(--gc-text-2);
}
.ai-badge-count {
  font-size: 10px; background: var(--gc-primary-light);
  color: var(--gc-primary); padding: 1px 6px; border-radius: 8px; font-weight: 600;
}
.ai-filter-row {
  display: flex; gap: 2px; padding: 6px 10px;
  border-bottom: 1px solid var(--gc-border);
}
.ai-filter-btn {
  flex: 1; padding: 3px 0; font-size: 10px; font-weight: 600;
  text-transform: capitalize; border-radius: 4px;
  background: transparent; color: var(--gc-text-3);
  border: 1px solid transparent; cursor: pointer;
  transition: all 0.15s;
}
.ai-filter-btn.active {
  background: var(--gc-primary-light); color: var(--gc-primary);
  border-color: var(--gc-primary-light);
}
.ai-issue-list { flex: 1; overflow-y: auto; padding: 6px; display: flex; flex-direction: column; gap: 4px; }
.ai-issue-item {
  padding: 8px 10px; border-radius: 6px; cursor: pointer;
  border: 1px solid var(--gc-border); background: var(--gc-surface-2);
  transition: all 0.15s;
}
.ai-issue-item:hover { border-color: var(--gc-primary); background: var(--gc-primary-light); }
.ai-issue-item.selected { border-color: var(--gc-primary); background: var(--gc-primary-light); }
.ai-issue-top { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.ai-issue-rule { font-size: 10px; color: var(--gc-text-3); font-family: 'JetBrains Mono', monospace; }
.ai-issue-msg { font-size: 11px; color: var(--gc-text); line-height: 1.4; margin-bottom: 3px; }
.ai-issue-file { font-size: 10px; color: var(--gc-text-3); font-family: 'JetBrains Mono', monospace; }
.ai-no-issues { text-align: center; padding: 20px; font-size: 12px; color: var(--gc-text-3); }

/* Severity chips */
.sev-chip {
  display: inline-flex; align-items: center;
  font-size: 9px; font-weight: 700; text-transform: uppercase;
  padding: 2px 6px; border-radius: 3px;
}
.sev-critical { background: rgba(239,68,68,.15); color: #ef4444; }
.sev-major    { background: rgba(249,115,22,.15); color: #f97316; }
.sev-minor    { background: rgba(234,179,8,.15);  color: #eab308; }
.sev-info     { background: rgba(96,165,250,.15); color: #60a5fa; }

/* Divider */
.ai-divider { width: 1px; background: var(--gc-border); flex-shrink: 0; }

/* Main panel */
.ai-main {
  flex: 1; display: flex; flex-direction: column; overflow: hidden;
}

/* Explain card */
.ai-explain-card {
  border-bottom: 1px solid var(--gc-border);
  background: var(--gc-surface);
  max-height: 340px; overflow-y: auto;
  flex-shrink: 0;
}
.ai-explain-hdr {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 16px; border-bottom: 1px solid var(--gc-border);
  background: var(--gc-surface-2); position: sticky; top: 0; z-index: 1;
}
.ai-explain-rule { font-size: 11px; color: var(--gc-primary); font-family: monospace; font-weight: 600; }
.ai-explain-path { font-size: 10px; color: var(--gc-text-3); font-family: monospace; flex: 1; }
.ai-close-btn {
  margin-left: auto; background: none; border: none;
  color: var(--gc-text-3); cursor: pointer; font-size: 14px; padding: 2px 6px;
}
.ai-close-btn:hover { color: var(--gc-text); }
.ai-explain-loading {
  display: flex; align-items: center; gap: 8px; padding: 16px;
  font-size: 12px; color: var(--gc-text-3);
}
.spin-dot {
  display: inline-block; width: 8px; height: 8px; border-radius: 50%;
  background: var(--gc-primary); animation: pulse 0.8s infinite;
}
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }
.ai-explain-body { padding: 12px 16px; display: flex; flex-direction: column; gap: 10px; }
.ai-explain-section {}
.ai-explain-label {
  font-size: 9px; font-weight: 700; letter-spacing: 0.1em;
  color: var(--gc-text-3); margin-bottom: 4px;
}
.ai-explain-text { font-size: 12px; color: var(--gc-text); line-height: 1.5; }
.ai-explain-code {
  font-family: 'JetBrains Mono', monospace; font-size: 11px;
  background: var(--gc-surface-2); border: 1px solid var(--gc-border);
  border-radius: 4px; padding: 8px 12px; color: #3ecf8e;
  white-space: pre-wrap; word-break: break-word; margin: 0;
}
.ai-explain-diff { padding: 0 16px 12px; }

/* Chat */
.ai-chat-hdr {
  display: flex; align-items: center; gap: 8px; padding: 8px 16px;
  border-bottom: 1px solid var(--gc-border); background: var(--gc-surface); flex-shrink: 0;
}
.ai-chat-title { font-size: 10px; font-weight: 700; letter-spacing: 0.1em; color: var(--gc-text-2); }
.ai-chat-model {
  font-size: 10px; color: var(--gc-primary); background: var(--gc-primary-light);
  padding: 1px 6px; border-radius: 4px;
}
.ai-clear-btn {
  margin-left: auto; font-size: 11px; color: var(--gc-text-3);
  background: none; border: none; cursor: pointer; padding: 2px 8px;
}
.ai-clear-btn:hover { color: var(--gc-text); }

.ai-messages { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 10px; }

.ai-suggestions { padding: 20px; }
.ai-suggest-title { font-size: 13px; color: var(--gc-text-2); margin-bottom: 12px; text-align: center; }
.ai-suggest-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.ai-suggest-btn {
  padding: 8px 12px; font-size: 11px; color: var(--gc-text-2);
  background: var(--gc-surface); border: 1px solid var(--gc-border);
  border-radius: 8px; cursor: pointer; text-align: left; line-height: 1.3;
  transition: all 0.15s;
}
.ai-suggest-btn:hover { border-color: var(--gc-primary); color: var(--gc-primary); }

.ai-msg-row { display: flex; }
.ai-msg-row.user { justify-content: flex-end; }
.ai-msg-row.assistant { justify-content: flex-start; }

.ai-msg-bubble {
  max-width: 75%; padding: 10px 14px; border-radius: 12px;
}
.ai-msg-bubble.user {
  background: var(--gc-primary); color: #fff;
  border-radius: 12px 12px 2px 12px;
}
.ai-msg-bubble.assistant {
  background: var(--gc-surface); border: 1px solid var(--gc-border);
  color: var(--gc-text); border-radius: 2px 12px 12px 12px;
}
.ai-msg-text { white-space: pre-wrap; font-family: inherit; font-size: 13px; line-height: 1.5; margin: 0; }

/* Typing animation */
.ai-typing { display: flex; align-items: center; gap: 4px; padding: 12px 16px; }
.ai-typing span {
  width: 6px; height: 6px; border-radius: 50%; background: var(--gc-text-3);
  animation: bounce 1.2s infinite;
}
.ai-typing span:nth-child(2) { animation-delay: 0.2s; }
.ai-typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce { 0%,80%,100% { transform: scale(0.8); opacity: 0.5; } 40% { transform: scale(1.2); opacity: 1; } }

.ai-quick-row {
  display: flex; gap: 6px; flex-wrap: wrap; padding: 6px 16px;
  border-top: 1px solid var(--gc-border);
}
.ai-quick-btn {
  padding: 4px 10px; font-size: 11px; color: var(--gc-text-3);
  background: var(--gc-surface); border: 1px solid var(--gc-border);
  border-radius: 12px; cursor: pointer; transition: all 0.15s;
}
.ai-quick-btn:hover { border-color: var(--gc-primary); color: var(--gc-primary); }

.ai-input-row {
  display: flex; gap: 8px; padding: 10px 16px;
  border-top: 1px solid var(--gc-border); background: var(--gc-surface);
  flex-shrink: 0;
}
.ai-textarea {
  flex: 1; padding: 10px 14px; resize: none;
  background: var(--gc-surface-2); border: 1px solid var(--gc-border);
  border-radius: 10px; color: var(--gc-text); font-size: 13px; line-height: 1.4;
  font-family: inherit;
}
.ai-textarea:focus { outline: none; border-color: var(--gc-primary); }
.ai-send-btn {
  padding: 0 16px; border-radius: 10px;
  background: var(--gc-primary); color: #fff; border: none; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: opacity 0.15s;
}
.ai-send-btn:disabled { opacity: 0.4; cursor: default; }
.ai-send-btn:not(:disabled):hover { opacity: 0.85; }

/* Explain tab switcher */
.ai-explain-tabs {
  display: flex; gap: 2px; margin-left: 8px;
  background: var(--gc-surface-2); border: 1px solid var(--gc-border);
  border-radius: 6px; padding: 2px;
}
.ai-etab {
  padding: 3px 10px; font-size: 10px; font-weight: 600; border-radius: 4px;
  border: none; cursor: pointer; background: transparent; color: var(--gc-text-3);
  transition: all .15s; position: relative;
}
.ai-etab.active { background: var(--gc-primary); color: #fff; }
.ai-etab:not(.active):hover { color: var(--gc-text); }
.ai-etab-dot {
  position: absolute; top: 3px; right: 4px;
  width: 5px; height: 5px; border-radius: 50%; background: #3ecf8e;
}

.ai-refs { display: flex; flex-wrap: wrap; gap: 5px; }

/* Code Fix panel */
.ai-codefix-panel { display: flex; flex-direction: column; min-height: 0; }
.ai-codefix-body  { display: flex; flex-direction: column; gap: 0; }

.ai-codefix-toolbar {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 14px; border-bottom: 1px solid var(--gc-border);
  background: var(--gc-surface-2); flex-shrink: 0; flex-wrap: wrap;
}
.ai-codefix-toggle {
  display: flex; background: var(--gc-surface); border: 1px solid var(--gc-border);
  border-radius: 6px; overflow: hidden;
}
.ai-toggle-btn {
  padding: 4px 12px; font-size: 11px; font-weight: 500; border: none; cursor: pointer;
  background: transparent; color: var(--gc-text-3); transition: all .15s;
}
.ai-toggle-btn.active { background: var(--gc-primary); color: #fff; }
.ai-toggle-btn:not(.active):hover { background: var(--gc-surface-2); color: var(--gc-text); }

.ai-codefix-split {
  display: grid; grid-template-columns: 1fr 1fr;
  border-bottom: 1px solid var(--gc-border);
}
.ai-codefix-pane { display: flex; flex-direction: column; overflow: hidden; }
.ai-codefix-pane:first-child { border-right: 1px solid var(--gc-border); }
.ai-codefix-pane-hdr {
  display: flex; justify-content: space-between; align-items: center;
  padding: 5px 10px; font-size: 10px; font-weight: 700; letter-spacing: .05em;
  flex-shrink: 0;
}
.ai-pane-bad  { background: rgba(239,68,68,.08); color: #ef4444; border-bottom: 1px solid rgba(239,68,68,.2); }
.ai-pane-good { background: rgba(62,207,142,.08); color: #3ecf8e; border-bottom: 1px solid rgba(62,207,142,.2); }
.ai-pane-file { font-family: var(--font-mono); font-size: 9px; color: var(--gc-text-3); font-weight: 400; }

.ai-code-editor {
  font-family: 'JetBrains Mono', 'Fira Mono', monospace; font-size: 11px;
  background: #0d1117; overflow: auto; max-height: 180px;
  line-height: 1.6;
}
.ai-fixed-only { padding: 4px 0; max-height: 200px; }
.ai-code-line {
  display: flex; align-items: flex-start; padding: 0 4px;
  transition: background .1s;
}
.ai-code-line:hover { background: rgba(255,255,255,.04); }
.ai-code-line-hl  { background: rgba(239,68,68,.12) !important; }
.ai-code-line-fix { background: rgba(62,207,142,.05); }
.ai-lineno {
  min-width: 32px; color: #3d4451; font-size: 10px; padding-right: 8px;
  user-select: none; text-align: right; flex-shrink: 0; padding-top: 1px;
}
.ai-linetext { color: #e6edf3; white-space: pre; }
.ai-code-placeholder {
  padding: 16px; font-size: 11px; color: var(--gc-text-3); font-style: italic; text-align: center;
}
.ai-code-paste {
  resize: none; font-size: 11px; font-family: 'JetBrains Mono', monospace;
  background: #0a0d12; border: none; border-top: 1px solid var(--gc-border);
  color: var(--gc-text-2); padding: 6px 10px; outline: none; width: 100%;
}
.ai-code-paste::placeholder { color: var(--gc-text-3); }

.ai-codefix-diff-wrap { max-height: 240px; overflow: auto; }
.ai-diff-inner { font-size: 11px; }

.ai-fix-notes {
  padding: 10px 14px; border-top: 1px solid var(--gc-border);
  background: var(--gc-surface-2);
}

/* Diff */
:deep(.diff-block) { background: #0a0e1a; border: 1px solid #1e2d47; border-radius: 4px; overflow-x: auto; }
:deep(.diff-add)   { color: #3ecf8e; background: rgba(62,207,142,.06); padding: 1px 8px; font-family: monospace; font-size: 11px; }
:deep(.diff-del)   { color: #f25555; background: rgba(242,85,85,.06);  padding: 1px 8px; font-family: monospace; font-size: 11px; }
:deep(.diff-hdr)   { color: #8a96b0; background: #0f1526; padding: 1px 8px; font-family: monospace; font-size: 11px; }
:deep(.diff-range) { color: #4a9ff5; padding: 1px 8px; font-family: monospace; font-size: 11px; }
:deep(.diff-ctx)   { color: #dde3ef; padding: 1px 8px; font-family: monospace; font-size: 11px; }

/* Slide transition */
.slide-down-enter-active, .slide-down-leave-active { transition: max-height 0.3s ease, opacity 0.3s ease; }
.slide-down-enter-from, .slide-down-leave-to { max-height: 0; opacity: 0; overflow: hidden; }
.slide-down-enter-to, .slide-down-leave-from { max-height: 340px; opacity: 1; }
</style>
