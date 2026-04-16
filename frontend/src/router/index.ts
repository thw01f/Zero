import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: () => import('../views/CommandCenter.vue') },
    { path: '/issues', component: () => import('../views/Issues.vue') },
    { path: '/heatmap', component: () => import('../views/Heatmap.vue') },
    { path: '/fixes', component: () => import('../views/FixStudio.vue') },
    { path: '/code-analysis', component: () => import('../views/CodeAnalysis.vue') },
    { path: '/deps', component: () => import('../views/DependencyIntel.vue') },
    { path: '/updates', component: () => import('../views/UpdateCenter.vue') },
    { path: '/misconfig', component: () => import('../views/MisconfigRadar.vue') },
    { path: '/advisories', component: () => import('../views/AdvisoryFeed.vue') },
    { path: '/security', component: () => import('../views/SecurityPosture.vue') },
    { path: '/compliance', component: () => import('../views/ComplianceDashboard.vue') },
    { path: '/git', component: () => import('../views/GitIntelligence.vue') },
    { path: '/trends', component: () => import('../views/TrendAnalysis.vue') },
    { path: '/infra', component: () => import('../views/InfraPosture.vue') },
    { path: '/ai', component: () => import('../views/AIAssistant.vue') },
    { path: '/self-health', component: () => import('../views/SelfHealth.vue') },
    { path: '/export', component: () => import('../views/ExportReports.vue') },
  ],
})

export default router
