<template>
  <div :data-theme="theme" class="app-layout">
    <!-- Auth pages get no shell -->
    <template v-if="isAuthRoute">
      <router-view />
    </template>

    <template v-else>
      <!-- Top navigation -->
      <nav class="gc-nav">
        <div class="gc-nav-logo">
          <button class="gc-icon-btn" @click="sidebarOpen = !sidebarOpen" style="width:36px;height:36px;font-size:18px;">☰</button>
          <span class="product-name">Dark<span>Lead</span></span>
        </div>

        <div class="gc-nav-center">
          <div class="gc-search" style="max-width:500px;">
            <span class="search-icon">🔍</span>
            <input v-model="searchQ" type="text" placeholder="Search issues, repos, advisories…" @keydown.enter="doSearch" />
          </div>
        </div>

        <!-- Scan progress bar (only when scanning) -->
        <div v-if="scanStore.status === 'running'" style="position:absolute;bottom:0;left:0;right:0;">
          <div class="gc-progress-track" style="border-radius:0;">
            <div class="gc-progress-fill" :style="{width: scanStore.progress + '%'}"></div>
          </div>
        </div>

        <div class="gc-nav-right">
          <!-- Theme toggle -->
          <button class="theme-toggle" @click="toggleTheme" :title="theme==='dark' ? 'Light mode' : 'Dark mode'">
            {{ theme === 'dark' ? '☀️' : '🌙' }}
          </button>

          <!-- Notifications -->
          <button class="gc-icon-btn" @click="showAlerts = !showAlerts" title="Notifications">
            🔔
            <span v-if="notifs.unread > 0" class="badge"></span>
          </button>

          <!-- Help -->
          <button class="gc-icon-btn" title="Help">❓</button>

          <!-- Avatar dropdown -->
          <div style="position:relative;" ref="avatarWrap">
            <button class="gc-avatar-btn" :style="{background: auth.user?.avatar_color || '#1a73e8'}" @click="showUserMenu = !showUserMenu">
              {{ auth.initials }}
            </button>

            <div v-if="showUserMenu" class="gc-dropdown" style="min-width:280px;">
              <div class="gc-dropdown-header">
                <div style="display:flex;align-items:center;gap:12px;">
                  <div class="gc-avatar-large" :style="{background: auth.user?.avatar_color, width:'48px', height:'48px', fontSize:'18px'}">{{ auth.initials }}</div>
                  <div>
                    <div style="font-weight:500;color:var(--gc-text);font-size:15px;">{{ auth.user?.full_name || auth.user?.username }}</div>
                    <div style="font-size:13px;color:var(--gc-text-2);">{{ auth.user?.email }}</div>
                  </div>
                </div>
              </div>
              <div class="gc-dropdown-item" @click="goProfile">👤 &nbsp;Manage account</div>
              <div class="gc-dropdown-divider"></div>
              <div class="gc-dropdown-item" @click="goSettings">⚙️ &nbsp;Settings</div>
              <div class="gc-dropdown-divider"></div>
              <div class="gc-dropdown-item danger" @click="doLogout">🚪 &nbsp;Sign out</div>
            </div>
          </div>
        </div>
      </nav>

      <!-- Body -->
      <div class="app-body" :class="sidebarOpen ? 'sidebar-open' : 'sidebar-collapsed'">
        <!-- Sidebar -->
        <aside class="gc-sidebar" :class="{collapsed: !sidebarOpen}">
          <!-- Scan form -->
          <div style="padding:12px;border-bottom:1px solid var(--gc-border);">
            <div v-if="sidebarOpen" style="display:flex;gap:6px;">
              <input v-model="repoUrl" class="gc-input" placeholder="github.com/owner/repo" style="font-size:12px;" @keydown.enter="doScan" />
              <button class="gc-btn gc-btn-primary gc-btn-sm" @click="doScan" :disabled="scanStore.status === 'running'">
                {{ scanStore.status === 'running' ? '…' : '▶' }}
              </button>
            </div>
            <button v-else class="gc-btn gc-btn-primary gc-btn-icon" style="width:100%;height:36px;" @click="sidebarOpen=true" title="New scan">▶</button>
          </div>

          <!-- Navigation -->
          <div v-for="section in navSections" :key="section.label" class="gc-sidebar-section">
            <div class="gc-sidebar-label">{{ section.label }}</div>
            <router-link v-for="item in section.items" :key="item.path"
              :to="item.path" class="gc-nav-item"
              :class="{active: $route.path === item.path}"
              @click="closeMenus">
              <span class="nav-icon">{{ item.icon }}</span>
              <span class="nav-label">{{ item.label }}</span>
              <span v-if="item.badge" class="nav-chip">{{ item.badge }}</span>
            </router-link>
          </div>
        </aside>

        <!-- Main content -->
        <main class="app-content">
          <router-view />
        </main>
      </div>

      <!-- Alert panel -->
      <transition name="slide-right">
        <div v-if="showAlerts" style="position:fixed;top:64px;right:0;width:360px;height:calc(100vh - 64px);background:var(--gc-surface);border-left:1px solid var(--gc-border);z-index:200;overflow-y:auto;box-shadow:var(--gc-shadow-lg);">
          <div style="padding:16px 20px;border-bottom:1px solid var(--gc-border);display:flex;justify-content:space-between;align-items:center;">
            <span style="font-weight:500;">Notifications</span>
            <div style="display:flex;gap:8px;">
              <button class="gc-btn gc-btn-ghost gc-btn-sm" @click="notifs.markAllRead()">Mark all read</button>
              <button class="gc-icon-btn" style="width:28px;height:28px;font-size:14px;" @click="showAlerts=false">✕</button>
            </div>
          </div>
          <div v-if="notifs.items.length === 0" style="padding:40px;text-align:center;color:var(--gc-text-3);">No notifications</div>
          <div v-for="n in notifs.items" :key="n.id"
            style="padding:14px 20px;border-bottom:1px solid var(--gc-divider);cursor:pointer;transition:background 0.1s;"
            :style="{background: n.read ? '' : 'var(--gc-primary-light)'}"
            @click="notifs.markRead(n.id)">
            <div style="display:flex;gap:8px;align-items:flex-start;">
              <span style="font-size:16px;">{{ ({info:'ℹ️',success:'✅',warning:'⚠️',error:'🚨'} as Record<string,string>)[n.level] }}</span>
              <div>
                <div style="font-weight:500;font-size:13px;color:var(--gc-text);">{{ n.title }}</div>
                <div style="font-size:12px;color:var(--gc-text-2);margin-top:2px;">{{ n.message }}</div>
                <div style="font-size:11px;color:var(--gc-text-3);margin-top:4px;">{{ timeAgo(n.ts) }}</div>
              </div>
            </div>
          </div>
        </div>
      </transition>

      <!-- Overlay for menus on mobile -->
      <div v-if="showUserMenu || showAlerts" style="position:fixed;inset:0;z-index:99;" @click="closeMenus"></div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { useNotificationsStore } from './stores/notifications'
import { useScanStore } from './stores/scan'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const notifs = useNotificationsStore()
const scanStore = useScanStore()

const theme = ref(localStorage.getItem('dl_theme') || 'light')
const sidebarOpen = ref(true)
const showUserMenu = ref(false)
const showAlerts = ref(false)
const searchQ = ref('')
const repoUrl = ref('')
const avatarWrap = ref<HTMLElement | null>(null)

const isAuthRoute = computed(() => ['/login', '/register'].includes(route.path))

onMounted(() => {
  document.documentElement.setAttribute('data-theme', theme.value)
  auth.fetchMe()
  document.addEventListener('click', handleOutsideClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleOutsideClick)
})

function handleOutsideClick(e: MouseEvent) {
  if (avatarWrap.value && !avatarWrap.value.contains(e.target as Node)) {
    showUserMenu.value = false
  }
}

function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  document.documentElement.setAttribute('data-theme', theme.value)
  localStorage.setItem('dl_theme', theme.value)
}

function closeMenus() {
  showUserMenu.value = false
  showAlerts.value = false
}

function goProfile() { router.push('/profile'); closeMenus() }
function goSettings() { router.push('/settings'); closeMenus() }

function doLogout() {
  auth.logout()
  router.push('/login')
  closeMenus()
}

function doSearch() {
  if (searchQ.value.trim()) router.push(`/issues?q=${encodeURIComponent(searchQ.value.trim())}`)
}

async function doScan() {
  const url = repoUrl.value.trim()
  if (!url) return
  const fullUrl = url.startsWith('http') ? url : `https://${url}`
  try {
    const r = await fetch('/api/scan', {
      method: 'POST',
      headers: { ...auth.authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_url: fullUrl })
    })
    if (r.ok) {
      notifs.push('info', 'Scan queued', `Scanning ${url}...`)
      router.push('/')
    }
  } catch {}
}

function timeAgo(ts: number): string {
  const diff = Date.now() - ts
  const m = Math.floor(diff / 60000)
  if (m < 1) return 'just now'
  if (m < 60) return `${m}m ago`
  return `${Math.floor(m/60)}h ago`
}

const navSections = [
  {
    label: 'Overview',
    items: [
      { path: '/',            icon: '🏠', label: 'Command Center' },
      { path: '/history',     icon: '📋', label: 'Scan History' },
    ]
  },
  {
    label: 'Analysis',
    items: [
      { path: '/issues',        icon: '🐛', label: 'Issues' },
      { path: '/code-analysis', icon: '💻', label: 'Code Analyzer', badge: 'AI' },
      { path: '/fixes',         icon: '🔧', label: 'Fix Studio' },
    ]
  },
  {
    label: 'Visualize',
    items: [
      { path: '/heatmap',  icon: '🗺', label: 'Heatmap' },
      { path: '/security', icon: '🛡', label: 'Security Posture' },
      { path: '/misconfig',icon: '⚙️', label: 'Misconfig Radar' },
    ]
  },
  {
    label: 'Compliance',
    items: [
      { path: '/compliance', icon: '✅', label: 'Compliance' },
      { path: '/deps',       icon: '📦', label: 'Dependencies' },
    ]
  },
  {
    label: 'Intelligence',
    items: [
      { path: '/advisories', icon: '📡', label: 'Advisory Feed' },
      { path: '/git',        icon: '🌿', label: 'Git Intelligence' },
      { path: '/trends',     icon: '📈', label: 'Trends' },
    ]
  },
  {
    label: 'Infrastructure',
    items: [
      { path: '/infra',   icon: '🐳', label: 'Infra Posture' },
      { path: '/updates', icon: '🔄', label: 'Update Center' },
    ]
  },
  {
    label: 'System',
    items: [
      { path: '/ai',          icon: '🤖', label: 'AI Assistant' },
      { path: '/self-health', icon: '💚', label: 'Self Health' },
      { path: '/export',      icon: '⬇️', label: 'Export' },
      { path: '/profile',     icon: '👤', label: 'Profile' },
      { path: '/settings',    icon: '⚙️', label: 'Settings' },
    ]
  },
]
</script>

<style>
.slide-right-enter-active, .slide-right-leave-active { transition: transform 0.2s ease; }
.slide-right-enter-from, .slide-right-leave-to { transform: translateX(100%); }
</style>
