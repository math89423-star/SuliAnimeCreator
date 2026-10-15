<template>
  <div class="suli-card kun-page" style="padding:14px">
    <div class="art-head">
      <h3 style="margin:0">美术工具</h3>
      <span style="flex:1" />
      <el-input v-model="kw" placeholder="搜索" clearable size="small" style="max-width:200px" />
      <el-button size="small" :loading="loading" @click="loadTools">刷新工具</el-button>
    </div>
    <div v-if="loading" class="suli-grid-3" style="margin-top:12px">
      <div v-for="i in 6" :key="i" class="skeleton" style="height:230px" />
    </div>
    <el-empty v-else-if="!tools.length" description="无工具" :image-size="72">
      <el-button type="primary" size="small" @click="loadTools">重试</el-button>
    </el-empty>
    <el-empty v-else-if="!filtered.length" description="无命中" :image-size="64" />
    <div v-else class="suli-grid-3" style="margin-top:12px">
      <div
        v-for="(t, i) in filtered" :key="t.id"
        class="slot-card suli-card tool-card enter"
        :style="{ '--d': (i % 9) * 45 + 'ms' }"
        @click="openInRef(t.id)"
      >
        <div class="slot-thumb shine tool-cover">
          <img
            v-if="shownCover(t.id).kind === 'img'"
            :src="(shownCover(t.id) as any).src" :alt="(shownCover(t.id) as any).alt" loading="lazy" class="cover-img"
            @error="coverDead[t.id] = true"
          />
          <div v-else-if="shownCover(t.id).kind === 'svg'" v-html="(shownCover(t.id) as any).svg" class="cover-svg" />
          <div v-else-if="shownCover(t.id).kind === 'strip'" class="cover-strip">
            <span v-for="h in (shownCover(t.id) as any).hexes" :key="h" :style="{ background: h }" />
          </div>
          <div v-else class="cover-specimen">
            <span class="spec-title">{{ (shownCover(t.id) as any).title }}</span>
            <span v-if="(shownCover(t.id) as any).dots" class="spec-dots">
              <i v-for="h in (shownCover(t.id) as any).dots" :key="h" :style="{ background: h }" />
            </span>
            <span class="spec-chips">
              <el-tag v-for="c in (shownCover(t.id) as any).chips" :key="c" size="small" class="mono-tag">{{ c }}</el-tag>
            </span>
          </div>
        </div>
        <div class="tool-meta">
          <b>{{ t.name }}</b>
          <span class="suli-muted">{{ t.id }}</span>
        </div>
        
        <div class="tool-foot">
          <el-button size="small" type="primary" @click.stop="openInRef(t.id)">速查打开</el-button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api } from '../api/client'
import { useAppStore } from '../stores/app'
import { coverOf, FALLBACK_COVER } from '../components/tools/covers'
const store = useAppStore()
const tools = ref<any[]>([])
const loading = ref(false)
const kw = ref('')
const coverDead = ref<Record<string, boolean>>({})
function shownCover(id: string) {
  const c = coverOf(id)
  if (c.kind === 'img' && coverDead.value[id]) return FALLBACK_COVER
  return c
}

const filtered = computed(() => {
  const k = kw.value.trim()
  if (!k) return tools.value
  return tools.value.filter(t => (t.name + t.id + (t.desc || '')).includes(k))
})

async function loadTools() {
  loading.value = true
  try { const r = await api.artTools(); tools.value = r.data }
  catch { tools.value = [] }
  finally { loading.value = false }
}
function openInRef(id: string) { store.openQuickRef(id) }
onMounted(loadTools)
</script>
<style scoped>
.art-head{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.tool-card{padding:10px;cursor:pointer;transition:transform .18s ease, box-shadow .18s ease;will-change:transform}
.tool-card:hover{box-shadow:var(--suli-shadow)}
.tool-cover{aspect-ratio:16/10;display:flex;align-items:center;justify-content:center;border-radius:12px;background:linear-gradient(135deg,var(--suli-bg-2),#fff);overflow:hidden}
.cover-svg{width:100%;height:100%}
.cover-img{width:100%;height:100%;object-fit:cover;display:block}
.cover-strip{display:flex;width:100%;height:100%}
.cover-strip span{flex:1}
.cover-specimen{display:flex;flex-direction:column;align-items:center;gap:8px;padding:8px}
.spec-title{font-size:52px;font-weight:800;line-height:1;color:var(--suli-text)}
.spec-dots{display:flex;gap:6px}
.spec-dots i{width:18px;height:18px;border-radius:50%;border:1px solid rgba(0,0,0,.12)}
.spec-chips{display:flex;gap:4px;flex-wrap:wrap;justify-content:center;max-width:100%}
.mono-tag{font-family:Consolas,monospace}
.tool-meta{margin-top:8px;display:flex;gap:6px;align-items:center}
.tool-desc{font-size:12px;margin-top:4px;min-height:38px;overflow:hidden;text-overflow:ellipsis;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.tool-foot{margin-top:8px;display:flex;justify-content:flex-end}
.enter{animation:rise .45s ease both;animation-delay:var(--d,0ms)}
@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
.shine{position:relative;overflow:hidden}
.shine::after{content:'';position:absolute;inset:0;background:linear-gradient(115deg,transparent 40%,rgba(255,255,255,.45) 50%,transparent 60%);transform:translateX(-120%);pointer-events:none}
.tool-card:hover .shine::after{animation:sheen .7s ease}
@keyframes sheen{to{transform:translateX(120%)}}
@media (prefers-reduced-motion: reduce) {
  .enter,.tool-card{animation:none !important;transition:none !important}
}
</style>
