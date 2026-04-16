<template>
  <div class="gc-auth-page">
    <div class="gc-auth-card">
      <div class="gc-auth-logo">
        <div class="logo-text">Dark<strong>Lead</strong></div>
        <div style="font-size:12px;color:var(--gc-text-3);margin-top:4px;">AI-Powered Code Intelligence</div>
      </div>

      <h1 class="gc-auth-title">Sign in</h1>
      <p class="gc-auth-subtitle">to continue to DarkLead</p>

      <div v-if="error" class="gc-alert gc-alert-error" style="margin-bottom:16px;">
        <span>⚠</span> {{ error }}
      </div>

      <form @submit.prevent="doLogin">
        <div class="gc-form-group">
          <label class="gc-label">Email or username</label>
          <input v-model="form.username" class="gc-input" type="text" placeholder="Enter email or username" required autocomplete="username" />
        </div>
        <div class="gc-form-group">
          <label class="gc-label">Password</label>
          <div style="position:relative;">
            <input v-model="form.password" class="gc-input" :type="showPwd ? 'text' : 'password'" placeholder="Enter password" required autocomplete="current-password" style="padding-right:44px;" />
            <button type="button" @click="showPwd=!showPwd" style="position:absolute;right:10px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;color:var(--gc-text-3);font-size:16px;">
              {{ showPwd ? '🙈' : '👁' }}
            </button>
          </div>
        </div>

        <button type="submit" class="gc-btn gc-btn-primary w-full" style="justify-content:center;height:44px;font-size:15px;" :disabled="auth.loading">
          <span v-if="auth.loading">Signing in…</span>
          <span v-else>Sign in</span>
        </button>
      </form>

      <div class="gc-auth-divider"><span>or</span></div>

      <div style="text-align:center;font-size:14px;color:var(--gc-text-2);">
        Don't have an account?
        <router-link to="/register" style="color:var(--gc-primary);font-weight:500;"> Create account</router-link>
      </div>
    </div>

    <!-- Theme toggle -->
    <button class="theme-toggle" @click="toggleTheme" style="position:fixed;top:16px;right:16px;" :title="isDark ? 'Switch to light mode' : 'Switch to dark mode'">
      {{ isDark ? '☀️' : '🌙' }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const error = ref('')
const showPwd = ref(false)
const isDark = ref(document.documentElement.getAttribute('data-theme') === 'dark')
const form = ref({ username: '', password: '' })

async function doLogin() {
  error.value = ''
  const res = await auth.login(form.value.username, form.value.password)
  if (res.ok) {
    router.push('/')
  } else {
    error.value = res.error || 'Login failed'
  }
}

function toggleTheme() {
  isDark.value = !isDark.value
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
  localStorage.setItem('dl_theme', isDark.value ? 'dark' : 'light')
}
</script>
