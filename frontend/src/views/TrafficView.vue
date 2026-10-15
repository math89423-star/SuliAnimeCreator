<template>
  <div class="kun-page mini">
    <div class="suli-card tcard" style="flex-direction:row;align-items:center;gap:8px;flex-wrap:wrap">
      <span class="suli-muted" style="font-size:12px">母本 {{ motherId }}</span>
      <el-tag v-if="libSource" size="small" type="info" class="tnum">高光池:{{ libSource }}</el-tag>
      <span style="flex:1" />
      <el-button size="small" @click="loadLib">从本集载入高光</el-button>
      <el-button size="small" @click="loadHist">历史包</el-button>
      <el-button size="small" @click="seedDemo" :loading="seeding">一键种子</el-button>
    </div>
    <div v-for="(t, i) in tasks" :key="t.id" class="suli-card tcard">
      <el-input v-model="t.desc" type="textarea" :rows="2" class="t-desc" />
      <div class="t-ctl">
        <el-segmented v-model="t.mode" :options="[{ label: '新生成', value: 'gen' }, { label: '素材库', value: 'lib' }]" size="small" />
        <el-select v-model="t.category" size="small" style="width:110px">
          <el-option v-for="c in CATS" :key="c" :label="c" :value="c" />
        </el-select>
        <el-segmented v-model="t.count" :options="[15, 30, 60].map(v => ({ label: `${v}`, value: v }))" size="small" />
        <el-input-number v-model="t.count" size="small" :min="1" :max="120" style="width:110px" />
        <el-button circle size="small" @click="tasks.splice(i, 1)" :disabled="tasks.length <= 1">−</el-button>
      </div>
      <div class="ref-row">
        <el-tag v-if="t.refVideo" size="small" closable class="tnum" @close="t.refVideo = ''">{{ shortName(t.refVideo) }}</el-tag>
        <span class="ref-add" @click="pickVideo(t)">+ 参考视频</span>
        <input :ref="(el: any) => { if (el) vidInputs[t.id] = el }" type="file" accept="video/*" hidden @change="(e: any) => onVideo(t, e)" />
        <span style="flex:1" />
        <span v-if="t.results?.length" class="tnum res-n">{{ t.results.length }}</span>
        <span v-if="t.engine" class="tnum eng">{{ t.engine }}</span>
        <el-button v-if="t.results?.length" size="small" link @click="t._open = !t._open">{{ t._open ? '收起' : '展开' }}</el-button>
      </div>
      <div v-show="t._open && t.results?.length" class="res">
        <div v-for="v in t.results" :key="v.variant_id" class="v" @click="v._open = !v._open">
          <b class="tnum">{{ v.variant_id }}</b>
          <span class="t">{{ v.title }}</span>
          <div v-show="v._open" class="d">
            <div>{{ v.hypothesis }}</div>
            <div>{{ v.hook_text }}</div>
            <div>{{ v.hl_id }}｜{{ v.hl_desc }}</div>
            <div>{{ v.cta_text }}</div>
            <div class="tnum f">{{ v.file_name }}</div>
            <el-button size="small" link type="primary" @click.stop="copyOne(v)">复制</el-button>
          </div>
        </div>
      </div>
    </div>
    <div class="add-zone" @click="addTask"><span>+ 任务</span></div>
    <div class="suli-card actionbar">
      <span v-if="running" class="run">运行中…</span>
      <span style="flex:1" />
      <el-button size="small" type="primary" @click="run" :loading="running">运行</el-button>
      <el-button size="small" @click="download" :disabled="!totalN">导出JSON</el-button>
      <el-button size="small" @click="downloadZip" :disabled="!lastPkg">导出ZIP</el-button>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const motherId = ref((store as any).episodeId || 'EP-DEMO01')
const libSource = ref('')
const seeding = ref(false)
watch(() => (store as any).episodeId, v => { if (v) motherId.value = v })
const CATS = ['红包点击', '付费解锁', '拉新关注', '直播引流']
let seq = 0
const tasks = ref<any[]>([{ id: ++seq, desc: '引导点击红包广告', mode: 'lib', category: '红包点击', count: 15, refVideo: '', _up: false, results: [], _open: true, engine: '' }])
const running = ref(false)
const lastPkg = ref<any>(null)
const totalN = computed(() => tasks.value.reduce((a, t) => a + (t.results?.length || 0), 0))
const vidInputs = ref<Record<number, HTMLInputElement>>({})
function shortName(p: string) {
  const s = String(p || '').split('/').pop() || p
  return s.length > 14 ? s.slice(0, 6) + '…' + s.slice(-7) : s
}
function pickVideo(t: any) { vidInputs.value[t.id]?.click() }
async function onVideo(t: any, e: any) {
  const f = e.target.files?.[0]
  e.target.value = ''
  if (!f) return
  t._up = true
  try {
    const r: any = await api.uploadFile(f)
    t.refVideo = r?.data?.path ?? r?.path ?? ''
    if (!t.refVideo) throw new Error('empty')
    if (!(t.desc || '').trim()) t.desc = '参考视频已传，按片内高光出变体'
    ElMessage.success('参考视频已上传')
  } catch { ElMessage.error('上传失败，后端未起？') }
  finally { t._up = false }
}
const LIB = [
  { id: 'LIB-01', desc: '开箱前对峙' }, { id: 'LIB-02', desc: '烘干机空转特写' },
  { id: 'LIB-03', desc: '取衣牌争夺' }, { id: 'LIB-04', desc: '人物惊愕反应' },
  { id: 'LIB-05', desc: '摔门离场' }, { id: 'LIB-06', desc: '深夜洗衣房空镜' },
  { id: 'LIB-07', desc: '金句贴脸' }, { id: 'LIB-08', desc: '证据反转' },
]
const HOOKS = ['冲突直给', '悬念提问', '反差', '台词爆点', '动作奇观']
function addTask() {
  tasks.value.push({ id: ++seq, desc: '', mode: 'lib', category: '红包点击', count: 15, refVideo: '', _up: false, results: [], _open: true, engine: '' })
}
async function run() {
  if (running.value) return
  const valid = tasks.value.filter(t => (t.desc || '').trim() || t.refVideo)
  if (!valid.length) return ElMessage.warning('填任务描述')
  running.value = true
  valid.forEach(t => { t.results = []; t.engine = '' })
  try {
    const r = await fetch('/api/v1/traffic/generate', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mother_id: (store as any).episodeId || motherId.value, tasks: valid.map(t => ({ desc: t.desc, mode: t.mode, category: t.category, count: t.count, refVideo: t.refVideo })) }),
    })
    const j = await r.json()
    if (j && j.code === 0 && j.data?.variants?.length) {
      lastPkg.value = j.data
      libSource.value = j.data.lib_source || j.data.checks?.lib_source || ''
      const eng = j.data.checks?.engine || 'llm'
      const byTask: Record<number, any[]> = {}
      j.data.variants.forEach((v: any) => { (byTask[v.task_id] = byTask[v.task_id] || []).push({ ...v, _open: false }) })
      valid.forEach((t, idx) => { t.results = byTask[idx + 1] || []; t.engine = eng; t._open = true })
      ElMessage.success(`已出${j.data.variants.length}条`)
      return
    }
    throw new Error(j?.msg || 'empty')
  } catch {
    buildLocal(valid)
  } finally { running.value = false }
}
function buildLocal(valid: any[]) {
  const batch = 'PKG-TRAFFIC-' + motherId.value + '-' + new Date().toISOString().slice(5, 10).replace('-', '')
  valid.forEach((t, ti) => {
    const out: any[] = []
    for (let i = 0; i < t.count; i++) {
      const lib = LIB[(i + ti) % LIB.length]
      const hk = HOOKS[i % HOOKS.length]
      const useGen = t.mode === 'gen' && i % 4 === 3
      const hlId = useGen ? `GEN-${String(i + 1).padStart(2, '0')}` : lib.id
      const vid = `T${ti + 1}-V${String(i + 1).padStart(2, '0')}`
      out.push({
        variant_id: vid, batch_id: batch, _open: false,
        hypothesis: `${hk}测${t.category}`,
        hook_text: `${hk}｜${useGen ? (t.desc || t.refVideo) : (t.refVideo || lib.desc)}`,
        hl_id: t.refVideo ? `REF-${t.refVideo.slice(0, 6)}` : hlId,
        hl_desc: t.refVideo ? `参考视频${shortName(t.refVideo)}` : (useGen ? t.desc.slice(0, 20) : lib.desc),
        title: `${t.category}｜${hk}`, cta_text: (t.desc || '').slice(0, 30),
        file_name: `${batch}_${vid}_${hlId}_1080x1920.mp4`,
      })
      if (out.length >= t.count) break
    }
    t.results = out; t.engine = 'local'; t._open = true
  })
  lastPkg.value = null
  ElMessage.success('已出（local回退）')
}
async function loadLib() {
  try {
    const r: any = await (api as any).library((store as any).episodeId || motherId.value)
    const d = r?.data ?? r
    libSource.value = d?.source || ''
    const lib = (d?.library || []) as any[]
    ElMessage.success(`高光池:${libSource.value} ${lib.length}条` + (lib[0] ? '｜首条:' + lib[0].desc.slice(0, 16) : ''))
  } catch { ElMessage.error('载入失败') }
}
async function loadHist() {
  try {
    const r: any = await (api as any).packages()
    const d = r?.data ?? r
    const rows = (d?.packages || []) as any[]
    if (!rows.length) return ElMessage.warning('暂无历史包')
    const latest = rows[0]
    const pr: any = await (api as any).package(latest.package_id)
    const pd = pr?.data ?? pr
    lastPkg.value = pd
    libSource.value = pd?.lib_source || ''
    const byTask: Record<number, any[]> = {}
    ;(pd.variants || []).forEach((v: any) => { (byTask[v.task_id] = byTask[v.task_id] || []).push({ ...v, _open: false }) })
    tasks.value.forEach((tt, idx) => { tt.results = byTask[idx + 1] || tt.results; tt._open = true })
    ElMessage.success(`已载入 ${latest.package_id}（${pd.variants?.length ?? 0}条）`)
  } catch { ElMessage.error('历史包载入失败') }
}
async function seedDemo() {
  seeding.value = true
  try {
    const r: any = await (api as any).demoSeed((store as any).episodeId || motherId.value)
    const d = r?.data ?? r
    ElMessage.success(`种子已灌：${d?.lineage?.shots?.length ?? 0}镜/${d?.lineage?.total_s ?? ''}s/${d?.lineage?.traffic_package ?? ''}`)
    await loadHist()
  } catch { ElMessage.error('种子失败，后端未起？') }
  finally { seeding.value = false }
}
async function downloadZip() {
  try {
    const pid = (lastPkg.value as any)?.package_id
    if (!pid) return
    const blob: any = await (api as any).exportBundle(pid)
    const url = URL.createObjectURL(new Blob([blob], { type: 'application/zip' }))
    const a = document.createElement('a')
    a.href = url; a.download = `${pid}.zip`; a.click()
    setTimeout(() => URL.revokeObjectURL(url), 5000)
  } catch { ElMessage.error('ZIP导出失败') }
}
async function copyOne(v: any) {
  try { await navigator.clipboard.writeText(`${v.variant_id}｜${v.hypothesis}\n${v.title}\n${v.hook_text}\n${v.hl_id}\n${v.cta_text}\n${v.file_name}`); ElMessage.success('已复制') } catch { ElMessage.error('复制失败') }
}
function download() {
  const all = tasks.value.flatMap(t => (t.results || []).map(({ _open, ...r }: any) => r))
  if (!all.length) return
  const p = lastPkg.value || { package_id: all[0].batch_id, mother_id: motherId.value, tasks: tasks.value.map(t => ({ desc: t.desc, mode: t.mode, category: t.category, count: t.count, refVideo: t.refVideo })), variants: all }
  const blob = new Blob([JSON.stringify(p, null, 2)], { type: 'application/json' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob); a.download = `${p.package_id}.json`; a.click()
  URL.revokeObjectURL(a.href)
}
onMounted(() => { motherId.value = (store as any).episodeId || motherId.value })
</script>
<style scoped>
.kun-page.mini{max-width:none;margin:0;width:100%;box-sizing:border-box}
.mini { display: flex; flex-direction: column; gap: 12px; }
.tcard { padding: 14px; display: flex; flex-direction: column; gap: 8px; }
.t-desc { width: 100%; }
.t-desc :deep(.el-textarea__inner) { font-size: 14px; line-height: 1.6; border-radius: 12px; padding: 10px 12px; }
.t-ctl { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.ref-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.ref-add { font-size: 12px; color: var(--suli-text-2); border: 1px dashed var(--suli-border-hover); border-radius: 999px; padding: 3px 12px; cursor: pointer; }
.ref-add:hover { border-color: var(--suli-primary); color: var(--suli-primary); }
.res-n { font-weight: 800; }
.eng { font-size: 11px; color: var(--suli-text-3); }
.run { font-size: 12px; color: var(--suli-primary); }
.res { border-top: 1px solid var(--suli-border); }
.v { padding: 8px 0; border-top: 1px dashed var(--suli-border); cursor: pointer; font-size: 13px; }
.v:first-child { border-top: none; }
.v b { margin-right: 8px; }
.d { margin-top: 4px; font-size: 12px; display: flex; flex-direction: column; gap: 2px; }
.f { color: var(--suli-text-3); font-size: 11px; word-break: break-all; }
.add-zone { border: 1.5px dashed var(--suli-border-hover); border-radius: 14px; padding: 12px; text-align: center; font-size: 13px; color: var(--suli-text-2); cursor: pointer; }
.add-zone:hover { border-color: var(--suli-primary); color: var(--suli-primary); }
.actionbar { padding: 12px 14px; display: flex; gap: 8px; align-items: center; }
</style>
