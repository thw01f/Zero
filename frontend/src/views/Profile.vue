<template>
  <div style="max-width:720px;margin:0 auto;">
    <h2 class="mb-6" style="font-weight:400;">My Profile</h2>

    <!-- Profile header -->
    <div class="gc-profile-header">
      <div class="gc-avatar-large" :style="{background: form.avatar_color}">{{ auth.initials }}</div>
      <div style="flex:1;">
        <div style="font-size:20px;font-weight:500;color:var(--gc-text);">{{ auth.user?.full_name || auth.user?.username }}</div>
        <div style="font-size:14px;color:var(--gc-text-2);margin-top:2px;">{{ auth.user?.email }}</div>
        <div style="font-size:12px;color:var(--gc-text-3);margin-top:4px;">@{{ auth.user?.username }} · {{ auth.user?.role }}</div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="gc-tabs mb-6">
      <div v-for="t in tabs" :key="t.id" class="gc-tab" :class="{active: tab===t.id}" @click="tab=t.id">{{ t.label }}</div>
    </div>

    <!-- Account info tab -->
    <div v-if="tab==='account'" class="gc-card">
      <div class="gc-card-header"><h3 class="gc-card-title">Account Information</h3></div>
      <div class="gc-card-body">
        <div v-if="saveMsg" class="gc-alert gc-alert-success mb-4"><span>✓</span> {{ saveMsg }}</div>
        <form @submit.prevent="saveProfile">
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
            <div class="gc-form-group">
              <label class="gc-label">Full name</label>
              <input v-model="form.full_name" class="gc-input" type="text" />
            </div>
            <div class="gc-form-group">
              <label class="gc-label">Username</label>
              <input v-model="form.username" class="gc-input" type="text" required />
            </div>
          </div>
          <div class="gc-form-group">
            <label class="gc-label">Email</label>
            <input :value="auth.user?.email" class="gc-input" type="email" disabled style="opacity:0.6;cursor:not-allowed;" />
            <span class="gc-hint">Email cannot be changed</span>
          </div>

          <div class="gc-form-group">
            <label class="gc-label">Avatar color</label>
            <div class="flex gap-2 mt-2">
              <div v-for="color in avatarColors" :key="color"
                class="gc-avatar-swatch" :class="{selected: form.avatar_color===color}"
                :style="{background:color}" @click="form.avatar_color=color" />
            </div>
          </div>

          <button type="submit" class="gc-btn gc-btn-primary" :disabled="saving">
            {{ saving ? 'Saving…' : 'Save changes' }}
          </button>
        </form>
      </div>
    </div>

    <!-- Security tab -->
    <div v-if="tab==='security'" class="gc-card">
      <div class="gc-card-header"><h3 class="gc-card-title">Change Password</h3></div>
      <div class="gc-card-body">
        <div v-if="pwdMsg" class="gc-alert" :class="pwdOk?'gc-alert-success':'gc-alert-error'" style="margin-bottom:16px;">
          {{ pwdMsg }}
        </div>
        <form @submit.prevent="changePassword" style="max-width:400px;">
          <div class="gc-form-group">
            <label class="gc-label">Current password</label>
            <input v-model="pwd.current" class="gc-input" type="password" required />
          </div>
          <div class="gc-form-group">
            <label class="gc-label">New password</label>
            <input v-model="pwd.new" class="gc-input" type="password" required />
          </div>
          <div class="gc-form-group">
            <label class="gc-label">Confirm new password</label>
            <input v-model="pwd.confirm" class="gc-input" type="password" required />
          </div>
          <button type="submit" class="gc-btn gc-btn-primary" :disabled="savingPwd">
            {{ savingPwd ? 'Updating…' : 'Update password' }}
          </button>
        </form>
      </div>
    </div>

    <!-- Activity tab -->
    <div v-if="tab==='activity'" class="gc-card">
      <div class="gc-card-header"><h3 class="gc-card-title">Activity</h3></div>
      <div class="gc-card-body">
        <div class="gc-metric-grid mb-6">
          <div class="gc-metric-tile">
            <div class="gc-metric-value">{{ stats.total_scans }}</div>
            <div class="gc-metric-label">Total Scans</div>
          </div>
          <div class="gc-metric-tile">
            <div class="gc-metric-value">{{ auth.user?.role }}</div>
            <div class="gc-metric-label">Role</div>
          </div>
          <div class="gc-metric-tile">
            <div class="gc-metric-value" style="font-size:16px;">{{ memberSince }}</div>
            <div class="gc-metric-label">Member Since</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const tab = ref('account')
const saving = ref(false)
const savingPwd = ref(false)
const saveMsg = ref('')
const pwdMsg = ref('')
const pwdOk = ref(false)
const stats = ref<{ total_scans: number; member_since?: string; role?: string }>({ total_scans: 0 })

const tabs = [
  { id: 'account', label: 'Account' },
  { id: 'security', label: 'Security' },
  { id: 'activity', label: 'Activity' },
]

const avatarColors = ['#1a73e8','#e8710a','#1e8e3e','#d93025','#a142f4','#007b83','#e52592','#12853f']

const form = ref({
  full_name: auth.user?.full_name || '',
  username: auth.user?.username || '',
  avatar_color: auth.user?.avatar_color || '#1a73e8',
})

const pwd = ref({ current: '', new: '', confirm: '' })

const memberSince = computed(() => {
  const d = stats.value.member_since
  return d ? new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'
})

onMounted(async () => {
  const r = await fetch('/api/profile/stats', { headers: auth.authHeaders() })
  if (r.ok) stats.value = await r.json()
})

async function saveProfile() {
  saving.value = true; saveMsg.value = ''
  try {
    const r = await fetch('/api/profile/', {
      method: 'PATCH',
      headers: { ...auth.authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ full_name: form.value.full_name, username: form.value.username, avatar_color: form.value.avatar_color })
    })
    const d = await r.json()
    if (!r.ok) throw new Error(d.detail)
    if (auth.user) Object.assign(auth.user, d)
    localStorage.setItem('dl_user', JSON.stringify(auth.user))
    saveMsg.value = 'Profile updated successfully'
    setTimeout(() => saveMsg.value = '', 3000)
  } catch (e) { saveMsg.value = (e as Error).message }
  saving.value = false
}

async function changePassword() {
  if (pwd.value.new !== pwd.value.confirm) { pwdMsg.value = 'Passwords do not match'; pwdOk.value = false; return }
  savingPwd.value = true; pwdMsg.value = ''
  const r = await fetch('/api/profile/change-password', {
    method: 'POST',
    headers: { ...auth.authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ current_password: pwd.value.current, new_password: pwd.value.new })
  })
  const d = await r.json()
  pwdOk.value = r.ok
  pwdMsg.value = r.ok ? 'Password updated successfully' : (d.detail || 'Failed')
  if (r.ok) { pwd.value = { current: '', new: '', confirm: '' } }
  savingPwd.value = false
}
</script>
