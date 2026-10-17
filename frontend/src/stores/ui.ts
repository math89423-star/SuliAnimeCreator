import { defineStore } from 'pinia'
import { ref } from 'vue'
export type ModuleKey = 'gallery' | 'story' | 'character' | 'scriptboard' | 'director' | 'art' | 'settings'
/** UI域：导航 + 健康 + 左右折叠 + 全局速查浮窗 */
export const useUiStore = defineStore('ui', () => {
  const module = ref<ModuleKey>('gallery')
  const health = ref<any>(null)
  const leftCollapsed = ref(false)
  const rightCollapsed = ref(false)
  // 全局速查本：浮窗跨路由保留；默认收起（仅图标），记住工具与几何，可关闭
  const quickRef = ref<{ open: boolean; minimized: boolean; tool: string; x: number | null; y: number | null; w: number | null; h: number | null }>(
    { open: false, minimized: false, tool: 'composition-camera', x: null, y: null, w: null, h: null })
  function openQuickRef(tool?: string) { if (tool) quickRef.value.tool = tool; quickRef.value.open = true; quickRef.value.minimized = false }
  function closeQuickRef() { quickRef.value.open = false; quickRef.value.minimized = false }
  function minimizeQuickRef() { quickRef.value.open = false; quickRef.value.minimized = true }
  function switchModule(m: any) { module.value = m }
  function toggleLeft() { leftCollapsed.value = !leftCollapsed.value }
  function toggleRight() { rightCollapsed.value = !rightCollapsed.value }
  // 投流页历史包弹窗信号：顶栏按钮只发信号，弹窗状态归 TrafficView
  const trafficHistSignal = ref(0)
  function openTrafficHist() { trafficHistSignal.value++ }
  return { module, health, leftCollapsed, rightCollapsed, quickRef, openQuickRef, closeQuickRef, minimizeQuickRef, switchModule, toggleLeft, toggleRight, trafficHistSignal, openTrafficHist }
})
