import { ref, watch } from 'vue'
import type { Ref } from 'vue'

export function useLocalStorage<T>(key: string, defaultVal: T): Ref<T> {
  const stored = localStorage.getItem(key)
  const val = ref<T>(stored !== null ? JSON.parse(stored) : defaultVal) as Ref<T>
  watch(val, v => localStorage.setItem(key, JSON.stringify(v)), { deep: true })
  return val
}
