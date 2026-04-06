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
            id: crypto.randomUUID(),
            type: event.type,
            data: event.data,
            timestamp: Date.now(),
            read: false,
          })
          if (this.alerts.length > 100) this.alerts.pop()
        } catch {}
      }
      es.onopen = () => { this.connected = true }
      es.onerror = () => { this.connected = false }
      this.es = es
    },
    markRead(id: string) {
      const a = this.alerts.find(a => a.id === id)
      if (a) a.read = true
    },
    markAllRead() {
      this.alerts.forEach(a => a.read = true)
    },
    disconnect() {
      this.es?.close()
      this.es = null
      this.connected = false
    }
  }
})
