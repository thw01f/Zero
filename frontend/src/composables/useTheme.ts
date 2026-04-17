import { ref, watchEffect } from 'vue'

type Theme = 'google-cloud-dark' | 'fortinet-dark' | 'minimal-dark' | 'high-contrast'

const theme = ref<Theme>((localStorage.getItem('darklead-theme') as Theme) ?? 'google-cloud-dark')

const THEME_VARS: Record<Theme, Record<string,string>> = {
  'google-cloud-dark': {
    '--gc-bg': '#202124', '--gc-surface': '#292a2d', '--gc-surface-2': '#35363a',
    '--gc-nav-bg': '#292a2d', '--gc-sidebar-bg': '#1e1e20', '--gc-sidebar-hover': '#35363a',
    '--gc-border': '#3c4043', '--gc-divider': '#3c4043', '--gc-primary': '#8ab4f8',
    '--gc-text': '#e8eaed', '--gc-text-2': '#9aa0a6', '--gc-text-3': '#80868b'
  },
  'fortinet-dark': {
    '--gc-bg': '#0a0e1a', '--gc-surface': '#141d30', '--gc-surface-2': '#1a2540',
    '--gc-nav-bg': '#141d30', '--gc-sidebar-bg': '#0a0e1a', '--gc-sidebar-hover': '#1a2540',
    '--gc-border': '#1e2d45', '--gc-divider': '#1e2d45', '--gc-primary': '#f26d21',
    '--gc-text': '#d4dde8', '--gc-text-2': '#8a96b0', '--gc-text-3': '#4a5568'
  },
  'minimal-dark': {
    '--gc-bg': '#111111', '--gc-surface': '#1a1a1a', '--gc-surface-2': '#242424',
    '--gc-nav-bg': '#1a1a1a', '--gc-sidebar-bg': '#111111', '--gc-sidebar-hover': '#242424',
    '--gc-border': '#333333', '--gc-divider': '#333333', '--gc-primary': '#f26d21',
    '--gc-text': '#eeeeee', '--gc-text-2': '#888888', '--gc-text-3': '#555555'
  },
  'high-contrast': {
    '--gc-bg': '#000000', '--gc-surface': '#0d0d0d', '--gc-surface-2': '#1a1a1a',
    '--gc-nav-bg': '#0d0d0d', '--gc-sidebar-bg': '#000000', '--gc-sidebar-hover': '#1a1a1a',
    '--gc-border': '#444444', '--gc-divider': '#444444', '--gc-primary': '#ff7b00',
    '--gc-text': '#ffffff', '--gc-text-2': '#cccccc', '--gc-text-3': '#999999'
  }
}

watchEffect(() => {
  const vars = THEME_VARS[theme.value]
  if (vars) {
    Object.entries(vars).forEach(([k, v]) => document.documentElement.style.setProperty(k, v))
  }
  localStorage.setItem('darklead-theme', theme.value)
})

export function useTheme() {
  return { theme, THEME_VARS: Object.keys(THEME_VARS) as Theme[] }
}
