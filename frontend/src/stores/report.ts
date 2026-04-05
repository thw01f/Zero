import { defineStore } from 'pinia'
import axios from 'axios'

export const useReportStore = defineStore('report', {
  state: () => ({
    data: null as any,
    loading: false,
    error: null as string | null,
  }),
  getters: {
    issues: (s) => s.data?.issues ?? [],
    modules: (s) => s.data?.modules ?? [],
    misconfigs: (s) => s.data?.misconfigs ?? [],
    depUpdates: (s) => s.data?.dep_updates ?? [],
    compliance: (s) => s.data?.compliance ?? [],
    criticalIssues: (s) => (s.data?.issues ?? []).filter((i: any) => i.severity === 'critical'),
    mandatoryUpdates: (s) => (s.data?.dep_updates ?? []).filter((d: any) => d.classification === 'MANDATORY'),
  },
  actions: {