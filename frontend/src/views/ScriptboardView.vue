<template>
  <div class="suli-card kun-page" style="padding:14px">
    <h3>剧本分镜 · 手工画布</h3>
    <el-input v-model="script" type="textarea" :rows="4" placeholder="剧本（手工排镜的底稿，只存不拆）" />
    <div style="margin-top:8px;display:flex;gap:8px;align-items:center;flex-wrap:wrap">
      <el-button @click="() => save()" :loading="saving">保存剧本</el-button>
      <el-button type="primary" @click="genOutline" :loading="agentLoading">生成大纲·轻</el-button>
      <el-button @click="genOutlineExpert" :loading="agentLoading">专家dsh</el-button>
      <el-button v-if="agentLoading" size="small" @click="agentAborter?.abort()">停止</el-button>
      <span v-if="agentProgress" class="suli-muted" style="font-size:12px">{{ agentProgress }}</span>
      <el-tag v-if="scriptDirty" size="small" type="warning">未存*</el-tag>

      <el-button type="primary" @click="addShot" :disabled="!canAdd">添加新镜</el-button>
      <span style="flex:1" />
      <el-tag size="small" class="tnum">{{ stat.shots }}镜</el-tag>
      <el-tag size="small" class="tnum">{{ stat.total_s }}s</el-tag>
      <el-tag size="small" :type="stat.verdict === 'PASS' ? 'success' : stat.verdict === 'BLOCK' ? 'danger' : 'info'">{{ stat.verdict }}</el-tag>
    </div>
    <div v-if="loading && !rows.length" class="shot-flow">
      <div v-for="i in 3" :key="i" class="suli-card" style="padding:14px"><div class="skeleton" style="height:20px;width:40%" /><div class="skeleton" style="height:14px;margin-top:8px" /><div class="skeleton" style="height:60px;margin-top:8px" /></div>
    </div>
    <el-empty v-else-if="!rows.length" description="无分镜，从下面待添加行逐行加" :image-size="64" />
    <div v-else class="shot-flow">
      <div v-for="(r, i) in rows" :key="r.id" class="suli-card shot-card">
        <div class="shot-head">
          <span class="shot-no tnum">{{ i + 1 }}</span>
          <span class="shot-sid">{{ r.id }}</span>
          <el-select v-model="r.camera.crop" style="width:130px" @change="saveRow(r, true)">
            <el-option v-for="c in crops" :key="c.value" :label="c.label" :value="c.value" />
          </el-select>
          <el-select v-model="r.camera.movement" style="width:110px" placeholder="运镜" @change="saveRow(r, true)">
            <el-option v-for="m in movements" :key="m" :label="m" :value="m" />
          </el-select>
          <el-input-number v-model="r.duration_s" style="width:140px" :min="0.5" :max="30" :step="0.5" @change="saveRow(r)" />
          <span class="suli-muted" style="font-size:13px">秒</span>
          <el-select v-model="r.tier" style="width:104px" placeholder="分级" @change="saveRow(r, true)">
            <el-option v-for="t in tierOpts" :key="t.key" :label="t.label" :value="t.key" />
          </el-select>
          <span style="flex:1" />
          <el-button link @click="move(i, -1)" :disabled="i === 0">↑</el-button>
          <el-button link @click="move(i, 1)" :disabled="i === rows.length - 1">↓</el-button>
          <el-button link type="primary" @click="saveRow(r)">存</el-button>
          <el-popconfirm title="删掉该镜？" confirm-button-text="删" cancel-button-text="留" @confirm="removeShot(r.id)">
            <template #reference><el-button link type="danger">删</el-button></template>
          </el-popconfirm>
        </div>
        <el-input v-model="r.duty" placeholder="画面内容：一句话写清这镜拍什么" @blur="saveRow(r)" />
        <el-input v-model="r.duty_en" type="textarea" :rows="2" resize="none" placeholder="英文正文" @blur="saveRow(r)" />
        <el-input v-model="r.sound" placeholder="口播/台词/字幕" @blur="saveRow(r)" />
        <div class="shot-pics">
          <div class="shot-pic">
            <span class="shot-kind">首帧</span>
            <el-image v-if="shotByKind(r, 'first')" :src="imgUrl(shotByKind(r, 'first').name)" :preview-src-list="[imgUrl(shotByKind(r, 'first').name)]" fit="cover" class="shot-thumb lg" preview-teleported />
            <el-button v-else link type="primary" @click="pickShotFile(r, 'first')">+首帧</el-button>
            <el-button v-if="shotByKind(r, 'first')" link type="danger" @click="delShotImg(r, shotByKind(r, 'first').name)">删</el-button>
          </div>
          <div class="shot-pic">
            <span class="shot-kind">尾帧</span>
            <el-image v-if="shotByKind(r, 'last')" :src="imgUrl(shotByKind(r, 'last').name)" :preview-src-list="[imgUrl(shotByKind(r, 'last').name)]" fit="cover" class="shot-thumb lg" preview-teleported />
            <el-button v-else link type="primary" @click="pickShotFile(r, 'last')">+尾帧</el-button>
            <el-button v-if="shotByKind(r, 'last')" link type="danger" @click="delShotImg(r, shotByKind(r, 'last').name)">删</el-button>
          </div>
          <div class="shot-pic">
            <span class="shot-kind">参考</span>
            <span v-for="im in shotRefImgs(r)" :key="im.name" class="shot-refwrap">
              <el-image :src="imgUrl(im.name)" :preview-src-list="[imgUrl(im.name)]" fit="cover" class="shot-thumb sm" preview-teleported />
              <el-button link type="danger" @click="delShotImg(r, im.name)">×</el-button>
            </span>
            <el-button link type="primary" @click="pickShotFile(r, 'ref')">+参考</el-button>
          </div>
        </div>
        <input :ref="(el: any) => { if (el) shotRefs[r.id] = el }" type="file" accept="image/*" hidden @change="(e: any) => onShotImg(r, e)" />
      </div>
    </div>
    <div class="suli-card" style="margin-top:10px;padding:10px;border-style:dashed">
      <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
        <el-select v-model="draft.crop" size="small" style="width:120px">
          <el-option v-for="c in crops" :key="c.value" :label="c.label" :value="c.value" />
        </el-select>
        <el-select v-model="draft.movement" size="small" style="width:100px">
          <el-option v-for="m in movements" :key="m" :label="m" :value="m" />
        </el-select>
        <el-input v-model="draft.duty" size="small" placeholder="职责/内容" style="flex:2;min-width:160px" @keyup.enter="addShot" />
        <el-input v-model="draft.sound" size="small" placeholder="台词/声音" style="flex:2;min-width:140px" @keyup.enter="addShot" />
        <el-input-number v-model="draft.duration" size="small" :min="0.5" :max="30" :step="0.5" />
        <el-button type="primary" size="small" @click="addShot" :disabled="!canAdd">添加新镜</el-button>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import { useAppStore } from '../stores/app'
const store = useAppStore()
const script = ref('## EP001-SC001 内·洗衣房·夜\n沈禾：取衣牌呢？\n蒋姨：烘干机停了。')
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
let suspendScriptWatch = false
let scriptTimer: any = null
const loading = ref(false)
const saving = ref(false)
async function save(silent = false) {
  saving.value = true
  try {
    await api.saveScreenplay(store.episodeId, script.value)
    savedScript.value = script.value
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
  } catch {} finally { suspendScriptWatch = false }
}
async function loadShots() { loading.value = true; try { const r = await api.listShots(store.episodeId); store.shots = r.data; await loadStat() } finally { loading.value = false } }
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
  await api.updateShot(r.id, { duty: r.duty, duty_en: r.duty_en || '', duration_s: r.duration_s, sound: r.sound, tier: r.tier || '', camera: { crop: r.camera?.crop || 'medium', movement: r.camera?.movement || '固定' } })
  if (!silent) ElMessage.success('已保存')
  await loadStat()
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
    '请按这张单图出方案大纲：看图写一份方案大纲markdown（含：方向一句话 / 基调与档位 / 分镜大纲表：镜号/内容一句话/预计时长/运镜方向/备注 / 合计时长），2-5镜，单镜3-8秒。然后 PUT /api/v1/scriptboard/outline/<集号> 保存 {outline_md: 全文, outline_image: 本图basename}，最后回复方向一句话+镜数+合计时长。只出大纲，不要写分镜库。',
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
      ElMessage.error('❌ ' + (errMsg || '流中断'))
    }
  } finally {
    agentLoading.value = false
    agentAborter.value = null
  }
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
async function onShotImg(r: any, e: any) {
  const f = e.target.files?.[0]
  e.target.value = ''
  if (!f) return
  const kind = shotKind.value[r.id] || 'ref'
  await api.uploadShotImage(r.id, f, kind)
  ElMessage.success(kind === 'ref' ? '参考图已上传' : (kind === 'first' ? '首帧已上传' : '尾帧已上传'))
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
  await loadScript()
  await loadShots()
})
</script>
<style scoped>
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
</style>
