<template>
  <div class="gc-auth-page">
    <div class="gc-auth-card">
      <div class="gc-auth-logo">
        <div class="logo-text">Dark<strong>Lead</strong></div>
      </div>
      <h1 class="gc-auth-title">Create account</h1>
      <p class="gc-auth-subtitle">to get started with DarkLead</p>

      <div v-if="error" class="gc-alert gc-alert-error">
        <span>⚠</span> {{ error }}
      </div>

      <form @submit.prevent="doRegister">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
          <div class="gc-form-group" style="margin-bottom:0;">
            <label class="gc-label">First name</label>
            <input v-model="form.full_name" class="gc-input" type="text" placeholder="John" />
          </div>
          <div class="gc-form-group" style="margin-bottom:0;">
            <label class="gc-label">Username</label>
            <input v-model="form.username" class="gc-input" type="text" placeholder="johndoe" required />
          </div>
        </div>
        <div class="gc-form-group mt-4">
          <label class="gc-label">Email</label>
          <input v-model="form.email" class="gc-input" type="email" placeholder="john@example.com" required />
        </div>
        <div class="gc-form-group">
          <label class="gc-label">Password</label>
          <input v-model="form.password" class="gc-input" type="password" placeholder="Min 6 characters" required />
        </div>

        <button type="submit" class="gc-btn gc-btn-primary w-full" style="justify-content:center;height:44px;font-size:15px;" :disabled="auth.loading">
          {{ auth.loading ? 'Creating account…' : 'Create account' }}
        </button>
      </form>

      <div class="gc-auth-divider"><span>or</span></div>
      <div style="text-align:center;font-size:14px;color:var(--gc-text-2);">
        Already have an account?
        <router-link to="/login" style="color:var(--gc-primary);font-weight:500;"> Sign in</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const error = ref('')
const form = ref({ email: '', username: '', password: '', full_name: '' })

async function doRegister() {
  error.value = ''
  const res = await auth.register(form.value.email, form.value.username, form.value.password, form.value.full_name || undefined)
  if (res.ok) router.push('/')
  else error.value = res.error || 'Registration failed'
}
</script>
