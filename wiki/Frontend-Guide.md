# Frontend Guide

The DarkLead frontend is a **Vue 3 + Vite + Tailwind** SPA with a custom **Fortinet FortiAnalyzer-style** dark theme.

---

## Design System

### Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `--ft-bg` | `#0a0e1a` | Page background |
| `--ft-card` | `#141d30` | Card/panel backgrounds |
| `--ft-accent` | `#f26d21` | Orange accent — active states, progress bars, CTA buttons |
| `--ft-border` | `#1e2d45` | Borders, dividers |
| `--ft-text` | `#d4dde8` | Primary text |
| `--ft-text-dim` | `#8899aa` | Secondary / muted text |
| `--ft-green` | `#3ecf8e` | Success, Grade A |
| `--ft-blue` | `#4a9ff5` | Info, links |
| `--ft-yellow` | `#f5a623` | Warning, Grade C |
| `--ft-red` | `#f25555` | Error, Grade F |

### Typography

- **Body:** Inter (sans-serif)
- **Code/monospace:** JetBrains Mono
- **Base size:** 14px
- **Headers:** 600–700 weight

### CSS Classes

```css
/* Cards */
.ft-card        /* Standard card with border */
.ft-widget      /* Card with 2px orange left border */

/* Tables */
.ft-table       /* Dark header, hover rows */

/* Severity badges */
.sev-critical   /* Red background */
.sev-major      /* Orange background */
.sev-minor      /* Amber background, dark text */
.sev-info       /* Blue background */

/* Buttons */
.ft-btn .ft-btn-primary   /* Orange fill */
.ft-btn .ft-btn-secondary /* Blue fill */
.ft-btn .ft-btn-ghost     /* No background */
.ft-btn .ft-btn-danger    /* Red fill */

/* Form inputs */
.ft-input       /* Dark input with orange focus ring */
.ft-select      /* Dark select */
.ft-textarea    /* Dark textarea, monospace option */

/* Metric tiles */
.metric-tile    /* Compact stat box */
.metric-value   /* Large number */
.metric-label   /* Small gray label */

/* Navigation */
.nav-item       /* Sidebar nav link */
.nav-item.active /* Orange left border + tinted bg */
.nav-cnt        /* Count badge on nav item */
```

---

## App Shell (`App.vue`)

### Header (44px)
- Logo: `DARK` + `LEAD` with orange accent
- Sidebar toggle button
- LLM status pill (green dot + "Ollama / qwen2.5-coder")
- Scan progress bar (3px, orange gradient, shows during active scan)
- Alert bell with unread badge count
- Clock (JetBrains Mono, live update)
- User avatar

### Sidebar (196px collapsed/expanded)
- **Scan Form** at top — repo URL input + scan button
- **Navigation groups** with group headers:

| Group | Routes |
|-------|--------|
| OVERVIEW | Command Center, Scan History |
| ANALYSIS | Issues, Code Analyzer, Fix Studio |
| VISUALIZE | Heatmap, Security Posture, Misconfig Radar |
| COMPLIANCE | Compliance Dashboard, Dependency Intel |
| INTELLIGENCE | Advisory Feed, Git Intelligence, Trend Analysis |
| INFRASTRUCTURE | Infra Posture, Update Center |
| SYSTEM | AI Assistant, Self-Health, Export Reports |
| SETTINGS | Settings, Repo Compare |

### Alert Panel
- Slides in from right
- Lists up to 15 recent notifications
- Each alert has level (info/success/warning/error), title, message, timestamp
- Mark all read button

---

## Views

### Command Center (`/`)
Main dashboard. Shows:
- 6 StatCard tiles: Grade, Debt Score, Critical, Major, Minor, Total
- Severity distribution donut chart (ApexCharts)
- Top 5 modules by debt treemap
- Recent scan timeline
- Latest findings table preview

### Issues (`/issues`)
Full paginated findings table with:
- TableFilter (text search + severity dropdown)
- Expandable rows with LLM explanation
- CWE links to mitre.org
- OWASP tags
- Tool attribution badge

### Code Analyzer (`/code-analysis`)
Direct code snippet analysis:
- CodeEditor textarea with tab-indent support + copy button
- Language selector (15 languages)
- Mode selector (full/security/quality/improve)
- Optional filename input
- Real-time analysis via `POST /api/analyze/code`
- Results: GradeRing SVG gauge, findings table, improvements list with code examples

### Fix Studio (`/fix-studio`)
AI-generated fixes:
- Side-by-side diff viewer (diff2html, dark theme)
- DiffStats (lines added/removed/similarity)
- Accept/reject fix workflow
- Export as patch file

### Heatmap (`/heatmap`)
D3 treemap:
- Files/modules sized by finding count
- Color-coded by max severity (red=critical, orange=major, yellow=minor)
- Click to drill into module
- Hover tooltip with debt score

### Security Posture (`/security-posture`)
OWASP Top 10 radar:
- Radar/spider chart (ApexCharts)
- Category scores for A01–A10
- CWE count per category
- Trend vs previous scan

### Misconfig Radar (`/misconfig-radar`)
Infrastructure misconfigurations:
- Grouped by type: Dockerfile / Terraform / YAML / .env
- Severity breakdown StatBars
- One-click fix links

### Compliance Dashboard (`/compliance`)
Regulatory mapping:
- OWASP 2021 Top 10 coverage table
- NIST SP 800-53 control coverage (AC, IA, SC, AU, SI families)
- Pass/fail per control family
- Export compliance report

### Dependency Intel (`/dependency-intel`)
Dependency vulnerability tracking:
- Table of all dependencies (PyPI + npm) from SBOM
- CVE overlay from OSV.dev
- CVSS scores
- Update recommendations

### Advisory Feed (`/advisories`)
Live CVE feed:
- Polled from NVD + OSV.dev every 6h
- Real-time SSE push to frontend
- Filter by severity/ecosystem
- Link to NVD entry

### Git Intelligence (`/git-intelligence`)
Repository history analysis:
- Hotspot files (most commits)
- Author attribution via git blame
- Commit frequency chart

### Trend Analysis (`/trends`)
Multi-scan comparison:
- Debt score over time (ApexCharts line)
- Severity distribution over time
- Grade progression

### Infra Posture (`/infra`)
Container/IaC security:
- Dockerfile findings (hadolint + DarkLead rules)
- Terraform/checkov findings
- K8s misconfig summary

### Self-Health (`/self-health`)
Platform health:
- Scanner availability grid (green/red per tool)
- LLM backend status
- DB metrics
- CPU/memory usage

### AI Assistant (`/ai-assistant`)
Chat interface:
- Conversational chat about current scan
- RAG: full report JSON as context
- Streaming responses
- Citation linking to specific findings

### Export Reports (`/export`)
Download options:
- JSON full report
- SARIF 2.1.0 (GitHub Code Scanning)
- HTML stakeholder report
- Markdown summary

### Scan History (`/history`)
All past scans table with:
- Repo name, grade badge, score, issue count, status chip, date
- Click to load report

### Settings (`/settings`)
Configuration panel:
- Active LLM backend + model
- Available models list with sizes
- Scanner configuration display

### Repo Compare (`/compare`)
Side-by-side comparison:
- Select two scans from dropdowns
- Compare grade/score/issues
- Delta calculation

---

## State Management (Pinia Stores)

| Store | File | Purpose |
|-------|------|---------|
| `useReportStore` | `stores/report.ts` | Current scan report data |
| `useScanStore` | `stores/scan.ts` | Active scan job, progress |
| `useAlertsStore` | `stores/alerts.ts` | Alert list (legacy) |
| `useNotificationsStore` | `stores/notifications.ts` | Typed notifications with levels |
| `useSettingsStore` | `stores/settings.ts` | LLM backend, UI preferences |
| `useHistoryStore` | `stores/history.ts` | Scan history with 30s cache |

---

## Key Composables

| Composable | Purpose |
|-----------|---------|
| `useWebSocket` | Auto-reconnect WS for scan progress |
| `useTheme` | 3 dark theme variants with CSS vars |
| `useApi` | Generic typed fetch wrapper with loading/error |
| `useClipboard` | Copy with clipboard API + execCommand fallback |
| `useDebounce` | Debounced reactive refs for search inputs |
| `usePagination` | Generic table pagination |
| `useLocalStorage` | Reactive localStorage binding |

---

## Development

```bash
cd frontend
npm install --legacy-peer-deps
npm run dev          # Vite dev server on :5173 (proxies /api to :7860)
npm run build        # Production build to dist/
npx vue-tsc --noEmit # Type check
```

Vite proxy config (`vite.config.ts`):
```typescript
proxy: {
  '/api/ws': { target: 'ws://localhost:7860', ws: true },
  '/api':     { target: 'http://localhost:7860' }
}
```
