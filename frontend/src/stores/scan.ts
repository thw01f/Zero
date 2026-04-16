import { defineStore } from 'pinia'
import axios from 'axios'

export const useScanStore = defineStore('scan', {
  state: () => ({
    jobId:         null as string | null,
    status:        'idle' as 'idle'|'queued'|'running'|'complete'|'failed',
    progress:      0,
    scannerEvents: [] as {scanner: string, count: number}[],
    currentStage:  '',
    error:         null as string | null,
    language:      '',
    phase:         'raw' as 'raw'|'enriched',
  }),

  actions: {
    async submitScan(repoUrl: string, language = 'auto', standardsDoc?: string) {
      this.status        = 'queued'
      this.progress      = 0
      this.scannerEvents = []
      this.error         = null
      this.phase         = 'raw'

      const { data } = await axios.post('/api/scan', {
        repo_url:      repoUrl,
        language,
        standards_doc: standardsDoc || null,
      }, { headers: _authHeaders() })

      this.jobId  = data.job_id
      this.status = 'queued'
      this._connectWs(data.job_id)
      return data.job_id
    },

    async submitUpload(formData: FormData) {
      this.status        = 'queued'
      this.progress      = 0
      this.scannerEvents = []
      this.error         = null

      const { data } = await axios.post('/api/scan/upload', formData, {
        headers: { ..._authHeaders() },
      })
      this.jobId  = data.job_id
      this.status = 'queued'
      this._connectWs(data.job_id)
      return data.job_id
    },

    _connectWs(jobId: string) {
      const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
      const ws    = new WebSocket(`${proto}//${location.host}/api/ws/${jobId}`)

      ws.onmessage = async (e) => {
        try {
          const msg = JSON.parse(e.data)
          this.handleWsMessage(msg)

          if (msg.event === 'complete') {
            ws.close()
            // Load report immediately
            const { useReportStore } = await import('./report')
            await useReportStore().fetchReport(jobId)
          }
          if (msg.event === 'enriched') {
            // LLM enrichment done — refresh report for updated explanations/fixes
            const { useReportStore } = await import('./report')
            await useReportStore().fetchReport(jobId)
            this.phase = 'enriched'
          }
          if (msg.event === 'error') {
            ws.close()
            // Still try to load partial results
            try {
              const { useReportStore } = await import('./report')
              await useReportStore().fetchReport(jobId)
            } catch {}
          }
        } catch {}
      }

      ws.onerror = () => {
        // Fallback: poll job status every 4s until complete
        this._pollUntilDone(jobId)
      }
    },

    _pollUntilDone(jobId: string) {
      const interval = setInterval(async () => {
        try {
          const { data } = await axios.get(`/api/scan/jobs/${jobId}`, { headers: _authHeaders() })
          if (data.progress !== undefined) this.progress = data.progress
          if (data.status === 'complete') {
            clearInterval(interval)
            this.status = 'complete'
            const { useReportStore } = await import('./report')
            await useReportStore().fetchReport(jobId)
          } else if (data.status === 'failed') {
            clearInterval(interval)
            this.status = 'failed'
          }
        } catch { clearInterval(interval) }
      }, 4000)
    },

    handleWsMessage(msg: any) {
      if (msg.progress !== undefined && msg.progress >= 0) this.progress = msg.progress
      if (msg.stage) this.currentStage = msg.stage
      if (msg.event === 'scanner_done') {
        this.scannerEvents.push({ scanner: msg.scanner, count: msg.count })
        this.status = 'running'
      }
      if (msg.event === 'complete') {
        this.status   = 'complete'
        this.progress = 100
      }
      if (msg.event === 'error') {
        this.status = 'failed'
        this.error  = msg.message
      }
    },

    reset() { this.$reset() },
  },
})

function _authHeaders(): Record<string, string> {
  try {
    const raw = localStorage.getItem('dl_token')
    if (raw) return { Authorization: `Bearer ${raw}` }
  } catch {}
  return {}
}
