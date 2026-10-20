<template>
  <div class="suli-card kun-page art-studio">
    <!-- 顶栏：方案选择 / 保存 / 状态 -->
    <div class="studio-head">
      <h3 style="margin:0">单图创作</h3>
      <el-select
        v-model="curPlanId" size="small" placeholder="选择方案" clearable class="w-plan"
        @change="(v: string) => loadPlan(v)"
      >
        <el-option v-for="p in plans" :key="p.id" :label="p.title || p.id" :value="p.id" />
      </el-select>
      <el-button size="small" @click="newPlan">新建方案</el-button>
      <el-button size="small" type="primary" :loading="saving" @click="savePlan">保存</el-button>
      <el-button size="small" type="danger" plain :disabled="!curPlanId" @click="delPlan">删除</el-button>
      <span style="flex:1" />
      <el-tag size="small" :type="statusTagType">{{ statusLabel }}</el-tag>
    </div>

    <div class="studio-grid">
      <!-- 左：方案（与 agent 讨论产出） -->
      <div class="studio-col">
        <el-input v-model="form.title" size="small" placeholder="标题" />

        <div class="block-title">方案意图</div>
        <div class="grow">
          <el-input v-model="form.intent_text" type="textarea" :rows="8" />
        </div>

        <div class="lower">
          <div class="lower-body">
            <div class="block-title">目标引擎</div>
            <el-checkbox-group v-model="form.engines" size="small" class="engines">
              <el-checkbox v-for="e in ENGINE_OPTS" :key="e.key" :value="e.key" :label="e.label" />
            </el-checkbox-group>

            <div class="block-title">参考图 <span class="suli-muted tnum">{{ form.ref_images.length }}/6</span></div>
            <div class="refs">
              <div v-for="(r, i) in form.ref_images" :key="i" class="ref-item">
                <el-image
                  class="ref-thumb" :src="refUrl(r)" fit="cover" :alt="r.name"
                  :preview-src-list="refPreview" :initial-index="i" preview-teleported hide-on-click-modal
                >
                  <template #error><div class="ref-thumb-ph"><el-icon><Picture /></el-icon></div></template>
                </el-image>
                <div class="ref-meta">
                  <span class="ref-name" :title="r.name">{{ r.name }}</span>
                  <el-button link type="danger" size="small" @click="form.ref_images.splice(i, 1)">移除</el-button>
                </div>
              </div>
              <el-button class="ref-add" size="small" :loading="refUploading" :disabled="form.ref_images.length >= 6" @click="refInput?.click()">
                + 参考图
              </el-button>
              <input ref="refInput" type="file" accept="image/*" style="display:none" @change="onRefFile" />
            </div>

            <div class="block-title">约束 / 改图指令</div>
            <div class="note-grow">
              <el-input v-model="form.note" type="textarea" :rows="2" />
            </div>
          </div>

          <div class="row">
            <el-button type="primary" size="small" :loading="pushing" :disabled="pushing" @click="pushToLport">直投 L-Port</el-button>
            <el-button size="small" :disabled="pushing" @click="reload">刷新回传</el-button>
          </div>
          <div v-if="pushing || pushStage" class="push-progress">
            <el-progress
              :percentage="pushPct" :indeterminate="pushing && pushPct >= 25"
              :status="pushErr ? 'exception' : (pushDone ? 'success' : undefined)"
              :stroke-width="6" :show-text="false"
            />
            <div class="push-line">
              <span class="push-stage">{{ pushStage }}</span>
              <span class="suli-muted tnum">{{ (pushMs / 1000).toFixed(1) }}s</span>
            </div>
          </div>
          <div class="suli-muted" v-if="pushHint && !pushStage" style="margin-top:4px">{{ pushHint }}</div>
        </div>
      </div>

      <!-- 右：回传提示词 -->
      <div class="studio-col">
        <div class="block-title">
          回传提示词
          <span class="suli-muted tnum">{{ promptKeys.length }}</span>
          <el-button v-if="promptKeys.length" size="small" text style="margin-left:auto" @click="copyAll">复制全部</el-button>
        </div>
        <div v-if="waiting" class="wait-panel">
          <el-progress :percentage="100" :indeterminate="true" :stroke-width="5" :show-text="false" />
          <div class="wait-line">
            <span class="wait-text">等待 L-Port 回传 · 已等 <span class="tnum">{{ fmtDur(waitSec) }}</span> · 第 {{ waitChecks }} 次检查</span>
            <el-button link size="small" @click="stopWait('已停止等待')">停止</el-button>
          </div>
        </div>
        <div v-else-if="waitNote" class="wait-note">{{ waitNote }}</div>
        <el-empty
          v-if="!promptKeys.length" class="empty-fill" :image-size="64"
          :description="waiting ? '等待 L-Port 回传' : '暂无回传'"
        />
        <div v-else class="prompt-scroll">
          <div v-for="k in promptKeys" :key="k" class="prompt-card">
            <div class="prompt-head">
              <b>{{ engineLabel(k) }}</b>
              <span class="suli-muted">{{ prompts[k]?.source || '' }}</span>
              <span style="flex:1" />
              <el-button size="small" text @click="copyPrompt(k)">复制</el-button>
            </div>
            <div class="prompt-row">
              <span class="lbl">正向</span>
              <pre>{{ prompts[k]?.positive || '—' }}</pre>
            </div>
            <div class="prompt-row" v-if="prompts[k]?.negative">
              <span class="lbl">负向</span>
              <pre>{{ prompts[k]?.negative }}</pre>
            </div>
            <div class="prompt-row" v-if="prompts[k]?.note">
              <span class="lbl">备注</span>
              <pre>{{ prompts[k]?.note }}</pre>
            </div>
            <div class="suli-muted" v-if="prompts[k]?.at" style="font-size:12px">回传于 {{ fmtTs(prompts[k]?.at) }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Picture } from '@element-plus/icons-vue'
import { api } from '../api/client'
import { useStudioStore } from '../stores/studio'

defineOptions({ name: 'ArtStudioView' })

const ENGINE_OPTS = [
  { key: 'novelai', label: 'NovelAI' },
  { key: 'tsubaki3', label: 'Tsubaki.3' },
  { key: 'seedream', label: 'Seedream' },
  { key: 'anima', label: 'Anima' },
  { key: 'gpt_image', label: 'GPT Image' },
  { key: 'flux', label: 'FLUX' },
  { key: 'sdxl', label: 'SDXL' },
  { key: 'pony', label: 'Pony' },
  { key: 'cloud', label: '云模板' },
]

type RefImg = { name: string; path: string; url: string }
type PlanForm = {
  title: string
  intent_text: string
  engines: string[]
  ref_images: RefImg[]
  note: string
}

const DEFAULT_ENGINES = ['novelai', 'tsubaki3', 'seedream']

const plans = ref<any[]>([])
const curPlanId = ref('')
const blankForm = (): PlanForm => ({ title: '', intent_text: '', engines: [...DEFAULT_ENGINES], ref_images: [], note: '' })
const form = ref<PlanForm>(blankForm())
const studio = useStudioStore()
// 右侧 Agent 的页面感知：把当前方案原样同步给 store（切方案/打字都跟着变）
watch([form, curPlanId], () => {
  studio.setPlan({
    id: curPlanId.value,
    title: form.value.title,
    intent_text: form.value.intent_text,
    engines: form.value.engines,
    note: form.value.note,
    ref_images: form.value.ref_images,
  })
}, { deep: true })
const prompts = ref<Record<string, any>>({})
const status = ref('draft')
const saving = ref(false)
const pushing = ref(false)
const pushHint = ref('')
const refInput = ref<HTMLInputElement | null>(null)
const refUploading = ref(false)

// 直投进度：保存 → 打包参考图/写收件箱（不确定阶段走 indeterminate）→ 完成/失败
const pushPct = ref(0)
const pushStage = ref('')
const pushMs = ref(0)
const pushDone = ref(false)
const pushErr = ref(false)
let pushT0 = 0
let pushTicker: number | null = null
let pushHideTimer: number | null = null
function pushStep(text: string, pct: number) { pushStage.value = text; pushPct.value = pct }
function pushStopTicker() { if (pushTicker !== null) { clearInterval(pushTicker); pushTicker = null } }
function pushReset() {
  pushPct.value = 0
  pushStage.value = ''
  pushMs.value = 0
  pushDone.value = false
  pushErr.value = false
}
// 回传等待：直投成功后（或载入一个刚投递的方案）轮询轻量状态，收敛即拉提示词。
// L-Port 跑节点是它自己的事、没有跨仓进度接口，所以这里只做「等结果」的诚实进度：
// 流动条 + 已等时长 + 检查次数，收到回传立刻拉取并停下。
const WAIT_INTERVAL = 3000
const WAIT_MAX_CHECKS = 240 // 3s × 240 ≈ 12 分钟
const waiting = ref(false)
const waitSec = ref(0)
const waitChecks = ref(0)
const waitNote = ref('')
let waitTick: number | null = null
let waitTimer: number | null = null
let waitT0 = 0
let waitBaseCount = 0
let waitBaseAt = ''

/** 后端时间戳统一按 UTC 解析：容器跑 UTC 且老数据没有时区后缀，浏览器会当本地时间 → 差 8 小时。 */
function tsMs(s: string): number {
  if (!s) return NaN
  return Date.parse(/[zZ]|[+-]\d{2}:?\d{2}$/.test(s) ? s : s + 'Z')
}
/** 时间戳按浏览器本地时区展示。 */
function fmtTs(s: string): string {
  const ms = tsMs(s)
  if (!isFinite(ms)) return s || ''
  const d = new Date(ms)
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}
function fmtDur(sec: number): string {
  const v = Math.max(0, Math.round(sec))
  const m = Math.floor(v / 60)
  return m ? `${m}:${String(v % 60).padStart(2, '0')}` : `${v}s`
}
function maxPromptAt(): string {
  return Object.values(prompts.value as Record<string, any>).map((p: any) => String(p?.at || '')).sort().pop() || ''
}
function waitClearTimers() {
  if (waitTick !== null) { clearInterval(waitTick); waitTick = null }
  if (waitTimer !== null) { clearTimeout(waitTimer); waitTimer = null }
}
function stopWait(note = '') {
  waitClearTimers()
  waiting.value = false
  if (note) waitNote.value = note
}
function startWait() {
  waitClearTimers()
  if (!curPlanId.value) return
  waiting.value = true
  waitNote.value = ''
  waitSec.value = 0
  waitChecks.value = 0
  waitT0 = Date.now()
  waitBaseCount = promptKeys.value.length
  waitBaseAt = maxPromptAt()
  waitTick = window.setInterval(() => { waitSec.value = Math.floor((Date.now() - waitT0) / 1000) }, 1000)
  waitTimer = window.setTimeout(pollWait, 1200)
}
async function pollWait() {
  if (!waiting.value || !curPlanId.value) return
  waitChecks.value += 1
  try {
    const r: any = await api.planStatus(curPlanId.value)
    const d = r?.data || {}
    const count = Number(d.prompt_count || 0)
    const at = String(d.prompt_at || '')
    if (count > waitBaseCount || (at && at > waitBaseAt)) {
      await applyReturned(d)
      return
    }
  } catch { /* 网络抖动：下一轮再看 */ }
  if (!waiting.value) return
  if (waitChecks.value >= WAIT_MAX_CHECKS) {
    stopWait(`已等 ${fmtDur(waitSec.value)} 还没收到回传：去 L-Port 看链路，或点「刷新回传」`)
    return
  }
  waitTimer = window.setTimeout(pollWait, WAIT_INTERVAL)
}
async function applyReturned(st: any) {
  const id = curPlanId.value
  waitClearTimers()
  waiting.value = false
  try {
    const r: any = await api.getPlan(id)
    if (r?.data?.prompts) prompts.value = r.data.prompts
    if (r?.data?.status) status.value = r.data.status
  } catch { /* 拉详情失败就等下一轮刷新按钮 */ }
  const keys: string[] = (st?.prompt_engines?.length ? st.prompt_engines : promptKeys.value)
  const names = keys.map(engineLabel)
  waitNote.value = `已回传 ${names.length} 个引擎：${names.join(' / ')} · 用时 ${fmtDur(waitSec.value)}`
  ElMessage.success('已回传：' + names.join(' / '))
  await loadPlans()
}


const promptKeys = computed(() => Object.keys(prompts.value))

/** 参考图地址：优先 url；老数据只存了 path/name 时按 basename 兜底（/api/images/<name>）。 */
function refUrl(r: RefImg): string {
  if (r?.url) return r.url
  const base = String(r?.path || r?.name || '').replace(/\\/g, '/').split('/').pop() || ''
  return base ? `/api/images/${encodeURIComponent(base)}` : ''
}
const refPreview = computed(() => form.value.ref_images.map(refUrl))
const statusLabel = computed(() =>
  ({ draft: '草案', pushed: '已投 L-Port', returned: '已回传' } as Record<string, string>)[status.value] || status.value)
const statusTagType = computed<'success' | 'warning' | 'info'>(() =>
  status.value === 'returned' ? 'success' : status.value === 'pushed' ? 'warning' : 'info')

function engineLabel(k: string): string {
  return ENGINE_OPTS.find(e => e.key === k)?.label || k
}

async function loadPlans() {
  try {
    const r: any = await api.listPlans()
    plans.value = r?.data || []
  } catch {
    ElMessage.error('方案列表拉取失败，后端未起？')
  }
}

function newPlan() {
  stopWait('')
  waitNote.value = ''
  curPlanId.value = ''
  form.value = blankForm()
  prompts.value = {}
  status.value = 'draft'
  pushHint.value = ''
}

async function loadPlan(id: string) {
  if (!id) return newPlan()
  try {
    const r: any = await api.getPlan(id)
    const d = r?.data || {}
    curPlanId.value = d.id || id // 自动载入也要认领 id，否则保存/直投会新建重复方案
    form.value = {
      title: d.title || '',
      intent_text: d.intent_text || '',
      engines: Array.isArray(d.engines) && d.engines.length ? d.engines : [...DEFAULT_ENGINES],
      ref_images: Array.isArray(d.ref_images) ? d.ref_images : [],
      note: d.note || '',
    }
    prompts.value = d.prompts || {}
    status.value = d.status || 'draft'
    pushHint.value = d.push?.package_id ? '已投 ' + d.push.package_id : ''
    // 续上回传等待：只有「已投递且还没有提示词」且投递在 30 分钟内的方案才自动等
    stopWait('')
    waitNote.value = ''
    const pushedAt = String(d.push?.at || '')
    const ageMin = pushedAt ? (Date.now() - tsMs(pushedAt)) / 60000 : 1e9
    if (curPlanId.value && status.value === 'pushed' && !promptKeys.value.length && ageMin <= 30) startWait()
  } catch (e: any) {
    ElMessage.error('方案拉取失败：' + (e?.response?.data?.msg || e?.message || e))
  }
}

/** 存当前表单；返回生效的方案 id（'' 表示失败）。 */
async function savePlan(): Promise<string> {
  if (!form.value.engines.length) {
    ElMessage.warning('至少选一个目标引擎')
    return ''
  }
  saving.value = true
  try {
    const body: any = {
      title: form.value.title,
      intent_text: form.value.intent_text,
      engines: form.value.engines,
      ref_images: form.value.ref_images,
      note: form.value.note,
    }
    if (curPlanId.value) body.id = curPlanId.value
    const r: any = await api.savePlan(body)
    const d = r?.data || {}
    curPlanId.value = d.id || curPlanId.value
    status.value = d.status || status.value
    await loadPlans()
    return curPlanId.value
  } catch (e: any) {
    ElMessage.error('保存失败：' + (e?.response?.data?.msg || e?.message || e))
    return ''
  } finally {
    saving.value = false
  }
}

async function delPlan() {
  if (!curPlanId.value) return
  try {
    await api.deletePlan(curPlanId.value)
    ElMessage.success('已删除')
    newPlan()
    await loadPlans()
  } catch (e: any) {
    ElMessage.error('删除失败：' + (e?.response?.data?.msg || e?.message || e))
  }
}

async function pushToLport() {
  if (pushing.value) return
  if (pushHideTimer !== null) { clearTimeout(pushHideTimer); pushHideTimer = null }
  pushReset()
  stopWait('')
  if (!form.value.intent_text.trim()) return ElMessage.warning('方案还没有意图文本：先与 agent 讨论出方案')
  pushing.value = true
  pushT0 = performance.now()
  pushTicker = window.setInterval(() => { pushMs.value = Math.round(performance.now() - pushT0) }, 100)
  try {
    pushStep('保存方案', 8)
    const id = await savePlan() // 直投前先存，保证包里是最新方案
    if (!id) { pushErr.value = true; pushStage.value = '保存失败，未投递'; return }
    const n = form.value.ref_images.length
    pushStep(n ? `打包 ${n} 张参考图 · 写 L-Port 收件箱` : '写 L-Port 收件箱', 25)
    const r: any = await api.pushToLport(id)
    const d = r?.data || {}
    pushPct.value = 100
    pushDone.value = true
    const ms = d.elapsed_ms != null ? `${d.elapsed_ms}ms` : `${(pushMs.value / 1000).toFixed(1)}s`
    const size = d.zip_bytes ? ` · ${Math.max(1, Math.round(d.zip_bytes / 1024))} KB` : ''
    pushStage.value = `已投 ${d.package_id || ''} · ${n} 张参考图${size} · 后端 ${ms}`
    pushHint.value = `已投 ${d.package_id || ''}`
    status.value = 'pushed'
    ElMessage.success('已直投 L-Port：' + (d.package_id || ''))
    startWait() // 投完进等待：L-Port 那边跑完会自动回传，这边自动亮
    pushHideTimer = window.setTimeout(pushReset, 4000)
  } catch (e: any) {
    pushErr.value = true
    pushStage.value = '直投失败：' + (e?.response?.data?.msg || e?.message || e)
    ElMessage.error('直投失败：' + (e?.response?.data?.msg || e?.message || e))
  } finally {
    pushing.value = false
    pushStopTicker()
  }
}

async function reload() {
  if (curPlanId.value) await loadPlan(curPlanId.value)
  await loadPlans()
}

async function onRefFile(e: any) {
  const f = e.target.files?.[0]
  e.target.value = ''
  if (!f) return
  if (!f.type.startsWith('image/')) return ElMessage.warning('只要图片')
  if (f.size > 10 * 1024 * 1024) return ElMessage.warning('图片超过 10MB')
  refUploading.value = true
  try {
    const d: any = await api.uploadFile(f)
    const row: any = d?.data || d
    form.value.ref_images.push({ name: f.name, path: row.path, url: row.url })
  } catch {
    ElMessage.error('上传失败，后端未起？')
  } finally {
    refUploading.value = false
  }
}

async function copyText(text: string) {
  try {
    await navigator.clipboard.writeText(text || '')
    ElMessage.success('已复制')
  } catch {
    ElMessage.warning('复制失败（浏览器不放行剪贴板）')
  }
}

function copyPrompt(k: string) {
  const p = prompts.value[k] || {}
  const parts: string[] = []
  if (p.positive) parts.push(p.positive)
  if (p.negative) parts.push('Negative: ' + p.negative)
  copyText(parts.join('\n\n'))
}

function copyAll() {
  const blocks = promptKeys.value.map(k => {
    const p = prompts.value[k] || {}
    const lines = [`【${engineLabel(k)}】`]
    if (p.positive) lines.push(p.positive)
    if (p.negative) lines.push('Negative: ' + p.negative)
    return lines.join('\n')
  })
  copyText(blocks.join('\n\n----------\n\n'))
}

onUnmounted(() => {
  pushStopTicker()
  waitClearTimers()
  if (pushHideTimer !== null) { clearTimeout(pushHideTimer); pushHideTimer = null }
})

onMounted(async () => {
  await loadPlans()
  if (plans.value.length) await loadPlan(plans.value[0].id)
})
</script>

<style scoped>
/* 工作台页统一放开 7xl 居中骨架（theme.css 的 .kun-page 是 96rem + margin:auto），
   否则宽屏下本页卡片被居中封在 1536px，与全宽顶栏（.topbar）左右都对不齐。 */
.kun-page { max-width:none; margin:0; width:100%; box-sizing:border-box }
/* 整页排版：卡片撑满中央工作区高度；内容更高时整页滚动，不裁切 */
.art-studio { min-height:100%; display:flex; flex-direction:column; padding:14px }
.studio-head { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.w-plan { width: 240px; }
.block-title { display:flex; align-items:center; gap:6px; margin:14px 0 6px; font-weight:600; font-size:13px; }
.studio-grid { display:grid; grid-template-columns: minmax(320px, 1fr) minmax(320px, 1fr); gap:18px; margin-top:12px; flex:1 0 auto; min-height:0 }
@media (max-width: 1000px) { .studio-grid { grid-template-columns: 1fr; flex:0 0 auto } }
.studio-col { min-width:0; display:flex; flex-direction:column; min-height:0 }
/* 左栏纵向平分：意图框上半 / 引擎·参考图·约束下半（各占一半；下半内容多时中段内滚，按钮常驻底部） */
.grow { flex:1 1 0; min-height:120px; display:flex }
.grow :deep(.el-textarea) { flex:1; display:flex }
.grow :deep(.el-textarea__inner) { height:100%; resize:none }
.lower { flex:1 1 0; min-height:0; display:flex; flex-direction:column }
.lower-body { flex:1 1 auto; min-height:0; overflow:auto; padding-right:4px; display:flex; flex-direction:column }
.lower .block-title { margin:8px 0 4px }
.lower > .lower-body > .block-title:first-child { margin-top:0 }
.lower .engines { gap:2px 12px }
.lower .refs { gap:8px }
.note-grow { flex:1 1 auto; min-height:44px; display:flex }
.note-grow :deep(.el-textarea) { flex:1; display:flex }
.note-grow :deep(.el-textarea__inner) { height:100%; resize:none }
.prompt-scroll { flex:1 1 0; min-height:0; overflow:auto; padding-right:4px }
.empty-fill { flex:1; display:flex; flex-direction:column; justify-content:center }
.row { display:flex; align-items:center; gap:8px; margin-top:8px; flex-wrap:wrap; }
/* 直投进度：细进度条 + 阶段文案 + 已用时间 */
.push-progress { margin-top:8px }
.push-line { display:flex; align-items:flex-start; gap:8px; margin-top:4px; font-size:12px; line-height:1.45 }
.push-stage { flex:1; min-width:0; word-break:break-all }
.push-line .suli-muted { flex:0 0 auto }
/* 回传等待：流动条 + 已等时长 + 检查次数（L-Port 那边没有进度接口，靠轮询状态收敛） */
.wait-panel { margin:0 0 8px; padding:8px 10px; border:1px solid var(--el-border-color-lighter); border-radius:8px; background:var(--el-fill-color-lighter) }
.wait-line { display:flex; align-items:center; gap:8px; margin-top:4px; font-size:12px; line-height:1.4 }
.wait-text { flex:1; min-width:0 }
.wait-note { font-size:12px; color:var(--el-text-color-secondary); margin:0 0 8px; line-height:1.4 }
.engines { display:flex; flex-wrap:wrap; gap:4px 12px; }
.refs { display:flex; flex-wrap:wrap; gap:10px; align-items:flex-start; }
.ref-item { display:flex; align-items:center; gap:8px; border:1px solid var(--el-border-color-lighter); border-radius:10px; padding:4px 10px 4px 4px; }
.ref-thumb { width:64px; height:64px; border-radius:8px; overflow:hidden; display:block; flex:0 0 auto; background:var(--el-fill-color-light); cursor:zoom-in; }
.ref-thumb-ph { width:100%; height:100%; display:flex; align-items:center; justify-content:center; font-size:20px; color:var(--el-text-color-placeholder); }
.ref-meta { display:flex; flex-direction:column; align-items:flex-start; gap:2px; min-width:0; }
.ref-name { font-size:12px; max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.ref-add { align-self:center; }
.prompt-card { border:1px solid var(--el-border-color-lighter); border-radius:10px; padding:10px; margin-bottom:10px; }
.prompt-head { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
.prompt-row { display:flex; gap:8px; margin-top:6px; }
.prompt-row .lbl { flex:0 0 32px; font-size:12px; color:var(--el-text-color-secondary); }
.prompt-row pre { flex:1; margin:0; white-space:pre-wrap; word-break:break-word; font-size:12px; background:var(--el-fill-color-light); border-radius:6px; padding:6px 8px; }
</style>
