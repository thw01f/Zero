
import { defineStore } from 'pinia'
import { ref } from 'vue'

interface ScanJob {
  job_id: string
  repo_url: string
  grade: string | null
  debt_score: number | null
  issue_count: number
  status: string
  created_at: string
}

export const useHistoryStore = defineStore('history', () => {
  const jobs = ref<ScanJob[]>([])
  const loading = ref(false)
  const lastFetch = ref<number>(0)

  async function fetchJobs(force = false) {
    if (!force && Date.now() - lastFetch.value < 30_000) return
    loading.value = true
    try {
      const r = await fetch('/api/scan/jobs')
      const d = await r.json()
      jobs.value = d.jobs ?? d
      lastFetch.value = Date.now()
    } finally {
      loading.value = false
    }
  }

  function getJob(id: string) {
    return jobs.value.find(j => j.job_id === id)
  }

  return { jobs, loading, fetchJobs, getJob }
})
