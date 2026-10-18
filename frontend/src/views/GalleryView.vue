<template>
  <div class="gallery suli-card kun-page" @pointermove="onGridGlow">
    <div class="cursor-glow" :style="glowStyle" />
    <h3>展览</h3>
    <!-- 精选大卡（学 Animiz hero：最新更新的角色做特写） -->
    <div v-if="featured" class="suli-card feature">
      <el-icon class="sparkle" style="top:16px;left:30%"><Star /></el-icon>
      <el-icon class="sparkle" style="top:60px;right:24%;animation-delay:1.1s"><Star /></el-icon>
      <div class="feature-art">
        <img v-if="featured.avatar_url" :src="featured.avatar_url" />
        <span v-else class="kana">{{ featured.name.slice(0, 1) }}</span>
      </div>
      <div class="feature-body">
        <h2 class="page-title">{{ featured.name }}</h2>
        <div class="suli-muted" style="font-size:13px">{{ featured.identity || featured.hairstyle || '设定待补' }}</div>
        <div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap">
          <el-tag size="small">{{ featured.outfits }}服装</el-tag>
          <el-tag size="small" type="info">{{ featured.slots }}槽位词</el-tag>
          <el-tag size="small" type="success">v{{ featured.versions }}</el-tag>
          <el-tag size="small" type="warning">{{ rel(featured.updated_at) }}更新</el-tag>
        </div>
        <div style="margin-top:10px;display:flex;gap:8px">
          <el-button size="small" type="primary" @click="open(featured.id)">进工作台</el-button>
          <el-button size="small" @click="goNew">新建角色</el-button>
        </div>
      </div>
      <div class="hero-num tnum"><b>{{ cards.length }}</b><span class="suli-muted"> 位</span></div>
    </div>
    <!-- 分区头（学 kun Container：标题 + 查看更多） -->
    <div class="section-head">
      <h2>全部角色</h2>
      <el-button size="small" link type="primary" @click="$router.push('/character')">查看更多 ›</el-button>
      <div class="chips">
        <el-button v-for="f in filters" :key="f.k" size="small" :type="flt === f.k ? 'primary' : 'default'" @click="flt = f.k">{{ f.label }}</el-button>
      </div>
      <span style="flex:1" />
      <el-input v-model="kw" placeholder="搜索" style="max-width:220px" size="small" />
    </div>
    <div v-if="loading" class="suli-grid-3" style="margin-top:12px">
      <div v-for="i in 6" :key="i" class="skeleton" style="height:220px" />
    </div>
    <el-empty v-else-if="!cards.length && loadError" class="empty-fill" description="加载失败" :image-size="72">
      <el-button type="primary" size="small" @click="load">重试</el-button>
    </el-empty>
    <el-empty v-else-if="!cards.length" class="empty-fill" description="无角色" :image-size="72">
      <el-button type="primary" size="small" @click="goNew">去新建</el-button>
    </el-empty>
    <div v-else class="suli-grid-3 grid-glow" :style="gridGlow" style="margin-top:12px">
      <div
        v-for="(c, i) in filtered" :key="c.id"
        class="slot-card suli-card char-card tilt enter"
        :style="{ '--d': (i % 9) * 45 + 'ms' }"
        @click="open(c.id)"
        @pointermove="(e: PointerEvent) => tilt(e)"
        @pointerleave="(e: PointerEvent) => untilt(e)"
      >
        <div class="slot-thumb shine">
          <img v-if="c.avatar_url" :src="c.avatar_url" style="width:100%;height:100%;object-fit:cover;border-radius:10px" />
          <span v-else>{{ c.name.slice(0, 1) || '无' }}</span>
        </div>
        <div style="margin-top:8px;display:flex;gap:6px;align-items:center"><b>{{ c.name }}</b><span class="suli-muted">{{ c.id }}</span></div>
        <div class="suli-muted" style="font-size:12px;margin-top:4px;overflow:hidden;text-overflow:ellipsis;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical">{{ c.identity || c.hairstyle || '设定待补' }}</div>
        <div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap">
          <el-tag size="small">{{ c.outfits }}服装</el-tag>
          <el-tag size="small" type="info">{{ c.slots }}槽位词</el-tag>
          <el-tag size="small" type="success">v{{ c.versions }}</el-tag>
        </div>
        <div class="suli-muted tnum" style="font-size:11px;margin-top:6px">{{ rel(c.updated_at) }}更新</div>
      </div>
    </div>
    <div v-if="!filtered.length && cards.length" style="margin-top:12px"><el-empty description="无命中" :image-size="64" /></div>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Star } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import { useAppStore } from '../stores/app'
const store = useAppStore()
const router = useRouter()
const cards = ref<any[]>([])
const kw = ref('')
const flt = ref('all')
const loading = ref(false)
const loadError = ref(false)
const filters = [
  { k: 'all', label: '全部' },
  { k: 'avatar', label: '有形象' },
  { k: 'full', label: '设定完整' },
  { k: 'rich', label: '多服装' },
]
const featured = computed(() => cards.value[0] || null)
const filtered = computed(() => {
  let rows = cards.value
  if (flt.value === 'avatar') rows = rows.filter(c => c.avatar_url)
  if (flt.value === 'full') rows = rows.filter(c => c.hairstyle && c.face && c.physique && c.identity)
  if (flt.value === 'rich') rows = rows.filter(c => c.outfits >= 2)
  const k = kw.value.trim()
  if (k) rows = rows.filter(c => (c.name + c.identity + c.hairstyle).includes(k))
  return rows
})
function rel(ts: number) {
  if (!ts) return '未知时间'
  const s = Math.floor((Date.now() - ts) / 1000)
  if (s < 60) return '刚刚'
  if (s < 3600) return Math.floor(s / 60) + '分钟前'
  if (s < 86400) return Math.floor(s / 3600) + '小时前'
  return Math.floor(s / 86400) + '天前'
}
const glow = ref({ x: -9999, y: -9999, on: false })
const glowStyle = computed(() => ({
  transform: `translate(${glow.value.x}px, ${glow.value.y}px)`,
  opacity: glow.value.on ? 1 : 0,
}))
const gridGlow = computed(() => ({
  '--mx': glow.value.x + 'px',
  '--my': glow.value.y + 'px',
}))
function onGridGlow(e: PointerEvent) {
  glow.value = { x: e.clientX, y: e.clientY, on: true }
}
function tilt(e: PointerEvent) {
  const el = e.currentTarget as HTMLElement
  const r = el.getBoundingClientRect()
  const px = (e.clientX - r.left) / r.width - 0.5
  const py = (e.clientY - r.top) / r.height - 0.5
  el.style.transform = `perspective(700px) rotateY(${px * 8}deg) rotateX(${-py * 8}deg) translateY(-3px)`
}
function untilt(e: PointerEvent) {
  const el = e.currentTarget as HTMLElement
  el.style.transform = ''
  glow.value.on = false
}
async function load() {
  loading.value = true
  loadError.value = false
  try { const r = await api.gallery(); cards.value = r.data }
  catch { loadError.value = true; ElMessage.error('后端未起') }
  finally { loading.value = false }
}
function open(id: string) { store.selectedCharId = id; router.push('/character') }
function goNew() { store.selectedCharId = ''; router.push('/character') }
onMounted(load)
</script>
<style scoped>
.gallery{position:relative;padding:14px;min-height:100%;display:flex;flex-direction:column}
.gallery .suli-grid-3{flex:1 0 auto;align-content:start}
/* 无数据空态：在剩余空间里居中，不挂顶部 */
.gallery .empty-fill{flex:1 0 auto;display:flex;flex-direction:column;justify-content:center}
/* 与顶栏对齐：取消96rem居中限宽，铺满中央区（同其他工作页一致） */
.gallery.kun-page{max-width:none;margin:0;width:100%;box-sizing:border-box}
.section-head{display:flex;gap:10px;align-items:center;margin-top:18px;flex-wrap:wrap}
.section-head h2{font-size:20px;font-weight:800;margin:0}
.feature{padding:18px;display:flex;gap:18px;align-items:center;overflow:hidden;position:relative;background:linear-gradient(135deg,#f4f4f5,#fafafa 70%);border-width:2px}
.feature-art{width:150px;height:200px;flex:none;border-radius:12px;overflow:hidden;border:2px solid #fff;box-shadow:var(--suli-shadow);background:linear-gradient(135deg,var(--suli-bg-2),#fff);display:flex;align-items:center;justify-content:center;font-size:64px;color:var(--suli-primary)}
.feature-art img{width:100%;height:100%;object-fit:cover}
.feature-body{position:relative;z-index:1;min-width:0}
.hero-num{margin-left:auto;font-size:28px;position:relative;z-index:1}
.section-head{display:flex;gap:10px;align-items:center;margin-top:14px;flex-wrap:wrap}
.section-head b{font-size:16px}
.chips{display:flex;gap:6px;flex-wrap:wrap}
.char-card{padding:10px;cursor:pointer;transition:transform .18s ease, box-shadow .18s ease;will-change:transform}
.char-card:hover{box-shadow:var(--suli-shadow)}
.enter{animation:rise .45s ease both;animation-delay:var(--d,0ms)}
@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
.shine{position:relative;overflow:hidden}
.shine::after{content:'';position:absolute;inset:0;background:linear-gradient(115deg,transparent 40%,rgba(255,255,255,.45) 50%,transparent 60%);transform:translateX(-120%);pointer-events:none}
.char-card:hover .shine::after{animation:sheen .7s ease}
@keyframes sheen{to{transform:translateX(120%)}}
.grid-glow{position:relative}
.cursor-glow{position:fixed;top:-140px;left:-140px;width:280px;height:280px;border-radius:50%;pointer-events:none;z-index:0;background:radial-gradient(circle,rgba(0,0,0,.05),transparent 65%);transition:opacity .25s}
@media (prefers-reduced-motion: reduce) {
  .enter,.char-card{animation:none !important;transition:none !important}
  .cursor-glow{display:none}
}
</style>
