<template>
  <div class="suli-card kun-page director" style="padding:14px">
    <div class="dir-head">
      <h3 style="margin:0">导演 · 动画</h3>
      <el-tag size="small" class="tnum">{{ store.episodeId }}</el-tag>
      <el-tag size="small" class="tnum">{{ store.shots.length }}镜</el-tag>
      <el-tag size="small" class="tnum">{{ totalS }}s</el-tag>
      <span style="flex:1" />
      <el-button size="small" @click="refresh">刷新</el-button>
    </div>

    <!-- 单图Agent导演 -->
    <AgentDirectCard
      v-model:ask="agentAsk" v-model:total="agentTotal" v-model:tier="agentTier"
      :img="agentImg" :loading="agentLoading" :progress="agentProgress" :answer="agentAnswer"
      :outline-md="outline.md" :tier-opts="tierOpts"
      @pick="agentFileEl?.click()" @clear="agentImg = null" @stop="stopAgent"
      @outline="startAgentDirect" @draft="buildDraftShots"
    />
    <div v-if="outline.md" class="suli-card outline-card">
      <div class="outline-head"><b>方案大纲</b><span style="flex:1" /><el-button size="small" @click="buildDraftShots" :loading="agentLoading">转草案分镜</el-button></div>
      <div class="outline-main">
        <el-image v-if="outline.image" :src="`/api/images/${outline.image}`" class="outline-thumb" fit="cover" :preview-src-list="[`/api/images/${outline.image}`]" preview-teleported />
        <div class="outline-text">{{ outline.md }}</div>
      </div>
    </div>
    <input ref="agentFileEl" type="file" accept="image/*" hidden @change="onAgentFile" />

    <!-- 组装工具条：动作在左，设置在右 -->
    <div class="dir-bar">
      <div class="bar-group">
        <el-button type="primary" size="small" @click="assembleAll" :loading="vloading" :disabled="!store.shots.length">全部组装</el-button>
        <el-button size="small" @click="assembleVEp" :loading="vloading" :disabled="!store.episodeId">整集组装</el-button>
        <el-button size="small" @click="assemble8" :loading="loading8" :disabled="!store.shots.length">8-block静帧</el-button>
        <el-button size="small" type="success" @click="onBundle" :loading="bundleLoading" :disabled="!store.episodeId">交付包</el-button>
      </div>
      <span class="bar-spacer" />
      <div class="bar-group">
        <el-select v-model="globalTier" size="small" class="w-tier" placeholder="分级">
          <el-option v-for="t in tierOpts" :key="t.key" :label="t.label" :value="t.key" />
        </el-select>
        <el-select v-model="engine" size="small" class="w-engine" placeholder="引擎">
          <el-option v-for="e in engineOpts" :key="e.key" :label="e.label" :value="e.key" />
        </el-select>
        <el-select v-if="engine === 'pixai'" v-model="pixaiModel" size="small" class="w-model" placeholder="型号">
          <el-option v-for="m in pixaiModels" :key="m.key" :label="m.label" :value="m.key" />
        </el-select>
        <el-select v-if="engine === 'pixai'" v-model="refMode" size="small" class="w-ref">
          <el-option label="锁首帧" value="startframe" />
          <el-option v-if="refSupportsMulti" label="锚身份" value="reference" />
        </el-select>
      </div>
    </div>

    <el-empty v-if="!store.shots.length" description="本集暂无分镜，先去分镜页加镜" :image-size="64" />

    <!-- 逐镜卡 -->
    <div v-else class="dir-flow">
      <ShotCard
        v-for="(s, i) in store.shots" :key="s.id"
        :shot="s" :index="i" :result="vmap[s.id]" :loading="oneLoading === s.id"
        :engine="engine" :tier-label="tierLabel"
        @assemble="assembleOne" @copy="copy" @board="goBoard"
      />
    </div>
    <!-- 执行回执：折叠面板，默认收起，不占版面 -->
    <el-collapse v-model="openPanels" class="dir-collapse">
      <el-collapse-item name="receipts">
        <template #title>
          <b>执行回执</b>
          <el-tag v-if="receiptRows.length" size="small" class="tnum">{{ receiptRows.length }}</el-tag>
          <el-tag v-else size="small" type="info">空</el-tag>
        </template>
        <div class="panel-actions">
          <el-button size="small" @click="loadReceipts">刷新</el-button>
        </div>
        <el-table v-if="receiptRows.length" :data="receiptRows" size="small">
          <el-table-column prop="shot_id" label="镜" width="170" />
          <el-table-column prop="task_id" label="任务" width="170" />
          <el-table-column prop="engine" label="引擎" width="90" />
          <el-table-column prop="status" label="态" width="80" />
          <el-table-column prop="media_url" label="媒体" />
        </el-table>
        <div v-else class="suli-muted" style="font-size:13px;padding:4px 0">暂无回执</div>
      </el-collapse-item>

      <el-collapse-item v-if="list8.length" name="still8">
        <template #title>
          <b>8-block 静帧</b>
          <el-tag size="small" class="tnum">{{ list8.length }}</el-tag>
        </template>
        <div style="display:flex;flex-direction:column;gap:8px">
          <div v-for="p in list8" :key="p.shot_id" class="suli-card" style="padding:10px">
            <div style="display:flex;gap:8px;align-items:center"><b>{{ p.shot_id }}</b><span style="flex:1" /><el-button size="small" @click="copy(p.assembled_en)">复制英文</el-button></div>
            <div style="font-size:13px;margin-top:6px;white-space:pre-wrap">{{ p.assembled_en }}</div>
          </div>
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import { useAppStore } from '../stores/app'
import { useShotAssemble } from '../composables/useShotAssemble'
import { useAgentDirect } from '../composables/useAgentDirect'
import ShotCard from '../components/director/ShotCard.vue'
import AgentDirectCard from '../components/director/AgentDirectCard.vue'

const store = useAppStore()
const router = useRouter()
function goBoard() { router.push('/board') }

// 分级四档（真源在后端 /director/tiers）：'' = 按镜设置
const tierOpts = ref<{ key: string; label: string }[]>([{ key: '', label: '不分级' }])
const agentTier = ref('')
const globalTier = ref('')
// 目标引擎：默认 PixAI 视频（v4.0 系列）；h3 = MiniMax 字段格式
const engineOpts = ref<{ key: string; label: string }[]>([{ key: 'pixai', label: 'PixAI 视频' }])
const engine = ref('pixai')
const refMode = ref('startframe')
// PixAI 视频各型号能力不同（时长上限/有无音频/参考图语义），组装时透传给后端
const pixaiModels = ref<any[]>([
  { key: 'tsubaki-video', label: 'Tsubaki Video', ref: 'multi' },
  { key: 'tsubaki-video-flash', label: 'Tsubaki Video Flash', ref: 'multi' },
  { key: 'v4', label: 'V4.0 Preview / Lite', ref: 'multi' },
  { key: 'v3.2', label: 'V3.2', ref: 'startframe' },
  { key: 'v3.0', label: 'V3.0 Lite', ref: 'startframe' },
  { key: 'v2.7', label: 'V2.7 HD', ref: 'startframe' },
])
const pixaiModel = ref('tsubaki-video')
const refSupportsMulti = computed(() => (pixaiModels.value.find(m => m.key === pixaiModel.value) || {}).ref === 'multi')
function assembleParams() { return { tier: globalTier.value, engine: engine.value, ref_mode: refMode.value, pixai_model: pixaiModel.value } }
const totalS = computed(() => Math.round((store.shots || []).reduce((a: number, s: any) => a + (Number(s.duration_s) || 0), 0) * 10) / 10)

async function refresh() {
  try { const r = await api.listShots(store.episodeId); store.shots = (r as any).data } catch {}
}

// 组装域（抽到 composable，视图只剩装配）
const { vmap, vloading, oneLoading, loading8, list8, bundleLoading, receiptRows, assembleOne, assembleAll, assembleVEp: _vep, assemble8, downloadBundle, loadReceipts, copy } = useShotAssemble(
  () => store.shots, assembleParams, refresh,
)
async function assembleVEp() { await _vep(store.episodeId) }
async function onBundle() { await downloadBundle({ episode_id: store.episodeId, engine: engine.value, pixai_model: pixaiModel.value, tier: globalTier.value }) }

// 单图Agent导演域（抽到 composable，大纲 brief 留在视图）
const { agentFileEl, agentImg, agentAsk, agentTotal, agentLoading, agentProgress, agentAnswer, outline, loadOutline, onAgentFile, stopAgent, runBrief } = useAgentDirect(
  () => store.episodeId, refresh,
)
async function startAgentDirect() {
  if (!agentImg.value || agentLoading.value) return
  const brief = [
    `@data/uploads/${agentImg.value.path}`,
    `集号：${store.episodeId}`,
    '请按这张单图出方案大纲：看图写一份方案大纲markdown（含：方向一句话 / 基调与档位 / 分镜大纲表：镜号/内容一句话/预计时长/运镜方向/备注 / 合计时长），2-5镜，单镜3-8秒。然后 PUT /api/v1/scriptboard/outline/<集号> 保存 {outline_md: 全文, outline_image: 本图basename}，最后回复方向一句话+镜数+合计时长。只出大纲，不要写分镜库。',
    `总时长要求：${agentTotal.value}秒内，按此时长分配镜数与每镜秒数（优先保证单镜3-8秒）。`,
    `目标引擎：${(engineOpts.value.find(e => e.key === engine.value) || {}).label || engine.value}${engine.value === 'pixai' ? '（提示词按 PixAI 视频格式：@image1 参考行 + [0-Xs] beat + 相机动词 + Voice/SFX 行，见 skills/video/pixai-video-prompting）' : '（提示词按 MiniMax H3 字段格式，见 skills/video/h3-prompt-writing）'}。`,
    agentTier.value ? `分级档位：${tierLabel(agentTier.value)}（${agentTier.value}）。按 skills/video/nsfw-directing 的该档水位出镜：成年虚构角色锚定、微动作预算（一镜一事件、呼吸级幅度）、遮挡结构、锚点carry；duty_en 用英文写可见层动作。` : '',
    agentAsk.value.trim() ? `补充要求：${agentAsk.value.trim()}` : '',
  ].filter(Boolean).join('\n')
  await runBrief(brief, 'Agent看图出大纲中…', '大纲已存，下方查看，确认后点转草案分镜', loadOutline)
}

async function buildDraftShots() {
  if (agentLoading.value || !outline.value.md) return
  const brief = [
    `集号：${store.episodeId}`,
    '读取本集已存方案大纲（GET /api/v1/scriptboard/outline/<集号>），按大纲建草案分镜写入分镜库：',
    '每镜 create 时带 draft:true；字段照单图导演规范（duty 中文看板 / duty_en 英文可见层动作 / duration_s / sound / tier / camera）；',
    `首镜挂大纲配图为首帧（attach kind=first，大纲配图：${outline.value.image || '无'}）；`,
    '最后回复镜清单（镜id/时长/运镜/内容一句话）+合计时长。只建草案，不要改大纲。',
  ].join('\n')
  await runBrief(brief, 'Agent按大纲建草案分镜中…', '草案已写库，下方分镜已刷新，逐镜检查后点组装', refresh)
}

const openPanels = ref<string[]>([])
function tierLabel(key: string) { return (tierOpts.value.find(t => t.key === key) || {} as any).label || key }
watch(() => store.centralApplySeq, async (seq, prev) => {
  if (!seq || seq === prev) return
  const target = (store as any).centralApplyEpisode || store.episodeId
  if (target && target !== store.episodeId) store.episodeId = target
  await refresh()
  await loadOutline()
})
onMounted(async () => {
  try {
    const e = await api.directorEngines()
    const erows = ((e as any)?.data || e || []) as any[]
    if (erows.length) {
      engineOpts.value = erows.map(x => ({ key: x.key, label: x.label }))
      const px = erows.find(x => x.key === 'pixai')
      if (px && px.models?.length) pixaiModels.value = px.models
    }
  } catch {}
  try {
    const r = await api.directorTiers()
    const rows = ((r as any)?.data || r || []) as any[]
    tierOpts.value = [{ key: '', label: '不分级' }, ...rows.map(t => ({ key: t.key, label: t.label }))]
  } catch {}
  await refresh()
  await loadOutline()
  loadReceipts()
})
</script>
<style scoped>
.director.kun-page { max-width: none; margin: 0; }
.director { padding: 12px !important; }
.dir-head { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.dir-bar { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-top: 10px; padding: 8px 10px; border: 1.5px solid var(--suli-border); border-radius: var(--suli-radius-sm); background: var(--suli-surface); }
.dir-bar .bar-group { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.bar-spacer { flex: 1 1 auto; min-width: 4px; }
.dir-collapse { margin-top: 12px; border-top: 1.5px solid var(--suli-border); --el-collapse-header-bg-color: transparent; --el-collapse-content-bg-color: transparent; }
.dir-collapse :deep(.el-collapse-item__header) { height: 40px; border-bottom: none; gap: 8px; }
.dir-collapse :deep(.el-collapse-item__wrap) { border-bottom: none; }
.dir-collapse :deep(.el-collapse-item__content) { padding-bottom: 8px; }
.panel-actions { display: flex; justify-content: flex-end; margin-bottom: 6px; }
.w-tier { width: 150px; }
.w-engine { width: 240px; }
.w-model { width: 210px; }
.w-ref { width: 190px; }
.dir-flow { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(620px, 100%), 1fr)); gap: 10px; margin-top: 8px; align-items: start; }
.outline-card { margin-top: 10px; padding: 10px 12px; display: flex; flex-direction: column; gap: 8px; }
.outline-head { display: flex; gap: 8px; align-items: center; }
.outline-main { display: flex; gap: 10px; align-items: flex-start; }
.outline-thumb { width: 260px; aspect-ratio: 3 / 4; border-radius: 10px; flex-shrink: 0; cursor: zoom-in; overflow: hidden; }
.outline-thumb :deep(img) { width: 100%; height: 100%; object-fit: cover; display: block; }
.outline-text { flex: 1; min-width: 0; font-size: 13px; white-space: pre-wrap; max-height: 347px; overflow-y: auto; }
.shot-prompt { font-size: 13px; white-space: pre-wrap; background: var(--el-fill-color-lighter); border-radius: 8px; padding: 10px; }
@media (max-width: 900px) {
  .outline-thumb { width: 170px; }
  .outline-text { max-height: 240px; }
}
</style>
