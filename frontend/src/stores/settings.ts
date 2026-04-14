
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useSettingsStore = defineStore('settings', () => {
  const llmBackend = ref<'ollama'|'anthropic'|null>(null)
  const llmModel = ref<string|null>(null)
  const availableModels = ref<any[]>([])
  const darkMode = ref(true)
  const compactMode = ref(false)
  const sidebarCollapsed = ref(false)

  const isOllama = computed(() => llmBackend.value === 'ollama')
  const isLocal = computed(() => llmBackend.value === 'ollama')

  async function fetchModels() {
    try {
      const r = await fetch('/api/analyze/models')
      const d = await r.json()
      llmBackend.value = d.active_backend
      llmModel.value = d.active_model
      availableModels.value = d.models ?? []
    } catch (e) {
      console.error('Failed to fetch models:', e)
    }
  }

  return { llmBackend, llmModel, availableModels, darkMode, compactMode, sidebarCollapsed, isOllama, isLocal, fetchModels }
})
