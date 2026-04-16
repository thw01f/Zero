
import { defineStore } from 'pinia'
import { ref } from 'vue'

export type NotifLevel = 'info' | 'success' | 'warning' | 'error'

export interface Notification {
  id: string
  level: NotifLevel
  title: string
  message: string
  ts: number
  read: boolean
}

let _seq = 0

export const useNotificationsStore = defineStore('notifications', () => {
  const items = ref<Notification[]>([])
  const unread = ref(0)

  function push(level: NotifLevel, title: string, message: string) {
    const n: Notification = { id: `n${_seq++}`, level, title, message, ts: Date.now(), read: false }
    items.value.unshift(n)
    if (items.value.length > 50) items.value.splice(50)
    unread.value++
    return n.id
  }

  function markRead(id: string) {
    const n = items.value.find(x => x.id === id)
    if (n && !n.read) { n.read = true; unread.value = Math.max(0, unread.value - 1) }
  }

  function markAllRead() {
    items.value.forEach(n => n.read = true)
    unread.value = 0
  }

  function clear() { items.value = []; unread.value = 0 }

  return { items, unread, push, markRead, markAllRead, clear }
})
