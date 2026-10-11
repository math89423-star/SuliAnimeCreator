import { defineStore } from 'pinia'
import { ref } from 'vue'
export const useAppStore = defineStore('app', () => {
  const module = ref<'gallery' | 'story' | 'character' | 'scriptboard' | 'director' | 'art'>('gallery')
  const episodeId = ref('EP-DEMO01')
  const projectId = ref('')
  const projects = ref<any[]>([])
  const selectedCharId = ref('')
  const lastSavedAt = ref(0)
  function touchSaved() { lastSavedAt.value = Date.now() }
  const shots = ref<any[]>([])
  const health = ref<any>(null)
  const leftCollapsed = ref(false)
  const rightCollapsed = ref(false)
  // 全局速查本：浮窗跨路由保留；默认收起（仅📖），记住工具与几何，可关闭
  const quickRef = ref<{ open: boolean; minimized: boolean; tool: string; x: number | null; y: number | null; w: number | null; h: number | null }>(
    { open: false, minimized: false, tool: 'composition-camera', x: null, y: null, w: null, h: null })
  function openQuickRef(tool?: string) { if (tool) quickRef.value.tool = tool; quickRef.value.open = true; quickRef.value.minimized = false }
  function closeQuickRef() { quickRef.value.open = false; quickRef.value.minimized = false }
  function minimizeQuickRef() { quickRef.value.open = false; quickRef.value.minimized = true }
  function switchModule(m: any) { module.value = m }
  function toggleLeft() { leftCollapsed.value = !leftCollapsed.value }
  function toggleRight() { rightCollapsed.value = !rightCollapsed.value }
  return { module, episodeId, projectId, projects, selectedCharId, lastSavedAt, touchSaved, shots, health, leftCollapsed, rightCollapsed, switchModule, toggleLeft, toggleRight, quickRef, openQuickRef, closeQuickRef, minimizeQuickRef }
})
