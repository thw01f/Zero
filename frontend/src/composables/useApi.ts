import { ref } from 'vue'

export function useApi<T>(url: string, opts?: RequestInit) {
  const data = ref<T | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function execute(overrideUrl?: string, overrideOpts?: RequestInit) {
    loading.value = true
    error.value = null
    try {
      const r = await fetch(overrideUrl ?? url, overrideOpts ?? opts)
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      data.value = await r.json()
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, execute }
}
