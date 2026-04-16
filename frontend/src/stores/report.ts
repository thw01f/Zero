import { defineStore } from 'pinia'

export const useReportStore = defineStore('report', {
  state: () => ({
    data:    null as any,
    loading: false,
    error:   null as string | null,
  }),
  getters: {
    issues:         (s) => s.data?.issues         ?? [],
    modules:        (s) => s.data?.modules         ?? [],
    misconfigs:     (s) => s.data?.misconfigs       ?? [],
    depUpdates:     (s) => s.data?.dep_updates      ?? [],
    compliance:     (s) => s.data?.compliance       ?? [],
    criticalIssues: (s) => (s.data?.issues ?? []).filter((i: any) => i.severity === 'critical'),
    mandatoryUpdates:(s) => (s.data?.dep_updates ?? []).filter((d: any) => d.classification === 'MANDATORY'),
  },
  actions: {
    async fetchReport(jobId: string) {
      this.loading = true
      this.error   = null
      try {
        const token = localStorage.getItem('dl_token') || ''
        const r = await fetch(`/api/report/${jobId}`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        })
        if (r.status === 202) {
          // Still running — wait and retry once
          await new Promise(res => setTimeout(res, 3000))
          return this.fetchReport(jobId)
        }
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        this.data = await r.json()
      } catch (e: any) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },

    async acceptFix(issueId: string, accepted: boolean) {
      const token = localStorage.getItem('dl_token') || ''
      await fetch(`/api/fixes/${issueId}/accept`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body:    JSON.stringify({ accepted }),
      })
      const issue = this.issues.find((i: any) => i.id === issueId)
      if (issue) issue.fix_accepted = accepted ? 1 : -1
    },

    clear() { this.data = null; this.error = null },
  },
})
