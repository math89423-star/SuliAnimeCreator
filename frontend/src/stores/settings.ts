import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export interface SuliSettings {
  accent: string
  compact: boolean
  leftCollapsed: boolean
  rightCollapsed: boolean
  defaultEpisode: string
  outlineMode: 'lite' | 'expert'
}

const KEY = 'suli-settings-v1'

const DEFAULTS: SuliSettings = {
  accent: '#FB7299',
  compact: false,
  leftCollapsed: false,
  rightCollapsed: false,
  defaultEpisode: 'EP-DEMO01',
  outlineMode: 'lite',
}

function load(): SuliSettings {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return { ...DEFAULTS }
    return { ...DEFAULTS, ...JSON.parse(raw) }
  } catch {
    return { ...DEFAULTS }
  }
}

export const ACCENT_PRESETS = [
  { label: '樱粉', value: '#FB7299' },
  { label: '晴蓝', value: '#23ADE5' },
  { label: '抹茶', value: '#3EC97F' },
  { label: '蜜橙', value: '#FF9F43' },
  { label: '墨紫', value: '#7C6FF0' },
]

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<SuliSettings>(load())

  function apply() {
    const el = document.documentElement
    el.style.setProperty('--suli-primary', settings.value.accent)
    el.style.setProperty('--el-color-primary', settings.value.accent)
    el.classList.toggle('suli-compact', settings.value.compact)
  }

  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(settings.value)) } catch {}
    apply()
  }

  function reset() {
    settings.value = { ...DEFAULTS }
    save()
  }

  watch(settings, save, { deep: true })

  return { settings, save, reset, apply }
})
