<template>
  <div
    ref="wrapRef"
    class="zoom-wrap"
    :style="{ aspectRatio: aspect }"
    @mousemove="onMove"
    @mouseenter="onEnter"
    @mouseleave="onLeave"
    @wheel.prevent="onWheel"
    @click="onOpen"
  >
    <img v-if="src" :src="src" class="zoom-img" draggable="false" alt="" @load="onImgLoad" />
    <div v-else class="zoom-empty" @click="$emit('upload')">
      <span>无图</span>
      <el-button type="primary" @click.stop="$emit('upload')">点击传图</el-button>
    </div>
    <div
      v-if="showLens && src && inContent && !viewerVisible"
      class="zoom-lens"
      :style="lensStyle"
    />
  </div>
  <teleport to="body">
    <div v-if="viewerVisible && src" class="viewer" @click="viewerVisible = false" title="点击空白处关闭">
      <img :src="src" class="viewer-img" alt="" @click.stop="viewerVisible = false" />
    </div>
  </teleport>
</template>
<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
defineEmits(['upload'])
const props = withDefaults(defineProps<{ src?: string; lensSize?: number; aspect?: string }>(), { src: '', lensSize: 150, aspect: '3/4' })
const wrapRef = ref<HTMLElement | null>(null)
const showLens = ref(false)
const viewerVisible = ref(false)
const zoom = ref(2.5)
const px = ref(0)
const py = ref(0)
const w = ref(0)
const h = ref(0)
const naturalW = ref(0)
const naturalH = ref(0)
// 容器固定 3:4 框，1:1列内居中；原图整图 contain 适配不变形不裁剪：
// 竖图→高占满、宽按比缩放（左右留白）；横图→宽占满、高按比缩放（上下留白）
function onImgLoad(e: Event) {
  const img = e.target as HTMLImageElement
  naturalW.value = img.naturalWidth || 0
  naturalH.value = img.naturalHeight || 0
}
// contain 内容区：整图等比缩进 3:4 框后的实际位置
const contentBox = computed(() => {
  if (!w.value || !h.value || !naturalW.value || !naturalH.value) {
    return { cw: w.value, ch: h.value, ox: 0, oy: 0 }
  }
  const s = Math.min(w.value / naturalW.value, h.value / naturalH.value)
  const cw = naturalW.value * s
  const ch = naturalH.value * s
  return { cw, ch, ox: (w.value - cw) / 2, oy: (h.value - ch) / 2 }
})
const inContent = computed(() => {
  const { cw, ch, ox, oy } = contentBox.value
  return px.value >= ox && px.value <= ox + cw && py.value >= oy && py.value <= oy + ch
})

function onEnter(e: MouseEvent) {
  if (!props.src) return
  showLens.value = true
  update(e)
}
function onLeave() { showLens.value = false }
function onMove(e: MouseEvent) { if (props.src) update(e) }
function onOpen() {
  if (!props.src) return
  showLens.value = false
  viewerVisible.value = true
}
function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') viewerVisible.value = false
}
onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))
function onWheel(e: WheelEvent) {
  if (!props.src) return
  const d = e.deltaY > 0 ? -0.2 : 0.2
  zoom.value = Math.min(4, Math.max(1.5, +(zoom.value + d).toFixed(1)))
  if (e.currentTarget) update(e as unknown as MouseEvent)
}
function update(e: MouseEvent) {
  const el = wrapRef.value
  if (!el) return
  const r = el.getBoundingClientRect()
  w.value = r.width
  h.value = r.height
  px.value = Math.min(Math.max(e.clientX - r.left, 0), r.width)
  py.value = Math.min(Math.max(e.clientY - r.top, 0), r.height)
}
const lensStyle = computed(() => {
  const s = props.lensSize
  const half = s / 2
  const { cw, ch, ox, oy } = contentBox.value
  const bx = -((px.value - ox) * zoom.value - half)
  const by = -((py.value - oy) * zoom.value - half)
  return {
    width: s + 'px',
    height: s + 'px',
    left: (px.value - half) + 'px',
    top: (py.value - half) + 'px',
    backgroundImage: `url("${props.src}")`,
    backgroundSize: `${Math.max(cw * zoom.value, 1)}px ${Math.max(ch * zoom.value, 1)}px`,
    backgroundPosition: `${bx}px ${by}px`,
  }
})
</script>
<style scoped>
.zoom-wrap {
  position: relative;
  width: 100%;
  aspect-ratio: 3/4;
  max-height: 620px;
  border-radius: 12px;
  overflow: hidden;
  background: linear-gradient(135deg, var(--suli-bg-2), #fff);
  border: 1.5px solid var(--suli-border);
  cursor: zoom-in;
  user-select: none;
}
.zoom-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
  display: block;
  pointer-events: none;
}
.zoom-empty {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: center;
  justify-content: center;
  color: var(--suli-text-3);
  font-size: 12px;
  cursor: pointer;
}
.zoom-lens {
  position: absolute;
  border-radius: 50%;
  border: 2px solid #fff;
  box-shadow: 0 8px 24px rgba(0,0,0,.25), 0 0 0 1px rgba(0,0,0,.12);
  pointer-events: none;
  background-repeat: no-repeat;
  background-color: #fff;
  z-index: 2;
}
.viewer {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0,0,0,0.88);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  cursor: zoom-out;
}
.viewer-img {
  max-width: 94vw;
  max-height: 94vh;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 24px 80px rgba(0,0,0,0.5);
}
</style>
