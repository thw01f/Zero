import { defineStore } from 'pinia'
import axios from 'axios'

export const useScanStore = defineStore('scan', {
  state: () => ({
    jobId: null as string | null,
    status: 'idle' as 'idle'|'queued'|'running'|'complete'|'failed',
    progress: 0,
    scannerEvents: [] as {scanner: string, count: number}[],
    currentStage: '',
    error: null as string | null,
    language: '',
  }),
  actions: {
    async submitScan(repoUrl: string, language: string, standardsDoc?: string) {
      this.status = 'queued'
      this.progress = 0
      this.scannerEvents = []
      this.error = null
      const { data } = await axios.post('/api/scan', {
        repo_url: repoUrl,
        language,
        standards_doc: standardsDoc || null,
      })
      this.jobId = data.job_id
      this.status = 'queued'
    },
    handleWsMessage(msg: any) {
      if (msg.progress !== undefined) this.progress = msg.progress
      if (msg.stage) this.currentStage = msg.stage
      if (msg.event === 'scanner_done') {
        this.scannerEvents.push({ scanner: msg.scanner, count: msg.count })
        this.status = 'running'
      }
      if (msg.event === 'complete') {
        this.status = 'complete'
        this.progress = 100
      }
      if (msg.event === 'error') {
        this.status = 'failed'
        this.error = msg.message
      }
    },
    reset() {
      this.$reset()
    }
  }
})
