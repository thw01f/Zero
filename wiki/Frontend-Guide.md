# Frontend Guide

The DarkLead frontend is a **Vue 3 + Vite** SPA with a **Google Cloud Console-themed** design system featuring full dark/light mode toggle.

---

## Authentication

### Default Login
| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `zero` |

### Auth Flow
- `/login` — Google-style centered auth card with username/password
- `/register` — create new account (full name, username, email, password)
- All protected routes redirect to `/login` if unauthenticated
- JWT token stored in `localStorage` as `dl_token` (24-hour expiry)
- On token expiry, router guard redirects to `/login`

### Profile Management (`/profile`)
Three tabs:
- **Account** — edit full name, username, avatar color (8 swatches)
- **Security** — change password (requires current password confirmation)
- **Activity** — scan count, issues found, fixes accepted, member since

---

## Design System

### Theme Toggle
Click the sun/moon icon in the top navigation bar to switch between light and dark mode. Preference is persisted to `localStorage` as `dl_theme`.

```html
<!-- Applied to <html> element -->
<html data-theme="dark">   <!-- or "light" -->
```

### Color Tokens (CSS Custom Properties)

**Light mode (default):**

| Token | Value | Usage |
|-------|-------|-------|
| `--gc-bg` | `#f8f9fa` | Page background |
| `--gc-surface` | `#ffffff` | Card/panel backgrounds |
| `--gc-border` | `#dadce0` | Borders, dividers |
| `--gc-text` | `#202124` | Primary text |
| `--gc-text-secondary` | `#5f6368` | Secondary text |
| `--gc-blue` | `#1a73e8` | Primary accent, links, buttons |
| `--gc-blue-hover` | `#1557b0` | Hover state |
| `--gc-nav-bg` | `#ffffff` | Navigation bar background |
| `--gc-sidebar-bg` | `#f8f9fa` | Sidebar background |

**Dark mode (`[data-theme="dark"]`):**

| Token | Value | Usage |
|-------|-------|-------|
| `--gc-bg` | `#0d1117` | Page background |
| `--gc-surface` | `#161b22` | Card/panel backgrounds |
| `--gc-border` | `#30363d` | Borders, dividers |
| `--gc-text` | `#e6edf3` | Primary text |
| `--gc-text-secondary` | `#8b949e` | Secondary text |
| `--gc-nav-bg` | `#161b22` | Navigation bar background |
| `--gc-sidebar-bg` | `#0d1117` | Sidebar background |

### Typography

- **Body:** Google Sans, Roboto (sans-serif)
- **Code/monospace:** Roboto Mono
- **Base size:** 14px
- **Headers:** 500–600 weight

### CSS Classes

```css
/* Cards */
.gc-card            /* Surface background, border-radius 8px */

/* Buttons */
.gc-btn             /* Base button */
.gc-btn-primary     /* Blue fill (Google blue) */
.gc-btn-secondary   /* Outlined */
.gc-btn-ghost       /* No background */
.gc-btn-danger      /* Red fill */

/* Form inputs */
.gc-input           /* Outlined input with blue focus ring */
.gc-select          /* Outlined select */

/* Tables */
.gc-table           /* Striped, hover rows */

/* Metric tiles */
.gc-metric-tile     /* Compact stat box */

/* Severity chips */
.chip-critical      /* Red */
.chip-major         /* Orange */
.chip-minor         /* Amber */
.chip-info          /* Blue */

/* Auth */
.gc-auth-page       /* Centered full-height auth layout */
.gc-auth-card       /* Login/register card */

/* Navigation */
.gc-nav             /* 64px fixed top navigation bar */
.gc-sidebar         /* 256px collapsible left sidebar */
```

---

## App Shell (`App.vue`)

### Top Navigation Bar (64px)
- Logo: `DarkLead` with blue accent dot
- Sidebar toggle (hamburger icon)
- LLM status pill (green dot + model name)
- Theme toggle (sun/moon icon)
- Notifications bell with unread badge
- User avatar (initials, colored per `avatar_color`) with dropdown:
  - Profile link
  - Settings link
  - Logout button

### Sidebar (256px, collapsible)
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
| `useAuthStore` | `stores/auth.ts` | JWT token, user object, login/logout/register |
| `useReportStore` | `stores/report.ts` | Current scan report data |
| `useScanStore` | `stores/scan.ts` | Active scan job, progress |
| `useAlertsStore` | `stores/alerts.ts` | Alert list (legacy) |
| `useNotificationsStore` | `stores/notifications.ts` | Typed notifications with levels |
| `useSettingsStore` | `stores/settings.ts` | LLM backend, UI preferences |
| `useHistoryStore` | `stores/history.ts` | Scan history with 30s cache |

### Auth Store API

```typescript
const auth = useAuthStore()

auth.isAuthenticated   // computed boolean
auth.user              // { id, email, username, full_name, avatar_color, role }
auth.initials          // computed "JD" from full_name or username[0]
auth.authHeaders()     // { Authorization: "Bearer <token>" }

await auth.login(username, password)   // stores token + user
await auth.register(email, username, password, fullName)
await auth.logout()                    // clears token + user
await auth.fetchMe()                   // re-hydrate from /api/auth/me
```

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
