<template>
  <div :data-theme="theme" class="app-root">
    <!-- Auth pages bypass shell -->
    <template v-if="isAuthRoute">
      <router-view />
    </template>

    <template v-else>
      <!-- ── Top Navigation ── -->
      <nav class="gc-nav">
        <div class="gc-nav-left">
          <button class="gc-icon-btn sidebar-toggle" @click="toggleSidebar" :title="sidebarOpen ? 'Collapse' : 'Expand'">
            <AppIcon name="menu" :size="18" />
          </button>
          <router-link to="/" class="nav-logo">
            <span class="logo-dark">Dark</span><span class="logo-lead">Lead</span>
          </router-link>
        </div>

        <div class="gc-nav-center">
          <div class="gc-search">
            <AppIcon name="search" :size="14" class="search-icon-svg" />
            <input v-model="searchQ" type="text"
              placeholder="Search issues, repos, files…"
              @keydown.enter="doSearch" />
          </div>
        </div>

        <div class="gc-nav-right">
          <ModelSelector />
          <button class="gc-icon-btn" @click="toggleTheme" :title="theme==='dark' ? 'Light mode' : 'Dark mode'">
            <AppIcon :name="theme==='dark' ? 'sun' : 'moon'" :size="17" />
          </button>
          <button class="gc-icon-btn notif-btn" @click="showAlerts = !showAlerts" title="Notifications">
            <AppIcon name="bell" :size="17" />
            <span v-if="notifs.unread > 0" class="notif-badge">{{ notifs.unread > 9 ? '9+' : notifs.unread }}</span>
          </button>
          <div ref="avatarWrap" style="position:relative;">
            <button class="nav-avatar" :style="{background: auth.user?.avatar_color ?? '#1a73e8'}"
              @click="showUserMenu = !showUserMenu" :title="auth.user?.username">
              {{ auth.initials }}
            </button>
            <transition name="menu-fade">
              <div v-if="showUserMenu" class="gc-dropdown user-menu">
                <div class="user-menu-header">
                  <div class="user-avatar-lg" :style="{background: auth.user?.avatar_color ?? '#1a73e8'}">{{ auth.initials }}</div>
                  <div>
                    <div class="user-name">{{ auth.user?.full_name || auth.user?.username }}</div>
                    <div class="user-email">{{ auth.user?.email }}</div>
                  </div>
                </div>
                <div class="gc-dropdown-divider" />
                <button class="gc-dropdown-item" @click="goProfile">
                  <AppIcon name="user" :size="15" /> Manage account
                </button>
                <button class="gc-dropdown-item" @click="goSettings">
                  <AppIcon name="settings2" :size="15" /> Settings
                </button>
                <div class="gc-dropdown-divider" />
                <button class="gc-dropdown-item danger" @click="doLogout">
                  <AppIcon name="logout" :size="15" /> Sign out
                </button>
              </div>
            </transition>
          </div>
        </div>

        <!-- Scan progress strip -->
        <div v-if="scanStore.status === 'running'" class="scan-progress-strip">
          <div class="scan-progress-fill" :style="{width: scanStore.progress + '%'}" />
        </div>
      </nav>

      <!-- mobile sidebar overlay -->
      <div v-if="mobileSidebarOpen" class="mobile-sidebar-overlay" @click="mobileSidebarOpen = false" />

      <!-- ── Body ── -->
      <div class="app-body">
        <!-- ── Sidebar ── -->
        <aside class="gc-sidebar" :class="{collapsed: !sidebarOpen, 'mobile-open': mobileSidebarOpen}">
          <div class="sidebar-scan">
            <template v-if="sidebarOpen">
              <div class="scan-input-wrap">
                <AppIcon name="search" :size="13" class="scan-icon" />
                <input v-model="repoUrl" class="scan-input"
                  placeholder="github.com/owner/repo"
                  @keydown.enter="doScan" />
              </div>
              <label class="scan-upload-btn" title="Upload zip/tar.gz">
                <input type="file" accept=".zip,.tar,.gz,.tgz" style="display:none"
                  @change="doUpload" :disabled="scanStore.status === 'running'" />
                <AppIcon name="upload" :size="14" />
              </label>
              <button class="scan-btn"
                :class="{running: scanStore.status === 'running'}"
                @click="doScan"
                :disabled="scanStore.status === 'running'">
                <span v-if="scanStore.status !== 'running'">▶</span>
                <span v-else class="spin-char">◌</span>
              </button>
            </template>
            <button v-else class="scan-btn-collapsed" @click="sidebarOpen=true" title="New scan">
              <AppIcon name="search" :size="16" />
            </button>
          </div>

          <nav class="sidebar-nav">
            <div v-for="section in navSections" :key="section.label" class="sidebar-section">
              <div class="sidebar-section-label" v-if="sidebarOpen">{{ section.label }}</div>
              <router-link v-for="item in section.items" :key="item.path"
                :to="item.path"
                class="sidebar-item"
                :class="{active: $route.path === item.path}"
                @click="closeSidebarAndMenus"
                :title="!sidebarOpen ? item.label : undefined">
                <span class="sidebar-icon"><AppIcon :name="item.icon" :size="16" /></span>
                <span v-if="sidebarOpen" class="sidebar-label">{{ item.label }}</span>
                <span v-if="item.badge && sidebarOpen" class="sidebar-chip">{{ item.badge }}</span>
              </router-link>
            </div>
          </nav>
        </aside>

        <!-- Main content -->
        <main class="app-content">
          <router-view />
        </main>
      </div>

      <!-- ── Notifications panel ── -->
      <transition name="slide-right">
        <div v-if="showAlerts" class="alerts-panel">
          <div class="alerts-header">
            <span class="alerts-title">Notifications</span>
            <div style="display:flex;gap:6px;">
              <button class="gc-btn gc-btn-ghost gc-btn-sm" @click="notifs.markAllRead()">Mark all read</button>
              <button class="gc-icon-btn" style="width:26px;height:26px;" @click="showAlerts=false">
                <AppIcon name="close" :size="14" />
              </button>
            </div>
          </div>
          <div v-if="!notifs.items.length" class="alerts-empty">
            <AppIcon name="bell" :size="28" style="opacity:.3" />
            <div>No notifications</div>
          </div>
          <div v-for="n in notifs.items" :key="n.id"
            class="alert-item" :class="{unread: !n.read}"
            @click="notifs.markRead(n.id)">
            <span class="alert-icon">{{ ({info:'ℹ️',success:'✅',warning:'⚠️',error:'🚨'} as any)[n.level] }}</span>
            <div class="alert-body">
              <div class="alert-title">{{ n.title }}</div>
              <div class="alert-msg">{{ n.message }}</div>
              <div class="alert-time">{{ timeAgo(n.ts) }}</div>
            </div>
          </div>
        </div>
      </transition>

      <div v-if="showUserMenu || showAlerts" class="menu-overlay" @click="closeMenus" />
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { useNotificationsStore } from './stores/notifications'
import { useScanStore } from './stores/scan'
import AppIcon from './components/AppIcon.vue'
import ModelSelector from './components/ModelSelector.vue'

const route     = useRoute()
const router    = useRouter()
const auth      = useAuthStore()
const notifs    = useNotificationsStore()
const scanStore = useScanStore()

const theme             = ref(localStorage.getItem('dl_theme') || 'dark')
const sidebarOpen       = ref(true)
const mobileSidebarOpen = ref(false)
const isMobile          = ref(window.innerWidth < 768)
const showUserMenu      = ref(false)
const showAlerts        = ref(false)
const searchQ           = ref('')
const repoUrl           = ref('')
const avatarWrap        = ref<HTMLElement | null>(null)

const isAuthRoute = computed(() => ['/login', '/register', '/demo'].includes(route.path))

onMounted(() => {
  document.documentElement.setAttribute('data-theme', theme.value)
  auth.fetchMe()
  document.addEventListener('click', handleOutside)
  window.addEventListener('resize', handleResize)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', handleOutside)
  window.removeEventListener('resize', handleResize)
})

function handleResize() {
  isMobile.value = window.innerWidth < 768
  if (!isMobile.value) mobileSidebarOpen.value = false
}

function toggleSidebar() {
  if (isMobile.value) {
    mobileSidebarOpen.value = !mobileSidebarOpen.value
  } else {
    sidebarOpen.value = !sidebarOpen.value
  }
}

function handleOutside(e: MouseEvent) {
  if (avatarWrap.value && !avatarWrap.value.contains(e.target as Node)) {
    showUserMenu.value = false
  }
}
function closeMenus()  { showUserMenu.value = false; showAlerts.value = false }
function closeSidebarAndMenus() { closeMenus(); mobileSidebarOpen.value = false }
function goProfile()   { router.push('/profile');  closeMenus() }
function goSettings()  { router.push('/settings'); closeMenus() }
function doLogout()    { auth.logout(); router.push('/login'); closeMenus() }
function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  document.documentElement.setAttribute('data-theme', theme.value)
  localStorage.setItem('dl_theme', theme.value)
}
function doSearch() {
  const q = searchQ.value.trim()
  if (q) router.push(`/issues?q=${encodeURIComponent(q)}`)
}
async function doScan() {
  const url = repoUrl.value.trim()
  if (!url) return
  try {
    const r = await fetch('/api/scan', {
      method: 'POST',
      headers: { ...auth.authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_url: url }),
    })
    if (r.ok) { notifs.push('info', 'Scan queued', `Scanning ${url}…`); router.push('/') }
  } catch {}
}

async function doUpload(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  const form = new FormData()
  form.append('file', file)
  form.append('language', 'auto')
  try {
    const r = await fetch('/api/scan/upload', {
      method: 'POST',
      headers: auth.authHeaders(),
      body: form,
    })
    if (r.ok) {
      const d = await r.json()
      notifs.push('info', 'Upload scan queued', `Scanning ${file.name}…`)
      router.push('/')
    } else {
      const d = await r.json()
      notifs.push('error', 'Upload failed', d.detail || 'Unknown error')
    }
  } catch (err) {
    notifs.push('error', 'Upload failed', String(err))
  }
  ;(e.target as HTMLInputElement).value = ''
}
function timeAgo(ts: number): string {
  const m = Math.floor((Date.now() - ts) / 60000)
  if (m < 1)  return 'just now'
  if (m < 60) return `${m}m ago`
  return `${Math.floor(m / 60)}h ago`
}

const navSections = [
  { label: 'Overview', items: [
    { path: '/',        icon: 'home',    label: 'Command Center' },
    { path: '/history', icon: 'history', label: 'Scan History'   },
  ]},
  { label: 'Analysis', items: [
    { path: '/issues',        icon: 'bug',   label: 'Issues'        },
    { path: '/code-analysis', icon: 'code',  label: 'Code Analyzer', badge: 'AI'  },
    { path: '/fixes',         icon: 'fix',   label: 'Fix Studio'    },
    { path: '/graph',         icon: 'graph', label: 'Code Graph',   badge: 'NEW' },
  ]},
  { label: 'Visualize', items: [
    { path: '/heatmap',  icon: 'heatmap',  label: 'Heatmap'         },
    { path: '/security', icon: 'shield',   label: 'Security Posture' },
    { path: '/misconfig',icon: 'settings2',label: 'Misconfig Radar'  },
  ]},
  { label: 'Compliance', items: [
    { path: '/compliance', icon: 'compliance', label: 'Compliance'   },
    { path: '/deps',       icon: 'package',    label: 'Dependencies' },
  ]},
  { label: 'Intelligence', items: [
    { path: '/advisories', icon: 'rss',   label: 'Advisory Feed'    },
    { path: '/git',        icon: 'git',   label: 'Git Intelligence'  },
    { path: '/trends',     icon: 'chart', label: 'Trends'            },
  ]},
  { label: 'Infrastructure', items: [
    { path: '/infra',   icon: 'docker', label: 'Infra Posture' },
    { path: '/siem',    icon: 'eye',    label: 'Live Logs',    badge: 'LIVE' },
    { path: '/updates', icon: 'update', label: 'Update Center' },
  ]},
  { label: 'System', items: [
    { path: '/ai',          icon: 'bot',      label: 'AI Assistant' },
    { path: '/self-health', icon: 'health',   label: 'Self Health'  },
    { path: '/export',      icon: 'download', label: 'Export'       },
    { path: '/compare',     icon: 'compare',  label: 'Compare'      },
    { path: '/settings',    icon: 'settings', label: 'Settings'     },
  ]},
]
</script>

<style>
.app-root { display:flex; flex-direction:column; height:100vh; overflow:hidden; background:var(--gc-bg); }

/* Nav */
.gc-nav {
  height:var(--nav-height); background:var(--gc-nav-bg); border-bottom:1px solid var(--gc-border);
  display:flex; align-items:center; gap:8px; padding:0 12px 0 8px;
  position:relative; z-index:100; flex-shrink:0;
}
.gc-nav-left  { display:flex; align-items:center; gap:6px; }
.gc-nav-center{ flex:1; display:flex; justify-content:center; padding:0 12px; }
.gc-nav-right { display:flex; align-items:center; gap:4px; margin-left:auto; }

.nav-logo { display:flex; align-items:center; font-size:18px; font-weight:700; text-decoration:none; letter-spacing:-.3px; }
.logo-dark{ color:var(--gc-text); }
.logo-lead{ color:var(--gc-primary); }

.gc-search {
  width:100%; max-width:500px; position:relative; display:flex; align-items:center;
  background:var(--gc-surface-2); border:1px solid var(--gc-border);
  border-radius:24px; padding:0 14px 0 36px;
  transition:border-color .15s, box-shadow .15s;
}
.gc-search:focus-within { border-color:var(--gc-primary); box-shadow:0 0 0 3px var(--gc-primary-light); }
.gc-search .search-icon-svg { position:absolute; left:12px; color:var(--gc-text-3); pointer-events:none; }
.gc-search input { flex:1; border:none; background:transparent; outline:none; color:var(--gc-text); font-size:13.5px; padding:8px 0; }
.gc-search input::placeholder { color:var(--gc-text-3); }

.nav-avatar {
  width:32px; height:32px; border-radius:50%; border:none; cursor:pointer;
  color:#fff; font-size:12px; font-weight:700;
  display:flex; align-items:center; justify-content:center; transition:box-shadow .15s;
}
.nav-avatar:hover { box-shadow:0 0 0 3px var(--gc-primary-light); }

.notif-btn { position:relative; }
.notif-badge {
  position:absolute; top:2px; right:2px; background:var(--gc-error); color:#fff;
  font-size:9px; font-weight:700; min-width:16px; height:16px; border-radius:8px; padding:0 3px;
  display:flex; align-items:center; justify-content:center; border:2px solid var(--gc-nav-bg);
}

.scan-progress-strip { position:absolute; bottom:0; left:0; right:0; height:3px; background:var(--gc-border); }
.scan-progress-fill  { height:100%; background:linear-gradient(90deg,var(--gc-primary),#34a853); transition:width .4s; border-radius:0 2px 2px 0; }

/* Dropdown */
.gc-dropdown {
  position:absolute; top:calc(100% + 6px); right:0; background:var(--gc-surface);
  border:1px solid var(--gc-border); border-radius:12px; box-shadow:var(--gc-shadow-lg);
  z-index:1000; overflow:hidden; min-width:200px;
}
.gc-dropdown-item {
  display:flex; align-items:center; gap:10px; padding:10px 16px;
  font-size:13.5px; color:var(--gc-text); cursor:pointer;
  transition:background .1s; background:none; border:none; width:100%; text-align:left;
}
.gc-dropdown-item:hover       { background:var(--gc-surface-2); }
.gc-dropdown-item.danger:hover{ background:var(--gc-error-bg); color:var(--gc-error); }
.gc-dropdown-divider          { border-top:1px solid var(--gc-border); }

.user-menu     { min-width:260px; }
.user-menu-header { display:flex; align-items:center; gap:12px; padding:14px 16px; }
.user-avatar-lg {
  width:44px; height:44px; border-radius:50%; flex-shrink:0;
  display:flex; align-items:center; justify-content:center; color:#fff; font-size:16px; font-weight:700;
}
.user-name  { font-size:14px; font-weight:500; color:var(--gc-text); }
.user-email { font-size:12px; color:var(--gc-text-3); margin-top:1px; }

/* Body */
.app-body { flex:1; display:flex; overflow:hidden; }

/* Sidebar */
.gc-sidebar {
  width:var(--sidebar-width); flex-shrink:0; background:var(--gc-sidebar-bg);
  border-right:1px solid var(--gc-border); display:flex; flex-direction:column;
  overflow:hidden; transition:width .2s ease;
}
.gc-sidebar.collapsed { width:56px; }

.sidebar-scan { padding:10px 8px; border-bottom:1px solid var(--gc-border); flex-shrink:0; display:flex; gap:6px; align-items:center; }
.scan-input-wrap { flex:1; position:relative; display:flex; align-items:center; }
.scan-icon { position:absolute; left:8px; color:var(--gc-text-3); pointer-events:none; }
.scan-input {
  width:100%; padding:7px 8px 7px 28px;
  border:1px solid var(--gc-border); border-radius:6px;
  background:var(--gc-surface); color:var(--gc-text); font-size:12px; outline:none;
  transition:border-color .15s;
}
.scan-input:focus { border-color:var(--gc-primary); }
.scan-upload-btn {
  width:30px; height:30px; flex-shrink:0; border-radius:6px; border:1px solid var(--gc-border);
  background:var(--gc-surface-2); color:var(--gc-text-2); cursor:pointer;
  display:flex; align-items:center; justify-content:center; transition:background .15s;
}
.scan-upload-btn:hover { background:var(--gc-primary-light); color:var(--gc-primary); border-color:var(--gc-primary); }
.scan-btn {
  width:32px; height:32px; flex-shrink:0; border-radius:6px; border:none; cursor:pointer;
  background:var(--gc-primary); color:#fff; font-size:13px;
  display:flex; align-items:center; justify-content:center; transition:background .15s;
}
.scan-btn:hover    { background:var(--gc-primary-dark); }
.scan-btn:disabled { opacity:.6; cursor:not-allowed; }
.scan-btn.running  { background:var(--gc-warning); }
.scan-btn-collapsed {
  width:40px; height:36px; border-radius:8px; border:1px solid var(--gc-border);
  background:transparent; color:var(--gc-text-2); cursor:pointer; margin:auto;
  display:flex; align-items:center; justify-content:center;
}
.scan-btn-collapsed:hover { background:var(--gc-surface-2); }
.spin-char { animation:spin .8s linear infinite; display:inline-block; }
@keyframes spin { to { transform:rotate(360deg); } }

.sidebar-nav { flex:1; overflow-y:auto; overflow-x:hidden; padding:6px 0 12px; }
.sidebar-nav::-webkit-scrollbar { width:4px; }
.sidebar-nav::-webkit-scrollbar-thumb { background:var(--gc-border); border-radius:2px; }
.sidebar-section { margin-bottom:2px; }
.sidebar-section-label {
  padding:10px 14px 4px; font-size:10.5px; font-weight:700;
  letter-spacing:.6px; text-transform:uppercase; color:var(--gc-text-3);
}
.sidebar-item {
  display:flex; align-items:center; gap:10px;
  padding:7px 12px; margin:1px 6px; border-radius:8px;
  color:var(--gc-text-2); text-decoration:none; font-size:13px; cursor:pointer;
  transition:background .1s, color .1s; white-space:nowrap; overflow:hidden;
}
.sidebar-item:hover   { background:var(--gc-surface-2); color:var(--gc-text); }
.sidebar-item.active  { background:var(--gc-primary-light); color:var(--gc-primary); font-weight:500; }
.sidebar-icon         { display:flex; align-items:center; flex-shrink:0; }
.sidebar-label        { flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; }
.sidebar-chip {
  font-size:9px; padding:1px 5px; border-radius:4px; font-weight:700;
  background:var(--gc-primary); color:#fff; flex-shrink:0; letter-spacing:.3px;
}

.gc-sidebar.collapsed .sidebar-section-label { display:none; }
.gc-sidebar.collapsed .sidebar-label         { display:none; }
.gc-sidebar.collapsed .sidebar-chip          { display:none; }
.gc-sidebar.collapsed .sidebar-item          { justify-content:center; padding:9px 0; }

/* Main */
.app-content { flex:1; overflow-y:auto; overflow-x:hidden; padding:22px 24px; background:var(--gc-bg); }

/* Alerts */
.alerts-panel {
  position:fixed; top:var(--nav-height); right:0; width:360px; height:calc(100vh - var(--nav-height));
  background:var(--gc-surface); border-left:1px solid var(--gc-border);
  z-index:200; overflow-y:auto; box-shadow:var(--gc-shadow-lg);
}
.alerts-header { padding:14px 16px; border-bottom:1px solid var(--gc-border); display:flex; justify-content:space-between; align-items:center; }
.alerts-title  { font-weight:600; font-size:14px; }
.alerts-empty  { padding:40px; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:8px; color:var(--gc-text-3); font-size:13px; }
.alert-item { padding:12px 16px; border-bottom:1px solid var(--gc-divider); display:flex; gap:10px; cursor:pointer; transition:background .1s; }
.alert-item:hover  { background:var(--gc-surface-2); }
.alert-item.unread { background:var(--gc-primary-light); }
.alert-icon  { font-size:16px; flex-shrink:0; margin-top:1px; }
.alert-body  { flex:1; min-width:0; }
.alert-title { font-size:13px; font-weight:500; color:var(--gc-text); }
.alert-msg   { font-size:12px; color:var(--gc-text-2); margin-top:2px; }
.alert-time  { font-size:11px; color:var(--gc-text-3); margin-top:3px; }

.menu-overlay { position:fixed; inset:0; z-index:99; }
.menu-fade-enter-active,.menu-fade-leave-active   { transition:opacity .15s, transform .15s; }
.menu-fade-enter-from,  .menu-fade-leave-to       { opacity:0; transform:translateY(-6px); }
.slide-right-enter-active,.slide-right-leave-active { transition:transform .2s ease; }
.slide-right-enter-from,.slide-right-leave-to       { transform:translateX(100%); }

/* ── Mobile responsive ──────────────────────────────────── */
@media (max-width: 768px) {
  /* Hide search bar on mobile — save nav space */
  .gc-nav-center { display: none; }

  /* Collapse right nav items */
  .gc-nav-right > *:not(.notif-btn):not([class*="nav-avatar"]) {
    display: none;
  }

  /* Sidebar becomes a fixed overlay on mobile */
  .gc-sidebar {
    position: fixed !important;
    top: var(--nav-height);
    left: 0;
    height: calc(100vh - var(--nav-height));
    z-index: 150;
    width: var(--sidebar-width) !important;
    transform: translateX(-110%);
    transition: transform .25s cubic-bezier(.4,0,.2,1), box-shadow .25s;
    box-shadow: none;
  }
  .gc-sidebar.mobile-open {
    transform: translateX(0);
    box-shadow: 6px 0 32px rgba(0,0,0,.5);
  }
  /* Ignore collapsed state on mobile — always show full width sidebar */
  .gc-sidebar.collapsed                       { width: var(--sidebar-width) !important; }
  .gc-sidebar.collapsed .sidebar-section-label{ display: block; }
  .gc-sidebar.collapsed .sidebar-label        { display: block; }
  .gc-sidebar.collapsed .sidebar-chip         { display: block; }
  .gc-sidebar.collapsed .sidebar-item         { justify-content: flex-start; padding: 7px 12px; }
  .gc-sidebar.collapsed .sidebar-icon         { width: auto; }

  /* Content takes full width since sidebar is overlay */
  .app-content { padding: 14px 12px; }

  /* Notifications panel full-width on mobile */
  .alerts-panel { width: 100%; }
}

/* Mobile sidebar backdrop */
.mobile-sidebar-overlay {
  position: fixed;
  inset: 0;
  top: var(--nav-height);
  background: rgba(0,0,0,.55);
  z-index: 149;
  display: none;
}
@media (max-width: 768px) {
  .mobile-sidebar-overlay { display: block; }
}
</style>
