
import { ref, watchEffect } from 'vue'

type Theme = 'fortinet-dark' | 'minimal-dark' | 'high-contrast'

const theme = ref<Theme>((localStorage.getItem('darklead-theme') as Theme) ?? 'fortinet-dark')

const THEME_VARS: Record<Theme, Record<string,string>> = {
  'fortinet-dark': {
    '--ft-bg': '#0a0e1a', '--ft-card': '#141d30', '--ft-accent': '#f26d21',
    '--ft-border': '#1e2d45', '--ft-text': '#d4dde8', '--ft-text-dim': '#8899aa',
  },
  'minimal-dark': {
    '--ft-bg': '#111', '--ft-card': '#1a1a1a', '--ft-accent': '#f26d21',
    '--ft-border': '#333', '--ft-text': '#eee', '--ft-text-dim': '#888',
  },
  'high-contrast': {
    '--ft-bg': '#000', '--ft-card': '#0d0d0d', '--ft-accent': '#ff7b00',
    '--ft-border': '#444', '--ft-text': '#fff', '--ft-text-dim': '#ccc',
  }
}

watchEffect(() => {
  const vars = THEME_VARS[theme.value]
  Object.entries(vars).forEach(([k, v]) => document.documentElement.style.setProperty(k, v))
  localStorage.setItem('darklead-theme', theme.value)
})

export function useTheme() {
  return { theme, THEME_VARS: Object.keys(THEME_VARS) as Theme[] }
}
