import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface User {
  id: string
  email: string
  username: string
  full_name: string | null
  avatar_color: string
  role: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('dl_token'))
  const user = ref<User | null>(JSON.parse(localStorage.getItem('dl_user') || 'null'))
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const initials = computed(() => {
    if (!user.value) return '?'
    const n = user.value.full_name || user.value.username
    const parts = n.trim().split(' ')
    return (parts[0][0] + (parts.length > 1 ? parts[parts.length-1][0] : (parts[0][1] || ''))).toUpperCase()
  })

  function setAuth(tok: string, u: User) {
    token.value = tok
    user.value = u
    localStorage.setItem('dl_token', tok)
    localStorage.setItem('dl_user', JSON.stringify(u))
  }

  async function login(usernameOrEmail: string, password: string) {
    loading.value = true
    try {
      const form = new FormData()
      form.append('username', usernameOrEmail)
      form.append('password', password)
      const r = await fetch('/api/auth/login', { method: 'POST', body: form })
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || 'Login failed')
      setAuth(d.access_token, d.user)
      return { ok: true }
    } catch (e) {
      return { ok: false, error: (e as Error).message }
    } finally {
      loading.value = false
    }
  }

  async function register(email: string, username: string, password: string, full_name?: string) {
    loading.value = true
    try {
      const r = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, username, password, full_name })
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || 'Registration failed')
      setAuth(d.access_token, d.user)
      return { ok: true }
    } catch (e) {
      return { ok: false, error: (e as Error).message }
    } finally {
      loading.value = false
    }
  }

  async function fetchMe() {
    if (!token.value) return
    try {
      const r = await fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${token.value}` }
      })
      if (r.ok) {
        const d = await r.json()
        user.value = d
        localStorage.setItem('dl_user', JSON.stringify(d))
      } else {
        logout()
      }
    } catch { logout() }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('dl_token')
    localStorage.removeItem('dl_user')
  }

  function authHeaders(): Record<string, string> {
    return token.value ? { 'Authorization': `Bearer ${token.value}` } : {}
  }

  return { token, user, loading, isAuthenticated, initials, login, register, logout, fetchMe, authHeaders, setAuth }
})
