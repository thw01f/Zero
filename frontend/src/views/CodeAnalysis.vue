<template>
  <div class="ca-root">
    <!-- Header bar -->
    <div class="ca-header">
      <div class="ca-title">CODE ANALYZER AI</div>
      <div class="ca-controls">
        <select v-model="language" class="ca-select">
          <option value="auto">Auto</option>
          <option value="python">Python</option>
          <option value="javascript">JavaScript</option>
          <option value="typescript">TypeScript</option>
          <option value="java">Java</option>
          <option value="go">Go</option>
          <option value="ruby">Ruby</option>
          <option value="bash">Bash</option>
        </select>
        <select v-model="mode" class="ca-select">
          <option value="full">Full Analysis</option>
          <option value="security">Security Only</option>
          <option value="quality">Quality Only</option>
          <option value="improve">Improvements</option>
        </select>
        <input v-model="filename" class="ca-input" placeholder="filename.py (optional)" style="width:160px" />
        <button class="ca-btn ca-btn-primary" :disabled="loading || !code.trim()" @click="analyze">
          <span v-if="loading" class="ca-spinner"></span>
          {{ loading ? 'Analyzing…' : '⚡ Analyze' }}
        </button>
        <button v-if="result" class="ca-btn ca-btn-ghost" @click="reset">Clear</button>
      </div>
    </div>

    <!-- Split pane -->
    <div class="ca-body">
      <!-- Left: code editor pane -->
      <div class="ca-editor-pane">
        <div class="ca-pane-header">
          <span>Code Input</span>
          <span class="ca-badge" style="color:#8a96b0">{{ lineCount }} lines</span>
        </div>
        <div class="ca-editor-wrap" ref="editorWrap">
          <div class="ca-line-nums" ref="lineNums">
            <div v-for="n in lineCount" :key="n"
              :class="['ca-linenum', highlightedLines.has(n) ? 'ca-linenum-hl ca-linenum-hl-' + lineHlSeverity(n) : '']">
              {{ n }}
            </div>
          </div>
          <textarea
            ref="textarea"
            v-model="code"
            class="ca-textarea"
            spellcheck="false"
            placeholder="Paste or type code here…"
            @scroll="syncScroll"
            @keydown.tab.prevent="insertTab"
          ></textarea>
        </div>
        <div v-if="result" class="ca-error-bar">
          <span v-if="errorText" style="color:#f25555">{{ errorText }}</span>
        </div>
      </div>

      <!-- Right: results pane -->
      <div class="ca-results-pane" :class="{ 'ca-results-empty': !result }">
        <!-- Empty state -->
        <div v-if="!result && !loading" class="ca-empty">
          <div class="ca-empty-icon">🔍</div>
          <div class="ca-empty-title">Ready to analyze</div>
          <div class="ca-empty-sub">Paste code on the left, then click Analyze</div>
          <div class="ca-example-grid">
            <button v-for="ex in examples" :key="ex.label" class="ca-example-btn" @click="loadExample(ex)">
              {{ ex.label }}
            </button>
          </div>
        </div>

        <!-- Loading state -->
        <div v-else-if="loading" class="ca-empty">
          <div class="ca-spin-lg"></div>
          <div class="ca-empty-title" style="margin-top:16px">Analyzing code…</div>
          <div class="ca-empty-sub">Running static analysis + AI review</div>
        </div>

        <!-- Results -->
        <template v-else-if="result">
          <!-- Score header -->
          <div class="ca-score-bar">
            <div class="ca-score-main">
              <div class="ca-grade" :class="'ca-grade-' + result.grade">{{ result.grade }}</div>
              <div>
                <div class="ca-score-num">{{ result.score ?? '—' }}<span class="ca-score-denom">/100</span></div>
                <div class="ca-score-label">Security Score</div>
              </div>
            </div>
            <div class="ca-metrics-row">
              <div class="ca-metric-chip" v-for="(val, key) in metricsList" :key="key">
                <span :style="{ color: metricColor(key) }">{{ val }}</span>
                <span>{{ key }}</span>
              </div>
              <div v-if="toolsRun.length" class="ca-tools-row">
                <span v-for="t in toolsRun" :key="t" class="ca-tool-tag">{{ t }}</span>
              </div>
            </div>
          </div>

          <!-- Severity filter tabs -->
          <div class="ca-sev-tabs">
            <button v-for="s in sevTabs" :key="s.key"
              class="ca-sev-tab"
              :class="{ 'ca-sev-tab-active': activeSev === s.key }"
              :style="{ '--tc': s.color }"
              @click="activeSev = s.key"
            >
              <span class="ca-sev-dot" :style="{ background: s.color }"></span>
              {{ s.label }}
              <span class="ca-sev-count">{{ countFor(s.key) }}</span>
            </button>
          </div>

          <!-- Findings list -->
          <div class="ca-findings-list" v-if="filteredFindings.length">
            <div
              v-for="(f, i) in filteredFindings"
              :key="i"
              class="ca-finding-card"
              :class="{ 'ca-finding-expanded': expanded === i }"
              @click="toggleExpand(i, f)"
            >
              <div class="ca-finding-header">
                <span class="ca-sev-badge" :class="'ca-sev-' + f.severity">{{ f.severity }}</span>
                <span class="ca-rule-id">{{ f.rule }}</span>
                <span class="ca-finding-msg">{{ f.message }}</span>
                <span class="ca-line-chip" @click.stop="jumpToLine(f.line)">L{{ f.line }}</span>
                <span class="ca-expand-icon">{{ expanded === i ? '▲' : '▼' }}</span>
              </div>

              <!-- Expanded detail -->
              <div v-if="expanded === i" class="ca-finding-detail">
                <div v-if="f.explanation || loadingExplain === i" class="ca-explain-box">
                  <div class="ca-explain-label">AI Explanation</div>
                  <div v-if="loadingExplain === i" class="ca-explain-loading">
                    <span class="ca-spin-sm"></span> Generating explanation…
                  </div>
                  <p v-else class="ca-explain-text">{{ f.explanation }}</p>
                </div>

                <!-- Code context snippet -->
                <div v-if="f.line" class="ca-code-ctx">
                  <div class="ca-ctx-label">Code Context</div>
                  <div class="ca-ctx-lines">
                    <div v-for="(cl, ci) in contextLines(f.line)" :key="ci"
                      :class="['ca-ctx-line', cl.highlight ? 'ca-ctx-line-hl' : '']">
                      <span class="ca-ctx-ln">{{ cl.num }}</span>
                      <span class="ca-ctx-code">{{ cl.text }}</span>
                    </div>
                  </div>
                </div>

                <!-- Fix suggestion -->
                <div v-if="f.fix" class="ca-fix-box">
                  <div class="ca-fix-label">Suggested Fix</div>
                  <div class="ca-fix-diff" v-html="renderDiff(f.fix)"></div>
                </div>

                <div class="ca-finding-actions">
                  <button v-if="!f.explanation && loadingExplain !== i"
                    class="ca-btn ca-btn-sm" @click.stop="explainFinding(i, f)">
                    🤖 Explain
                  </button>
                  <span v-if="f.cwe" class="ca-meta-chip">CWE-{{ f.cwe }}</span>
                  <span v-if="f.owasp" class="ca-meta-chip">{{ f.owasp }}</span>
                  <span class="ca-meta-chip" style="color:#8a96b0">{{ f.tool }}</span>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="ca-no-findings">
            <span style="color:#3ecf8e">✓</span> No {{ activeSev === 'all' ? '' : activeSev + ' ' }}findings
          </div>

          <!-- Summary -->
          <div v-if="result.summary" class="ca-summary-box">
            <div class="ca-summary-label">AI Summary</div>
            <p class="ca-summary-text">{{ result.summary }}</p>
          </div>

          <!-- Improvements -->
          <div v-if="improvements.length" class="ca-improvements">
            <div class="ca-improve-label">Improvement Suggestions</div>
            <div v-for="(imp, i) in improvements" :key="i" class="ca-improve-item">
              <span class="ca-sev-badge" :class="'ca-sev-' + priorityClass(imp.priority)">{{ imp.priority }}</span>
              <div>
                <div class="ca-improve-title">{{ imp.title }}</div>
                <div class="ca-improve-desc">{{ imp.description }}</div>
                <pre v-if="imp.example" class="ca-code-block">{{ imp.example }}</pre>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import axios from 'axios'

const code     = ref('')
const language = ref('auto')
const mode     = ref('full')
const filename = ref('')
const loading  = ref(false)
const errorText = ref('')
const result   = ref<any>(null)
const expanded = ref<number | null>(null)
const activeSev = ref('all')
const loadingExplain = ref<number | null>(null)
const textarea = ref<HTMLTextAreaElement | null>(null)
const lineNums = ref<HTMLElement | null>(null)

const SEV_COLORS: Record<string, string> = {
  critical: '#f25555', major: '#f26d21', minor: '#f5a623', info: '#4a9ff5',
}

// ── Example snippets ──────────────────────────────────────────────────────────
const examples = [
  {
    label: 'SQL Injection',
    language: 'python',
    code: `import sqlite3\n\ndef get_user(username):\n    conn = sqlite3.connect("users.db")\n    cursor = conn.cursor()\n    query = "SELECT * FROM users WHERE username = '" + username + "'"\n    cursor.execute(query)\n    return cursor.fetchone()\n\ndef login(request):\n    user = get_user(request.form['username'])\n    if user and user['password'] == request.form['password']:\n        return "Welcome " + user['name']\n    return "Invalid credentials"`,
  },
  {
    label: 'XSS Vuln',
    language: 'javascript',
    code: `function renderComment(userInput) {\n  document.getElementById('comments').innerHTML = userInput;\n}\n\nfunction loadPage() {\n  const url = new URL(window.location);\n  const name = url.searchParams.get('name');\n  document.title = "Hello " + name;\n  renderComment(localStorage.getItem('comment'));\n}`,
  },
  {
    label: 'Hardcoded Secrets',
    language: 'python',
    code: `import requests\n\nAPI_KEY = "sk-1234567890abcdef"\nDB_PASSWORD = "admin123"\nSECRET_TOKEN = "ghp_xxxxxxxxxxxx"\n\ndef call_api(endpoint):\n    headers = {"Authorization": f"Bearer {API_KEY}"}\n    return requests.get(endpoint, headers=headers)\n\ndef connect_db():\n    return f"postgresql://admin:{DB_PASSWORD}@localhost/prod"`,
  },
  {
    label: 'Path Traversal',
    language: 'python',
    code: `import os\nfrom flask import Flask, request, send_file\n\napp = Flask(__name__)\n\n@app.route('/download')\ndef download():\n    filename = request.args.get('file')\n    filepath = os.path.join('/var/www/files', filename)\n    return send_file(filepath)\n\n@app.route('/read')\ndef read_file():\n    path = request.args.get('path')\n    with open(path) as f:\n        return f.read()`,
  },
]

function loadExample(ex: any) {
  code.value = ex.code
  language.value = ex.language
  filename.value = `example.${ex.language === 'python' ? 'py' : 'js'}`
}

// ── Analysis ──────────────────────────────────────────────────────────────────
async function analyze() {
  if (!code.value.trim()) return
  loading.value = true
  errorText.value = ''
  result.value = null
  expanded.value = null
  activeSev.value = 'all'
  try {
    const { data } = await axios.post('/api/analyze/code', {
      code: code.value,
      language: language.value === 'auto' ? detectLanguage() : language.value,
      mode: mode.value,
      filename: filename.value || null,
    })
    // Merge static findings with LLM findings
    result.value = {
      ...data,
      findings: mergeFindingsByLine(data.findings || []),
    }
  } catch (e: any) {
    errorText.value = e.response?.data?.detail || e.message
  } finally {
    loading.value = false
  }
}

function detectLanguage(): string {
  if (filename.value) {
    const ext = filename.value.split('.').pop()?.toLowerCase()
    const map: Record<string, string> = { py: 'python', js: 'javascript', ts: 'typescript', java: 'java', go: 'go', rb: 'ruby', sh: 'bash' }
    if (ext && map[ext]) return map[ext]
  }
  // Simple heuristic
  if (code.value.includes('def ') || code.value.includes('import ') && code.value.includes(':')) return 'python'
  if (code.value.includes('function ') || code.value.includes('=>') || code.value.includes('const ')) return 'javascript'
  return 'python'
}

function mergeFindingsByLine(findings: any[]): any[] {
  // Deduplicate by rule+line
  const seen = new Set<string>()
  return findings.filter(f => {
    const key = `${f.rule}:${f.line}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  }).sort((a, b) => {
    const sevO: Record<string, number> = { critical: 0, major: 1, minor: 2, info: 3 }
    return (sevO[a.severity] ?? 4) - (sevO[b.severity] ?? 4)
  })
}

function reset() {
  result.value = null
  code.value = ''
  errorText.value = ''
}

// ── Per-finding AI explain ────────────────────────────────────────────────────
async function explainFinding(idx: number, f: any) {
  loadingExplain.value = idx
  try {
    const { data } = await axios.post('/api/analyze/explain', {
      code: code.value,
      finding: { rule: f.rule, line: f.line, message: f.message, severity: f.severity },
      language: language.value,
    })
    f.explanation = data.explanation
    f.fix = data.fix || f.fix
  } catch {
    f.explanation = `This ${f.severity} issue (${f.rule}) at line ${f.line} indicates: ${f.message}. Review the code at this location and apply the relevant security pattern.`
  } finally {
    loadingExplain.value = null
  }
}

// ── UI helpers ────────────────────────────────────────────────────────────────
const lineCount = computed(() => (code.value.match(/\n/g) || []).length + 1)

const highlightedLines = computed(() => {
  const s = new Set<number>()
  if (!result.value?.findings) return s
  for (const f of result.value.findings) {
    if (f.line) s.add(f.line)
  }
  return s
})

function lineHlSeverity(n: number): string {
  if (!result.value?.findings) return ''
  const f = result.value.findings.find((f: any) => f.line === n)
  return f?.severity ?? ''
}

function syncScroll() {
  if (textarea.value && lineNums.value) {
    lineNums.value.scrollTop = textarea.value.scrollTop
  }
}

function insertTab(e: KeyboardEvent) {
  const el = e.target as HTMLTextAreaElement
  const start = el.selectionStart
  const end   = el.selectionEnd
  code.value  = code.value.slice(0, start) + '  ' + code.value.slice(end)
  nextTick(() => { el.selectionStart = el.selectionEnd = start + 2 })
}

function jumpToLine(line: number) {
  if (!textarea.value || !line) return
  const lines = code.value.split('\n')
  const pos = lines.slice(0, line - 1).reduce((a, l) => a + l.length + 1, 0)
  textarea.value.focus()
  textarea.value.selectionStart = textarea.value.selectionEnd = pos
  const lineH = textarea.value.scrollHeight / lineCount.value
  textarea.value.scrollTop = (line - 3) * lineH
}

function contextLines(lineNum: number) {
  const lines = code.value.split('\n')
  const start = Math.max(0, lineNum - 3)
  const end   = Math.min(lines.length, lineNum + 2)
  return lines.slice(start, end).map((text, i) => ({
    num: start + i + 1,
    text,
    highlight: start + i + 1 === lineNum,
  }))
}

function toggleExpand(i: number, f: any) {
  expanded.value = expanded.value === i ? null : i
}

const sevTabs = [
  { key: 'all',      label: 'All',      color: '#8a96b0' },
  { key: 'critical', label: 'Critical', color: '#f25555' },
  { key: 'major',    label: 'Major',    color: '#f26d21' },
  { key: 'minor',    label: 'Minor',    color: '#f5a623' },
  { key: 'info',     label: 'Info',     color: '#4a9ff5' },
]

const filteredFindings = computed(() => {
  if (!result.value?.findings) return []
  return activeSev.value === 'all'
    ? result.value.findings
    : result.value.findings.filter((f: any) => f.severity === activeSev.value)
})

function countFor(key: string) {
  if (!result.value?.findings) return 0
  return key === 'all'
    ? result.value.findings.length
    : result.value.findings.filter((f: any) => f.severity === key).length
}

const toolsRun = computed(() => result.value?.static_tools_run ?? result.value?.tools_run ?? [])
const improvements = computed(() => result.value?.improvements ?? [])

const metricsList = computed(() => {
  const m = result.value?.metrics ?? {}
  const out: Record<string, any> = {}
  if (m.loc        != null) out['LOC']     = m.loc
  if (m.security_issues != null) out['Security'] = m.security_issues
  if (m.quality_issues  != null) out['Quality']  = m.quality_issues
  return out
})

function metricColor(key: string) {
  if (key === 'Security') return '#f25555'
  if (key === 'Quality')  return '#f26d21'
  return '#4a9ff5'
}

function priorityClass(p: string): string {
  return { high: 'critical', medium: 'major', low: 'minor', critical: 'critical' }[p?.toLowerCase()] ?? 'info'
}

function renderDiff(diff: string): string {
  if (!diff) return ''
  return diff.split('\n').map(line => {
    const esc = line.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    if (line.startsWith('+++') || line.startsWith('---'))
      return `<div class="df-hdr">${esc}</div>`
    if (line.startsWith('+'))
      return `<div class="df-add">${esc}</div>`
    if (line.startsWith('-'))
      return `<div class="df-del">${esc}</div>`
    if (line.startsWith('@@'))
      return `<div class="df-info">${esc}</div>`
    return `<div class="df-ctx">${esc}</div>`
  }).join('')
}
</script>

<style scoped>
.ca-root { display: flex; flex-direction: column; height: calc(100vh - 56px); background: var(--gc-bg); overflow: hidden; }

/* Header */
.ca-header {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  padding: 8px 12px; border-bottom: 1px solid var(--gc-border);
  background: var(--gc-surface); flex-shrink: 0;
}
.ca-title { font-size: 11px; font-weight: 700; letter-spacing: .1em; color: var(--gc-primary); white-space: nowrap; }
.ca-controls { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-left: auto; }
.ca-select {
  background: var(--gc-surface-2); border: 1px solid var(--gc-border);
  color: var(--gc-text-2); border-radius: 5px; padding: 5px 8px; font-size: 12px;
}
.ca-input {
  background: var(--gc-surface-2); border: 1px solid var(--gc-border);
  color: var(--gc-text-2); border-radius: 5px; padding: 5px 8px; font-size: 12px;
}
.ca-btn {
  padding: 6px 14px; border-radius: 5px; font-size: 12px; font-weight: 600;
  cursor: pointer; border: none; display: flex; align-items: center; gap: 5px;
  transition: opacity .15s;
}
.ca-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.ca-btn-primary { background: var(--gc-primary); color: #fff; }
.ca-btn-primary:hover:not(:disabled) { opacity: 0.88; }
.ca-btn-ghost { background: var(--gc-surface-2); color: var(--gc-text-2); border: 1px solid var(--gc-border); }
.ca-btn-sm { padding: 3px 9px; font-size: 11px; background: var(--gc-surface-2); color: var(--gc-text-2); border: 1px solid var(--gc-border); border-radius: 4px; cursor: pointer; }
.ca-spinner { width:12px; height:12px; border:2px solid rgba(255,255,255,.3); border-top-color:#fff; border-radius:50%; animation:spin .7s linear infinite; }

/* Body */
.ca-body { flex: 1; display: grid; grid-template-columns: 1fr 1fr; overflow: hidden; }

/* Editor pane */
.ca-editor-pane { display: flex; flex-direction: column; border-right: 1px solid var(--gc-border); overflow: hidden; }
.ca-pane-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 6px 10px; background: var(--gc-surface-2); border-bottom: 1px solid var(--gc-border);
  font-size: 11px; font-weight: 600; color: var(--gc-text-3); flex-shrink: 0;
}
.ca-badge { font-size: 10px; }
.ca-editor-wrap { flex: 1; display: flex; overflow: hidden; }
.ca-line-nums {
  width: 40px; flex-shrink: 0; overflow: hidden; padding: 8px 0;
  background: var(--gc-surface-2); border-right: 1px solid var(--gc-border);
}
.ca-linenum {
  height: 18px; line-height: 18px; text-align: right; padding-right: 8px;
  font-size: 11px; font-family: 'JetBrains Mono', monospace;
  color: var(--gc-text-3); white-space: nowrap;
}
.ca-linenum-hl { font-weight: 700; border-right: 2px solid; }
.ca-linenum-hl-critical { color: #f25555; border-color: #f25555; background: rgba(242,85,85,.1); }
.ca-linenum-hl-major    { color: #f26d21; border-color: #f26d21; background: rgba(242,109,33,.1); }
.ca-linenum-hl-minor    { color: #f5a623; border-color: #f5a623; background: rgba(245,166,35,.08); }
.ca-linenum-hl-info     { color: #4a9ff5; border-color: #4a9ff5; background: rgba(74,159,245,.07); }
.ca-textarea {
  flex: 1; resize: none; border: none; outline: none;
  background: transparent; color: var(--gc-text);
  font-family: 'JetBrains Mono', monospace; font-size: 13px; line-height: 18px;
  padding: 8px 12px; overflow-y: scroll;
}
.ca-error-bar { padding: 4px 10px; font-size: 11px; flex-shrink: 0; min-height: 22px; background: var(--gc-surface-2); border-top: 1px solid var(--gc-border); }

/* Results pane */
.ca-results-pane { display: flex; flex-direction: column; overflow-y: auto; }
.ca-results-empty { align-items: center; justify-content: center; }

.ca-empty { display: flex; flex-direction: column; align-items: center; padding: 48px 24px; gap: 8px; }
.ca-empty-icon { font-size: 42px; }
.ca-empty-title { font-size: 15px; font-weight: 600; color: var(--gc-text); }
.ca-empty-sub { font-size: 12px; color: var(--gc-text-3); }
.ca-example-grid { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; justify-content: center; }
.ca-example-btn {
  padding: 5px 12px; background: var(--gc-surface-2); border: 1px solid var(--gc-border);
  color: var(--gc-primary); border-radius: 20px; font-size: 11px; cursor: pointer;
}
.ca-example-btn:hover { background: var(--gc-primary-light); }

/* Spinner */
.ca-spin-lg { width: 36px; height: 36px; border: 3px solid var(--gc-border); border-top-color: var(--gc-primary); border-radius: 50%; animation: spin .8s linear infinite; }
.ca-spin-sm { width: 12px; height: 12px; border: 2px solid var(--gc-border); border-top-color: var(--gc-primary); border-radius: 50%; animation: spin .7s linear infinite; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Score bar */
.ca-score-bar { padding: 14px; border-bottom: 1px solid var(--gc-border); background: var(--gc-surface); flex-shrink: 0; }
.ca-score-main { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.ca-grade { width: 52px; height: 52px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 26px; font-weight: 800; }
.ca-grade-A { background: rgba(62,207,142,.15); color: #3ecf8e; }
.ca-grade-B { background: rgba(74,159,245,.15); color: #4a9ff5; }
.ca-grade-C { background: rgba(245,166,35,.15); color: #f5a623; }
.ca-grade-D { background: rgba(242,109,33,.15); color: #f26d21; }
.ca-grade-F { background: rgba(242,85,85,.15); color: #f25555; }
.ca-score-num { font-size: 22px; font-weight: 700; color: var(--gc-text); }
.ca-score-denom { font-size: 12px; color: var(--gc-text-3); }
.ca-score-label { font-size: 11px; color: var(--gc-text-3); }
.ca-metrics-row { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.ca-metric-chip { display: flex; flex-direction: column; align-items: center; background: var(--gc-surface-2); border-radius: 6px; padding: 5px 10px; font-size: 11px; color: var(--gc-text-3); }
.ca-metric-chip span:first-child { font-size: 16px; font-weight: 700; }
.ca-tools-row { display: flex; gap: 5px; flex-wrap: wrap; }
.ca-tool-tag { padding: 2px 7px; background: rgba(62,207,142,.1); color: #3ecf8e; border-radius: 10px; font-size: 10px; }

/* Severity tabs */
.ca-sev-tabs { display: flex; gap: 2px; padding: 8px 10px 0; border-bottom: 1px solid var(--gc-border); flex-shrink: 0; }
.ca-sev-tab {
  display: flex; align-items: center; gap: 5px; padding: 5px 10px;
  font-size: 11px; color: var(--gc-text-3); cursor: pointer; border: none; background: none;
  border-bottom: 2px solid transparent; margin-bottom: -1px;
}
.ca-sev-tab:hover { color: var(--gc-text-2); }
.ca-sev-tab-active { color: var(--var, --gc-text); border-color: var(--tc, var(--gc-primary)); }
.ca-sev-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.ca-sev-count { background: var(--gc-surface-2); color: var(--gc-text-3); border-radius: 8px; padding: 0 5px; font-size: 10px; }

/* Findings */
.ca-findings-list { flex: 1; padding: 8px; display: flex; flex-direction: column; gap: 4px; }
.ca-finding-card {
  border: 1px solid var(--gc-border); border-radius: 7px;
  cursor: pointer; overflow: hidden; transition: border-color .15s;
}
.ca-finding-card:hover { border-color: var(--gc-primary); }
.ca-finding-expanded { border-color: var(--gc-primary); }
.ca-finding-header {
  display: flex; align-items: center; gap: 8px; padding: 8px 10px;
  background: var(--gc-surface);
}
.ca-sev-badge {
  padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 700;
  text-transform: uppercase; flex-shrink: 0;
}
.ca-sev-critical { background: rgba(242,85,85,.15); color: #f25555; }
.ca-sev-major    { background: rgba(242,109,33,.15); color: #f26d21; }
.ca-sev-minor    { background: rgba(245,166,35,.12); color: #f5a623; }
.ca-sev-info     { background: rgba(74,159,245,.12); color: #4a9ff5; }
.ca-rule-id { font-size: 11px; font-family: monospace; color: var(--gc-primary); flex-shrink: 0; }
.ca-finding-msg { font-size: 12px; color: var(--gc-text-2); flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ca-line-chip { padding: 1px 6px; background: var(--gc-surface-2); color: var(--gc-text-3); border-radius: 4px; font-size: 10px; font-family: monospace; flex-shrink: 0; cursor: pointer; }
.ca-line-chip:hover { color: var(--gc-primary); }
.ca-expand-icon { font-size: 10px; color: var(--gc-text-3); flex-shrink: 0; }

.ca-finding-detail { padding: 12px; background: var(--gc-bg); border-top: 1px solid var(--gc-border); display: flex; flex-direction: column; gap: 10px; }
.ca-explain-box, .ca-code-ctx, .ca-fix-box { border-radius: 6px; overflow: hidden; }
.ca-explain-label, .ca-ctx-label, .ca-fix-label { font-size: 10px; font-weight: 700; color: var(--gc-text-3); text-transform: uppercase; letter-spacing: .5px; padding: 5px 8px; background: var(--gc-surface-2); border-bottom: 1px solid var(--gc-border); }
.ca-explain-text { font-size: 12px; color: var(--gc-text-2); line-height: 1.6; padding: 8px; margin: 0; }
.ca-explain-loading { padding: 8px; font-size: 11px; color: var(--gc-text-3); display: flex; align-items: center; gap: 6px; }

.ca-ctx-lines { background: var(--gc-surface-2); }
.ca-ctx-line { display: flex; gap: 8px; padding: 1px 8px; font-size: 11px; font-family: monospace; }
.ca-ctx-line-hl { background: rgba(242,85,85,.12); border-left: 2px solid #f25555; }
.ca-ctx-ln { color: var(--gc-text-3); min-width: 28px; text-align: right; user-select: none; }
.ca-ctx-code { color: var(--gc-text); white-space: pre; }

.ca-fix-diff { background: var(--gc-surface-2); padding: 4px; font-family: monospace; font-size: 11px; overflow-x: auto; }
:deep(.df-hdr) { color: var(--gc-text-3); padding: 2px 8px; background: var(--gc-surface); }
:deep(.df-add) { background: rgba(62,207,142,.1); color: #3ecf8e; padding: 2px 8px; }
:deep(.df-del) { background: rgba(242,85,85,.1); color: #f25555; padding: 2px 8px; }
:deep(.df-info){ color: #4a9ff5; padding: 2px 8px; }
:deep(.df-ctx) { color: var(--gc-text-2); padding: 2px 8px; }

.ca-finding-actions { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.ca-meta-chip { padding: 2px 7px; background: var(--gc-surface-2); color: var(--gc-text-3); border-radius: 10px; font-size: 10px; }

.ca-no-findings { padding: 20px; text-align: center; font-size: 13px; color: var(--gc-text-3); }

/* Summary + improvements */
.ca-summary-box { margin: 8px; padding: 12px; background: var(--gc-surface); border-radius: 7px; border: 1px solid var(--gc-border); }
.ca-summary-label { font-size: 10px; font-weight: 700; color: var(--gc-text-3); text-transform: uppercase; letter-spacing: .5px; margin-bottom: 6px; }
.ca-summary-text { font-size: 12px; color: var(--gc-text-2); line-height: 1.6; margin: 0; }

.ca-improvements { padding: 8px; display: flex; flex-direction: column; gap: 6px; }
.ca-improve-label { font-size: 10px; font-weight: 700; color: var(--gc-text-3); text-transform: uppercase; letter-spacing: .5px; margin: 4px 0; }
.ca-improve-item { display: flex; gap: 8px; align-items: flex-start; padding: 8px; background: var(--gc-surface); border-radius: 6px; border: 1px solid var(--gc-border); }
.ca-improve-title { font-size: 12px; font-weight: 600; color: var(--gc-text); }
.ca-improve-desc { font-size: 11px; color: var(--gc-text-3); margin-top: 2px; }
.ca-code-block { background: var(--gc-surface-2); color: var(--gc-text); padding: 6px 8px; border-radius: 4px; font-size: 11px; font-family: monospace; margin-top: 6px; overflow-x: auto; white-space: pre; }
</style>
