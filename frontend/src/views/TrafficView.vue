<template>
  <div class="kun-page mini">
    <div v-for="(t, i) in tasks" :key="t.id" class="suli-card tcard">
      <div class="suli-muted" style="font-size:12px">任务描述</div>
      <el-input v-model="t.desc" type="textarea" :rows="6" class="t-desc" />
      <div class="t-ctl">
        <span class="suli-muted" style="font-size:12px">生成数量</span>
        <el-input-number v-model="t.count" size="small" :min="1" :max="120" style="width:110px" />
      </div>
      <div class="t-mount">
        <el-input v-model="t.mount.search_word" size="small" placeholder="挂载搜索词" maxlength="30" class="m-in" />
        <el-input v-model="t.mount.app_name" size="small" placeholder="小程序名" maxlength="30" class="m-in" />
        <el-input v-model="t.mount.overlay_text" size="small" placeholder="贴片文案" maxlength="40" class="m-in" />
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
            <div v-if="v.mount && (v.mount.search_word || v.mount.app_name || v.mount.overlay_text)" class="tnum f">挂载：{{ v.mount.search_word || '-' }}/{{ v.mount.app_name || '-' }}/{{ v.mount.overlay_text || '-' }}</div>
            <div class="tnum f">{{ v.file_name }}</div>
            <el-button size="small" link type="primary" @click.stop="copyOne(v)">复制</el-button>
          </div>
        </div>
      </div>
    </div>
    <div class="suli-card tcard lib-card">
      <div class="lib-head" @click="libOpen = !libOpen" style="cursor:pointer;display:flex;gap:8px;align-items:center">
        <span style="font-size:13px;font-weight:700">素材库</span>
        <el-segmented v-model="libTab" size="small" :options="[
          { label: `视频资源${kindCount('video')}`, value: 'video' },
          { label: `广告素材${kindCount('image')}`, value: 'image' },
        ]" @click.stop />
        <span style="flex:1" />
        <template v-if="delMode">
          <span @click.stop><el-checkbox :model-value="allSel" :indeterminate="selKeys.length > 0 && !allSel" @change="toggleAllSel">全选</el-checkbox></span>
          <span class="tnum" style="font-size:11px;color:var(--suli-text-3)">已选{{ selKeys.length }}</span>
          <el-button size="small" type="danger" :disabled="!selKeys.length" :loading="deleting" @click.stop="confirmDelSel">删除</el-button>
          <el-button size="small" link @click.stop="exitDelMode">取消</el-button>
        </template>
        <template v-else>
          <el-button size="small" link @click.stop="enterDelMode">删除</el-button>
        </template>
        <el-button size="small" link @click.stop="refreshLib" :loading="libScanning">重扫</el-button>
        <el-button size="small" link>{{ libOpen ? '收起' : '展开' }}</el-button>
      </div>
      <div v-show="libOpen" class="lib-body">
        <div v-if="libTab === 'video'">
          <div class="lib-filters">
            <el-input v-model="libQ" size="small" placeholder="搜文件名/描述" style="width:180px" clearable />
          </div>
          <div v-if="libLoading" style="color:var(--suli-text-3);font-size:12px;margin-top:6px">载入中…</div>
          <div v-else-if="!libRows.length" style="color:var(--suli-text-3);font-size:12px;margin-top:6px">无匹配素材</div>
          <div v-else class="lib-list">
            <div v-for="a in libRows" :key="a.file" class="lib-item">
              <el-checkbox v-if="delMode" :model-value="isSel(a)" @change="() => toggleSel(a)" @click.stop />
              <img :src="thumbSrc(a)" class="v-thumb" loading="lazy" @click="delMode || openPlay(a)" :style="delMode ? 'cursor:default' : 'cursor:pointer'" />
              <div class="lib-main" @click="delMode ? toggleSel(a) : openPlay(a)" style="cursor:pointer">
                <div class="lib-name">{{ a.name }}</div>
                <div class="lib-meta tnum">{{ a.hook || '未分类' }}{{ a.cool ? '/' + a.cool : '' }} · {{ a.dur }}s · {{ a.w }}×{{ a.h }} · 用过{{ a.used || 0 }}次</div>
              </div>
              <template v-if="!delMode">
                <el-button size="small" link @click="renameRow(a)">改名</el-button>
                <el-button size="small" link type="primary" @click="copyAsset(a)">复制</el-button>
              </template>
            </div>
          </div>
        </div>
        <div v-else>
          <div class="lib-filters">
            <el-input v-model="libQ" size="small" placeholder="搜文件名" style="width:180px" clearable />
          </div>
          <div v-if="libLoading" style="color:var(--suli-text-3);font-size:12px;margin-top:6px">载入中…</div>
          <div v-else-if="!libRows.length" style="color:var(--suli-text-3);font-size:12px;margin-top:6px">无匹配素材</div>
          <div v-else class="img-grid">
            <div v-for="a in libRows" :key="a.file" class="img-cell" :title="a.name">
              <el-checkbox v-if="delMode" class="cell-check" :model-value="isSel(a)" @change="() => toggleSel(a)" @click.stop />
              <img :src="assetUrl(a)" class="img-thumb" loading="lazy" @click="delMode ? toggleSel(a) : openPlay(a)" style="cursor:pointer" />
              <div class="img-name">{{ a.name }}</div>
              <div class="img-meta tnum">{{ a.w }}×{{ a.h }}</div>
              <template v-if="!delMode">
                <el-button size="small" link @click="renameRow(a)">改名</el-button>
                <el-button size="small" link type="primary" @click="copyAsset(a)">复制</el-button>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="suli-card actionbar actionbar-fixed" :style="footStyle">
      <span v-if="running" class="run">运行中…</span>
      <span style="flex:1" />
      <el-button size="small" type="primary" @click="run" :loading="running">运行</el-button>
      <el-button size="small" type="danger" plain @click="clearWorkspace">清空</el-button>
      <el-button size="small" @click="download" :disabled="!totalN">导出JSON</el-button>
      <el-button size="small" @click="downloadZip" :disabled="!lastPkg">导出ZIP</el-button>
      <el-checkbox v-model="autoRunLport" size="small" :disabled="!lastPkg">投完直接出片</el-checkbox>
      <el-button size="small" type="success" plain :loading="pushing" :disabled="!lastPkg" @click="pushToLport">直投 L-Port</el-button>
    </div>
    <el-dialog v-model="histOpen" title="历史包" width="520px" append-to-body>
      <div v-if="histLoading" style="color:var(--suli-text-3);font-size:12px">载入中…</div>
      <div v-else-if="!histRows.length" style="color:var(--suli-text-3);font-size:12px">暂无历史包</div>
      <div v-else class="hist-list">
        <div v-for="h in histRows" :key="h.package_id" class="hist-item"
          :class="{ active: (lastPkg as any)?.package_id === h.package_id }">
          <div class="hist-main" @click="loadPkg(h.package_id)">
            <div class="hist-pid tnum">{{ h.package_id }}</div>
            <div class="hist-meta">{{ h.mother_id }} · {{ h.variants }}条 · {{ h.lib_source }} · {{ fmtTime(h.created_at) }}</div>
          </div>
          <el-button size="small" link type="danger" @click.stop="delPkg(h.package_id)">删除</el-button>
        </div>
      </div>
    </el-dialog>
    <el-dialog v-model="playOpen" :title="playItem?.name || '预览'" width="560px" append-to-body>
      <div v-if="playItem" style="text-align:center">
        <video v-if="(playItem.kind || 'video') === 'video'" :src="playSrc()" controls autoplay style="width:100%;max-height:60vh;background:#000;border-radius:8px" />
        <img v-else :src="playSrc()" style="max-width:100%;max-height:60vh;border-radius:8px" />
        <div class="lib-meta tnum" style="margin-top:6px">{{ playItem.hook || '未分类' }}{{ playItem.cool ? '/' + playItem.cool : '' }} · {{ playItem.dur }}s · {{ playItem.w }}×{{ playItem.h }} · 用过{{ playItem.used || 0 }}次</div>
      </div>
    </el-dialog>
    <el-dialog v-model="renameOpen" title="重命名" width="440px" append-to-body>
      <el-input v-model="renameValue" placeholder="新文件名" clearable @keyup.enter="confirmRename" />
      <template #footer>
        <el-button size="small" @click="renameOpen = false">取消</el-button>
        <el-button size="small" type="primary" @click="confirmRename" :loading="renaming">改名</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api/client'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const motherId = ref((store as any).episodeId || 'EP-DEMO01');
const libSource = ref('')
watch(() => (store as any).episodeId, v => {
  if (!v || v === motherId.value) return
  saveSnap()
  motherId.value = v
  if (!restoreSnap()) {
    tasks.value = [{ id: ++seq, desc: '引导点击红包广告', mode: 'lib', category: '红包点击', count: 15, refVideo: '', _up: false, results: [], _open: true, engine: '', mount: { search_word: '', app_name: '', overlay_text: '' } }]
    lastPkg.value = null
  }
  recoverRunning()
})
const CATS = ['红包点击', '付费解锁', '拉新关注', '直播引流']
let seq = 0
const tasks = ref<any[]>([{ id: ++seq, desc: '引导点击红包广告', mode: 'lib', category: '红包点击', count: 15, refVideo: '', _up: false, results: [], _open: true, engine: '', mount: { search_word: '', app_name: '', overlay_text: '' } }])
const running = ref(false)
const lastPkg = ref<any>(null)
const totalN = computed(() => tasks.value.reduce((a, t) => a + (t.results?.length || 0), 0))
// 尾部钉视口底部：按左右折叠态算出中央列左右边距
const footStyle = computed(() => {
  const left = ((store as any).leftCollapsed ? 44 : 212) + 12
  const right = ((store as any).rightCollapsed ? 44 : 440) + 12
  return { left: left + 'px', right: right + 'px' }
})
// 持久化：切页面不丢任务，回来自动认领服务端已出的包
const snapKey = () => `traffic-snap:${motherId.value || 'global'}`
const runKey = () => `traffic-running:${motherId.value || 'global'}`
function stripTask(t: any) {
  return { desc: t.desc, mode: t.mode, category: t.category, count: t.count, refVideo: t.refVideo,
    mount: { ...(t.mount || { search_word: '', app_name: '', overlay_text: '' }) },
    results: t.results || [], engine: t.engine || '', _open: !!t._open }
}
function saveSnap() {
  try {
    localStorage.setItem(snapKey(), JSON.stringify({
      tasks: tasks.value.map(stripTask),
      lastPkgId: (lastPkg.value as any)?.package_id || '',
      libSource: libSource.value, savedAt: Date.now(),
    }))
  } catch {}
}
function attachPkg(pd: any) {
  if (!pd) return false
  lastPkg.value = pd
  libSource.value = pd?.lib_source || ''
  const eng = pd?.checks?.engine || 'llm'
  const byTask: Record<number, any[]> = {}
  ;(pd.variants || []).forEach((v: any) => { (byTask[v.task_id] = byTask[v.task_id] || []).push({ ...v, _open: false }) })
  tasks.value.forEach((tt, idx) => {
    const got = byTask[idx + 1] || []
    if (got.length) { tt.results = got; tt.engine = eng; tt._open = true }
  })
  return (pd.variants || []).length > 0
}
async function recoverRunning() {
  // 切走时正在跑的任务：回来先亮运行态，轮询等服务端包出来再认领
  let flag = 0
  try { flag = Number(localStorage.getItem(runKey()) || 0) } catch {}
  if (!flag) return
  running.value = true
  pollStop = false
  const deadline = Date.now() + 8 * 60 * 1000
  const since = flag - 120000 // 允许时钟偏差
  try {
    while (!pollStop && Date.now() < deadline) {
      try {
        const r: any = await (api as any).packages()
        const rows = ((r?.data ?? r)?.packages || []) as any[]
        const hit = rows.find(x => (!x.mother_id || x.mother_id === motherId.value) && (x.created_at || 0) >= since)
        if (hit) {
          const pr: any = await (api as any).package(hit.package_id)
          const pd = pr?.data ?? pr
          if (pd && (!pd.mother_id || pd.mother_id === motherId.value) && attachPkg(pd)) {
            ElMessage.success(`已认领切走期间出的包 ${hit.package_id}`)
            break
          }
        }
      } catch {}
      await new Promise(res => setTimeout(res, 3000))
      if (!localStorage.getItem(runKey())) break // 别处已完成
    }
    if (!pollStop && Date.now() >= deadline) ElMessage.warning('等待超时，去点历史包手动载入')
  } finally {
    running.value = false
    try { localStorage.removeItem(runKey()) } catch {}
  }
  saveSnap()
}
let pollStop = false
onBeforeUnmount(() => { pollStop = true })
function restoreSnap() {
  try {
    const raw = localStorage.getItem(snapKey())
    if (!raw) return false
    const d = JSON.parse(raw)
    if (!d?.tasks?.length) return false
    // 单任务制：老快照有多任务只保留第一个
    tasks.value = d.tasks.slice(0, 1).map((t: any) => ({ id: ++seq, _up: false, ...t }))
    libSource.value = d.libSource || ''
    return true
  } catch { return false }
}
watch(tasks, saveSnap, { deep: true })
// 顶栏历史包按钮信号
watch(() => (store as any).trafficHistSignal, () => { loadHist() })
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
const HOOK_FILTERS = [{ label: '全部', value: '' }, ...['冲突直给', '悬念提问', '反差', '台词爆点', '动作奇观'].map(h => ({ label: h.slice(0, 2), value: h }))]
// 内嵌素材库（读后端索引，不碰原视频）：视频资源 / 广告素材双类
const libOpen = ref(true)
const libTab = ref('video')
const libRows = ref<any[]>([])
const libTotal = ref(0)
const libKinds = ref<Record<string, number>>({})
const libQ = ref('')
const libHook = ref('')
const libLoading = ref(false)
const libScanning = ref(false)
function kindCount(k: string) {
  const n = libKinds.value[k] || 0
  return n ? `(${n})` : ''
}
let libTimer: any = null
let libSeq = 0
async function loadLib2() {
  const my = ++libSeq
  libLoading.value = true
  try {
    const r: any = await (api as any).assets({ kind: libTab.value, q: libQ.value, hook: libTab.value === 'video' ? libHook.value : '', limit: 100 })
    if (my !== libSeq) return // tab/搜索切得快时只认最后一次
    const d = r?.data ?? r
    libRows.value = d?.rows || []
    libTotal.value = Number(d?.facets?.indexed ?? d?.total ?? 0)
    libKinds.value = d?.facets?.kinds || {}
  } catch { if (my === libSeq) libRows.value = [] }
  finally { if (my === libSeq) libLoading.value = false }
}
watch([libQ, libHook, libTab], () => { clearTimeout(libTimer); libTimer = setTimeout(loadLib2, 300) })
function assetUrl(a: any) {
  return `/api/v1/traffic/asset-file?lib=${a.lib || 'flow'}&path=${encodeURIComponent(a.file || '')}`
}
function thumbSrc(a: any) {
  return `/api/v1/traffic/thumb?lib=${a.lib || 'flow'}&path=${encodeURIComponent(a.file || '')}`
}
async function refreshLib() {
  if (libScanning.value) return
  libScanning.value = true
  try {
    const r: any = await (api as any).rescanAssets()
    const d = r?.data ?? r
    if (d?.ok === false) return ElMessage.warning(d?.msg || '素材库未挂载')
    ElMessage.success(`索引共${d.total}条（新增${d.new}）`)
    loadLib2()
  } catch { ElMessage.error('重扫失败') }
  finally { libScanning.value = false }
}
async function copyAsset(a: any) {
  try { await navigator.clipboard.writeText(`${a.name}｜${a.desc || ''}｜${a.hook || '未分类'}｜${a.dur}s`); ElMessage.success('已复制') } catch { ElMessage.error('复制失败') }
}
// 删除模式：右上角小方框多选 + 全选 + 删除
const delMode = ref(false)
const selKeys = ref<string[]>([])
const deleting = ref(false)
const selKeyOf = (a: any) => `${a.lib || 'flow'}|${a.file || ''}`
function isSel(a: any) { return selKeys.value.includes(selKeyOf(a)) }
function toggleSel(a: any) {
  const k = selKeyOf(a)
  selKeys.value = selKeys.value.includes(k) ? selKeys.value.filter(x => x !== k) : [...selKeys.value, k]
}
const allSel = computed(() => libRows.value.length > 0 && libRows.value.every(isSel))
function toggleAllSel() {
  selKeys.value = allSel.value ? [] : libRows.value.map(selKeyOf)
}
function enterDelMode() { selKeys.value = []; delMode.value = true; libOpen.value = true }
function exitDelMode() { delMode.value = false; selKeys.value = [] }
async function confirmDelSel() {
  if (!selKeys.value.length) return
  try { await ElMessageBox.confirm(`删除选中的 ${selKeys.value.length} 个素材？文件与索引一起删，不可恢复。`, '删除素材', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }) } catch { return }
  deleting.value = true
  try {
    const items = selKeys.value.map(k => { const [lib, ...rest] = k.split('|'); return { lib, path: rest.join('|') } })
    const r: any = await (api as any).deleteAssets(items)
    const d = r?.data ?? r
    ElMessage.success(`已删除${d?.count ?? 0}个${d?.failed?.length ? `，${d.failed.length}个失败` : ''}`)
    exitDelMode()
    loadLib2()
  } catch { ElMessage.error('删除失败') }
  finally { deleting.value = false }
}
const playOpen = ref(false)
const playItem = ref<any>(null)
function openPlay(a: any) { playItem.value = a; playOpen.value = true }
function playSrc() {
  const a = playItem.value
  if (!a) return ''
  return assetUrl(a)
}
const renameOpen = ref(false)
const renameTarget = ref<any>(null)
const renameValue = ref('')
const renaming = ref(false)
function renameRow(a: any) {
  renameTarget.value = a
  renameValue.value = a.name
  renameOpen.value = true
}
async function confirmRename() {
  const a = renameTarget.value
  if (!a) return
  const val = (renameValue.value || '').trim()
  if (!val || val.includes('/') || val.includes('\\')) return ElMessage.warning('文件名非法')
  const oldExt = a.name.slice(a.name.lastIndexOf('.')).toLowerCase()
  const newExt = val.slice(val.lastIndexOf('.')).toLowerCase()
  if (!val.includes('.') || oldExt !== newExt) return ElMessage.warning('不许改扩展名')
  if (val === a.name) { renameOpen.value = false; return }
  renaming.value = true
  try {
    const r: any = await (api as any).renameAsset({ lib: a.lib, path: a.file, new_name: val })
    const e = (r?.data ?? r)?.entry
    if (e) Object.assign(a, e)
    ElMessage.success(`已改名${e?.hook ? `（钩子:${e.hook}）` : ''}`)
    renameOpen.value = false
    loadLib2()
  } catch (e: any) { ElMessage.error((e?.response?.data?.msg || e?.message || '改名失败').slice(0, 80)) }
  finally { renaming.value = false }
}
async function run() {
  if (running.value) return
  const valid = tasks.value.filter(t => (t.desc || '').trim() || t.refVideo)
  if (!valid.length) return ElMessage.warning('填任务描述')
  running.value = true
  valid.forEach(t => { t.results = []; t.engine = '' })
  try { localStorage.setItem(runKey(), String(Date.now())) } catch {}
  saveSnap()
  try {
    const r = await fetch('/api/v1/traffic/generate', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mother_id: (store as any).episodeId || motherId.value, tasks: valid.map(t => ({ desc: t.desc, mode: 'lib', category: '红包点击', count: t.count, refVideo: t.refVideo, mount: t.mount || { search_word: '', app_name: '', overlay_text: '' } })) }),
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
      try { localStorage.removeItem(runKey()) } catch {}
      saveSnap()
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
        mount: { ...(t.mount || { search_word: '', app_name: '', overlay_text: '' }) },
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
  try { localStorage.removeItem(runKey()) } catch {}
  saveSnap()
  ElMessage.success('已出（local回退）')
}
async function loadHist() {
  histOpen.value = true
  await refreshHist()
}
const histOpen = ref(false)
const histRows = ref<any[]>([])
const histLoading = ref(false)
async function refreshHist() {
  histLoading.value = true
  try {
    const r: any = await (api as any).packages()
    const rows = ((r?.data ?? r)?.packages || []) as any[]
    const cur = motherId.value
    histRows.value = [...rows].sort((a, b) => {
      const am = a.mother_id === cur ? 0 : 1, bm = b.mother_id === cur ? 0 : 1
      return am - bm || (b.created_at || 0) - (a.created_at || 0)
    })
  } catch { ElMessage.error('历史包载入失败') }
  finally { histLoading.value = false }
}
function fmtTime(ts: number) {
  if (!ts) return '--'
  const d = new Date(ts)
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getMonth() + 1}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}
async function loadPkg(pid: string) {
  try {
    const pr: any = await (api as any).package(pid)
    const pd = pr?.data ?? pr
    lastPkg.value = pd
    libSource.value = pd?.lib_source || ''
    const byTask: Record<number, any[]> = {}
    ;(pd.variants || []).forEach((v: any) => { (byTask[v.task_id] = byTask[v.task_id] || []).push({ ...v, _open: false }) })
    tasks.value.forEach((tt, idx) => { if (byTask[idx + 1]?.length) { tt.results = byTask[idx + 1]; tt._open = true } })
    saveSnap()
    histOpen.value = false
    ElMessage.success(`已载入 ${pid}（${pd.variants?.length ?? 0}条）`)
  } catch { ElMessage.error('载入失败') }
}
async function delPkg(pid: string) {
  try {
    await (api as any).deletePackage(pid)
    histRows.value = histRows.value.filter(x => x.package_id !== pid)
    if ((lastPkg.value as any)?.package_id === pid) {
      lastPkg.value = null
      tasks.value.forEach(t => { t.results = []; t.engine = '' })
    }
    saveSnap()
    ElMessage.success(`已删除 ${pid}`)
  } catch { ElMessage.error('删除失败') }
}
async function downloadZip() {
  try {
    const pid = (lastPkg.value as any)?.package_id
    if (!pid) return
    const blob: any = await api.exportTrafficBundle(pid)
    const url = URL.createObjectURL(new Blob([blob], { type: 'application/zip' }))
    const a = document.createElement('a')
    a.href = url; a.download = `${pid}.zip`; a.click()
    setTimeout(() => URL.revokeObjectURL(url), 5000)
  } catch { ElMessage.error('ZIP导出失败') }
}
// 直投 L-Port：把包写进对方收件箱（共享挂载 /lport-lib）；勾了「投完直接出片」就顺带触发 run-traffic
const autoRunLport = ref(false)
const pushing = ref(false)
async function pushToLport() {
  const pid = (lastPkg.value as any)?.package_id
  if (!pid || pushing.value) return
  pushing.value = true
  try {
    const r: any = await (api as any).pushToLport(pid, autoRunLport.value, 0)
    const d = r?.data || r
    const n = d?.variants ?? (lastPkg.value as any)?.variants?.length ?? 0
    const job = d?.job_id || ''
    const err = d?.lport?.error || ''
    if (job) {
      ElMessage.success(`已投递并开始出片（${n} 条 · job ${job.slice(0, 8)}）→ L-Port「投流素材 → 产物」看结果`)
    } else if (err) {
      ElMessage.warning(`已投进 L-Port 收件箱（${n} 条），但触发出片失败：${err}`)
    } else {
      ElMessage.success(`已直投 L-Port（${n} 条）：L-Port 投流素材页选包点「运行」即可`)
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.msg || '直投失败（L-Port 没起？）')
  } finally { pushing.value = false }
}
async function copyOne(v: any) {
  const mt = v.mount || {}
  const mountLine = (mt.search_word || mt.app_name || mt.overlay_text) ? `\n挂载：${mt.search_word || '-'}/${mt.app_name || '-'}/${mt.overlay_text || '-'}` : ''
  try { await navigator.clipboard.writeText(`${v.variant_id}｜${v.hypothesis}\n${v.title}\n${v.hook_text}\n${v.hl_id}\n${v.cta_text}\n${v.file_name}${mountLine}`); ElMessage.success('已复制') } catch { ElMessage.error('复制失败') }
}
function blankTask() {
  return { id: ++seq, desc: '', mode: 'lib', category: '红包点击', count: 15, refVideo: '', _up: false, results: [], _open: true, engine: '', mount: { search_word: '', app_name: '', overlay_text: '' } }
}
// 清空工作区：任务描述/挂载位/结果/本地快照全清；服务端历史包不受影响（历史包 dialog 里单独删）
async function clearWorkspace() {
  const hasResults = tasks.value.some(t => (t.results?.length || 0) > 0)
  const hasInput = tasks.value.some(t => (t.desc || '').trim() || t.refVideo || t.mount?.search_word || t.mount?.app_name || t.mount?.overlay_text)
  if (!hasResults && !hasInput) return ElMessage.info('工作区已空')
  try {
    await ElMessageBox.confirm('清空当前任务的描述、挂载位与全部结果？本地快照一起清除，历史包不受影响。', '清空工作区', { type: 'warning', confirmButtonText: '清空', cancelButtonText: '取消' })
  } catch { return }
  tasks.value = [blankTask()]
  lastPkg.value = null
  try { localStorage.removeItem(snapKey()); localStorage.removeItem(runKey()) } catch {}
  saveSnap()
  ElMessage.success('工作区已清空')
}
function download() {
  const all = tasks.value.flatMap(t => (t.results || []).map(({ _open, ...r }: any) => r))
  if (!all.length) return
  const p = lastPkg.value || { package_id: all[0].batch_id, mother_id: motherId.value, tasks: tasks.value.map(t => ({ desc: t.desc, mode: t.mode, category: t.category, count: t.count, refVideo: t.refVideo, mount: t.mount })), variants: all }
  const blob = new Blob([JSON.stringify(p, null, 2)], { type: 'application/json' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob); a.download = `${p.package_id}.json`; a.click()
  URL.revokeObjectURL(a.href)
}
onMounted(() => {
  motherId.value = (store as any).episodeId || motherId.value
  restoreSnap()
  loadLib2()
  // 开机对账：快照里的结果必须能在服务端找到包，否则就是已删包的幽灵数据，直接清掉
  // （local回退的本地结果 engine==='local'，无包也合法，保留）
  const reconcile = () => {
    const hasServerResults = tasks.value.some(t => (t.results?.length || 0) > 0 && t.engine !== 'local')
    if (!hasServerResults) return
    let lastPkgId = ''
    try { lastPkgId = JSON.parse(localStorage.getItem(snapKey()) || '{}').lastPkgId || '' } catch {}
    if (!lastPkgId) {
      tasks.value.forEach(t => { if (t.engine !== 'local') { t.results = []; t.engine = '' } })
      lastPkg.value = null
      saveSnap()
      return
    }
    ;(api as any).package(lastPkgId).then((pr: any) => {
      const pd = pr?.data ?? pr
      if (pd && (!pd.mother_id || pd.mother_id === motherId.value)) {
        if (attachPkg(pd)) saveSnap()
      } else {
        tasks.value.forEach(t => { t.results = []; t.engine = '' })
        lastPkg.value = null
        saveSnap()
      }
    }).catch(() => {
      tasks.value.forEach(t => { t.results = []; t.engine = '' })
      lastPkg.value = null
      saveSnap()
    })
  }
  // 有运行标记（切走时正在跑）→ 先认领服务端已出的包，再对账
  recoverRunning().then(reconcile)
})
</script>
<style scoped>
.kun-page.mini{max-width:none;margin:0;width:100%;box-sizing:border-box;height:100%;display:flex;flex-direction:column;padding-bottom:76px}
.mini { display: flex; flex-direction: column; gap: 12px; }
.tcard { padding: 14px; display: flex; flex-direction: column; gap: 8px; flex-shrink: 0; }
.tcard.lib-card { flex: 1; min-height: 0; }
.t-desc { width: 100%; }
.t-desc :deep(.el-textarea__inner) { font-size: 14px; line-height: 1.6; border-radius: 12px; padding: 10px 12px; }
.t-ctl { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.t-mount { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.t-mount .m-in { flex: 1 1 120px; min-width: 0; max-width: 220px; }
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
.hist-list { display: flex; flex-direction: column; gap: 8px; max-height: 50vh; overflow-y: auto; }
.hist-item { display: flex; gap: 8px; align-items: center; border: 1px solid var(--suli-border); border-radius: 10px; padding: 8px 10px; }
.hist-item.active { border-color: var(--suli-primary); }
.hist-main { flex: 1; cursor: pointer; min-width: 0; }
.hist-pid { font-size: 12px; font-weight: 700; word-break: break-all; }
.hist-meta { font-size: 11px; color: var(--suli-text-3); margin-top: 2px; }
.lib-filters { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-top: 8px; flex-shrink: 0; }
.lib-body { flex: 1; min-height: 0; display: flex; flex-direction: column; }
.lib-body > div:last-child { flex: 1; min-height: 0; display: flex; flex-direction: column; }
.lib-list { margin-top: 6px; border-top: 1px solid var(--suli-border); flex: 1; min-height: 120px; overflow-y: auto; }
.lib-item { display: flex; gap: 8px; align-items: center; padding: 6px 0; border-top: 1px dashed var(--suli-border); font-size: 12px; }
.lib-item:first-child { border-top: none; }
.v-thumb { width: 96px; height: 54px; object-fit: cover; border-radius: 6px; background: var(--suli-bg-2, #f4f4f5); flex-shrink: 0; }
.lib-main { flex: 1; min-width: 0; }
.lib-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.lib-meta { font-size: 11px; color: var(--suli-text-3); margin-top: 2px; }
.img-grid { margin-top: 8px; display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 10px; flex: 1; min-height: 120px; overflow-y: auto; align-content: start; }
.img-cell { border: 1px solid var(--suli-border); border-radius: 10px; padding: 6px; text-align: center; position: relative; }
.cell-check { position: absolute; top: 4px; right: 4px; z-index: 2; background: var(--suli-surface); border-radius: 4px; }
.img-thumb { width: 100%; height: 90px; object-fit: contain; border-radius: 6px; background: var(--suli-bg-2, #f4f4f5); }
.img-name { font-size: 11px; margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.img-meta { font-size: 10px; color: var(--suli-text-3); }
.actionbar { padding: 12px 16px; display: flex; gap: 10px; align-items: center; flex-shrink: 0;
  background: color-mix(in srgb, var(--suli-surface) 92%, transparent);
  backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
  border-radius: 16px; box-shadow: 0 -6px 24px rgba(0, 0, 0, .10); }
.actionbar .el-button { border-radius: 999px; padding: 8px 22px; }
.actionbar .el-button--primary { font-weight: 800; letter-spacing: 2px; padding: 8px 34px;
  box-shadow: 0 4px 14px rgba(251, 114, 153, .45); }
.actionbar .el-button--primary:hover { filter: brightness(1.06); }
.actionbar .el-button.is-disabled { box-shadow: none; }
.actionbar-fixed { position: fixed; bottom: 12px; z-index: 100; }
</style>
