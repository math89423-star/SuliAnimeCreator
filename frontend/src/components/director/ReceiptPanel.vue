<template>
  <div class="receipt-panel">
    <div class="rc-bar">
      <el-button size="small" @click="load" :loading="loading">刷新</el-button>
      <el-tag size="small" class="tnum">{{ segList.length }}镜可投</el-tag>
      <el-tag size="small" type="info" class="tnum">{{ projectLabel }}</el-tag>
      <el-tag size="small" type="info" class="tnum">{{ props.episodeId || '无集号' }}</el-tag>
      <el-tag size="small" type="warning">形式以回执为准（三者互斥）</el-tag>
      <span style="flex:1" />
      <el-button size="small" text @click="toggleAll">{{ allOpen ? '全部收起' : '全部展开' }}</el-button>
    </div>
    <div class="suli-muted" style="font-size:11px">首尾帧（锁构图）/ 多图参考（只锚身份）/ 文本（无图T2V）三者互斥，以lport回执单定为准；回执未定前显示组装自动判定。</div>
    <div v-if="err" class="rc-err">加载失败：{{ err }}（后端未起？）</div>
    <el-empty v-if="!loading && !segList.length" description="本集暂无可执行落地" :image-size="64" />

    <el-collapse v-else v-model="openIds" class="rc-collapse">
      <el-collapse-item v-for="s in segList" :key="s.id" :name="s.id">
        <template #title>
          <div class="rc-title">
            <b class="tnum">{{ s.id }}</b>
            <el-tag size="small" class="tnum">{{ s.duration_s }}s</el-tag>
            <el-tag size="small">{{ s.tier || '不分级' }}</el-tag>
            <el-tag size="small" type="info" class="tnum">{{ s.camera_text || '-' }}</el-tag>
            <el-tag size="small" :type="segMode(s) === 't2v' ? 'danger' : segMode(s) === 'reference' ? 'success' : 'primary'">{{ modeLabel(s) }}</el-tag>
            <el-tag size="small" :type="formSource(s) === '回执指定' ? 'success' : 'warning'">{{ formSource(s) }}</el-tag>
            <el-tag v-if="segMissing(s)" size="small" type="danger">缺首帧</el-tag>
          </div>
        </template>

        <div class="rc-body">
          <!-- 文本区 -->
          <div class="rc-block rc-text">
            <div class="rc-block-head">
              <span class="rc-block-title">文本 · seg提示词</span>
              <span style="flex:1" />
              <el-button size="small" @click="copyPrompt(s)">复制seg提示词</el-button>
            </div>
            <pre class="rc-prompt">{{ s.prompt }}</pre>
            <div class="rc-row"><span class="rc-k">声场</span><span class="rc-v">{{ s.sound || '—' }}</span></div>
            <div class="rc-row"><span class="rc-k">回执</span><span class="rc-v">{{ receiptLine(s) }}</span></div>
            <div class="rc-row"><span class="rc-k">投放</span><span class="rc-v">{{ modeDesc(s) }} · {{ s.video_model_label || 'Tsubaki Video' }} · {{ formSource(s) }}{{ s.ref_note ? ' · ' + s.ref_note : '' }}</span></div>
          </div>

          <!-- 图片区：互斥三选一 -->
          <div class="rc-block rc-imgs">
            <div class="rc-block-head"><span class="rc-block-title">图片 · {{ modeLabel(s) }}</span><span class="suli-muted" style="font-size:11px">{{ mutedNote(s) }}</span></div>
            <div v-if="segMode(s) === 't2v'" class="suli-muted rc-row">文本描述：本seg不挂图，纯文本投T2V。要切图模式请先垫图（首尾帧）或补参考（多图参考），三者只能选一。</div>
            <div v-else class="rc-slotgrid">
              <div v-for="slot in slotsOf(s)" :key="slot.key" class="rc-slot">
                <div class="rc-slot-head">
                  <b>{{ slot.label }}</b>
                  <el-tag size="small" :type="slot.imgs.length ? 'success' : 'danger'">{{ slot.imgs.length ? slot.imgs.length + '张' : '空' }}</el-tag>
                </div>
                <div v-if="slot.imgs.length" class="rc-slot-imgs">
                  <div v-for="im in slot.imgs" :key="im.tag + im.name" class="rc-imgcell">
                    <el-image
                      :src="im.url || `/api/images/${im.name}`"
                      :preview-src-list="[im.url || `/api/images/${im.name}`]"
                      fit="cover"
                      class="rc-thumb"
                      preview-teleported
                    />
                    <div class="rc-imgmeta">
                      <span class="tnum">{{ im.tag }}</span>
                      <span v-if="im.role" class="suli-muted">{{ im.role }}</span>
                    </div>
                  </div>
                </div>
                <button v-else class="rc-empty" @click="openGen(s, slot.key)">
                  <span class="rc-empty-plus">+</span>
                  <span>空 · 点击看该怎么生成</span>
                </button>
                <el-button v-if="!slot.imgs.length" size="small" text type="primary" @click="openGen(s, slot.key)">生成法</el-button>
              </div>
            </div>

            <div v-if="segMissing(s)" class="rc-pad">
              <div class="rc-row"><span class="rc-k">垫图</span><span class="rc-v">缺首帧：先垫同集图投T2V顶上，成片前到分镜页补传首帧后重组</span></div>
              <div class="rc-padgrid">
                <div v-for="p in padCandidates" :key="p.name" class="rc-imgcell">
                  <el-image :src="`/api/images/${p.name}`" :preview-src-list="[`/api/images/${p.name}`]" fit="cover" class="rc-thumb sm" preview-teleported />
                  <div class="rc-imgmeta"><span class="tnum">{{ p.label }}</span></div>
                  <el-button size="small" @click="padToFirst(s, p)">垫为本镜首帧</el-button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-collapse-item>
    </el-collapse>

    <!-- 空槽生成：直接给结果（方式+参考/垫图+可生成提示词） -->
    <el-dialog v-model="genVisible" :title="genTitle" width="560px">
      <div class="rc-gen">
        <div class="rc-row"><span class="rc-k">方式</span><span class="rc-v">{{ genMethod }}</span></div>
        <div class="rc-row"><span class="rc-k">参考</span><span class="rc-v">{{ genRefsLine }}</span></div>
        <div class="rc-padgrid">
          <div v-for="p in genPads" :key="p.name" class="rc-imgcell">
            <el-image :src="`/api/images/${p.name}`" :preview-src-list="[`/api/images/${p.name}`]" fit="cover" class="rc-thumb sm" preview-teleported />
            <div class="rc-imgmeta"><span class="tnum">{{ p.label }}</span></div>
          </div>
          <span v-if="!genPads.length" class="suli-muted" style="font-size:12px">无垫图：先到分镜页传首帧</span>
        </div>
        <pre class="rc-prompt">{{ genPrompt }}</pre>
      </div>
      <template #footer>
        <el-button size="small" @click="genVisible = false">关闭</el-button>
        <el-button size="small" type="primary" @click="copyGenReq">复制生成提示词</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { systemApi } from '../../api/system'
import { directorApi } from '../../api/director'
import { api } from '../../api/client'

const props = defineProps<{ episodeId: string; projectId?: string; projectName?: string; refreshKey?: number }>()
const receipts = ref<any[]>([])
const segs = ref<any[]>([])
const outlineImage = ref('')
const loading = ref(false)
const err = ref('')
const openIds = ref<string[]>([])

const allOpen = computed(() => segList.value.length > 0 && openIds.value.length >= segList.value.length)
const projectLabel = computed(() => {
  if (props.projectName) return props.projectName
  if (props.projectId) return props.projectId
  return '未指定项目'
})
function toggleAll() {
  openIds.value = allOpen.value ? [] : segList.value.map(s => s.id)
}

function segMode(s: any) {
  // 形式以回执为准：回执行若带 form/ref_mode 则用它，否则回退组装自动判定
  const rec = receiptOf(s)
  const f = String((rec as any)?.form || (rec as any)?.ref_mode || '').trim()
  if (f === 'reference' || f === 'startframe' || f === 't2v') return f
  return String(s?.ref_mode || (s?.missing_image ? 't2v' : 'startframe'))
}
function formSource(s: any) {
  const rec = receiptOf(s)
  const f = String((rec as any)?.form || (rec as any)?.ref_mode || '').trim()
  if (f === 'reference' || f === 'startframe' || f === 't2v') return '回执指定'
  return '回执未定·组装判定'
}
function receiptOf(s: any) {
  return receipts.value.find(r => String(r.shot_id) === String(s?.shot_id))
}
function receiptLine(s: any) {
  const r = receiptOf(s)
  if (!r) return '未登记'
  const scope = r.scope_source === 'explicit' ? '已归位' : r.scope_source === 'inferred' ? '推断归位' : '未归位'
  return `${r.package_id || '无包'} · ${r.project_id || '未归属项目'} · ${r.episode_id || props.episodeId || '未归属集号'} · ${scope}`
}
function modeLabel(s: any) {
  const m = segMode(s)
  if (m === 'reference') return '多图参考'
  if (m === 't2v') return '无图T2V'
  return '首尾帧'
}
function modeDesc(s: any) {
  const m = segMode(s)
  if (m === 'reference') return '多图参考：@image1锚身份不锁构图，其余按role carry'
  if (m === 't2v') return '无参考图：纯文本投，须先垫图'
  return '首尾帧：@image1首帧锁构图，尾帧定ending'
}
function segMissing(s: any) {
  return !!s?.missing_image || segMode(s) === 't2v' || !(s?.refs || []).length
}

const segList = computed(() => {
  const doneIds = new Set(receipts.value.filter(r => String(r.status) === 'done').map(r => String(r.shot_id)))
  return segs.value
    .filter(s => s?.shot_id && doneIds.has(String(s.shot_id)))
    .map(s => ({ id: s.shot_id, ...s }))
    .sort((a, b) => String(a.id).localeCompare(String(b.id)))
})

// 三槽互斥：首尾帧只留首帧+尾帧，多图参考只留首帧+参考，文本不留图槽
function slotsOf(s: any) {
  const refs = (s?.refs || []) as any[]
  const m = segMode(s)
  if (m === 't2v') return []
  if (m === 'reference') return [
    { key: 'first', label: '首帧（身份锚）', imgs: refs.filter(r => r?.kind === 'first') },
    { key: 'ref', label: '参考（按role）', imgs: refs.filter(r => r?.kind !== 'first') },
  ]
  return [
    { key: 'first', label: '首帧（锁构图）', imgs: refs.filter(r => r?.kind === 'first') },
    { key: 'last', label: '尾帧（定ending）', imgs: refs.filter(r => r?.kind === 'last') },
  ]
}
function mutedNote(s: any) {
  const m = segMode(s)
  if (m === 't2v') return '文本描述：不挂图，纯文本投T2V'
  if (m === 'reference') return '多图参考：与首尾帧Keyframe互斥，尾帧槽已隐藏（ending可作参考role）'
  return '首尾帧：与多图参考互斥，参考槽已隐藏'
}

const padCandidates = computed(() => {
  const seen = new Map<string, string>()
  if (outlineImage.value) seen.set(outlineImage.value, '大纲图')
  for (const s of segs.value) {
    const f = s?.first_image
    if (f && !seen.has(f)) seen.set(f, `垫·${s.shot_id}`)
  }
  return [...seen.entries()].map(([name, label]) => ({ name, label }))
})

// 空槽生成：直接给结果（方式+参考/垫图+可执行提示词），只用元数据，不复述可见层
const genVisible = ref(false)
const genShot = ref<any>(null)
const genSlot = ref('')
const genTitle = computed(() => genShot.value ? `${genShot.value.id} · 生成${slotLabel(genSlot.value)}` : '生成')
function slotLabel(k: string) {
  if (k === 'first') return '首帧'
  if (k === 'last') return '尾帧'
  return '参考图'
}
const genPads = computed(() => padCandidates.value.slice(0, 3))
const genMethod = computed(() => {
  if (!genShot.value) return ''
  if (genSlot.value === 'first') return `复用垫图直出首帧（kind=first），重组后本seg切首尾帧/Keyframe`
  if (genSlot.value === 'last') return `沿首帧收束尾帧（kind=last，role=ending），无尾帧也能投`
  return `按缺的role补参考（kind=ref），首帧+参考齐即切多图参考`
})
const genRefsLine = computed(() => {
  if (!genShot.value) return ''
  const pads = genPads.value.map(p => `${p.label}=${p.name}`).join('、') || '无垫图'
  return `垫图：${pads}`
})
const genPrompt = computed(() => {
  if (!genShot.value) return ''
  const s = genShot.value
  const pad = genPads.value[0]?.name || '(无垫图，先传首帧)'
  const cam = s.camera_text || '-'
  if (genSlot.value === 'first') return `生成 ${s.id} 首帧：复用垫图 ${pad} 直出，attach kind=first 到 ${s.id}；机位${cam} / ${s.duration_s}s / ${s.tier || '不分级'}。重组后切首尾帧，T2V解除，投Enhanced/Professional。`
  if (genSlot.value === 'last') return `生成 ${s.id} 尾帧：沿首帧同人物场景收束ending，attach kind=last role=ending 到 ${s.id}；机位${cam}。无尾帧也能投（单首帧即Keyframe）。`
  return `补 ${s.id} 参考：按缺的role（outfit/face/pose/scene/prop）各1张，attach kind=ref并填role/desc；首帧+参考齐即切多图参考（与Keyframe互斥，上限6张）。垫图 ${pad} 可暂代同要素。`
})
function openGen(s: any, slot: string) {
  genShot.value = s
  genSlot.value = slot
  genVisible.value = true
}
async function copyGenReq() {
  if (!genShot.value || !genPrompt.value) return
  try {
    await navigator.clipboard.writeText(genPrompt.value)
    ElMessage.success('生成提示词已复制，直接执行')
  } catch {
    ElMessage.error('复制失败，手动选中复制')
  }
}

async function copyPrompt(s: any) {
  if (!s?.prompt) return
  try {
    await navigator.clipboard.writeText(s.prompt)
    ElMessage.success(`已复制 ${s.id}，直接粘贴投seg`)
  } catch {
    ElMessage.error('复制失败，手动选中复制')
  }
}

async function padToFirst(s: any, p: { name: string }) {
  try {
    await api.attachShotImage(s.id, p.name, 'first')
    ElMessage.success(`已垫 ${p.name} 为 ${s.id} 首帧，重组后即首尾帧`)
    await load()
  } catch {
    ElMessage.error('垫图失败，后端未起？')
  }
}

async function load() {
  loading.value = true
  err.value = ''
  try {
    const r: any = await systemApi.receipts({
      ...(props.projectId ? { project_id: props.projectId } : {}),
      ...(props.episodeId ? { episode_id: props.episodeId } : {}),
    })
    const data = (r as any)?.data ?? r ?? []
    receipts.value = Array.isArray(data) ? data : []
  } catch (e: any) {
    err.value = e?.response?.data?.msg || e?.message || 'request failed'
    receipts.value = []
  }
  try {
    const eid = (props.episodeId || '').trim()
    if (eid) {
      const o: any = await api.getOutline(eid).catch(() => null)
      outlineImage.value = (o as any)?.data?.outline_image ?? (o as any)?.outline_image ?? ''
      const reqMode = 'startframe'
      const ex: any = await directorApi.assembleI2VAEpisode(eid, { engine: 'pixai', pixai_model: 'tsubaki-video', ref_mode: reqMode })
      const prompts = (ex as any)?.data?.prompts ?? (ex as any)?.prompts ?? []
      let camById = new Map<string, any>()
      try {
        const ls: any = await api.listShots(eid)
        const rows = (ls as any)?.data ?? ls ?? []
        if (Array.isArray(rows)) for (const r of rows) camById.set(String(r.id), r)
      } catch {}
      const next = Array.isArray(prompts) ? prompts.map((p: any) => {
        const base = camById.get(String(p.shot_id)) || {}
        const cam = base.camera || {}
        return {
          ...p,
          sound: base.sound ?? '',
          tier: p.tier || base.tier || '',
          duration_s: p.duration_s ?? base.duration_s ?? 0,
          camera_text: [cam.crop, cam.movement].filter(Boolean).join(' '),
        }
      }) : []
      segs.value = next
      const ids = next.filter((s: any) => s?.shot_id).map((s: any) => String(s.shot_id)).sort()
      if (!openIds.value.length && ids.length) openIds.value = [ids[0]]
    } else {
      segs.value = []
      outlineImage.value = ''
    }
  } catch {
    segs.value = []
  } finally {
    loading.value = false
  }
}

watch(() => [props.projectId, props.episodeId], () => { openIds.value = []; load() })
watch(() => props.refreshKey, (k) => { if (k) load() })
onMounted(() => { load() })
</script>
<style scoped>
.receipt-panel { margin-top: 10px; display: flex; flex-direction: column; gap: 8px; }
.rc-bar { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.rc-err { color: var(--el-color-danger); font-size: 12px; }
.rc-collapse { border-top: 1px solid var(--el-border-color); }
.rc-title { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.rc-body { display: flex; flex-direction: column; gap: 10px; padding: 4px 2px; }
.rc-block { border: 1px solid var(--el-border-color); border-radius: 10px; padding: 10px 12px; display: flex; flex-direction: column; gap: 8px; background: var(--el-fill-color-blank, #fff); }
.rc-text { background: var(--el-fill-color-lighter); }
.rc-block-head { display: flex; gap: 8px; align-items: center; }
.rc-block-title { font-weight: 700; font-size: 13px; }
.rc-prompt { font-size: 12px; line-height: 1.7; white-space: pre-wrap; background: #fff; border: 1px solid var(--el-border-color); border-radius: 8px; padding: 10px; margin: 0; }
.rc-row { display: flex; gap: 8px; align-items: baseline; font-size: 12px; }
.rc-k { flex: 0 0 36px; color: var(--el-text-color-secondary); }
.rc-v { flex: 1; min-width: 0; }
.rc-slotgrid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
@media (max-width: 900px) { .rc-slotgrid { grid-template-columns: 1fr; } }
.rc-slot { border: 1px solid var(--el-border-color); border-radius: 10px; padding: 8px; display: flex; flex-direction: column; gap: 8px; background: #fff; }
.rc-slot-head { display: flex; gap: 8px; align-items: center; }
.rc-slot-imgs { display: flex; gap: 8px; flex-wrap: wrap; }
.rc-imgcell { border: 1px solid var(--el-border-color); border-radius: 8px; padding: 6px; display: flex; flex-direction: column; gap: 4px; align-items: center; }
.rc-thumb { width: 110px; aspect-ratio: 3 / 4; border-radius: 8px; overflow: hidden; cursor: zoom-in; }
.rc-thumb :deep(img) { width: 100%; height: 100%; object-fit: cover; display: block; }
.rc-imgmeta { display: flex; flex-direction: column; align-items: center; font-size: 11px; }
.rc-empty { border: 1px dashed var(--el-color-danger); border-radius: 10px; min-height: 120px; display: flex; flex-direction: column; gap: 4px; align-items: center; justify-content: center; color: var(--el-color-danger); background: #fff; cursor: pointer; }
.rc-empty-plus { font-size: 22px; line-height: 1; }
.rc-pad { border-top: 1px dashed var(--el-border-color); padding-top: 8px; display: flex; flex-direction: column; gap: 8px; }
.rc-padgrid { display: flex; gap: 8px; flex-wrap: wrap; }
.rc-gen { display: flex; flex-direction: column; gap: 8px; }
.rc-gensteps { display: flex; flex-direction: column; gap: 6px; border-top: 1px solid var(--el-border-color); padding-top: 8px; }
</style>
