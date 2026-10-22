<template>
  <div class="suli-card kun-page art-studio">
    <!-- 顶栏：方案选择 / 保存 / 状态 -->
    <div class="studio-head">
      <h3 style="margin:0">{{ mode === 'comic' ? '漫画创作' : '单图创作' }}</h3>
      <el-radio-group v-model="mode" size="small" @change="onModeChange">
        <el-radio-button label="single">单图</el-radio-button>
        <el-radio-button label="comic">漫画</el-radio-button>
      </el-radio-group>
      <el-select
        v-if="mode === 'single'"
        v-model="curPlanId" size="small" placeholder="选择方案" clearable class="w-plan"
        @change="(v: string) => loadPlan(v)"
      >
        <el-option v-for="p in singlePlans" :key="p.id" :label="p.title || p.id" :value="p.id" />
      </el-select>
      <el-button v-if="mode === 'single'" size="small" @click="newPlan">新建方案</el-button>
      <el-button size="small" type="primary" :loading="saving" @click="savePlan">保存</el-button>
      <el-button size="small" type="danger" plain :disabled="!curPlanId" @click="delPlan">删除</el-button>
      <span style="flex:1" />
      <el-tag size="small" :type="statusTagType">{{ statusLabel }}</el-tag>
    </div>

    <!-- 漫画：集号 + 大纲 + 剧本条 + 页/格条 -->
    <ComicStrip
      v-if="mode === 'comic'"
      :pages="pages"
      :panels="panels"
      :current-page-index="currentPageIndex"
      :current-plan-id="curPlanId"
      :episode-id="episodeId"
      :outline="outlineMd"
      :outline-loading="outlineLoading"
      @select="loadPlan"
      @select-page="selectComicPage"
      @new-page="newComicPage"
      @new-panel="newComicPanel"
      @read-outline="readOutline(false)"
      @apply-outline="applyOutline"
    >
      <template #script>
        <div class="script-bar">
          <span class="suli-muted">剧本 <b class="tnum">{{ scriptPanels.length }}</b> 格</span>
          <el-tag v-if="scriptMeta.tier" size="small" type="danger">{{ tierLabel(scriptMeta.tier) }}</el-tag>
          <el-button size="small" :loading="scriptBusy === 'outline'" @click="scriptFromOutline">从大纲转</el-button>
          <el-button size="small" type="primary" :loading="scriptBusy === 'split'" @click="splitScript">拆格</el-button>
          <el-button size="small" @click="scriptDialog = true">编辑剧本</el-button>
        </div>
      </template>
    </ComicStrip>

    <!-- 剧本编辑：整表在宽弹层里改，不挤工作区 -->
    <el-dialog v-model="scriptDialog" title="编辑剧本" width="min(1400px, 94vw)" top="5vh" class="script-dialog">
      <ComicScript
        v-model:panels="scriptPanels"
        v-model:meta="scriptMeta"
        :busy="scriptBusy"
        @save="saveScript"
        @split="splitScript"
      />
    </el-dialog>

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

            <div class="tier-row">
              <span class="tier-lbl">水位</span>
              <el-select v-model="form.tier" size="small" clearable placeholder="常规" class="tier-sel">
                <el-option v-for="t in TIERS" :key="t.value" :label="t.label" :value="t.value" />
              </el-select>
              <span class="tier-lbl">衣物</span>
              <el-select v-model="form.clothing_level" size="small" clearable placeholder="—" class="tier-sel">
                <el-option v-for="c in CLOTH" :key="c" :label="c" :value="c" />
              </el-select>
            </div>

            <!-- 参考图 与 本格成图 并排：两个素材区各占一半，省纵向空间 -->
            <div class="asset-row">
              <div class="asset-block">
                <div class="block-title">参考图 <span class="suli-muted tnum">{{ form.ref_images.length }}/6</span></div>
                <div class="refs">
                  <div v-for="(r, i) in form.ref_images" :key="i" class="ref-item">
                    <el-image
                      class="ref-thumb" :src="refUrl(r)" fit="cover" :alt="r.name"
                      :preview-src-list="refPreview" :initial-index="i" preview-teleported hide-on-click-modal
                    >
                      <template #error><div class="ref-thumb-ph"><el-icon><Picture /></el-icon></div></template>
                    </el-image>
                    <button class="ref-tag" :title="'插入 @参考' + (i + 1)" @click.stop="insertRefToken(i)">@参考{{ i + 1 }}</button>
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
              </div>

              <!-- 漫画格：本格成图（下一格自动带进参考图） -->
              <div v-if="mode === 'comic'" class="asset-block">
                <div class="block-title">本格成图</div>
                <div class="page-shot">
                  <el-image
                    v-if="pageImage" class="page-shot-img" :src="pageImage.url" fit="cover"
                    :preview-src-list="[pageImage.url]" preview-teleported hide-on-click-modal
                  />
                  <div v-else class="page-shot-ph"><el-icon><Picture /></el-icon></div>
                  <div class="page-shot-act">
                    <el-button size="small" :loading="shotUploading" @click="shotInput?.click()">上传成图</el-button>
                    <el-button size="small" text :disabled="!pageImage" @click="removePageImage">移除</el-button>
                    <input ref="shotInput" type="file" accept="image/*" style="display:none" @change="onShotFile" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 约束：固定高度常驻（不跟上面的内容一起被滚走）；@ 唤起参考图内联引用 -->
          <div class="note-block">
            <div class="block-title">约束</div>
            <div class="note-grow">
              <div class="textarea-wrap">
                <div
                  ref="noteEditor"
                  class="note-editor"
                  contenteditable="true"
                  data-ph="约束"
                  @input="onNoteInput"
                  @keydown="onNoteKeydown"
                  @click="updateNoteMention"
                  @blur="noteMentionOpen = false"
                />
                <div v-if="noteMentionOpen && noteCandidates.length" class="mention-popup">
                  <div class="mention-popup-title">参考图</div>
                  <button
                    v-for="(c, i) in noteCandidates"
                    :key="c.token"
                    :class="['mention-item', { active: i === noteMentionIndex }]"
                    @mousedown.prevent="applyNoteMention(c.token)"
                  >
                    <img v-if="c.url" :src="c.url" class="mention-thumb" alt="" />
                    <span class="mention-name">{{ c.token }}</span>
                    <span class="mention-sub">{{ c.sub }}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <PlanChangeCard
            v-if="changeRows.length"
            class="chg-card"
            :plan-id="curPlanId"
            :rows="changeRows"
            :action="formDirty"
            @action="reloadPlan"
          />

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
import { useAppStore } from '../stores/app'
import PlanChangeCard from '../components/PlanChangeCard.vue'
import ComicStrip, { type ComicPage, type ComicPanel } from '../components/studio/ComicStrip.vue'
import ComicScript, { type ScriptPanel, type ScriptMeta } from '../components/studio/ComicScript.vue'
import { TIERS, CLOTH, tierLabel } from '../utils/tier'
import { planChangeRows, refNames } from '../utils/planDiff'

defineOptions({ name: 'ArtStudioView' })

const ENGINE_OPTS = [
  { key: 'novelai', label: 'NovelAI' },
  { key: 'tsubaki3', label: 'Tsubaki.3' },
  { key: 'seedream', label: 'Seedream' },
  { key: 'mango3', label: 'Mango 3' },
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
  tier: string
  clothing_level: string
}
/** 漫画页上下文（落在方案的 page 字段） */
type PageMeta = {
  episode_id: string
  index: number
  panel_index: number
  prev_plan_id: string
  outline_text: string
  image: RefImg | null
}

const DEFAULT_ENGINES = ['novelai', 'tsubaki3', 'seedream']

const plans = ref<any[]>([])
const curPlanId = ref('')
const blankForm = (): PlanForm => ({ title: '', intent_text: '', engines: [...DEFAULT_ENGINES], ref_images: [], note: '', tier: '', clothing_level: '' })
const form = ref<PlanForm>(blankForm())
const studio = useStudioStore()
const store = useAppStore()
// 单图模式下拉只列非漫画页的方案（漫画页归页条管）
const singlePlans = computed(() => plans.value.filter(p => !p.page))
// 右侧 Agent 的页面感知：把当前方案原样同步给 store（切方案/打字都跟着变）
watch([form, curPlanId], () => {
  studio.setPlan({
    id: curPlanId.value,
    title: form.value.title,
    intent_text: form.value.intent_text,
    engines: form.value.engines,
    note: form.value.note,
    ref_images: form.value.ref_images,
    tier: form.value.tier,
  })
}, { deep: true })
const prompts = ref<Record<string, any>>({})
/** 最近一次从服务端读到的方案原样（含 prev 改前快照） */
const planRaw = ref<any>(null)
const status = ref('draft')
const saving = ref(false)
const pushing = ref(false)
const pushHint = ref('')
const refInput = ref<HTMLInputElement | null>(null)
const refUploading = ref(false)

// ── 漫画模式（页序列）───────────────────────────────────────────────────────
// 漫画一页由若干格组成，**一格 = 一个方案**（一次直投 = 一格出图）：
//   page.index = 页序；page.panel_index = 页内格序；page.prev_plan_id = 上一格。
// 衔接靠两样：本页成图（下一格自动进参考图）、大纲快照（整页共享）。
const mode = ref<'single' | 'comic'>('single')
const episodeId = computed(() => store.episodeId || '')
const allPanels = ref<ComicPanel[]>([])   // 全部格（按页序+格序）
const pages = ref<ComicPage[]>([])         // 页（按页序聚合）
const panels = ref<ComicPanel[]>([])       // 当前页的格
const currentPageIndex = ref(0)
const outlineMd = ref('')
const outlineLoading = ref(false)
const outlineCache = ref<Record<string, string>>({})
// 漫画剧本：一本剧本 = 页/格分条；拆格后每格变成一个方案
const scriptPanels = ref<ScriptPanel[]>([])
const scriptMeta = ref<ScriptMeta>({ premise: '', characters: '', style_hint: '', tier: '' })
const scriptBusy = ref('')
const scriptDialog = ref(false)
const blankPage = (): PageMeta => ({ episode_id: '', index: 0, panel_index: 0, prev_plan_id: '', outline_text: '', image: null })
const pageMeta = ref<PageMeta>(blankPage())
const pageImage = computed(() => pageMeta.value.image)
const shotInput = ref<HTMLInputElement | null>(null)
const shotUploading = ref(false)
/** 上一格的成图文件名（给右栏 agent 看：这一格接着哪张图画） */
const prevImageName = computed(() => {
  const prev = allPanels.value.find(p => p.planId === pageMeta.value.prev_plan_id)
  return prev?.image?.name || ''
})
// 页/格上下文也同步给右栏：agent 才知道这是第几页第几格、大纲是什么、上一格长什么样
watch([pageMeta, allPanels], () => {
  studio.setPageCtx({
    episode_id: pageMeta.value.episode_id,
    index: pageMeta.value.index,
    panel_index: pageMeta.value.panel_index,
    outline_text: pageMeta.value.outline_text,
    prev_image: prevImageName.value,
  })
}, { deep: true })
// 剧本也同步给右栏：agent 照着它改格
watch(scriptPanels, () => {
  studio.setScript(scriptPanels.value.map(p => ({
    page: p.page, panel: p.panel, text: p.text, dialogue: p.dialogue, camera: p.camera,
    tier: p.tier, clothing_level: p.clothing_level,
  })))
}, { deep: true })

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

// ── 约束内联编辑器：@ 唤起参考图引用，插入的 token 是带缩略图的原子丸子（学 L-Port /prompt）──
const noteEditor = ref<HTMLDivElement | null>(null)

const PILL_STYLE =
  'display:inline-flex;align-items:center;gap:3px;height:1.3em;max-height:1.3em;' +
  'padding:0 7px 0 3px;border-radius:5px;vertical-align:-0.25em;font-size:.92em;' +
  'white-space:nowrap;font-weight:600;background:rgba(99,102,241,.12);color:#6366f1;'
const PILL_IMG_STYLE =
  'width:1.15em;height:1.15em;max-width:1.15em;max-height:1.15em;flex:none;' +
  'object-fit:cover;border-radius:3px;'

const RE_REF_TOKEN = /(@参考[1-6])/g
const RE_REF_ONE = /@参考([1-6])/

function pillNode(token: string): HTMLSpanElement {
  const span = document.createElement('span')
  span.className = 'pill'
  span.contentEditable = 'false'
  span.dataset.name = token
  span.setAttribute('style', PILL_STYLE)
  const m = token.match(RE_REF_ONE)
  const r = m ? form.value.ref_images[Number(m[1]) - 1] : null
  if (r) {
    const img = document.createElement('img')
    img.src = refUrl(r)
    img.alt = ''
    img.className = 'pill-thumb'
    img.setAttribute('style', PILL_IMG_STYLE)
    img.contentEditable = 'false'
    img.draggable = false
    span.appendChild(img)
  }
  span.appendChild(document.createTextNode(token))
  return span
}

/** 编辑器 DOM → 纯文本：丸子还原成 token，BR 还原成换行。 */
function serializeNoteNode(node: Node): string {
  if (node.nodeType === Node.TEXT_NODE) return node.textContent || ''
  if (node.nodeName === 'BR') return '\n'
  if (node instanceof HTMLElement) {
    if (node.classList.contains('pill')) return node.dataset.name || ''
    let s = ''
    node.childNodes.forEach((c) => { s += serializeNoteNode(c) })
    if (node.nodeName === 'DIV' || node.nodeName === 'P') return s + '\n'
    return s
  }
  return ''
}

function readNote(): string {
  const el = noteEditor.value
  if (!el) return form.value.note
  let s = ''
  el.childNodes.forEach((c) => { s += serializeNoteNode(c) })
  return s.replace(/\n+$/, '')
}

/** 纯文本 → 编辑器 DOM：token 段落还原成丸子。 */
function renderNote(text: string) {
  const el = noteEditor.value
  if (!el) return
  el.innerHTML = ''
  const frag = document.createDocumentFragment()
  text.split('\n').forEach((line, li) => {
    if (li > 0) frag.appendChild(document.createElement('br'))
    line.split(RE_REF_TOKEN).forEach((p) => {
      if (!p) return
      if (RE_REF_ONE.test(p)) frag.appendChild(pillNode(p))
      else frag.appendChild(document.createTextNode(p))
    })
  })
  if (!frag.hasChildNodes()) frag.appendChild(document.createElement('br'))
  el.appendChild(frag)
}

// 编辑器里的内容已经和 form.note 一致时（自己刚回写的）不重建，保光标
watch(() => form.value.note, (v) => {
  const el = noteEditor.value
  if (!el) return
  if (readNote() === v) return
  renderNote(v)
})

function insertNodesAtCaret(nodes: Node[]) {
  const el = noteEditor.value
  if (!el) return
  el.focus()
  const sel = window.getSelection()
  let range: Range
  if (sel && sel.rangeCount && el.contains(sel.getRangeAt(0).startContainer)) {
    range = sel.getRangeAt(0)
  } else {
    range = document.createRange()
    range.selectNodeContents(el)
    range.collapse(false)
  }
  const pre = range.cloneRange()
  pre.selectNodeContents(el)
  pre.setEnd(range.startContainer, range.startOffset)
  const needLeadingSpace = !!pre.toString() && !/\s$/.test(pre.toString())
  range.deleteContents()
  const frag = document.createDocumentFragment()
  if (needLeadingSpace) frag.appendChild(document.createTextNode(' '))
  nodes.forEach((n) => frag.appendChild(n))
  const lastNode = frag.lastChild as Node | null
  range.insertNode(frag)
  const after = document.createRange()
  if (lastNode && lastNode.parentNode) after.setStartAfter(lastNode)
  else after.selectNodeContents(el)
  after.collapse(false)
  sel?.removeAllRanges()
  sel?.addRange(after)
  form.value.note = readNote()
}

/** 参考图缩略图上的 @参考N 角标：点了把丸子插进约束光标处。 */
function insertRefToken(i: number) {
  if (i < 0 || i >= form.value.ref_images.length) return
  insertNodesAtCaret([pillNode('@参考' + (i + 1)), document.createTextNode(' ')])
}

// ── @ 联想：光标前有 @xxx 待补全时弹出候选，↑↓选择、Enter/Tab 确认 ──
const noteMentionOpen = ref(false)
const noteMentionFilter = ref('')
const noteMentionIndex = ref(0)

const noteCandidates = computed(() => {
  const list = form.value.ref_images.map((r, i) => ({
    token: '@参考' + (i + 1), sub: r.name, url: refUrl(r),
  }))
  const q = noteMentionFilter.value
  if (!q) return list
  return list.filter((c) => c.token.startsWith('@' + q))
})

/** 光标前的 @xxx 待补全：返回过滤词 + 待删选区。 */
function getNoteAtQuery(): { filter: string; del: Range } | null {
  const sel = window.getSelection()
  const el = noteEditor.value
  if (!sel || !sel.rangeCount || !el) return null
  const r = sel.getRangeAt(0)
  if (!r.collapsed || !el.contains(r.startContainer)) return null
  let node: Node | null = r.startContainer
  let offset = r.startOffset
  if (node.nodeType !== Node.TEXT_NODE) {
    const prev = offset > 0 ? node.childNodes[offset - 1] : null
    if (!prev || prev.nodeType !== Node.TEXT_NODE) return null
    node = prev
    offset = (prev.textContent || '').length
  }
  const m = ((node.textContent || '').slice(0, offset)).match(/@([\w\u4e00-\u9fa5]*)$/)
  if (!m) return null
  const del = document.createRange()
  del.setStart(node, offset - m[0].length)
  del.setEnd(node, offset)
  return { filter: m[1], del }
}

function updateNoteMention() {
  const q = getNoteAtQuery()
  if (!q || !form.value.ref_images.length) {
    noteMentionOpen.value = false
    return
  }
  noteMentionFilter.value = q.filter
  noteMentionIndex.value = 0
  noteMentionOpen.value = true
}

function onNoteInput() {
  form.value.note = readNote()
  updateNoteMention()
}

function applyNoteMention(token: string) {
  const el = noteEditor.value
  const q = getNoteAtQuery()
  if (!el || !q) {
    noteMentionOpen.value = false
    return
  }
  el.focus()
  const sel = window.getSelection()
  sel?.removeAllRanges()
  sel?.addRange(q.del)
  const frag = document.createDocumentFragment()
  frag.appendChild(pillNode(token))
  frag.appendChild(document.createTextNode(' '))
  const lastNode = frag.lastChild as Node | null
  q.del.deleteContents()
  q.del.insertNode(frag)
  const after = document.createRange()
  if (lastNode && lastNode.parentNode) after.setStartAfter(lastNode)
  else after.selectNodeContents(el)
  after.collapse(false)
  sel?.removeAllRanges()
  sel?.addRange(after)
  form.value.note = readNote()
  noteMentionOpen.value = false
}

function onNoteKeydown(e: KeyboardEvent) {
  if (!noteMentionOpen.value || !noteCandidates.value.length) return
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    noteMentionIndex.value = (noteMentionIndex.value + 1) % noteCandidates.value.length
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    noteMentionIndex.value = (noteMentionIndex.value - 1 + noteCandidates.value.length) % noteCandidates.value.length
  } else if (e.key === 'Enter' || e.key === 'Tab') {
    e.preventDefault()
    const c = noteCandidates.value[noteMentionIndex.value]
    if (c) applyNoteMention(c.token)
  } else if (e.key === 'Escape') {
    e.preventDefault()
    noteMentionOpen.value = false
  }
}
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
  planRaw.value = null
  form.value = blankForm()
  pageMeta.value = blankPage()
  prompts.value = {}
  status.value = 'draft'
  pushHint.value = ''
}

// ── 漫画：页 / 格序列 / 大纲 / 成图 ───────────────────────────────────────

function toComicPanel(p: any): ComicPanel {
  const pg = p.page || {}
  return {
    planId: p.id,
    pageIndex: Number(pg.index) || 0,
    panelIndex: Number(pg.panel_index) || 1,
    title: p.title || '',
    status: p.status || 'draft',
    promptCount: Number(p.prompt_count) || 0,
    tier: p.tier || '',
    image: pg.image || null,
  }
}

/** 把扁平的格列表聚成页，并挑出当前页的格。 */
function rebuildPages() {
  const byPage = new Map<number, ComicPanel[]>()
  for (const p of allPanels.value) {
    const arr = byPage.get(p.pageIndex) || []
    arr.push(p)
    byPage.set(p.pageIndex, arr)
  }
  const list: ComicPage[] = [...byPage.entries()]
    .sort((a, b) => a[0] - b[0])
    .map(([idx, ps]) => {
      ps.sort((a, b) => a.panelIndex - b.panelIndex)
      const last = ps[ps.length - 1]
      return {
        index: idx,
        panels: ps,
        panelCount: ps.length,
        promptCount: ps.reduce((n, x) => n + x.promptCount, 0),
        image: last?.image || ps.find(x => x.image)?.image || null,
      }
    })
  pages.value = list
  panels.value = list.find(p => p.index === currentPageIndex.value)?.panels || []
}

async function loadComics() {
  try {
    const r: any = await api.listComics(episodeId.value)
    allPanels.value = ((r?.data || []) as any[]).map(toComicPanel)
  } catch {
    allPanels.value = []
  }
  rebuildPages()
}

/** 读本集漫画剧本。 */
async function loadScript() {
  const eid = episodeId.value
  if (!eid) { scriptPanels.value = []; scriptMeta.value = { premise: '', characters: '', style_hint: '', tier: '' }; return }
  try {
    const r: any = await api.getComicScript(eid)
    scriptPanels.value = ((r?.data?.panels || []) as any[]).map(p => ({
      page: Number(p.page) || 1,
      panel: Number(p.panel) || 1,
      text: p.text || '',
      dialogue: p.dialogue || '',
      camera: p.camera || '',
      note: p.note || '',
      tier: p.tier || '',
      clothing_level: p.clothing_level || '',
    }))
    scriptMeta.value = {
      premise: r?.data?.premise || '',
      characters: r?.data?.characters || '',
      style_hint: r?.data?.style_hint || '',
      tier: r?.data?.tier || '',
    }
  } catch {
    scriptPanels.value = []
  }
}

/** 从本集大纲转成剧本（冷启动：先有大纲，再转格）。 */
async function scriptFromOutline() {
  const eid = episodeId.value
  if (!eid) return ElMessage.warning('先选集号')
  scriptBusy.value = 'outline'
  try {
    await api.comicScriptFromOutline({ episode_id: eid })
    await loadScript()
    ElMessage.success(`已转出 ${scriptPanels.value.length} 格`)
  } catch (e: any) {
    ElMessage.error('从大纲转失败：' + (e?.response?.data?.msg || e?.message || e))
  } finally {
    scriptBusy.value = ''
  }
}

/** 存剧本（页面改完落库）。 */
async function saveScript() {
  const eid = episodeId.value
  if (!eid) return ElMessage.warning('先选集号')
  scriptBusy.value = 'save'
  try {
    const r: any = await api.saveComicScript({
      episode_id: eid,
      panels: scriptPanels.value,
      ...scriptMeta.value,
    })
    ElMessage.success(`剧本已存：${r?.data?.panel_count ?? scriptPanels.value.length} 格`)
  } catch (e: any) {
    ElMessage.error('存剧本失败：' + (e?.response?.data?.msg || e?.message || e))
  } finally {
    scriptBusy.value = ''
  }
}

/** 拆格：一条剧本 = 一个方案（页序/格序/上一格链/水位自动排好），之后逐格直投。
 *  先存剧本再拆：拆格永远按当前表格内容走（弹层里改了没存也不丢）。 */
async function splitScript() {
  const eid = episodeId.value
  if (!eid) return ElMessage.warning('先选集号')
  if (!scriptPanels.value.length) return ElMessage.warning('剧本还没有格')
  scriptBusy.value = 'split'
  try {
    await api.saveComicScript({
      episode_id: eid,
      panels: scriptPanels.value,
      ...scriptMeta.value,
    })
    const r: any = await api.splitComicScript({ episode_id: eid, engines: form.value.engines })
    const d = r?.data || {}
    await loadComics()
    const first = allPanels.value.find(p => p.planId === (d.plan_ids || [])[0])
    if (first) { currentPageIndex.value = first.pageIndex; rebuildPages(); await loadPlan(first.planId) }
    ElMessage.success(`已拆 ${d.created || 0} 格（跳过 ${d.skipped || 0}，刷新 ${d.refreshed || 0}）`)
  } catch (e: any) {
    ElMessage.error('拆格失败：' + (e?.response?.data?.msg || e?.message || e))
  } finally {
    scriptBusy.value = ''
  }
}

/** 读本集大纲（缓存：换集再切回来不用重读）。silent=true 时没集号也不打扰。 */
async function readOutline(silent = false) {
  const eid = episodeId.value
  if (!eid) {
    if (!silent) ElMessage.warning('先选集号')
    return
  }
  if (outlineCache.value[eid] !== undefined) {
    outlineMd.value = outlineCache.value[eid]
    return
  }
  outlineLoading.value = true
  try {
    const r: any = await api.getOutline(eid)
    const md = String(r?.data?.outline_md || '')
    outlineCache.value[eid] = md
    outlineMd.value = md
    if (!silent) ElMessage.success(md ? `已读大纲 ${md.length} 字` : '该集没有大纲')
  } catch {
    if (!silent) ElMessage.error('读大纲失败，后端未起？')
  } finally {
    outlineLoading.value = false
  }
}

/** 把大纲写进本页（存进方案的 page.outline_text，直投时随页上下文带给 L-Port）。 */
async function applyOutline() {
  if (!outlineMd.value) return ElMessage.warning('先读大纲')
  if (!curPlanId.value) {
    await newComicPage()
    if (!curPlanId.value) return
  }
  pageMeta.value = { ...pageMeta.value, outline_text: outlineMd.value }
  await savePlan()
  ElMessage.success('大纲已写入本页')
}

/** 链上的上一格：同页上一格；本页第一格则接上一页的末格。 */
function prevPanelOf(pageIndex: number, panelIndex: number): ComicPanel | null {
  const same = allPanels.value.filter(p => p.pageIndex === pageIndex && p.panelIndex < panelIndex)
  if (same.length) return same.sort((a, b) => a.panelIndex - b.panelIndex)[same.length - 1]
  const before = allPanels.value.filter(p => p.pageIndex < pageIndex)
  if (!before.length) return null
  const lastPage = Math.max(...before.map(p => p.pageIndex))
  const inLast = before.filter(p => p.pageIndex === lastPage).sort((a, b) => a.panelIndex - b.panelIndex)
  return inLast[inLast.length - 1] || null
}

/** 新建一页（页内第 1 格）：页序接在最后一条后面，参考图自动带上链上上一格的成图。 */
async function newComicPage() {
  const eid = episodeId.value
  if (!eid) return ElMessage.warning('先选集号')
  stopWait('')
  waitNote.value = ''
  const idx = pages.value.length ? Math.max(...pages.value.map(p => p.index)) + 1 : 1
  const prev = prevPanelOf(idx, 1)
  const prevImg = prev?.image || null
  form.value = {
    ...blankForm(),
    title: `${eid} 第${idx}页 第1格`,
    ref_images: prevImg ? [{ name: prevImg.name, path: prevImg.path, url: prevImg.url }] : [],
  }
  pageMeta.value = {
    episode_id: eid,
    index: idx,
    panel_index: 1,
    prev_plan_id: prev?.planId || '',
    outline_text: outlineMd.value || '',
    image: null,
  }
  curPlanId.value = ''
  planRaw.value = null
  prompts.value = {}
  status.value = 'draft'
  pushHint.value = ''
  currentPageIndex.value = idx
  const id = await savePlan()   // 立刻落库：页条上就多这一页
  if (id) await loadComics()
}

/** 当前页追加一格：格序接在最后一条后面，参考图自动带上一格的成图。 */
async function newComicPanel() {
  const eid = episodeId.value
  if (!eid) return ElMessage.warning('先选集号')
  const pageIdx = currentPageIndex.value
  if (!pageIdx) return ElMessage.warning('先选页')
  stopWait('')
  waitNote.value = ''
  const panelIdx = panels.value.length + 1
  const prev = prevPanelOf(pageIdx, panelIdx)
  const prevImg = prev?.image || null
  form.value = {
    ...blankForm(),
    title: `${eid} 第${pageIdx}页 第${panelIdx}格`,
    ref_images: prevImg ? [{ name: prevImg.name, path: prevImg.path, url: prevImg.url }] : [],
  }
  pageMeta.value = {
    episode_id: eid,
    index: pageIdx,
    panel_index: panelIdx,
    prev_plan_id: prev?.planId || '',
    outline_text: outlineMd.value || '',
    image: null,
  }
  curPlanId.value = ''
  planRaw.value = null
  prompts.value = {}
  status.value = 'draft'
  pushHint.value = ''
  const id = await savePlan()
  if (id) await loadComics()
}

/** 点页条：切到该页，落点取该页最后一格（续写的 frontier）。 */
async function selectComicPage(idx: number) {
  currentPageIndex.value = idx
  rebuildPages()
  const ps = panels.value
  if (!ps.length) return
  await loadPlan(ps[ps.length - 1].planId)
}

/** 上传本格成图（出好图后传回来）：后端落 uploads 并写进方案的 page.image。 */
async function onShotFile(e: any) {
  const f = e.target.files?.[0]
  e.target.value = ''
  if (!f) return
  if (!f.type.startsWith('image/')) return ElMessage.warning('只要图片')
  if (!curPlanId.value) {
    const id = await savePlan()
    if (!id) return
  }
  shotUploading.value = true
  try {
    const r: any = await api.uploadPlanImage(curPlanId.value, f)
    const img = r?.data?.image
    if (img) pageMeta.value = { ...pageMeta.value, image: img }
    await loadComics()
    ElMessage.success('本格成图已挂上')
  } catch {
    ElMessage.error('上传失败，后端未起？')
  } finally {
    shotUploading.value = false
  }
}

async function removePageImage() {
  if (!curPlanId.value) return
  try {
    await api.deletePlanImage(curPlanId.value)
    pageMeta.value = { ...pageMeta.value, image: null }
    await loadComics()
  } catch {
    ElMessage.error('撤图失败，后端未起？')
  }
}

/** 切模式：漫画模式先拉格序列与大纲，再落到最后一页的最后一格。 */
async function onModeChange(v: any) {
  const m = v === 'comic' ? 'comic' : 'single'
  mode.value = m
  try { localStorage.setItem('suli.studio.mode', m) } catch {}
  if (m !== 'comic') {
    // 单图模式的下拉里没有漫画格：当前选中的是漫画格就清掉，别让下拉与内容对不上
    if (curPlanId.value && !singlePlans.value.some(p => p.id === curPlanId.value)) newPlan()
    return
  }
  await loadComics()
  await loadScript()
  await readOutline(true)
  const cur = allPanels.value.find(p => p.planId === curPlanId.value)
  if (cur) { currentPageIndex.value = cur.pageIndex; rebuildPages(); await loadPlan(cur.planId); return }
  if (pages.value.length) {
    const last = pages.value[pages.value.length - 1]
    currentPageIndex.value = last.index
    rebuildPages()
    const ps = last.panels
    if (ps.length) await loadPlan(ps[ps.length - 1].planId)
  }
}

/** 换集号：页条与大纲跟着换（大纲重新读，页缓存留着切回来用）。 */
watch(() => store.episodeId, async (nv, ov) => {
  if (mode.value !== 'comic' || nv === ov) return
  outlineMd.value = ''
  currentPageIndex.value = 0
  await loadComics()
  await loadScript()
  await readOutline(true)
  if (pages.value.length) {
    const last = pages.value[pages.value.length - 1]
    currentPageIndex.value = last.index
    rebuildPages()
    const ps = last.panels
    if (ps.length) await loadPlan(ps[ps.length - 1].planId)
  } else {
    newPlan()
  }
})

/** 方案变更卡：后端留的改前快照 vs 现在这份（没有改前快照 = 没有待审变更） */
const changeRows = computed(() => planChangeRows(planRaw.value?.prev, planRaw.value))

/** 表单相对服务端最新状态有没有未保存的改动（有就别自动覆盖主人的手输） */
const formDirty = computed(() => {
  const p = planRaw.value
  if (!p) return false
  if (form.value.title !== (p.title || '')) return true
  if (form.value.intent_text !== (p.intent_text || '')) return true
  if (form.value.note !== (p.note || '')) return true
  if (form.value.engines.join(',') !== (p.engines || []).join(',')) return true
  if ((form.value.tier || '') !== (p.tier || '')) return true
  if ((form.value.clothing_level || '') !== (p.clothing_level || '')) return true
  if (refNames(form.value.ref_images).join(',') !== refNames(p.ref_images).join(',')) return true
  return false
})

function reloadPlan() {
  if (curPlanId.value) return loadPlan(curPlanId.value)
}

/** 右栏发现 agent 改了方案：表单没被手输改动就直接同步过去，有手输就只出变更卡 */
watch(() => studio.remoteChange, async (c) => {
  if (!c?.planId) return
  if (c.planId !== curPlanId.value) { await loadPlan(c.planId); return }
  if (!formDirty.value) await loadPlan(c.planId)
})

/** 右栏点了别的方案会话：方案页切到那个方案（会话和表单必须是同一个方案） */
watch(() => studio.planPick, async (id) => {
  if (!id || id === curPlanId.value) return
  await loadPlan(id)
})

async function loadPlan(id: string) {
  if (!id) return newPlan()
  try {
    const r: any = await api.getPlan(id)
    const d = r?.data || {}
    curPlanId.value = d.id || id // 自动载入也要认领 id，否则保存/直投会新建重复方案
    planRaw.value = d
    form.value = {
      title: d.title || '',
      intent_text: d.intent_text || '',
      engines: Array.isArray(d.engines) && d.engines.length ? d.engines : [...DEFAULT_ENGINES],
      ref_images: Array.isArray(d.ref_images) ? d.ref_images : [],
      note: d.note || '',
      tier: d.tier || '',
      clothing_level: d.clothing_level || '',
    }
    const pg = d.page || null
    pageMeta.value = pg
      ? {
          episode_id: pg.episode_id || '',
          index: Number(pg.index) || 0,
          panel_index: Number(pg.panel_index) || 1,
          prev_plan_id: pg.prev_plan_id || '',
          outline_text: pg.outline_text || '',
          image: pg.image || null,
        }
      : blankPage()
    // 漫画格自带参考图为空时，接上链上上一格的成图（拆格时上一格还没出图，出图是后来的事）
    if (pageMeta.value.index && !form.value.ref_images.length) {
      const prev = prevPanelOf(pageMeta.value.index, pageMeta.value.panel_index)
      if (prev?.image) {
        const inherited = { name: prev.image.name, path: prev.image.path, url: prev.image.url }
        form.value = { ...form.value, ref_images: [inherited] }
        // 继承来的参考图不是手改：同步进 planRaw，别让「未保存」指示器亮起来
        planRaw.value = { ...planRaw.value, ref_images: [inherited] }
      }
    }
    if (pageMeta.value.index) {
      currentPageIndex.value = pageMeta.value.index
      rebuildPages()
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
      tier: form.value.tier,
      clothing_level: form.value.clothing_level,
      source: 'ui',   // 页面自己改的：不算待审变更，后端不留改前快照
    }
    // 漫画页上下文：漫画模式必带；单图模式下只在原本就是漫画页时带（别把页信息抹掉）
    if (mode.value === 'comic' || pageMeta.value.episode_id || pageMeta.value.index) {
      body.page = pageMeta.value
    }
    if (curPlanId.value) body.id = curPlanId.value
    const r: any = await api.savePlan(body)
    const d = r?.data || {}
    curPlanId.value = d.id || curPlanId.value
    status.value = d.status || status.value
    // 自己改的算「人已看过」：本地这份待审快照同步清掉，变更卡收起
    planRaw.value = { ...(planRaw.value || {}), ...d, prev: null, prev_at: null }
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
    if (mode.value === 'comic') await loadComics()
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
  // 模式记住：上次在漫画页就回漫画页
  let m = 'single'
  try { m = localStorage.getItem('suli.studio.mode') || 'single' } catch {}
  mode.value = m === 'comic' ? 'comic' : 'single'
  if (mode.value === 'comic') {
    await loadComics()
    await loadScript()
    await readOutline(true)
    if (pages.value.length) {
      const last = pages.value[pages.value.length - 1]
      currentPageIndex.value = last.index
      rebuildPages()
      const ps = last.panels
      if (ps.length) await loadPlan(ps[ps.length - 1].planId)
    }
  } else if (singlePlans.value.length) {
    await loadPlan(singlePlans.value[0].id)
  }
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
.studio-grid { display:grid; grid-template-columns: minmax(420px, 1.3fr) minmax(340px, 1fr); gap:18px; margin-top:12px; flex:1 0 auto; min-height:0 }
@media (max-width: 1000px) { .studio-grid { grid-template-columns: 1fr; flex:0 0 auto } }
.studio-col { min-width:0; display:flex; flex-direction:column; min-height:0 }
/* 意图框吃掉富余高度；中段（引擎/素材）按内容占位，不够时才自己滚 */
.grow { flex:1 1 0; min-height:100px; display:flex }
.grow :deep(.el-textarea) { flex:1; display:flex }
.grow :deep(.el-textarea__inner) { height:100%; resize:none }
.lower { flex:0 1 auto; min-height:0; display:flex; flex-direction:column }
.lower-body { flex:1 1 auto; min-height:0; overflow:auto; padding-right:4px; display:flex; flex-direction:column }
.lower .block-title { margin:8px 0 4px }
.lower > .lower-body > .block-title:first-child { margin-top:0 }
.lower .engines { gap:2px 12px }
.lower .refs { gap:8px }
/* 素材区：参考图 与 本格成图 并排 */
.asset-row { display:flex; gap:16px; align-items:flex-start }
.asset-block { flex:1 1 0; min-width:0 }
.asset-block .block-title { margin:8px 0 4px }
/* 水位/衣物：贴着引擎区一行，宽度收住，别把整行拉满 */
.tier-row { display:flex; align-items:center; gap:6px; margin-top:8px }
.tier-lbl { font-size:12px; color:var(--suli-text-2) }
.tier-sel { width:110px }
/* 剧本条（漫画导航行右侧） */
.script-bar { display:flex; align-items:center; gap:6px; font-size:13px }
/* 剧本编辑弹层：整表全宽 */
:deep(.script-dialog .el-dialog__body) { padding-top:8px }
.note-grow { flex:1 1 auto; min-height:44px; display:flex }
.note-grow :deep(.el-textarea) { flex:1; display:flex }
.note-grow :deep(.el-textarea__inner) { height:100%; resize:none }
.textarea-wrap { position:relative; flex:1; display:flex; min-width:0 }
.note-editor { flex:1; min-height:44px; padding:5px 11px; border:1px solid var(--el-border-color); border-radius:var(--el-border-radius-base); font-size:14px; line-height:1.5; overflow-y:auto; outline:none; transition:border-color .2s; background:var(--el-fill-color-blank); }
.note-editor:hover { border-color:var(--el-border-color-hover) }
.note-editor:focus { border-color:var(--el-color-primary) }
.note-editor:empty::before { content:attr(data-ph); color:var(--el-text-color-placeholder); pointer-events:none }
.mention-popup { position:absolute; left:0; bottom:100%; z-index:30; min-width:220px; max-width:340px; margin-bottom:6px; background:var(--el-bg-color-overlay); border:1px solid var(--el-border-color-light); border-radius:10px; box-shadow:var(--el-box-shadow-light); padding:6px 0; }
.mention-popup-title { font-size:12px; color:var(--el-text-color-secondary); padding:2px 10px 6px }
.mention-item { display:flex; align-items:center; gap:8px; width:100%; padding:6px 10px; border:none; background:none; cursor:pointer; text-align:left; color:inherit }
.mention-item:hover, .mention-item.active { background:var(--el-fill-color-light) }
.mention-thumb { width:40px; height:40px; object-fit:cover; border-radius:6px; flex:0 0 auto }
.mention-name { font-size:13px; font-weight:600; color:var(--el-color-primary); flex:0 0 auto }
.mention-sub { font-size:12px; color:var(--el-text-color-secondary); overflow:hidden; text-overflow:ellipsis; white-space:nowrap }
/* 约束块：固定高度常驻底部，不被上面的滚动区带走 */
.note-block { flex:0 0 auto }
.note-block .block-title { margin:8px 0 4px }
/* 方案变更卡：夹在内容区和操作行之间，自身不参与伸缩 */
.chg-card { flex:0 0 auto }
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
.ref-item { display:flex; align-items:center; gap:8px; border:1px solid var(--el-border-color-lighter); border-radius:10px; padding:4px 10px 4px 4px; position:relative }
.ref-thumb { width:64px; height:64px; border-radius:8px; overflow:hidden; display:block; flex:0 0 auto; background:var(--el-fill-color-light); cursor:zoom-in; }
.ref-tag { position:absolute; left:8px; bottom:14px; z-index:2; font-size:10px; line-height:1; padding:3px 6px; border-radius:4px; border:none; background:rgba(0,0,0,.6); color:#fff; cursor:pointer }
.ref-tag:hover { background:var(--el-color-primary) }
.ref-thumb-ph { width:100%; height:100%; display:flex; align-items:center; justify-content:center; font-size:20px; color:var(--el-text-color-placeholder); }
.ref-meta { display:flex; flex-direction:column; align-items:flex-start; gap:2px; min-width:0; }
.ref-name { font-size:12px; max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.ref-add { align-self:center; }
/* 漫画页：本页成图槽（缩略图 + 上传/移除） */
.page-shot { display:flex; align-items:center; gap:10px; }
.page-shot-img { width:56px; height:72px; border-radius:8px; overflow:hidden; background:var(--el-fill-color-light); flex:0 0 auto; }
.page-shot-ph { width:56px; height:72px; border-radius:8px; background:var(--el-fill-color-light); display:flex; align-items:center; justify-content:center; font-size:20px; color:var(--suli-text-3); flex:0 0 auto; }
.page-shot-act { display:flex; flex-direction:row; gap:6px; align-items:center; }
.prompt-card { border:1px solid var(--el-border-color-lighter); border-radius:10px; padding:10px; margin-bottom:10px; }
.prompt-head { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
.prompt-row { display:flex; gap:8px; margin-top:6px; }
.prompt-row .lbl { flex:0 0 32px; font-size:12px; color:var(--el-text-color-secondary); }
.prompt-row pre { flex:1; margin:0; white-space:pre-wrap; word-break:break-word; font-size:12px; background:var(--el-fill-color-light); border-radius:6px; padding:6px 8px; }
</style>
