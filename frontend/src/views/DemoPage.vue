<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'

const router = useRouter()

const DEMO_STATS = {
  total_issues: 127,
  critical: 8,
  major: 34,
  minor: 51,
  info: 34,
  grade: 'C+',
  debt_score: 6.2,
  scan_time_ms: 18420,
  files_scanned: 94,
  secrets_found: 3,
}

const DEMO_ISSUES = [
  { severity: 'critical', file: 'auth/login.py',       line: 42,  rule: 'CWE-89',  cve: 'N/A',          title: 'SQL Injection via unsanitized user input',          fix: 'Use parameterized queries' },
  { severity: 'critical', file: 'config/settings.py',  line: 17,  rule: 'CWE-798', cve: 'N/A',          title: 'Hardcoded secret key in source code',               fix: 'Move to environment variable' },
  { severity: 'critical', file: 'api/upload.py',       line: 89,  rule: 'CWE-22',  cve: 'CVE-2023-1544', title: 'Path traversal in file upload handler',            fix: 'Sanitize and restrict upload path' },
  { severity: 'major',    file: 'utils/crypto.py',     line: 203, rule: 'CWE-326', cve: 'N/A',          title: 'Weak cryptographic algorithm (MD5)',                fix: 'Replace with SHA-256 or bcrypt' },
  { severity: 'major',    file: 'models/user.py',      line: 58,  rule: 'CWE-732', cve: 'N/A',          title: 'Overly permissive file permissions (0777)',         fix: 'Use 0o640 or stricter' },
  { severity: 'major',    file: 'routes/admin.py',     line: 121, rule: 'CWE-284', cve: 'N/A',          title: 'Missing authorization check on admin endpoint',    fix: 'Add require_admin() dependency' },
  { severity: 'minor',    file: 'templates/index.html',line: 34,  rule: 'CWE-79',  cve: 'N/A',          title: 'Reflected XSS via unescaped URL parameter',        fix: 'HTML-escape all user-controlled output' },
  { severity: 'info',     file: 'requirements.txt',    line: 12,  rule: 'DEP-001', cve: 'CVE-2024-0001', title: 'Outdated dependency: requests==2.28.0',            fix: 'Upgrade to requests>=2.31.0' },
]

const DEMO_MODULES = [
  { path: 'auth/',        grade: 'D', debt: 8.1, issues: 12, loc: 420 },
  { path: 'api/',         grade: 'C', debt: 5.9, issues: 8,  loc: 1240 },
  { path: 'models/',      grade: 'B', debt: 4.2, issues: 5,  loc: 680 },
  { path: 'utils/',       grade: 'C', debt: 6.3, issues: 9,  loc: 290 },
  { path: 'routes/',      grade: 'C+',debt: 5.5, issues: 7,  loc: 890 },
  { path: 'templates/',   grade: 'B+',debt: 3.1, issues: 3,  loc: 320 },
]

const FEATURES = [
  { icon: 'bug',    title: '12 SAST Tools',       desc: 'Bandit, Semgrep, ESLint, Trivy, Checkov, Gitleaks and more run in parallel.' },
  { icon: 'shield', title: 'CVE Scoring',          desc: 'Every finding mapped to CWE/CVE with CVSS scores pulled from NVD in real-time.' },
  { icon: 'code',   title: 'AI Fix Studio',        desc: 'LLM-generated patch diffs for each issue — accept with one click.' },
  { icon: 'graph',  title: 'Code Graph',           desc: 'Obsidian-style dependency graph visualising coupling and risk hotspots.' },
  { icon: 'star',   title: 'Multi-LLM',            desc: 'Ollama local · HuggingFace · Anthropic Claude · Google Gemini — switch at runtime.' },
  { icon: 'upload', title: 'GitHub / Upload',      desc: 'Scan any public repo URL or upload a zip/tar archive directly.' },
]

const severityColor: Record<string, string> = {
  critical: '#d93025', major: '#f29900', minor: '#1a73e8', info: '#5f6368',
}

const gradeColor = (g: string) => {
  if (g.startsWith('A')) return '#1e8e3e'
  if (g.startsWith('B')) return '#1a73e8'
  if (g.startsWith('C')) return '#f29900'
  return '#d93025'
}
</script>

<template>
  <div class="demo-wrap">

    <!-- ── Hero ── -->
    <div class="demo-hero">
      <div class="demo-hero-badge">DEMO · Pre-loaded scan results</div>
      <h1 class="demo-hero-title">DarkLead</h1>
      <p class="demo-hero-sub">AI-powered SAST · Technical Debt Analyzer · Code Intelligence</p>
      <div class="demo-hero-actions">
        <button class="gc-btn gc-btn-primary demo-cta" @click="router.push('/login')">
          <AppIcon name="shield" :size="16" /> Enter Platform
        </button>
        <a href="https://github.com/thw01f/TR-104-DarkLead" target="_blank" class="gc-btn demo-cta-ghost">
          <AppIcon name="code" :size="16" /> View Source
        </a>
      </div>
    </div>

    <!-- ── Stats ribbon ── -->
    <div class="demo-stats">
      <div class="demo-stat">
        <div class="demo-stat-val" :style="{color: gradeColor(DEMO_STATS.grade)}">{{ DEMO_STATS.grade }}</div>
        <div class="demo-stat-lbl">Overall Grade</div>
      </div>
      <div class="demo-stat">
        <div class="demo-stat-val" style="color:#d93025;">{{ DEMO_STATS.critical }}</div>
        <div class="demo-stat-lbl">Critical</div>
      </div>
      <div class="demo-stat">
        <div class="demo-stat-val" style="color:#f29900;">{{ DEMO_STATS.major }}</div>
        <div class="demo-stat-lbl">Major</div>
      </div>
      <div class="demo-stat">
        <div class="demo-stat-val">{{ DEMO_STATS.total_issues }}</div>
        <div class="demo-stat-lbl">Total Issues</div>
      </div>
      <div class="demo-stat">
        <div class="demo-stat-val">{{ DEMO_STATS.files_scanned }}</div>
        <div class="demo-stat-lbl">Files Scanned</div>
      </div>
      <div class="demo-stat">
        <div class="demo-stat-val" style="color:#d93025;">{{ DEMO_STATS.secrets_found }}</div>
        <div class="demo-stat-lbl">Secrets Found</div>
      </div>
      <div class="demo-stat">
        <div class="demo-stat-val">{{ DEMO_STATS.debt_score }}/10</div>
        <div class="demo-stat-lbl">Debt Score</div>
      </div>
      <div class="demo-stat">
        <div class="demo-stat-val">{{ (DEMO_STATS.scan_time_ms / 1000).toFixed(1) }}s</div>
        <div class="demo-stat-lbl">Scan Time</div>
      </div>
    </div>

    <!-- ── Issues table ── -->
    <div class="demo-section">
      <h2 class="demo-section-title">Sample Findings</h2>
      <div class="gc-card" style="overflow:hidden;">
        <table class="demo-table">
          <thead>
            <tr>
              <th>Severity</th>
              <th>File</th>
              <th>Line</th>
              <th>Rule</th>
              <th>CVE</th>
              <th>Finding</th>
              <th>Suggested Fix</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="issue in DEMO_ISSUES" :key="issue.title">
              <td>
                <span class="demo-sev-chip" :style="{background: severityColor[issue.severity]+'22', color: severityColor[issue.severity]}">
                  {{ issue.severity }}
                </span>
              </td>
              <td><code class="demo-file">{{ issue.file }}</code></td>
              <td style="color:var(--gc-text-3);font-size:12px;">{{ issue.line }}</td>
              <td><code class="demo-rule">{{ issue.rule }}</code></td>
              <td style="font-size:11px;color:var(--gc-text-3);">{{ issue.cve }}</td>
              <td style="font-size:13px;color:var(--gc-text);">{{ issue.title }}</td>
              <td style="font-size:11px;color:var(--gc-text-2);">{{ issue.fix }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── Module grades ── -->
    <div class="demo-section">
      <h2 class="demo-section-title">Module Health</h2>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;">
        <div v-for="mod in DEMO_MODULES" :key="mod.path" class="gc-card demo-mod-card">
          <div class="demo-mod-grade" :style="{color: gradeColor(mod.grade), borderColor: gradeColor(mod.grade)+'44'}">
            {{ mod.grade }}
          </div>
          <div class="demo-mod-path">{{ mod.path }}</div>
          <div class="demo-mod-meta">{{ mod.issues }} issues · {{ mod.loc }} LOC</div>
          <div class="demo-mod-debt">Debt: {{ mod.debt }}/10</div>
        </div>
      </div>
    </div>

    <!-- ── Feature grid ── -->
    <div class="demo-section">
      <h2 class="demo-section-title">Platform Capabilities</h2>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px;">
        <div v-for="feat in FEATURES" :key="feat.title" class="gc-card demo-feat-card">
          <div class="demo-feat-icon">
            <AppIcon :name="feat.icon" :size="22" style="color:var(--gc-primary);" />
          </div>
          <div class="demo-feat-title">{{ feat.title }}</div>
          <div class="demo-feat-desc">{{ feat.desc }}</div>
        </div>
      </div>
    </div>

    <!-- ── CTA strip ── -->
    <div class="demo-cta-strip">
      <div style="font-size:20px;font-weight:500;color:var(--gc-text);margin-bottom:8px;">Ready to scan your codebase?</div>
      <div style="font-size:14px;color:var(--gc-text-2);margin-bottom:24px;">
        Login with <code style="background:var(--gc-surface-2);padding:2px 6px;border-radius:4px;">admin / zero</code>
        or register a new account.
      </div>
      <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
        <button class="gc-btn gc-btn-primary demo-cta" @click="router.push('/login')">
          Sign In
        </button>
        <button class="gc-btn demo-cta-ghost" @click="router.push('/register')">
          Create Account
        </button>
      </div>
    </div>

  </div>
</template>

<style scoped>
.demo-wrap {
  min-height: 100vh;
  background: var(--gc-bg);
  padding: 0 0 80px;
}

/* Hero */
.demo-hero {
  text-align: center;
  padding: 80px 24px 60px;
  background: linear-gradient(160deg, var(--gc-surface) 0%, var(--gc-bg) 100%);
  border-bottom: 1px solid var(--gc-border);
}
.demo-hero-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  background: var(--gc-primary-light);
  color: var(--gc-primary);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .6px;
  text-transform: uppercase;
  margin-bottom: 20px;
}
.demo-hero-title {
  font-size: clamp(36px, 6vw, 72px);
  font-weight: 300;
  letter-spacing: -1px;
  color: var(--gc-text);
  margin: 0 0 12px;
}
.demo-hero-sub {
  font-size: 16px;
  color: var(--gc-text-2);
  margin: 0 0 36px;
}
.demo-hero-actions { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }

.demo-cta {
  display: flex; align-items: center; gap: 8px;
  padding: 0 24px; height: 42px; border-radius: 21px; font-size: 14px; font-weight: 500;
}
.demo-cta-ghost {
  display: flex; align-items: center; gap: 8px;
  padding: 0 24px; height: 42px; border-radius: 21px; font-size: 14px; font-weight: 500;
  border: 1px solid var(--gc-border); background: transparent; color: var(--gc-text);
  cursor: pointer; text-decoration: none; transition: background .15s;
}
.demo-cta-ghost:hover { background: var(--gc-surface-2); }

/* Stats */
.demo-stats {
  display: flex; flex-wrap: wrap; justify-content: center; gap: 0;
  background: var(--gc-surface);
  border-bottom: 1px solid var(--gc-border);
}
.demo-stat {
  padding: 20px 28px;
  text-align: center;
  border-right: 1px solid var(--gc-border);
}
.demo-stat:last-child { border-right: none; }
.demo-stat-val { font-size: 28px; font-weight: 300; color: var(--gc-text); }
.demo-stat-lbl { font-size: 11px; color: var(--gc-text-3); text-transform: uppercase; letter-spacing: .5px; margin-top: 2px; }

/* Sections */
.demo-section { max-width: 1100px; margin: 40px auto 0; padding: 0 24px; }
.demo-section-title {
  font-size: 16px; font-weight: 500; color: var(--gc-text);
  margin: 0 0 16px; letter-spacing: -.2px;
}

/* Table */
.demo-table {
  width: 100%; border-collapse: collapse;
}
.demo-table th {
  text-align: left; padding: 10px 14px;
  font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .5px;
  color: var(--gc-text-3); border-bottom: 1px solid var(--gc-border);
}
.demo-table td {
  padding: 10px 14px; border-bottom: 1px solid var(--gc-divider); vertical-align: middle;
}
.demo-table tr:last-child td { border-bottom: none; }
.demo-table tr:hover td { background: var(--gc-surface-2); }

.demo-sev-chip {
  display: inline-block; padding: 2px 8px; border-radius: 10px;
  font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .4px;
}
.demo-file { font-size: 11px; color: var(--gc-text-2); }
.demo-rule { font-size: 11px; background: var(--gc-border); padding: 1px 5px; border-radius: 3px; color: var(--gc-text); }

/* Module cards */
.demo-mod-card { padding: 16px; text-align: center; }
.demo-mod-grade {
  font-size: 32px; font-weight: 300; width: 52px; height: 52px;
  display: flex; align-items: center; justify-content: center;
  border: 2px solid; border-radius: 50%; margin: 0 auto 8px;
}
.demo-mod-path  { font-size: 13px; font-weight: 500; color: var(--gc-text); margin-bottom: 4px; }
.demo-mod-meta  { font-size: 11px; color: var(--gc-text-3); }
.demo-mod-debt  { font-size: 11px; color: var(--gc-text-3); margin-top: 2px; }

/* Feature cards */
.demo-feat-card { padding: 20px; }
.demo-feat-icon { margin-bottom: 12px; }
.demo-feat-title { font-size: 14px; font-weight: 600; color: var(--gc-text); margin-bottom: 6px; }
.demo-feat-desc  { font-size: 12px; color: var(--gc-text-2); line-height: 1.6; }

/* CTA strip */
.demo-cta-strip {
  max-width: 500px; margin: 60px auto 0;
  padding: 40px 24px;
  text-align: center;
  background: var(--gc-surface);
  border-radius: 16px;
  border: 1px solid var(--gc-border);
}
</style>
