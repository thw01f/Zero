import { defineStore } from 'pinia'

export interface Alert {
  id: string
  type: string
  data: any
  timestamp: number
  read: boolean
}

export const useAlertsStore = defineStore('alerts', {
  state: () => ({
    alerts: [] as Alert[],
    connected: false,
    es: null as EventSource | null,
  }),
  getters: {
    unreadCount: (s) => s.alerts.filter(a => !a.read).length,
  },
  actions: {
    connectSSE() {
      if (this.es) return
      const es = new EventSource('/api/sse/alerts')
      es.onmessage = (e) => {
        try {
          const event = JSON.parse(e.data)
          if (event.type === 'heartbeat') return
          this.alerts.unshift({