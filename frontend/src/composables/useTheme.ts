import { ref, onMounted } from 'vue'

export type ThemeMode = 'system' | 'light' | 'dark'

const STORAGE_KEY = 'theme'

const isDark = ref(false)
const mode = ref<ThemeMode>('system')
let media: MediaQueryList | null = null

function systemPrefersDark() {
  return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
}

function apply(dark: boolean) {
  isDark.value = dark
  document.documentElement.dataset.theme = dark ? 'dark' : 'light'
}

function resolveDark(m: ThemeMode) {
  return m === 'system' ? systemPrefersDark() : m === 'dark'
}

function persist(m: ThemeMode) {
  if (m === 'system') localStorage.removeItem(STORAGE_KEY)
  else localStorage.setItem(STORAGE_KEY, m)
}

function setMode(m: ThemeMode) {
  mode.value = m
  persist(m)
  const root = document.documentElement
  root.classList.add('theme-transition')
  apply(resolveDark(m))
  window.setTimeout(() => root.classList.remove('theme-transition'), 350)
  watchSystem()
}

function watchSystem() {
  media?.removeEventListener('change', onSystemChange)
  if (mode.value === 'system' && window.matchMedia) {
    media = window.matchMedia('(prefers-color-scheme: dark)')
    media.addEventListener('change', onSystemChange)
  } else {
    media = null
  }
}

function onSystemChange(e: MediaQueryListEvent) {
  if (mode.value === 'system') apply(e.matches)
}

function toggle() {
  setMode(isDark.value ? 'light' : 'dark')
}

function init() {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved === 'dark' || saved === 'light') mode.value = saved
  else mode.value = 'system'
  apply(resolveDark(mode.value))
  watchSystem()
}

onMounted(init)

export function useTheme() {
  return { isDark, mode, setMode, toggle }
}
