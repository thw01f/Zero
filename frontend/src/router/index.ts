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