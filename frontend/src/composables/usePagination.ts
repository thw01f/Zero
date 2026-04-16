
import { ref, computed } from 'vue'

export function usePagination<T>(items: T[], pageSize: number = 20) {
  const page = ref(1)
  const total = computed(() => items.length)
  const totalPages = computed(() => Math.ceil(total.value / pageSize))
  const slice = computed(() => items.slice((page.value - 1) * pageSize, page.value * pageSize))
  const hasPrev = computed(() => page.value > 1)
  const hasNext = computed(() => page.value < totalPages.value)

  function next() { if (hasNext.value) page.value++ }
  function prev() { if (hasPrev.value) page.value-- }
  function goto(n: number) { page.value = Math.max(1, Math.min(n, totalPages.value)) }

  return { page, total, totalPages, slice, hasPrev, hasNext, next, prev, goto }
}
