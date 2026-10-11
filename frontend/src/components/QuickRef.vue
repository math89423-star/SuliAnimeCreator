<template>
  <div v-if="store.quickRef.open" ref="panelRef" class="qr-panel" :style="panelStyle">
    <div class="qr-head" @mousedown="onDragStart">
      <span class="qr-title">📖 速查</span>
      <span class="qr-tool">{{ toolName }}</span>
      <span style="flex:1" />
      <el-button size="small" text @click="store.minimizeQuickRef()" title="收起">－</el-button>
      <el-button size="small" text @click="store.closeQuickRef()" title="关闭">×</el-button>
    </div>
    <div class="qr-chips">
      <el-button
        v-for="t in TOOL_TABS" :key="t.id" size="small" :type="t.id === store.quickRef.tool ? 'primary' : 'default'"
        :title="t.desc" @click="switchTool(t.id)">{{ t.name }}</el-button>
    </div>
    <div class="qr-body">
      <component :is="TOOL_COMPONENTS[store.quickRef.tool]" :key="store.quickRef.tool" />
    </div>
    <div class="qr-rz qr-rz-l" title="向左/右拖动缩放宽度" @mousedown="startResize($event, 'l')" />
    <div class="qr-rz qr-rz-r" title="向左/右拖动缩放宽度" @mousedown="startResize($event, 'r')" />
    <div class="qr-rz qr-rz-b" title="拖动缩放高度" @mousedown="startResize($event, 'b')" />
    <div class="qr-rz qr-rz-br" title="拖动缩放宽高" @mousedown="startResize($event, 'br')" />
    <div class="qr-rz qr-rz-bl" title="拖动缩放宽高" @mousedown="startResize($event, 'bl')" />
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAppStore } from '../stores/app'
import { TOOL_TABS, TOOL_COMPONENTS } from './tools/index'
const store = useAppStore()
const panelRef = ref<HTMLElement | null>(null)
const LS = 'suli-quickref'
const toolName = computed(() => TOOL_TABS.find(t => t.id === store.quickRef.tool)?.name || '')
function persist() {
  const q = store.quickRef
  localStorage.setItem(LS, JSON.stringify({ tool: q.tool, x: q.x, y: q.y, w: q.w, h: q.h }))
}
function switchTool(id: string) { store.quickRef.tool = id; persist() }
const panelStyle = computed(() => {
  const q = store.quickRef
  const st: any = {
    width: (q.w ?? 680) + 'px',
    height: (q.h ?? Math.min(660, Math.round(window.innerHeight * 0.72))) + 'px',
  }
  if (q.x != null && q.y != null) { st.left = q.x + 'px'; st.top = q.y + 'px' }
  else { st.right = '464px'; st.top = '90px' }
  return st
})
// 拖拽（只认头部空白区，按钮不触发）
let drag: { sx: number; sy: number; ox: number; oy: number } | null = null
function onDragStart(e: MouseEvent) {
  if ((e.target as HTMLElement).closest('button')) return
  const el = panelRef.value
  if (!el) return
  const r = el.getBoundingClientRect()
  store.quickRef.x = Math.round(r.left)
  store.quickRef.y = Math.round(r.top)
  drag = { sx: e.clientX, sy: e.clientY, ox: r.left, oy: r.top }
  window.addEventListener('mousemove', onDragMove)
  window.addEventListener('mouseup', onDragEnd, { once: true })
}
function onDragMove(e: MouseEvent) {
  if (!drag) return
  const maxX = Math.max(window.innerWidth - 120, 0)
  const maxY = Math.max(window.innerHeight - 60, 0)
  store.quickRef.x = Math.round(Math.min(Math.max(drag.ox + e.clientX - drag.sx, 0), maxX))
  store.quickRef.y = Math.round(Math.min(Math.max(drag.oy + e.clientY - drag.sy, 0), maxY))
}
function onDragEnd() {
  window.removeEventListener('mousemove', onDragMove)
  drag = null
  persist()
}
// 边缘缩放：左右边调宽（左边同时平移 x），底边调高，四角调宽高
const MIN_W = 360
const MIN_H = 280
const MAX_W = 1200
const MAX_H = 860
function clampWH(w: number, h: number): [number, number] {
  return [
    Math.round(Math.min(Math.max(w, MIN_W), Math.min(MAX_W, window.innerWidth - 16))),
    Math.round(Math.min(Math.max(h, MIN_H), Math.min(MAX_H, window.innerHeight - 16))),
  ]
}
let rz: { dir: string; sx: number; sy: number; x: number; y: number; w: number; h: number } | null = null
function startResize(e: MouseEvent, dir: string) {
  e.preventDefault()
  e.stopPropagation()
  const el = panelRef.value
  if (!el) return
  const r = el.getBoundingClientRect()
  // 无坐标时先把当前位置落盘，避免左手柄跳变
  if (store.quickRef.x == null || store.quickRef.y == null) {
    store.quickRef.x = Math.round(r.left)
    store.quickRef.y = Math.round(r.top)
  }
  store.quickRef.w = Math.round(r.width)
  store.quickRef.h = Math.round(r.height)
  rz = { dir, sx: e.clientX, sy: e.clientY, x: r.left, y: r.top, w: r.width, h: r.height }
  window.addEventListener('mousemove', onResizeMove)
  window.addEventListener('mouseup', onResizeEnd, { once: true })
}
function onResizeMove(e: MouseEvent) {
  if (!rz) return
  const dx = e.clientX - rz.sx
  const dy = e.clientY - rz.sy
  let { x, y, w, h } = rz
  if (rz.dir.includes('r')) w = rz.w + dx
  if (rz.dir.includes('l')) { w = rz.w - dx; x = rz.x + dx }
  if (rz.dir.includes('b')) h = rz.h + dy
  ;[w, h] = clampWH(w, h)
  if (rz.dir.includes('l')) {
    // 左边缩放时按实际宽度反推 x，防止最小宽度钳制后漂移
    x = Math.round(Math.min(Math.max(rz.x + rz.w - w, 0), window.innerWidth - 120))
    store.quickRef.x = x
  }
  store.quickRef.w = w
  store.quickRef.h = h
  if (y != null) store.quickRef.y = Math.round(Math.min(Math.max(y, 0), Math.max(window.innerHeight - 60, 0)))
}
function onResizeEnd() {
  window.removeEventListener('mousemove', onResizeMove)
  rz = null
  persist()
}
// 缩放结束落盘（尺寸唯一写入者是拖拽/缩放手柄，不再回读 DOM，避免回写打架）
function onUp() { persist() }
onMounted(() => {
  try {
    const s = JSON.parse(localStorage.getItem(LS) || 'null')
    if (s) {
      if (s.tool) store.quickRef.tool = s.tool
      if (typeof s.x === 'number') store.quickRef.x = s.x
      if (typeof s.y === 'number') store.quickRef.y = s.y
      if (typeof s.w === 'number' || typeof s.h === 'number') {
        // 存过的超大尺寸钳回来：工具永远是背包卡片，不铺全页
        const [cw, ch] = clampWH(
          typeof s.w === 'number' ? s.w : 680,
          typeof s.h === 'number' ? s.h : 660,
        )
        store.quickRef.w = cw
        store.quickRef.h = ch
      }
    }
  } catch {}
  store.quickRef.open = false // 默认收起
  store.quickRef.minimized = false
  window.addEventListener('mouseup', onUp)
})
onUnmounted(() => { window.removeEventListener('mouseup', onUp) })
</script>
<style scoped>
.qr-panel {
  position: fixed;
  z-index: 1900;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  background: var(--suli-surface);
  border: 1.5px solid var(--suli-border);
  border-radius: 16px;
  box-shadow: var(--suli-shadow);
  overflow: hidden;
  min-width: 360px;
  min-height: 280px;
  max-width: calc(100vw - 16px);
  max-height: calc(100vh - 16px);
}
/* 自定义边缘缩放把手：原生 resize 只有右下角，左右边拖不动 */
.qr-rz { position: absolute; z-index: 5; touch-action: none; }
.qr-rz-l, .qr-rz-r { top: 0; bottom: 0; width: 8px; cursor: ew-resize; }
.qr-rz-l { left: 0; }
.qr-rz-r { right: 0; }
.qr-rz-b { left: 8px; right: 8px; bottom: 0; height: 8px; cursor: ns-resize; }
.qr-rz-br, .qr-rz-bl { bottom: 0; width: 14px; height: 14px; }
.qr-rz-br { right: 0; cursor: nwse-resize; }
.qr-rz-bl { left: 0; cursor: nesw-resize; }
.qr-rz:hover { background: rgba(251, 114, 153, 0.25); }
.qr-head { display: flex; gap: 8px; align-items: center; padding: 6px 8px; cursor: move; border-bottom: 1px solid var(--suli-border); flex-shrink: 0; }
.qr-title { font-weight: 800; font-size: 13px; }
.qr-tool { font-size: 12px; color: var(--suli-text-2); }
.qr-chips { display: flex; gap: 6px; flex-wrap: wrap; padding: 6px 8px; border-bottom: 1px solid var(--suli-border); flex-shrink: 0; }
.qr-body { flex: 1; min-height: 0; overflow: auto; background: #fff; container-type: inline-size; }
@media (max-width: 700px) {
  .qr-panel { left: 8px !important; right: 8px !important; top: 64px !important; bottom: 8px !important; width: auto !important; height: auto !important; }
  .qr-rz { display: none; }
}
</style>
