<template>
  <div class="suli-card kun-page board-page">
    <h3 class="script-title">{{ store.episodeId }} 故事剧本</h3>
    <el-input v-model="script" type="textarea" :rows="8" />
    <div style="margin-top:8px;display:flex;gap:8px;align-items:center;flex-wrap:wrap">
      <el-button @click="() => save()">保存剧本</el-button>
      <el-button type="primary" @click="genOutlineByMode" :loading="agentLoading">生成</el-button>
      <el-button v-if="agentLoading" size="small" @click="agentAborter?.abort()">停止</el-button>
      <span v-if="agentProgress" class="suli-muted" style="font-size:12px">{{ agentProgress }}</span>
      <span class="save-state tnum">{{ saveStateText }}</span>

      <el-button type="primary" @click="addShot" :disabled="!canAdd">添加新镜</el-button>
      <el-button size="small" type="warning" @click="doReview">审查</el-button>
      <el-button size="small" type="danger" plain @click="clearWorkspace">清空</el-button>
      <span v-if="qaMsg" class="suli-muted" style="font-size:12px">{{ qaMsg }}</span>
      <span style="flex:1" />
      <el-tag size="small" class="tnum">{{ stat.shots }}镜</el-tag>
      <el-tag size="small" class="tnum">{{ stat.total_s }}s</el-tag>
      <el-tag size="small" :type="stat.verdict === 'PASS' ? 'success' : stat.verdict === 'BLOCK' ? 'danger' : stat.verdict === 'REVISE' ? 'warning' : 'info'">{{ stat.verdict }}</el-tag>
    </div>
    <div v-if="loading && !rows.length" class="shot-flow">
      <div v-for="i in 3" :key="i" class="suli-card" style="padding:14px"><div class="skeleton" style="height:20px;width:40%" /><div class="skeleton" style="height:14px;margin-top:8px" /><div class="skeleton" style="height:60px;margin-top:8px" /></div>
    </div>
    <el-empty v-else-if="!rows.length" class="empty-fill" description="暂无分镜" :image-size="64" />
    <div v-else class="seg-table">
      <div class="seg-row seg-head">
        <div class="c-check"><el-checkbox v-model="allChecked" /></div>
        <div class="c-outline">大纲</div>
        <div class="c-desc">分镜描述</div>
        <div class="c-clip">已拍摄片段</div>
        <div class="c-line">台词文案</div>
        <div class="c-note">备注</div>
      </div>
      <div v-for="(r, i) in rows" :key="r.id" class="seg-row seg-body">
        <div class="c-check">
          <el-checkbox :model-value="selected.includes(r.id)" @change="() => toggleOne(r.id)" />
          <span class="seg-no tnum">{{ String(i + 1).padStart(2, '0') }}</span>
          <span class="seg-move">
            <el-button link size="small" @click="move(i, -1)" :disabled="i === 0">↑</el-button>
            <el-button link size="small" @click="move(i, 1)" :disabled="i === rows.length - 1">↓</el-button>
          </span>
        </div>
        <div class="c-outline">
          <div class="seg-label">seg{{ i + 1 }}</div>
          <div class="seg-meta tnum">{{ r.camera?.movement || '固定' }} · {{ r.duration_s }}s</div>
          <div class="seg-tags">
            <el-tag v-if="r.draft" size="small" type="warning">草案</el-tag>
            <el-tag v-if="r.tier" size="small" :type="r.tier === 'nsfw' ? 'danger' : 'info'">{{ r.tier }}</el-tag>
            <el-tag v-if="r.water_level" size="small" type="danger" effect="plain">{{ WATER_LABEL[r.water_level] || r.water_level }}</el-tag>
          </div>
          <el-select v-model="r.gen_mode" size="small" class="seg-gen" placeholder="生成方式" @change="saveRow(r, true)">
            <el-option v-for="g in genModeOpts" :key="g.key" :label="g.label" :value="g.key" />
          </el-select>
          <div class="seg-id">{{ r.id }}</div>
          <el-popconfirm title="删掉该镜？" confirm-button-text="删" cancel-button-text="留" @confirm="removeShot(r.id)">
            <template #reference><el-button link type="danger" size="small">删</el-button></template>
          </el-popconfirm>
        </div>
        <div class="c-desc">
          <el-input v-model="r.duty" type="textarea" :rows="4" resize="none" placeholder="内容" @blur="saveRow(r)" />
          <el-input v-model="r.duty_en" type="textarea" :rows="4" resize="none" placeholder="英文正文" @blur="saveRow(r)" />
        </div>
        <div class="c-clip">
          <div v-if="uploading[r.id]" class="clip-loading">转码中…</div>
          <el-image
            v-else-if="shotByKind(r, 'first') && shotByKind(r, 'first').exists !== false"
            :src="imgUrl(shotByKind(r, 'first').name)"
            :preview-src-list="[imgUrl(shotByKind(r, 'first').name)]"
            fit="cover" class="clip-thumb" preview-teleported
            @error="shotByKind(r, 'first').exists = false"
          />
          <div v-else-if="shotByKind(r, 'first')" class="clip-missing">
            <el-icon><WarningFilled /></el-icon><span>待生成</span>
          </div>
          <button v-else class="clip-add" @click="pickShotFile(r, 'first')"><span class="clip-plus">+</span><span>添加拍摄片段</span></button>
          <el-button v-if="shotByKind(r, 'first') && !uploading[r.id]" link type="danger" size="small" @click="delShotImg(r, shotByKind(r, 'first').name)">删</el-button>
        </div>
        <div class="c-line">
          <el-input v-model="r.sound" type="textarea" :rows="4" resize="none" placeholder="台词" @blur="saveRow(r)" />
        </div>
        <div class="c-note">
          <el-input v-model="r.note" type="textarea" :rows="4" resize="none" placeholder="内容" @blur="saveRow(r)" />
        </div>
        <input :ref="(el: any) => { if (el) shotRefs[r.id] = el }" type="file" accept="image/*" hidden @change="(e: any) => onShotImg(r, e)" />
      </div>
    </div>
    <div class="seg-foot">
      <el-input-number v-model="addCount" size="small" :min="1" :max="10" :step="1" />
      <el-button class="seg-add" type="primary" @click="addRows">+ 添加 {{ addCount }} 行</el-button>
      <el-button v-if="selected.length" size="small" type="danger" @click="delSelected">删除所选({{ selected.length }})</el-button>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { WarningFilled } from '@element-plus/icons-vue'
import { api } from '../api/client'
import { useAppStore } from '../stores/app'
import { useSettingsStore } from '../stores/settings'
import { castNames, loadCastInput } from '../utils/cast'
import { purgeLegacySeeds } from '../utils/legacySeeds'
const store = useAppStore()
const WATER_LABEL: Record<string, string> = { tease: '暗示', undress: '半露', explicit: '直白', closeup: '特写' }
// 生成方式：意图由本页定，能力校验在组装层（型号不支持就降级并回报）
const genModeOpts = ref<{ key: string; label: string }[]>([
  { key: '', label: '自动' }, { key: 't2v', label: '纯文本' },
  { key: 'i2v-first', label: '首帧' }, { key: 'i2v-first-last', label: '首尾帧' },
  { key: 'multi-ref', label: '多图参考' },
])
const settings = useSettingsStore()
// 剧本底稿：空着等生成/手写。旧演示样稿（含固定人名那两句）不再预填，
// 老浏览器里残留的同一份样稿也清掉，免得 debounce 自动保存把它写进库里。
purgeLegacySeeds()
const script = ref('')
const rows = computed(() => store.shots)
const crops = [
  { label: '大特写', value: 'extreme_close' }, { label: '特写', value: 'closeup' },
  { label: '近景', value: 'close' }, { label: '中近景', value: 'medium_close' },
  { label: '中景', value: 'medium' }, { label: '中全景', value: 'medium_full' },
  { label: '全景', value: 'full' }, { label: '远景', value: 'wide' },
  { label: '大远景', value: 'extreme_wide' },
]
const tierOpts = ref<{ key: string; label: string }[]>([{ key: '', label: '不分级' }])
const draft = ref({ crop: 'medium', movement: '固定', duty: '', sound: '', duration: 3 })
const shotRefs = ref<Record<string, HTMLInputElement>>({})
const shotKind = ref<Record<string, string>>({})
function imgUrl(name: string) { return `/api/images/${name}` }
function shotImgs(r: any): any[] {
  if (!r) return []
  if (r.images && r.images.length) return r.images
  if (r.image) return [{ name: r.image, kind: 'ref' }]
  return []
}
function shotByKind(r: any, kind: string) { return shotImgs(r).find(x => x.kind === kind) }
function shotRefImgs(r: any) { return shotImgs(r).filter(x => !x.kind || x.kind === 'ref') }
function shortId(id: string) { const p = String(id || '').split('-'); return p.length > 1 ? p[p.length - 1] : String(id || '') }
const movements = ['固定', '推', '拉', '摇', '移', '跟', '环绕', '升降', '手持', '航拍']
const canAdd = computed(() => draft.value.duty.trim() !== '' || draft.value.sound.trim() !== '')
const savedScript = ref('')
const scriptDirty = computed(() => script.value !== savedScript.value)
const savedAt = ref('')
const saveStateText = computed(() => saving.value ? '保存中…' : (scriptDirty.value ? '未存*' : (savedAt.value ? '已保存' + savedAt.value : '')))
let suspendScriptWatch = false
let scriptTimer: any = null
const loading = ref(false)
const saving = ref(false)
async function save(silent = false, force = false) {
  saving.value = true
  try {
    // 出镜角色留空：后端按「本集已记 cast → 手工点名 → 正文说话人」取角，存稿时顺手记住
    // force 只在「清空工作区」走：空内容默认被后端护栏拒（防自动保存把稿冲空），清空必须显式声明
    await api.saveScreenplay(store.episodeId, script.value, force ? { force: true } : {})
    savedScript.value = script.value
    const d = new Date()
    savedAt.value = String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0')
    if (!silent) ElMessage.success('已保存')
  } catch { if (!silent) ElMessage.error('保存失败，后端未起？') }
  finally { saving.value = false }
}
watch(script, () => {
  if (suspendScriptWatch) return
  clearTimeout(scriptTimer)
  scriptTimer = setTimeout(() => save(true), 3000)
})
async function loadScript() {
  suspendScriptWatch = true
  try {
    const r = await api.getScreenplay(store.episodeId)
    script.value = ((r as any).data?.screenplay_md ?? script.value) as string
    savedScript.value = script.value
    const _d = new Date()
    savedAt.value = String(_d.getHours()).padStart(2, '0') + ':' + String(_d.getMinutes()).padStart(2, '0')
  } catch {} finally { suspendScriptWatch = false }
}
async function loadShots() { loading.value = true; try { const r = await api.listShots(store.episodeId); store.shots = r.data; selected.value = selected.value.filter(id => (store.shots as any[]).some(s => s.id === id)); await loadStat() } finally { loading.value = false } }
const stat = ref<any>({ verdict: 'draft', shots: 0, total_s: 0 })
async function loadStat() { try { const r = await api.reviewStat(store.episodeId); stat.value = r.data } catch {} }
async function addShot() {
  if (!canAdd.value) return ElMessage.warning('先写职责或台词')
  await api.createShot({ episode_id: store.episodeId, duty: draft.value.duty.trim(), sound: draft.value.sound.trim(), duration_s: draft.value.duration, camera: { crop: draft.value.crop, movement: draft.value.movement } })
  draft.value = { crop: 'medium', movement: '固定', duty: '', sound: '', duration: 3 }
  ElMessage.success('已加一镜')
  await loadShots()
}
async function saveRow(r: any, silent = false) {
  await api.updateShot(r.id, { duty: r.duty, duty_en: r.duty_en || '', duration_s: r.duration_s, sound: r.sound, note: r.note || '', tier: r.tier || '', gen_mode: r.gen_mode || '', camera: { crop: r.camera?.crop || 'medium', movement: r.camera?.movement || '固定' } })
  if (!silent) ElMessage.success('已保存')
  await loadStat()
}
// 剪映式表格：选择 + 批量加行 + 上传态
const selected = ref<string[]>([])
const addCount = ref(3)
const uploading = ref<Record<string, boolean>>({})
const allChecked = computed({
  get: () => rows.value.length > 0 && selected.value.length === rows.value.length,
  set: (v: boolean) => { selected.value = v ? (rows.value as any[]).map(r => r.id) : [] },
})
function toggleOne(id: string) {
  selected.value = selected.value.includes(id) ? selected.value.filter(x => x !== id) : [...selected.value, id]
}
async function addRows() {
  const n = Math.max(1, Math.min(10, Number(addCount.value) || 3))
  for (let k = 0; k < n; k++) {
    await api.createShot({ episode_id: store.episodeId, duty: '', sound: '', duration_s: 3, camera: { crop: 'medium', movement: '固定' } })
  }
  ElMessage.success(`已添加 ${n} 行`)
  await loadShots()
}
async function delSelected() {
  const n = selected.value.length
  for (const id of [...selected.value]) await api.deleteShot(id)
  selected.value = []
  ElMessage.success(`已删 ${n} 行`)
  await loadShots()
}
// 生成大纲：复用右侧工作区 Agent（episode 会话），图用本集现成首帧；结果存大纲，去导演页看
const agentLoading = ref(false)
const agentProgress = ref('')
const agentAborter = ref<AbortController | null>(null)
function episodeFirstImage(): string {
  for (const r of rows.value as any[]) {
    const imgs = shotImgs(r)
    const hit = imgs.find(x => x.kind === 'first') || imgs[0]
    if (hit?.name) return hit.name
  }
  return ''
}
async function genOutlineByMode() {
  if (settings.settings.outlineMode === 'expert') return genOutlineExpert()
  return genOutline()
}
async function genOutline() {
  // 轻链默认：不走 dsh，直接调 outline/generate 落盘
  if (agentLoading.value) return
  const img = episodeFirstImage()
  agentLoading.value = true
  agentProgress.value = '轻大纲生成中…'
  try {
    await save(true)
    const r = await api.outlineGenerate(store.episodeId, {
      total_s: stat.value.total_s || 15,
      engine: 'pixai',
      hint: script.value.slice(0, 800),
      image: img,
      cast: castNames(loadCastInput()),  // 故事页点名；空数组=没点名，后端按「本集已记 → 正文说话人 → 角色库」取角
    })
    const eng = (r as any)?.data?.engine || (r as any)?.engine || 'template'
    agentProgress.value = ''
    ElMessage.success(`大纲已存（轻·${eng}），去导演页·大纲页签查看`)
  } catch { ElMessage.error('轻大纲失败，后端未起？') }
  finally { agentLoading.value = false; agentProgress.value = '' }
}
async function genOutlineExpert() {
  if (agentLoading.value) return
  const img = episodeFirstImage()
  if (!img) return ElMessage.warning('本集还没有配图，先给分镜传一张首帧/参考图')
  agentLoading.value = true
  agentProgress.value = '建会话…'
  try { await api.dshEnsure('episode', store.episodeId) }
  catch { ElMessage.error('Agent会话建失败，后端未起？'); agentLoading.value = false; return }
  const total = stat.value.total_s || 15
  const brief = [
    `@data/uploads/${img}`,
    `集号：${store.episodeId}`,
    '请按这张单图出方案大纲：看图写一份方案大纲markdown（含：方向一句话 / 基调与档位 / 分镜大纲表：镜号/内容一句话/预计时长/运镜方向/生成方式/备注（生成方式填 t2v / i2v-first / i2v-first-last / multi-ref） / 合计时长），2-5镜，单镜3-8秒。然后 PUT /api/v1/scriptboard/outline/<集号> 保存 {outline_md: 全文, outline_image: 本图basename}，最后回复方向一句话+镜数+合计时长。只出大纲，不要写分镜库。',
    `总时长要求：${total}秒内，按此时长分配镜数与每镜秒数（优先保证单镜3-8秒）。`,
    '目标引擎：PixAI 视频（提示词按 PixAI 视频格式：@image1 参考行 + [0-Xs] beat + 相机动词 + Voice/SFX 行，见 skills/video/pixai-video-prompting）。',
  ].join('\n')
  agentProgress.value = 'Agent看图出大纲中…'
  const ac = new AbortController()
  agentAborter.value = ac
  try {
    let done: any = null
    let errMsg = ''
    await api.dshRunStream(
      { scope: 'episode', key: store.episodeId, message: brief },
      (ev, d) => {
        if (ev === 'dsh') agentProgress.value = `Agent出大纲中…事件 ${d.n || ''}`
        else if (ev === 'retry') agentProgress.value = '检测到拒答，自动重试中…'
        else if (ev === 'done') done = d
        else if (ev === 'error') errMsg = (d as any).msg || '调用失败'
      },
      ac.signal,
    )
    if (done) {
      agentProgress.value = ''
      ElMessage.success('大纲已存，去导演页·大纲页签查看')
    } else {
      agentProgress.value = ''
      ElMessage.error('[失败] ' + (errMsg || '流中断'))
    }
  } finally {
    agentLoading.value = false
    agentAborter.value = null
  }
}
const qaMsg = ref('')
async function doReview() {
  try {
    await save(true)
    const r: any = await api.reviewRun(store.episodeId)
    const d = r?.data ?? r
    await loadStat()
    const f = (d?.findings || []) as any[]
    qaMsg.value = `${d?.verdict ?? ''} ${f.length}项` + (f[0] ? '：' + f[0].fix : '')
    ElMessage[d?.verdict === 'BLOCK' ? 'error' : d?.verdict === 'REVISE' ? 'warning' : 'success'](qaMsg.value || '审查完成')
  } catch { ElMessage.error('审查失败') }
}
async function move(i: number, dir: number) {
  const a = rows.value[i]
  const b = rows.value[i + dir]
  if (!a || !b) return
  const t = a.ord ?? i
  await api.updateShot(a.id, { ord: b.ord ?? (i + dir) })
  await api.updateShot(b.id, { ord: t })
  await loadShots()
}
async function removeShot(id: string) { await api.deleteShot(id); ElMessage.success('已删'); await loadShots() }
// 清空工作区：剧本清掉 + 本集全部分镜行逐个删（后端无批量口径），二次确认
async function clearWorkspace() {
  if (!rows.value.length && !script.value.trim()) return ElMessage.info('工作区已空')
  try {
    await ElMessageBox.confirm(`清空当前集 ${store.episodeId} 的剧本与全部 ${rows.value.length} 镜？不可恢复。`, '清空工作区', { type: 'warning', confirmButtonText: '清空', cancelButtonText: '取消' })
  } catch { return }
  for (const r of [...rows.value] as any[]) { try { await api.deleteShot(r.id) } catch {} }
  selected.value = []
  // 先把 3s 自动保存的定时器掐掉：否则它会在清空之后拿着旧稿再 PUT 一次，把刚清掉的稿写回来
  clearTimeout(scriptTimer)
  script.value = ''
  savedScript.value = ''
  await save(true, true)   // force：空内容必须显式声明，否则后端护栏会拒（2026-10-16 事故）
  await loadShots()
  ElMessage.success('工作区已清空')
}
async function onShotImg(r: any, e: any) {
  const f = e.target.files?.[0]
  e.target.value = ''
  if (!f) return
  const kind = shotKind.value[r.id] || 'ref'
  uploading.value[r.id] = true
  try {
    await api.uploadShotImage(r.id, f, kind)
    ElMessage.success(kind === 'ref' ? '参考图已上传' : (kind === 'first' ? '首帧已上传' : '尾帧已上传'))
  } finally {
    uploading.value[r.id] = false
  }
  await loadShots()
}
function pickShotFile(r: any, kind: string) { shotKind.value[r.id] = kind; shotRefs.value[r.id]?.click() }
async function delShotImg(r: any, name: string) { await api.deleteShotImage(r.id, name); ElMessage.success('已删'); await loadShots() }
watch(() => (store as any).centralApplySeq, async (seq: number, prev: number) => {
  if (!seq || seq === prev) return
  const target = (store as any).centralApplyEpisode || store.episodeId
  if (target && target !== store.episodeId) store.episodeId = target
  await loadScript()
  await loadShots()
})
onMounted(async () => {
  try {
    const r = await api.directorTiers()
    const rows = (r?.data || r || []) as any[]
    tierOpts.value = [{ key: '', label: '不分级' }, ...rows.map(t => ({ key: t.key, label: t.label }))]
  } catch {}
  try {
    const g = await api.genModes()
    const rows = (g?.data || g || []) as any[]
    if (rows.length) genModeOpts.value = [{ key: '', label: '自动' }, ...rows.map(x => ({ key: x.key, label: x.label }))]
  } catch {}
  await loadScript()
  await loadShots()
})
</script>
<style scoped>
.kun-page{max-width:none;margin:0;width:100%;box-sizing:border-box}
.board-page{min-height:100%;display:flex;flex-direction:column;padding:14px}
/* 无数据空态：在剩余空间里居中，不挂顶部 */
.board-page .empty-fill{flex:1 0 auto;display:flex;flex-direction:column;justify-content:center}
.shot-flow { display: flex; flex-direction: column; gap: 12px; margin-top: 10px; }
.shot-card { padding: 14px; display: flex; flex-direction: column; gap: 10px; }
.shot-head { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.shot-no { width: 30px; height: 30px; border-radius: 50%; background: var(--suli-primary); color: #fff; font-size: 14px; font-weight: 800; display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; }
.shot-sid { font-family: var(--suli-mono); font-size: 13px; white-space: nowrap; }
.shot-pics { display: flex; gap: 18px; flex-wrap: wrap; align-items: flex-end; padding: 6px 0; }
.shot-pic { display: flex; gap: 8px; align-items: flex-end; }
.shot-kind { font-size: 13px; color: var(--suli-text-2); flex-shrink: 0; }
.shot-thumb { border-radius: 10px; overflow: hidden; cursor: zoom-in; }
.shot-thumb.lg { width: 160px; aspect-ratio: 3 / 4; }
.shot-thumb.sm { width: 96px; aspect-ratio: 3 / 4; }
.shot-thumb :deep(img) { width: 100%; height: 100%; object-fit: cover; display: block; }
.shot-refwrap { display: inline-flex; gap: 4px; align-items: center; }
.script-title { font-size: 20px; font-weight: 800; margin: 0 0 4px; }
.save-state { display: inline-block; min-width: 96px; font-size: 12px; color: var(--suli-text-3); }
.seg-table { border: 1px solid var(--suli-border); border-radius: 10px; overflow: auto; background: #fff; margin-top: 10px; flex: 1 0 auto; min-height: 200px; }
.seg-row { display: grid; grid-template-columns: 52px 180px 1.4fr 170px 1fr 1fr; min-width: 1000px; }
.seg-head { background: var(--suli-bg-2); font-size: 13px; color: var(--suli-text-2); }
.seg-head > div { padding: 10px 12px; }
.seg-body { border-top: 1px dotted var(--el-border-color); }
.seg-body > div { padding: 10px 12px; border-left: 1px dotted var(--el-border-color); min-width: 0; }
.seg-body > div:first-child { border-left: none; }
.c-check { display: flex; flex-direction: column; gap: 4px; align-items: center; }
.seg-no { font-size: 12px; color: var(--suli-text-2); }
.seg-move { display: flex; }
.seg-label { font-weight: 700; font-size: 13px; }
.seg-meta { font-size: 12px; color: var(--suli-text-2); margin: 4px 0; }
.seg-tags { display: flex; gap: 4px; flex-wrap: wrap; }
.seg-gen { width: 100%; margin-top: 4px; }
.seg-id { font-family: var(--suli-mono); font-size: 11px; color: var(--suli-text-3); margin: 4px 0; }
.clip-thumb { width: 100%; aspect-ratio: 16 / 9; border-radius: 6px; overflow: hidden; cursor: zoom-in; }
.clip-thumb :deep(img) { width: 100%; height: 100%; object-fit: cover; display: block; }
.clip-add { width: 100%; aspect-ratio: 16 / 9; border: 1px dashed var(--el-border-color); border-radius: 6px; background: #fafafa; color: var(--suli-text-3); font-size: 12px; cursor: pointer; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; }
.clip-add:hover { border-color: var(--suli-primary); color: var(--suli-primary); }
.clip-plus { font-size: 18px; line-height: 1; }
.clip-loading { width: 100%; aspect-ratio: 16 / 9; border-radius: 6px; background: #2b2b2b; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 12px; }
.clip-missing { width: 100%; aspect-ratio: 16 / 9; border-radius: 6px; border: 1px dashed var(--el-color-warning); color: var(--el-color-warning); display: flex; flex-direction: column; gap: 4px; align-items: center; justify-content: center; font-size: 12px; }
.clip-missing .el-icon { font-size: 20px; }
.seg-foot { display: flex; justify-content: center; gap: 10px; align-items: center; margin: 14px 0 4px; }
.seg-add { background: #14b8a6; border: none; }
</style>
