<template>
  <div class="space-y-4">
    <div class="ft-card-title" style="font-size:11px;letter-spacing:0.12em">DIRECT CODE ANALYSIS</div>

    <div class="ft-card">
      <div class="ft-card-header">
        <span class="ft-card-title">Code Input</span>
      </div>
      <div class="ft-card-body space-y-3">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-2">
          <div>
            <label class="ft-card-title block mb-1">Language</label>
            <select v-model="language" class="ft-input ft-select">
              <option value="auto">Auto-detect</option>
              <option value="python">Python</option>
              <option value="javascript">JavaScript</option>
              <option value="typescript">TypeScript</option>
              <option value="java">Java</option>
              <option value="go">Go</option>
              <option value="ruby">Ruby</option>
            </select>
          </div>
          <div>
            <label class="ft-card-title block mb-1">Mode</label>
            <select v-model="mode" class="ft-input ft-select">
              <option value="full">Full Analysis</option>
              <option value="security">Security</option>
              <option value="quality">Quality</option>
              <option value="improve">Improvements</option>
            </select>
          </div>
          <div>
            <label class="ft-card-title block mb-1">Filename (optional)</label>
            <input v-model="filename" placeholder="e.g. main.py" class="ft-input" />
          </div>
        </div>

        <div>
          <label class="ft-card-title block mb-1">Code</label>
          <textarea
            v-model="code"
            class="ft-input ft-textarea"
            style="min-height:200px;font-family:'JetBrains Mono',monospace;font-size:12px"
            placeholder="Paste your code here..."
          ></textarea>
        </div>

        <div class="flex items-center gap-3">
          <button
            class="ft-btn ft-btn-primary"
            :disabled="loading || !code.trim()"
            @click="analyze"
          >
            <span v-if="loading" class="status-dot status-running" style="margin-right:4px"></span>
            {{ loading ? 'Analyzing...' : 'Analyze' }}
          </button>
          <button v-if="result" class="ft-btn ft-btn-secondary" @click="result = null">Clear Results</button>
          <span v-if="error" class="text-xs" style="color:#f25555">{{ error }}</span>
        </div>
      </div>
    </div>

    <!-- Results -->
    <template v-if="result">
      <!-- Score & metrics -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div class="ft-widget metric-tile">
          <div class="metric-value" :class="'grade-' + result.grade">{{ result.score ?? '—' }}</div>
          <div class="metric-label">Score / 100</div>
          <div class="metric-sub">Grade {{ result.grade }}</div>
        </div>
        <div class="ft-widget metric-tile">
          <div class="metric-value" style="color:#4a9ff5">{{ result.metrics?.loc ?? '—' }}</div>
          <div class="metric-label">Lines of Code</div>
        </div>
        <div class="ft-widget metric-tile">
          <div class="metric-value" style="color:#f25555">{{ result.metrics?.security_issues ?? '—' }}</div>
          <div class="metric-label">Security Issues</div>
        </div>
        <div class="ft-widget metric-tile">
          <div class="metric-value" style="color:#f5a623">{{ result.metrics?.quality_issues ?? '—' }}</div>
          <div class="metric-label">Quality Issues</div>
        </div>
      </div>

      <!-- Summary -->
      <div v-if="result.summary" class="ft-card">
        <div class="ft-card-header"><span class="ft-card-title">Summary</span></div>
        <div class="ft-card-body">
          <p class="text-sm leading-relaxed" style="color:#dde3ef">{{ result.summary }}</p>
        </div>
      </div>

      <!-- Static tools -->
      <div v-if="toolsRun.length" class="ft-card">
        <div class="ft-card-header"><span class="ft-card-title">Static Analysis Tools</span></div>
        <div class="ft-card-body">
          <div class="flex flex-wrap gap-2">
            <span v-for="t in toolsRun" :key="t" class="ft-tag" style="color:#3ecf8e">{{ t }}</span>
          </div>
        </div>
      </div>

      <!-- Findings table -->
      <div v-if="result.findings && result.findings.length" class="ft-card">
        <div class="ft-card-header">
          <span class="ft-card-title">Findings</span>
          <span class="ft-tag">{{ result.findings.length }}</span>
        </div>
        <div style="overflow-x:auto">
          <table class="ft-table">
            <thead>
              <tr>
                <th>Line</th>
                <th>Severity</th>
                <th>Rule</th>
                <th>Message</th>
                <th>Explanation</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="(f, i) in result.findings" :key="i">
                <tr @click="toggleFinding(i)" class="cursor-pointer">
                  <td class="font-mono text-xs" style="color:#8a96b0">{{ f.line ?? '—' }}</td>
                  <td><span class="sev" :class="'sev-' + f.severity">{{ f.severity }}</span></td>
                  <td style="color:#4a9ff5;font-size:11px">{{ f.rule }}</td>
                  <td style="max-width:260px" class="truncate">{{ f.message }}</td>
                  <td style="color:#4a5568;font-size:10px">{{ f.explanation ? '▼ expand' : '' }}</td>
                </tr>
                <tr v-if="expandedFindings.has(i) && f.explanation" style="background:#0f1526">
                  <td colspan="5" class="px-3 py-2 text-sm" style="color:#dde3ef">{{ f.explanation }}</td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Improvements -->
      <div v-if="result.improvements && result.improvements.length" class="ft-card">
        <div class="ft-card-header">
          <span class="ft-card-title">Improvements</span>
          <span class="ft-tag">{{ result.improvements.length }}</span>
        </div>
        <div class="ft-card-body space-y-4">
          <div v-for="(imp, i) in result.improvements" :key="i" class="border-b pb-4 last:border-b-0 last:pb-0" style="border-color:#1e2d47">
            <div class="flex items-start gap-3 mb-2">
              <span class="sev" :class="priorityClass(imp.priority)">{{ imp.priority }}</span>
              <div>
                <div class="font-medium text-sm" style="color:#dde3ef">{{ imp.title }}</div>
                <div class="text-xs mt-1" style="color:#8a96b0">{{ imp.description }}</div>
              </div>
            </div>
            <div v-if="imp.example" class="ft-code text-xs">{{ imp.example }}</div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import axios from 'axios'

const code = ref('')
const language = ref('auto')
const mode = ref('full')
const filename = ref('')
const loading = ref(false)
const error = ref('')
const result = ref<any>(null)
const expandedFindings = ref(new Set<number>())
const toolsRun = computed(() => result.value?.static_tools_run ?? result.value?.tools_run ?? [])

async function analyze() {
  if (!code.value.trim()) return
  loading.value = true
  error.value = ''
  result.value = null
  try {
    const { data } = await axios.post('/api/analyze/code', {
      code: code.value,
      language: language.value,
      mode: mode.value,
      filename: filename.value || null,
    })
    result.value = data
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    loading.value = false
  }
}

function toggleFinding(i: number) {
  const s = new Set(expandedFindings.value)
  s.has(i) ? s.delete(i) : s.add(i)
  expandedFindings.value = s
}

function priorityClass(p: string) {
  const map: Record<string, string> = {
    high: 'sev-critical', medium: 'sev-major', low: 'sev-minor',
    critical: 'sev-critical', info: 'sev-info',
  }
  return map[(p || '').toLowerCase()] ?? 'sev-info'
}
</script>
