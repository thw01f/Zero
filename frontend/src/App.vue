<template>
  <div class="app-shell">
    <!-- Top Header Bar -->
    <header class="app-header">
      <div class="header-left">
        <button class="icon-btn" @click="sidebarOpen = !sidebarOpen" title="Toggle sidebar">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        </button>
        <div class="logo-area">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="#f26d21" stroke-width="2.2" stroke-linejoin="round"/>
          </svg>
          <span class="logo-name">DARK<span class="logo-accent">LEAD</span></span>
          <span class="logo-badge">AI</span>
        </div>
        <div class="breadcrumb">
          <span class="breadcrumb-div">/</span>
          <span class="breadcrumb-page">{{ pageTitle }}</span>
        </div>
      </div>

      <div class="header-right">
        <div class="llm-pill" :title="`Backend: ${llmBackend} | Model: ${llmModel}`">
          <span class="status-dot status-ok" style="width:6px;height:6px"></span>
          <span>{{ llmLabel }}</span>
        </div>

        <div v-if="scan.status !== 'idle'" class="scan-pill" :class="`scan-${scan.status}`">
          <span class="status-dot" :class="scanDotClass"></span>
          <span>{{ scan.status }}</span>
          <span v-if="scan.status === 'running'" class="scan-pct">{{ scan.progress }}%</span>
        </div>

        <button class="icon-btn alert-btn" @click="alertsOpen = !alertsOpen">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
          <span v-if="alertsStore.unreadCount" class="badge-dot">{{ alertsStore.unreadCount }}</span>
        </button>

        <span class="clock">{{ clock }}</span>
        <div class="avatar">DL</div>
      </div>
    </header>

    <!-- Alerts Dropdown -->
    <transition name="fade">
      <div v-if="alertsOpen" class="alerts-overlay" @click="alertsOpen = false">
        <div class="alerts-panel" @click.stop>
          <div class="alerts-head">
            <span style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:#8a96b0">Alerts</span>
            <button class="ft-btn ft-btn-ghost" style="font-size:11px;padding:3px 8px" @click="alertsStore.markAllRead()">Mark all read</button>
          </div>
          <div v-if="!alertsStore.alerts.length" style="padding:20px;text-align:center;color:#4a5568;font-size:12px">No alerts</div>
          <div v-for="a in alertsStore.alerts.slice(0,15)" :key="a.id" class="alert-row" :class="{dimmed: a.read}" @click="alertsStore.markRead(a.id)">
            <span class="status-dot" style="flex-shrink:0" :class="a.type.includes('critical') ? 'status-critical' : 'status-warn'"></span>
            <div style="flex:1;overflow:hidden">
              <div style="font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ a.type.replace(/_/g,' ') }}</div>
              <div style="color:#4a5568;font-size:10px">{{ new Date(a.timestamp).toLocaleTimeString() }}</div>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <div class="app-body">
      <!-- Sidebar -->
      <aside class="sidebar" :class="{ 'sidebar-closed': !sidebarOpen }">
        <!-- Scan Form -->
        <div class="sidebar-scan">
          <ScanForm />
        </div>

        <!-- Nav -->
        <nav class="sidebar-nav">
          <div class="nav-section">
            <div class="nav-group-hdr">Dashboard</div>
            <router-link to="/" class="nav-item" active-class="active" exact>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
              Command Center
            </router-link>
            <router-link to="/heatmap" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="4" height="4"/><rect x="10" y="3" width="4" height="4"/><rect x="17" y="3" width="4" height="4"/><rect x="3" y="10" width="4" height="4"/><rect x="10" y="10" width="4" height="4"/><rect x="17" y="10" width="4" height="4"/><rect x="3" y="17" width="4" height="4"/><rect x="10" y="17" width="4" height="4"/><rect x="17" y="17" width="4" height="4"/></svg>
              Risk Heatmap
            </router-link>
          </div>

          <div class="nav-section">
            <div class="nav-group-hdr">Code Analysis</div>
            <router-link to="/issues" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              Issue Tracker
              <span v-if="report.issues.length" class="nav-cnt">{{ report.issues.length }}</span>
            </router-link>
            <router-link to="/code-analysis" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
              Code Analyzer
              <span class="nav-new">NEW</span>
            </router-link>
            <router-link to="/fixes" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
              Fix Studio
            </router-link>
          </div>

          <div class="nav-section">
            <div class="nav-group-hdr">Security</div>
            <router-link to="/security" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              Security Posture
            </router-link>
            <router-link to="/misconfig" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/></svg>
              Misconfig Radar
            </router-link>
            <router-link to="/compliance" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
              Compliance
            </router-link>
            <router-link to="/infra" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>
              Infra Posture
            </router-link>
          </div>

          <div class="nav-section">
            <div class="nav-group-hdr">Dependencies</div>
            <router-link to="/deps" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="5" r="3"/><path d="M12 8v13M5 16H3a2 2 0 0 0-2 2v1M19 16h2a2 2 0 0 1 2 2v1"/><circle cx="5" cy="20" r="1"/><circle cx="19" cy="20" r="1"/></svg>
              Dependency Intel
            </router-link>
            <router-link to="/updates" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-.08-3.02"/></svg>
              Update Center
              <span v-if="mandatoryCount" class="nav-cnt urgent">{{ mandatoryCount }}</span>
            </router-link>
            <router-link to="/advisories" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
              Advisory Feed
            </router-link>
          </div>

          <div class="nav-section">
            <div class="nav-group-hdr">Intelligence</div>
            <router-link to="/git" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M13 6h3a2 2 0 0 1 2 2v7"/><line x1="6" y1="9" x2="6" y2="21"/></svg>
              Git Intelligence
            </router-link>
            <router-link to="/trends" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>
              Trend Analysis
            </router-link>
            <router-link to="/ai" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              AI Assistant
            </router-link>
          </div>

          <div class="nav-section">
            <div class="nav-group-hdr">Platform</div>
            <router-link to="/self-health" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
              Self Health
            </router-link>
            <router-link to="/export" class="nav-item" active-class="active">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              Export Reports
            </router-link>
          </div>
        </nav>
      </aside>

      <!-- Main -->
      <main class="app-main">
        <div v-if="scan.status === 'running'" class="scan-bar">
          <div class="scan-bar-fill" :style="{width: scan.progress + '%'}"></div>
        </div>
        <div class="content-area">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>
<script setup lang="ts">
// TODO: implement logic
</script>
