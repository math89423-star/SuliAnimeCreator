<template>
  <div class="right">
    <div class="head"><h4 style="margin:0">Agent</h4><span style="flex:1" /><el-button size="small" circle title="会话历史" @click="histOpen = true"><el-icon><Clock /></el-icon></el-button><el-button size="small" circle :title="`${pageSessionLabel}（名即${pageKindLabel}）`" @click="backToPageSession"><el-icon><Plus /></el-icon></el-button><el-button size="small" circle @click="store.toggleRight()">›</el-button></div>
    <div class="agent-sub">
      <span class="suli-muted" style="font-size:12px">{{ pageKindLabel }} {{ pageKey || '未选' }} · skill {{ skills.length ? `${skills.length}已载` : '载入中…' }}</span>
      <span style="flex:1" />
      <el-select v-model="model" size="small" style="width:178px" title="Agent 运行模型（每次发送按当前选择生效）">
        <el-option v-for="m in MODEL_OPTIONS" :key="m.value" :label="m.label" :value="m.value" />
      </el-select>
      <el-button size="small" text @click="backToPageSession">{{ pageSessionLabel }}</el-button>
    </div>
    <!-- 当前会话卡：点击打开会话历史（照参考：标题行 + 会话名） -->
    <div class="suli-card cur-card" @click="histOpen = true" :title="`打开${pageKindLabel}会话历史`">
      <div class="cur-title"><el-icon class="cur-ico"><Clock /></el-icon><span>当前会话即{{ pageKindLabel }}</span><span class="cur-count tnum">{{ pageSessions.length }}个</span></div>
      <div class="cur-key">{{ pageKey || '未选' }}</div>
    </div>
    <div v-if="loadingList" style="margin-top:8px"><div class="skeleton" style="height:32px" /></div>

    <!-- 消息区：居中滚动（常驻占位把输入框压到底；无会话时内部留空） -->
    <div ref="turnBox" class="turns">
      <el-empty v-if="!turns.length && !loading" description="无对话" :image-size="64" />
      <template v-else>
        <div v-for="(t, i) in turns" :key="i" class="turn">
          <div class="bubble-row from-user">
            <div class="bubble user-b">
              <MarkdownView class="q-md" :content="t.q" />
              <div v-if="t.files && t.files.length" class="files files-end">
                <el-image
                  v-for="(f, j) in t.files.filter((x: Att) => x.kind === 'image')"
                  :key="'i' + j"
                  :src="f.url"
                  :preview-src-list="t.files.filter((x: Att) => x.kind === 'image').map((x: Att) => x.url)"
                  class="thumb"
                  fit="cover"
                  hide-on-click-modal
                />
                <a
                  v-for="(f, j) in t.files.filter((x: Att) => x.kind !== 'image')"
                  :key="'f' + j"
                  :href="f.url"
                  target="_blank"
                  rel="noopener"
                  class="file-chip"
                ><el-icon style="vertical-align:-2px;margin-right:2px"><Paperclip /></el-icon>{{ f.name }}</a>
              </div>
            </div>
          </div>
          <div class="bubble-row from-agent">
            <div class="bubble agent-b">
              <div v-if="!t.a" class="a thinking">思考中…</div>
              <MarkdownView v-else class="a-md" :content="displayAnswer(t)" />
          <PlanChangeCard
            v-if="changeCard[i]"
            :plan-id="changeCard[i].planId"
            :rows="changeCard[i].rows"
          />
          <div v-if="canApply(t)" class="turn-apply">
            <template v-if="!probe[i]">
              <span class="apply-hint">{{ applyHint(t) }}</span>
              <el-button size="small" type="primary" @click="probeCentral(t, i)" :loading="probingIdx === i"><el-icon style="margin-right:4px"><Check /></el-icon>接受并填充中央</el-button>
            </template>
            <template v-else>
              <span class="apply-hint">{{ probeText(probe[i]) }}</span>
              <el-button size="small" type="primary" @click="applyTurnToCentral(t, i)" :loading="applyingIdx === i">确认填充</el-button>
              <el-button size="small" @click="cancelProbe(i)">取消</el-button>
            </template>
          </div>
          <div v-if="applyMsg[i]" class="apply-msg">{{ applyMsg[i] }}</div>
              <div v-if="t.a" class="msg-actions">
                <el-button text size="small" @click="quoteText(displayAnswer(t))">引用</el-button>
                <el-button text size="small" @click="copyText(displayAnswer(t))">复制</el-button>
                <el-button text size="small" @click="delTurn(i)">删除</el-button>
              </div>
            </div>
          </div>
        </div>
      </template>
      <div v-if="loading" class="run-card suli-card">
        <div class="run-head">
          <span class="run-pulse" />
          <b>运行中</b>
          <span class="suli-muted tnum" style="font-size:12px">{{ progress || '已发车…' }}</span>
        </div>
        <div class="run-acts">
          <div v-for="(a, i) in acts" :key="i" class="run-act">
            <span class="run-dot" :class="a.kind" />
            <span class="run-label">{{ a.label }}</span>
            <span class="run-time tnum">{{ secAgo(a.t) }}</span>
          </div>
          <div v-if="!acts.length" class="suli-muted" style="font-size:12px">等 dsh 冷启动首帧…（首 token 常见 10–30s）</div>
        </div>
        <div class="run-foot suli-muted">
          单步静默 1–3 分钟属正常（模型在写长文），整轮常见 3–6 分钟；任务跑在后端，切页/刷新都不中断。
        </div>
      </div>
    </div>

    <!-- 输入区：沉底 -->
    <div class="composer">
      <div v-if="pending.length" class="pending">
        <div v-for="(f, i) in pending" :key="i" class="pend-chip">
          <img v-if="f.kind === 'image'" :src="f.url" class="pend-thumb" />
          <span v-else-if="f.kind === 'video'" class="pend-file" title="参考视频"><el-icon><VideoCamera /></el-icon></span>
          <span v-else class="pend-file"><el-icon><Paperclip /></el-icon></span>
          <span class="pend-name">{{ f.name }}{{ f.dur ? ` · ${Math.round(f.dur)}s` : '' }}</span>
          <el-button v-if="f.kind === 'video'" size="small" type="primary" @click="extractFrames(f)" :loading="framing === f.path">抽帧</el-button>
          <el-button size="small" text circle @click="pending.splice(i, 1)"><el-icon><Close /></el-icon></el-button>
        </div>
      </div>
      <div class="input-row">
        <el-input
          v-model="msg"
          type="textarea"
          :autosize="{ minRows: 2, maxRows: 5 }"
          placeholder="输入指令…"
          @keydown.enter.exact.prevent="send"
          class="msg-input"
        />
      </div>
      <div class="toolbar">
        <div class="tools">
          <el-button circle size="small" @click="imgInput?.click()" :loading="uploading" title="上传图片"><el-icon><Picture /></el-icon></el-button>
          <el-button circle size="small" @click="vidInput?.click()" :loading="uploading" title="上传参考视频（≤300MB，可抽帧）"><el-icon><VideoCamera /></el-icon></el-button>
          <el-button circle size="small" @click="fileInput?.click()" :loading="uploading" title="上传文件"><el-icon><Paperclip /></el-icon></el-button>
        </div>
        <span class="tip suli-muted">Enter 发送 · Shift+Enter 换行</span>
        <el-button v-if="loading" type="danger" round size="small" @click="stop"><el-icon style="margin-right:4px"><CircleClose /></el-icon>停止</el-button>
        <el-button v-else type="primary" round size="small" @click="send" :disabled="!msg.trim() && !pending.length">发送</el-button>
      </div>
      <input ref="imgInput" type="file" accept="image/*" multiple hidden @change="onPick($event, 'image')" />
      <input ref="vidInput" type="file" accept="video/*" multiple hidden @change="onPick($event, 'video')" />
      <input ref="fileInput" type="file" multiple hidden @change="onPick($event, 'file')" />
    </div>

    <!-- 会话历史抽屉（照参考：标题左 + 导出/清空/关闭右，空态居中一行字） -->
    <div v-if="histOpen" class="hist-mask" @click="histOpen = false" />
    <div class="hist-drawer" :class="{ open: histOpen }">
      <div class="hist-head">
        <b>会话历史</b>
        <span style="flex:1" />
        <el-button size="small" text circle title="导出全部会话" @click="exportAll"><el-icon><Download /></el-icon></el-button>
        <el-button size="small" text circle title="清空全部会话" @click="clearAll"><el-icon><Delete /></el-icon></el-button>
        <el-button size="small" text circle title="关闭" @click="histOpen = false"><el-icon><Close /></el-icon></el-button>
      </div>
      <div class="hist-tools">
        <el-input v-model="histKw" size="small" :placeholder="`搜索${pageKindLabel}`" clearable style="flex:1;min-width:0">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-checkbox v-model="histAll" size="small" style="margin:0">全部</el-checkbox>
        <el-button size="small" type="primary" @click="backToPageSession(); histOpen = false"><el-icon style="margin-right:2px"><Plus /></el-icon>{{ pageSessionLabel }}</el-button>
      </div>
      <div class="suli-muted" style="font-size:11px;padding:0 12px 6px">{{ histHint }}</div>
      <div class="hist-list">
        <div v-if="!filteredSessions.length" class="hist-empty">暂无历史会话</div>
        <div
          v-for="s in filteredSessions" :key="s.scope + ':' + s.key"
          class="suli-card hist-item" :class="{ active: curKey === s.key && curScope === s.scope }"
          @click="pickAndClose(s)"
        >
          <div class="hist-top">
              <span class="dot" :class="s.dsh_session_id ? 'on' : 'off'" />
              <b class="hist-key">{{ s.key }}</b>
              <span style="flex:1" />
              <el-button size="small" text circle title="导出该会话" @click.stop="exportOne(s)"><el-icon><Download /></el-icon></el-button>
              <el-button size="small" text circle title="删除该会话" @click.stop="delSession(s)"><el-icon><Close /></el-icon></el-button>
            </div>
            <div class="hist-meta tnum">{{ scopeKind(s.scope) }}会话 · {{ rel(s.last_active) }} · {{ fmtTime(s.last_active) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api/client'
import { Close, Check, Paperclip, Picture, CircleClose, Clock, Plus, Download, Delete, Search, VideoCamera } from '@element-plus/icons-vue'
import MarkdownView from './MarkdownView.vue'
import PlanChangeCard from './PlanChangeCard.vue'
import { diffPlanRows } from '../utils/planDiff'
import { useAppStore } from '../stores/app'
import { useUiStore } from '../stores/ui'
import { useStudioStore } from '../stores/studio'

interface Att { name: string; url: string; path: string; kind: 'image' | 'file' | 'video'; dur?: number; size?: number }
interface Turn { q: string; a: string; files?: Att[]; applied?: boolean }

const store = useAppStore()
const studio = useStudioStore()
const ui = useUiStore()
const route = useRoute()
// 会话列表：scope 是存储字段（各域并存，见 ANCHORS）
const curScope = ref('episode')
const sessions = ref<any[]>([])
const curKey = ref('')
const curSid = ref('')
const msg = ref('')
// 页面感知：右栏的会话键 = 这一页「正在改的那个对象」，不是页面本身，也不是整个项目。
//   有对象 → 跟对象（方案 / 集号 / 参考素材 / 投流批次）；没对象 → 跟页面各自分桶。
//   同一集号的四个页（导演/剧本分镜/故事/角色）共享集号会话——它们改的是同一样东西。
type AgentCtx = 'plan' | 'episode' | 'none'
interface AgentAnchor { scope: string; kind: string; label: string; ctx: AgentCtx; need: string }
const ANCHORS: Record<string, AgentAnchor> = {
  '/studio':    { scope: 'art',     kind: '方案', label: '本方案会话', ctx: 'plan',    need: '先新建或选择方案' },
  '/director':  { scope: 'episode', kind: '本集', label: '本集会话',   ctx: 'episode', need: '先选择或新建集号' },
  '/board':     { scope: 'episode', kind: '本集', label: '本集会话',   ctx: 'episode', need: '先选择或新建集号' },
  '/story':     { scope: 'episode', kind: '本集', label: '本集会话',   ctx: 'episode', need: '先选择或新建集号' },
  '/character': { scope: 'episode', kind: '本集', label: '本集会话',   ctx: 'episode', need: '先选择或新建集号' },
  '/video':     { scope: 'video',   kind: '本片', label: '本片会话',   ctx: 'none',    need: '先选一个参考视频' },
  '/traffic':   { scope: 'traffic', kind: '本批', label: '本批会话',   ctx: 'episode', need: '先选一个母集号' },
  '/art':       { scope: 'page',    kind: '本页', label: '本页会话',   ctx: 'none',    need: '' },
  '/settings':  { scope: 'page',    kind: '本页', label: '本页会话',   ctx: 'none',    need: '' },
  '/':          { scope: 'page',    kind: '本页', label: '本页会话',   ctx: 'none',    need: '' },
}
const SCOPE_KIND: Record<string, string> = { art: '方案', episode: '本集', video: '本片', traffic: '本批', page: '本页', lab: '实验', global: '全局' }
const anchor = computed<AgentAnchor>(() => ANCHORS[route.path] || ANCHORS['/'])
const pageScope = computed(() => anchor.value.scope)
const pageKey = computed(() => {
  const a = anchor.value
  if (a.scope === 'art') return studio.planId || ''
  if (a.scope === 'episode') return store.episodeId || ''
  if (a.scope === 'video') return ui.videoAnchor || ''
  if (a.scope === 'traffic') return ui.trafficAnchor || ''
  return String(route.meta?.title || route.path || 'page')   // page 域：一页一个桶，互不串
})
const pageKindLabel = computed(() => anchor.value.kind)
const pageSessionLabel = computed(() => anchor.value.label)
const pageSessions = computed(() => sessions.value.filter(s => (s.scope || 'episode') === pageScope.value))
// 给 agent 看什么：方案原文 / 集号 / 参考片 / 什么都不给（工具页与设置页不塞剧集上下文）
const pageContext = computed(() => {
  const a = anchor.value
  if (a.ctx === 'plan') return studio.contextBlock()
  if (a.ctx === 'episode') {
    const k = pageKey.value
    return /^EP-/.test(k) ? `集号：${k}` : ''
  }
  if (a.scope === 'video') {
    const k = pageKey.value
    return k ? `参考片：${k}` : ''
  }
  return ''
})
// Agent 运行模型（2026-10-17）：白名单与后端 _RUN_MODELS 对齐；每次发送按当前选择生效
const MODEL_OPTIONS = [
  { label: '跟随设置页', value: '' },
  { label: 'DeepSeek V4.1 Flash', value: 'deepseek-v4.1-flash' },
  { label: 'LongCat 2.5 Preview Free', value: 'longcat-2.5-preview-free' },
]
const model = ref('')
try { const m = localStorage.getItem('suli.agent.model'); if (m && MODEL_OPTIONS.some(x => x.value === m)) model.value = m } catch {}
// 选择持久化：watch 实现（不依赖组件事件绑定，刷新后保持选择）
watch(model, v => { try { localStorage.setItem('suli.agent.model', v) } catch {} })

function findSession(scope: string, key: string) {
  return sessions.value.find(s => s.scope === scope && s.key === key)
}
// 会话历史抽屉（右侧滑入，标题左 + 导出/清空/关闭右）
const histOpen = ref(false)
const histKw = ref('')
const histAll = ref(false)   // 勾上 = 看所有域的会话（不只当前页的对象域）
function scopeKind(scope: string): string {
  return SCOPE_KIND[scope || 'episode'] || '会话'
}
const histHint = computed(() => {
  if (histAll.value) return '全部域：点卡片即切到那条会话'
  const a = anchor.value
  if (a.scope === 'art') return '一方案一会话：点卡片即切到该方案'
  if (a.scope === 'episode') return '一集一会：会话名即集号，点击切换中央集号'
  if (a.scope === 'video') return '一素材一会话：点卡片即切到该素材'
  if (a.scope === 'traffic') return '一批一会话：点卡片即切到该批'
  return '一页一会话：点卡片即切到那条会话'
})
const filteredSessions = computed(() => {
  // 历史按当前页面的对象域过滤；勾「全部」则所有域一起看
  const kw = histKw.value.trim().toLowerCase()
  const rows = [...(histAll.value ? sessions.value : pageSessions.value)]
    .sort((a, b) => (b.last_active || 0) - (a.last_active || 0))
  if (!kw) return rows
  return rows.filter(s => String(s.key || '').toLowerCase().includes(kw))
})
function fmtTime(ts: number) {
  if (!ts) return '--'
  const d = new Date(ts)
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}
function downloadJson(name: string, obj: any) {
  const blob = new Blob([JSON.stringify(obj, null, 2)], { type: 'application/json' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = name
  a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 5000)
}
function exportAll() {
  if (!sessions.value.length) return ElMessage.warning('暂无历史会话')
  downloadJson(`dsh-sessions-${Date.now()}.json`, sessions.value)
  ElMessage.success(`已导出 ${sessions.value.length} 个会话`)
}
function exportOne(s: any) {
  let turns: any[] = []
  try { turns = JSON.parse(localStorage.getItem(`dsh-turns:${s.scope}:${s.key}`) || '[]') } catch { turns = [] }
  downloadJson(`dsh-${s.key}.json`, { ...s, turns })
  ElMessage.success(`已导出 ${s.key}`)
}
async function clearAll() {
  if (!sessions.value.length) return ElMessage.warning('暂无历史会话')
  try {
    await ElMessageBox.confirm(`清空全部 ${sessions.value.length} 个会话？本地聊天记录一起删。`, '清空会话历史', { type: 'warning', confirmButtonText: '清空', cancelButtonText: '取消' })
  } catch { return }
  if (loading.value) stop()
  for (const s of [...sessions.value]) {
    try { await api.dshDeleteSession(s.scope, s.key) } catch {}
    try { localStorage.removeItem(`dsh-turns:${s.scope}:${s.key}`) } catch {}
  }
  sessions.value = []
  curKey.value = ''
  curSid.value = ''
  turns.value = []
  saveLocal()
  ElMessage.success('已清空')
}
const turns = ref<Turn[]>([])
const loading = ref(false)
const loadingList = ref(false)
const progress = ref('')
const pending = ref<Att[]>([])
const uploading = ref(false)
const aborter = ref<AbortController | null>(null)
const acts = ref<{ label: string; kind: string; t: number }[]>([])   // 实时动作流（进度卡）
const nowTs = ref(Date.now())
const turnBox = ref<HTMLElement | null>(null)
const imgInput = ref<HTMLInputElement | null>(null)
const vidInput = ref<HTMLInputElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const applyingIdx = ref(-1)
const probingIdx = ref(-1)
const probe = ref<Record<number, any>>({})
const applyMsg = ref<Record<number, string>>({})
// 方案变更卡：回合结束后 agent 改了方案就挂在那一轮下面
const changeCard = ref<Record<number, { planId: string; rows: any[] }>>({})

// ── 方案变更对比（单图创作页）──────────────────────────────────────────────
// 发消息前抓一份服务端方案快照，回合结束再拉一次比对：变了就出变更卡，
// 并通知方案页重拉表单（agent 挂的参考图、改的约束当场可见）。
let planBefore: any = null
let planIdsBefore: string[] = []

async function snapPlan() {
  planBefore = null
  planIdsBefore = []
  if (pageScope.value !== 'art') return
  try {
    const r: any = await api.listPlans()
    planIdsBefore = (r?.data || []).map((x: any) => String(x?.id || ''))
  } catch { planIdsBefore = [] }
  const id = studio.planId
  if (!id) return
  try {
    const r: any = await api.getPlan(id)
    planBefore = r?.data || null
  } catch { planBefore = null }
}

/** 回合结束后核方案：变了 → 右栏出变更卡 + 通知方案页。 */
async function checkPlanChange(idx: number) {
  if (pageScope.value !== 'art') return
  const id = planBefore?.id || studio.planId
  // 原来没有方案（agent 自己新建了一个）：按方案列表找新出现的
  if (!id) {
    try {
      const r: any = await api.listPlans()
      const rows: any[] = r?.data || []
      const fresh = rows.find(x => x?.id && !planIdsBefore.includes(String(x.id)))
      if (!fresh) return
      const d: any = (await api.getPlan(fresh.id))?.data
      const rr = diffPlanRows({}, d)
      if (!rr.length) return
      changeCard.value = { ...changeCard.value, [idx]: { planId: fresh.id, rows: rr } }
      studio.setRemoteChange({ planId: fresh.id, rows: rr, created: true })
    } catch { /* 后端未起就静默 */ }
    return
  }
  let after: any = null
  try { after = (await api.getPlan(id))?.data || null } catch { return }
  if (!after) return
  // 基准：回合前快照（只算这一轮 agent 改了什么）；没有快照（重连/刷新）才用后端留的改前快照
  const rows = planBefore
    ? diffPlanRows(planBefore, after)
    : (after.prev ? diffPlanRows(after.prev, after) : [])
  if (!rows.length) return
  changeCard.value = { ...changeCard.value, [idx]: { planId: id, rows } }
  studio.setRemoteChange({ planId: id, rows })
}

function rel(ts: number) {
  if (!ts) return '未开始'
  const s = Math.floor((Date.now() - ts) / 1000)
  if (s < 60) return '刚刚'
  if (s < 3600) return Math.floor(s / 60) + '分钟前'
  if (s < 86400) return Math.floor(s / 3600) + '小时前'
  return Math.floor(s / 86400) + '天前'
}
function secAgo(ts: number) {
  const s = Math.max(0, Math.floor((nowTs.value - ts) / 1000))
  return s < 60 ? `${s}s 前` : `${Math.floor(s / 60)}m${s % 60}s 前`
}
function actKind(label: string) {
  if (label.startsWith('调用')) return 'tool'
  if (label.startsWith('返回')) return 'result'
  if (label.startsWith('出稿')) return 'write'
  if (label.startsWith('思考')) return 'think'
  return 'step'
}
function pushAct(label: string) {
  if (!label) return
  const kind = actKind(label)
  const list = acts.value.slice()
  const last = list[list.length - 1]
  // 流式动作（思考 / 正文片段）原地刷新同一行，别把日志刷成一片“思考”
  if (last && last.kind === kind && (kind === 'think' || kind === 'write')) {
    list[list.length - 1] = { label, kind, t: Date.now() }
  } else if (last && last.label === label) {
    list[list.length - 1] = { label, kind, t: Date.now() }
  } else {
    list.push({ label, kind, t: Date.now() })
  }
  acts.value = list.slice(-8)
}
function histKey() { return `dsh-turns:${curScope.value}:${curKey.value || 'new'}` }
function loadLocal() { try { turns.value = JSON.parse(localStorage.getItem(histKey()) || '[]') } catch { turns.value = [] } }
function saveLocal() { try { localStorage.setItem(histKey(), JSON.stringify(turns.value.slice(-30))) } catch {} }
function fillAAt(i: number, a: string) { if (turns.value[i]) { turns.value[i].a = a; saveLocal() } }
// 长任务持久化：run 由后端持有，这里只记"本会话正在跟随哪个 run"，刷新后据此重连
function runStoreKey() { return `dsh-run:${curScope.value}:${curKey.value || 'new'}` }
function rememberRun(rid: string) { try { localStorage.setItem(runStoreKey(), rid) } catch {} }
function forgetRun() { try { localStorage.removeItem(runStoreKey()) } catch {} }
function savedRun() { try { return localStorage.getItem(runStoreKey()) || '' } catch { return '' } }
function scrollBottom() {
  nextTick(() => {
    const el = turnBox.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

// 接受并填充中央：唯一开关是 LLM 自己打的落盘标记 `APPLY: EP-xxx`（见 AGENTS.md 落盘标记节）。
// 前端不再猜关键词（已删硬编码词表），没标记一律不给入口；点了还会验盘，空盘拦下。
const APPLY_RE = /(?:^|\n)\s*(?:APPLY|FILL|填充)\s*[:：]\s*(EP-[A-Za-z0-9\u4e00-\u9fa5_-]+)/i
function extractApplyMark(t: Turn): string {
  const m = (t.a || '').match(APPLY_RE)
  return m ? m[1] : ''
}
function displayAnswer(t: Turn): string {
  // 展示时藏掉标记行（单独一行 APPLY: EP-xxx），复制/引用也用藏后的
  return (t.a || '').replace(/^\s*(?:APPLY|FILL|填充)\s*[:：]\s*EP-[^\s]+\s*$/gim, '').replace(/\n{3,}/g, '\n\n').trim()
}
function extractShots(t: Turn): string[] {
  const m = (t.a || '').match(/SHOT-[A-Za-z0-9_-]+/g)
  return m ? [...new Set(m)] : []
}
function detectTargetEpisode(t: Turn): string {
  const mark = extractApplyMark(t)
  if (mark) return mark
  if (/^EP-/.test(curKey.value)) return curKey.value
  return store.episodeId
}
function canApply(t: Turn) {
  if (!t.a) return false
  if (t.applied) return false
  if (/^(\[失败\]|\[已停止\])/.test(t.a.trim())) return false
  return !!extractApplyMark(t)
}
function applyHint(t: Turn) {
  const target = detectTargetEpisode(t)
  const shots = extractShots(t)
  const switchNote = target !== store.episodeId ? `（中央将从 ${store.episodeId} 切换）` : ''
  const shotNote = shots.length ? ` · 文中${shots.length}镜 ${shots.slice(0, 2).join('、')}${shots.length > 2 ? '…' : ''}` : ''
  return `将填充 ${target}${shotNote}${switchNote}`
}
function probeText(p: any) {
  const same = p.target === store.episodeId
  return `磁盘 ${p.target}：${p.rows.length}镜${p.oChars ? `＋大纲${p.oChars}字` : ''}${p.sChars ? `＋底稿${p.sChars}字` : ''}${p.imgNote}${same ? ' → 刷新中央' : ` → 中央将从 ${store.episodeId} 切换`}`
}
function cancelProbe(i: number) { probe.value[i] = null }
// 第一步：验盘——把目标集的落盘现状摆出来批（diff 预览），空盘直接拦下
async function probeCentral(t: Turn, i: number) {
  const target = detectTargetEpisode(t)
  if (!target) return ElMessage.warning('找不到目标集号')
  probingIdx.value = i
  try {
    const [sR, oR, scR] = await Promise.all([
      api.listShots(target),
      api.getOutline(target).catch(() => null),
      api.getScreenplay(target).catch(() => null),
    ])
    const rows = ((sR as any)?.data ?? sR ?? []) as any[]
    const oChars = ((((oR as any)?.data?.outline_md) || '') as string).length
    const sChars = ((((scR as any)?.data?.screenplay_md) || '') as string).length
    if (!rows.length && !oChars && !sChars) {
      ElMessage.warning(`目标 ${target} 暂无落盘内容（无镜、无大纲、无底稿）`)
      return
    }
    const oImg = ((((oR as any)?.data?.outline_image) || '') as string)
    const firstImg = (rows[0] as any)?.images?.[0]?.name || ''
    probe.value[i] = { target, rows, oChars, sChars, imgNote: (oImg || firstImg) ? ` · 首帧 ${oImg || firstImg}` : '' }
    scrollBottom()
  } catch {
    ElMessage.error('读取落盘失败，后端未起？')
  } finally {
    probingIdx.value = -1
  }
}
async function applyTurnToCentral(t: Turn, i: number) {
  const target = detectTargetEpisode(t)
  if (!target) return ElMessage.warning('找不到目标集号')
  applyingIdx.value = i
  try {
    // 有验盘结果就直接用，不再拉第二遍
    let rows: any[] = []
    let oChars = 0
    let imgNote = ''
    const p = probe.value[i]
    if (p && p.target === target && Array.isArray(p.rows)) {
      rows = p.rows
      oChars = p.oChars || 0
      imgNote = p.imgNote || ''
    } else {
      const [sR, oR] = await Promise.all([
        api.listShots(target),
        api.getOutline(target).catch(() => null),
      ])
      rows = ((sR as any)?.data ?? sR ?? []) as any[]
      oChars = ((((oR as any)?.data?.outline_md) || '') as string).length
      if (!rows.length && !oChars) {
        ElMessage.warning(`目标 ${target} 暂无落盘内容（无镜、无大纲），未切换中央`)
        return
      }
      const oImg = ((((oR as any)?.data?.outline_image) || '') as string)
      const firstImg = (rows[0] as any)?.images?.[0]?.name || ''
      imgNote = (oImg || firstImg) ? ` · 首帧 ${oImg || firstImg}` : ''
    }
    store.episodeId = target
    store.shots = Array.isArray(rows) ? rows : []
    store.touchSaved()
    store.requestCentralApply(target)
    t.applied = true
    probe.value[i] = null
    saveLocal()
    applyMsg.value[i] = `已填充 ${target}：${store.shots.length}镜${oChars ? `＋大纲${oChars}字` : ''}${imgNote}，中央已同步`
    ElMessage.success(`中央已填充：${target} ${store.shots.length}镜${imgNote}`)
    scrollBottom()
  } catch {
    ElMessage.error('填充失败，后端未起？')
  } finally {
    applyingIdx.value = -1
  }
}
async function reload() {
  loadingList.value = true
  try {
    const r = await api.dshSessions('')
    sessions.value = r.data as any[]
    // 当前会话恒等于当前页面锚点：studio=选中的方案 id（没选就没有会话），其余=集号
    const scope = pageScope.value
    const key = pageKey.value
    curScope.value = scope
    if (key) {
      curKey.value = key
      curSid.value = (findSession(scope, key) || {}).dsh_session_id || ''
    } else {
      curKey.value = ''
      curSid.value = ''
    }
    loadLocal()
    scrollBottom()
  } catch { ElMessage.error('后端未起') }
  finally { loadingList.value = false }
}
const skills = ref<any[]>([])
async function loadSkills() {
  try {
    const r = await api.dshSkills()
    skills.value = ((r as any)?.data?.skills ?? (r as any)?.skills ?? []) as any[]
  } catch { skills.value = [] }
}
async function backToPageSession() {
  // 回到当前页面的锚点会话（没有就建，有就选中）
  const key = pageKey.value
  if (!key) return ElMessage.warning(anchor.value.need || '先选一个对象')
  const scope = pageScope.value
  try { await api.dshEnsure(scope, key) } catch {}
  await reload()
  curKey.value = key
  curScope.value = scope
  curSid.value = (findSession(scope, key) || {}).dsh_session_id || ''
  loadLocal()
  scrollBottom()
  await resumeIfAny()
}
async function ensure(silent = false) {
  // 只确保当前页面锚点会话存在（集号/方案/素材/批次），不再产生 EP-xxx-2 后缀
  const key = pageKey.value
  const scope = pageScope.value
  if (!key) { if (!silent) ElMessage.warning(anchor.value.need || '先选一个对象'); return }
  try {
    await api.dshEnsure(scope, key)
  } catch { if (!silent) ElMessage.error('新建会话失败，后端未起？'); return }
  await reload()
  curKey.value = key
  curScope.value = scope
  curSid.value = (findSession(scope, key) || {}).dsh_session_id || ''
  loadLocal()
  await resumeIfAny()
  if (!silent) ElMessage.success(`已切到${pageSessionLabel.value} ${key}`)
}
function pick(s: any) {
  // 点历史卡 = 切到那条会话对应的对象：集号切中央、方案切方案页、素材切拉片室、批次切投流页
  const scope = s?.scope || pageScope.value
  const key = s?.key || ''
  if (scope === 'episode' && key && key !== store.episodeId && /^EP-/.test(key)) {
    store.episodeId = key
  } else if (scope === 'art' && key) {
    studio.pickPlan(key)
  } else if (scope === 'video' && key) {
    ui.pickVideo(key)
  } else if (scope === 'traffic' && key) {
    ui.trafficAnchor = key
  }
  curKey.value = s.key
  curScope.value = scope
  curSid.value = s.dsh_session_id || ''
  loadLocal()
  scrollBottom()
  void resumeIfAny()
  // 点卡即进入该对话：聚焦输入框，可直接继续聊
  nextTick(() => {
    const ta = document.querySelector('.right .msg-input textarea') as HTMLElement | null
    ta?.focus()
  })
}
function pickAndClose(s: any) {
  pick(s)
  histOpen.value = false
}

// 单轮操作：引用进输入框 / 复制 / 删除整轮（一问一答一起删）
function focusComposer() {
  nextTick(() => {
    const ta = document.querySelector('.right .msg-input textarea') as HTMLElement | null
    ta?.focus()
  })
}
function quoteText(s: string) {
  if (!s) return
  const q = s.split('\n').map(l => `> ${l}`).join('\n')
  msg.value = msg.value ? msg.value.replace(/\s+$/, '') + `\n${q}\n` : `${q}\n`
  focusComposer()
}
async function copyText(s: string) {
  if (!s) return
  try {
    await navigator.clipboard.writeText(s)
    ElMessage.success('已复制')
  } catch {
    try {
      const ta = document.createElement('textarea')
      ta.value = s
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      ta.remove()
      ElMessage.success('已复制')
    } catch { ElMessage.error('复制失败') }
  }
}
function delTurn(i: number) {
  turns.value.splice(i, 1)
  // 索引键的状态（验盘/回执/变更卡）一起清，免得错位挂到别的轮
  probe.value = {}
  applyMsg.value = {}
  changeCard.value = {}
  saveLocal()
}

// 一集一会：会话名即集号，不提供改名入口

async function delSession(s: any) {
  if (loading.value && s.key === curKey.value) stop()
  let remoteOk = true
  try {
    await api.dshDeleteSession(s.scope || curScope.value, s.key)
  } catch {
    remoteOk = false
  }
  // 本地秒删：即使后端是没重启的老版本也先清掉，不让卡片卡死
  try { localStorage.removeItem(`dsh-turns:${s.scope || curScope.value}:${s.key}`) } catch {}
  sessions.value = sessions.value.filter(x => !(x.key === s.key && (x.scope || '') === (s.scope || '')))
  if (curKey.value === s.key) {
    // 删的是当前锚点会话：仍收敛回当前页面锚点（下次发送自动重建）
    curKey.value = pageKey.value
    curScope.value = pageScope.value
    curSid.value = ''
    loadLocal()
    scrollBottom()
  }
  ElMessage.success(remoteOk ? '会话已删除' : '本地已删除（后端待重启同步，刷新后若重现请重启后端）')
}

async function stop() {
  // 显式停止＝杀后端 run（唯一会杀进程的入口）。先断本地跟随，UI 立刻响应。
  const rid = savedRun()
  aborter.value?.abort()
  if (rid) { try { await api.dshRunStop(rid) } catch {} }
  forgetRun()
  const last = turns.value[turns.value.length - 1]
  if (last && !last.a) { last.a = '[已停止]'; saveLocal() }
  loading.value = false
  progress.value = ''
}

async function onPick(e: Event, kind: 'image' | 'file' | 'video') {
  const input = e.target as HTMLInputElement
  const files = Array.from(input.files || [])
  input.value = ''
  if (!files.length) return
  // 上传上限：图片 10MB / 文件 20MB / 参考视频 300MB（与后端抽帧上限对齐）
  const limit = kind === 'image' ? 10 * 1024 * 1024 : kind === 'video' ? 300 * 1024 * 1024 : 20 * 1024 * 1024
  uploading.value = true
  try {
    for (const f of files) {
      if (kind === 'image' && !f.type.startsWith('image/')) continue
      if (kind === 'video' && !f.type.startsWith('video/')) continue
      if (f.size > limit) { ElMessage.warning(`${f.name} 超过${Math.round(limit / 1024 / 1024)}MB，已跳过`); continue }
      const d = await api.uploadFile(f)
      const row = d?.data || d
      const att: Att = { name: f.name, url: row.url, path: row.path, kind, size: f.size }
      if (kind === 'video') att.dur = await probeVideoDur(f)
      pending.value.push(att)
    }
  } catch {
    ElMessage.error('上传失败，后端未起？')
  } finally {
    uploading.value = false
  }
}

function probeVideoDur(f: File): Promise<number> {
  return new Promise(resolve => {
    try {
      const url = URL.createObjectURL(f)
      const v = document.createElement('video')
      v.preload = 'metadata'
      v.onloadedmetadata = () => { const d = v.duration || 0; URL.revokeObjectURL(url); resolve(d) }
      v.onerror = () => { URL.revokeObjectURL(url); resolve(0) }
      v.src = url
      setTimeout(() => resolve(0), 8000)
    } catch { resolve(0) }
  })
}

// 参考视频抽帧：调 video-frames，关键帧引用拼进输入框，agent 直接看图找灵感
const framing = ref('')
async function extractFrames(f: Att) {
  if (framing.value) return
  framing.value = f.path
  try {
    const r: any = await api.videoFrames({ path: f.path, max_frames: 12 })
    const d = r?.data ?? r
    const frames = (d?.frames ?? []) as any[]
    if (!frames.length) { ElMessage.warning('没抽出关键帧'); return }
    const refs = frames.map(x => `@data/uploads/${x.name}`).join('\n')
    msg.value = msg.value ? msg.value.replace(/\s+$/, '') + `\n${refs}\n` : `${refs}\n`
    ElMessage.success(`已抽 ${frames.length} 帧（片长${d?.duration_s ?? '?'}s），引用已填入输入框`)
    focusComposer()
  } catch (e: any) {
    ElMessage.error((e?.response?.data?.msg || e?.message || '抽帧失败').slice(0, 120))
  } finally {
    framing.value = ''
  }
}

async function send() {
  const text = msg.value.trim()
  if ((!text && !pending.value.length) || loading.value) return
  // 会话锚点 = 这一页正在改的对象（没对象就没有会话，不建占位会话）
  const key = pageKey.value
  const scope = pageScope.value
  if (!key) return ElMessage.warning(anchor.value.need || '先选一个对象')
  if (!curKey.value || curKey.value !== key || !findSession(scope, key)) {
    try { await ensure(true) } catch { ElMessage.error('新建会话失败，后端未起？'); return }
  }
  if (!curKey.value) return
  // 附件以后端 cwd 为基准的 @path 引用拼进消息，dsh 侧可直接读取；分镜域默认带上集号，防 agent 从图片文件名猜集号
  const refs = pending.value.map(f => `@data/uploads/${f.path}`).join('\n')
  // 页面感知：给 agent 看这一页的对象（方案原文 / 集号 / 什么都不给）
  const ctx = pageContext.value
  const q = [ctx, text, refs].filter(Boolean).join('\n')
  const files = pending.value.slice()
  msg.value = ''
  pending.value = []
  // 先行落屏：用户消息与附件立刻可见，不等回包
  turns.value.push({ q: text || '(附件)', a: '', files })
  saveLocal()
  const idx = turns.value.length - 1
  loading.value = true
  progress.value = '运行中…'
  scrollBottom()
  // 方案快照先抓：这轮 agent 改了什么，回合结束靠它算差
  await snapPlan()
  const ac = new AbortController()
  let runId = ''
  try {
    // 起 run：任务由后端线程持有，切页/刷新只会断"跟随"，不再杀掉这一轮
    const st: any = await api.dshRunStart({ scope: curScope.value, key: curKey.value, message: q, session_id: curSid.value || undefined, model: model.value || undefined })
    runId = st?.data?.run_id || ''
    if (!runId) throw new Error('起任务失败：' + JSON.stringify(st).slice(0, 140))
    rememberRun(runId)
    const r = await followRun(runId, 0, idx, ac)
    if (r.done) {
      forgetRun()
      if (r.done.session_id && r.done.session_id !== curSid.value) { curSid.value = r.done.session_id; await reload() }
      fillAAt(idx, r.done.answer || '(空回包)')
      if (r.done.retried) ElMessage.info('上一轮被拒答，已自动重试并替换结果')
      void checkPlanChange(idx)
    } else if (r.aborted) {
      // 断开跟随（切页/刷新）：任务在后端继续跑，run_id 已记住，回来会自动重连
    } else if (r.stoppedFlag) {
      forgetRun()
      fillAAt(idx, '[已停止]')
      void checkPlanChange(idx)
    } else {
      // 流断了（切页/刷新/网络）：去问 run 的真实状态——任务可能还在跑，也可能已经跑完
      let st: any = null
      try { st = (await api.dshRunState(runId))?.data } catch {}
      if (st && st.status !== 'running') { forgetRun(); applyFinished(st) }
      else { rememberRun(runId) }   // 保留 run_id，回来/刷新后自动重连
      void checkPlanChange(idx)
    }
  } catch (e: any) {
    forgetRun()
    const m = (e?.message || '调用失败').slice(0, 200)
    fillAAt(idx, '[失败] ' + m)
    ElMessage.error(m.slice(0, 120))
    void checkPlanChange(idx)
  } finally {
    loading.value = false
    progress.value = ''
    aborter.value = null
  }
  scrollBottom()
}

/** 跟随一个后端 run：进度文案 + 事件计数 + 断线即返回（不杀任务）。 */
async function followRun(runId: string, from: number, idx: number, ac: AbortController, tag = '') {
  const t0 = Date.now()
  let evCount = 0
  let evAt = Date.now()
  let done: any = null
  let errMsg = ''
  let stoppedFlag = false
  let aborted = false
  let streamErr = ''
  // 事件计数由 tick 统一渲染（历史 bug：tick 每秒覆盖 SSE 处理器写的文案，
  // 长任务永远只显示"运行中…Ns"，看着像卡死；写 3 分钟剧本单步静默可超 100s，属正常）
  acts.value = []
  const tick = setInterval(() => {
    nowTs.value = Date.now()
    const s = Math.floor((Date.now() - t0) / 1000)
    if (idx >= 0 && turns.value[idx]?.a) return
    if (!evCount) {
      if (s >= 8) progress.value = `运行中…${tag}${s}s（dsh 冷启动 + 首 token 较慢；长剧本单步可能要几分钟，进度看事件计数）`
      return
    }
    const gap = Math.floor((Date.now() - evAt) / 1000)
    const tail = evCount > 200 ? '（事件过多，疑似空转，可点停止）'
      : gap >= 60 ? `（已 ${gap}s 无新事件：模型在写长文/长思考，正常，别点停止）`
      : gap >= 20 ? `（${gap}s 无新事件）` : ''
    progress.value = `运行中…${tag} 事件 ${evCount} · ${s}s ${tail}`
  }, 1000)
  loading.value = true
  progress.value = `运行中…${tag}`
  aborter.value = ac
  try {
    await api.dshRunFollow(runId, from, (ev, d) => {
      if (ev === 'dsh') { evCount = d?.n || evCount; evAt = Date.now(); pushAct(d?.label || '') }
      else if (ev === 'retry') progress.value = d?.msg || '检测到拒答，自动重试中…'
      else if (ev === 'done') done = d
      else if (ev === 'error') { errMsg = d?.msg || '调用失败'; stoppedFlag = !!d?.stopped }
    }, ac.signal)
  } catch (e: any) {
    // 连接类失败（切页 abort / 刷新 network error / nginx 断）都不再当成任务失败：
    // run 在后端，调用方会去问 run 的真实状态再决定怎么显示
    if (ac.signal.aborted) aborted = true
    else streamErr = (e?.message || '流中断').slice(0, 200)
  } finally {
    clearInterval(tick)
    progress.value = ''
  }
  return { done, errMsg, stoppedFlag, aborted, streamErr }
}

/** 把已完成/中断的 run 结果补回最后一轮气泡（刷新、切页回来后走这里）。 */
function applyFinished(st: any) {
  const last = turns.value[turns.value.length - 1]
  if (!last) return
  // 空答案 or 之前的"[失败] …"占位才覆盖；真答案/已停止不动
  if (last.a && !last.a.startsWith('[失败]')) return
  if (st.status === 'done') last.a = st.answer || '(空回包)'
  else if (st.status === 'stopped') last.a = '[已停止]'
  else last.a = '[失败] ' + String(st.err || '流中断').slice(0, 200)
  saveLocal()
  scrollBottom()
}

/** 重连：页面加载/切回会话时，把后端还在跑（或刚跑完）的那一轮接回气泡。 */
async function resumeIfAny() {
  if (loading.value) return
  let rid = savedRun()
  if (!rid) {
    // 本地游标丢了（新标签页/换设备）：按会话键问后端还有没有在跑的 run
    try {
      const arr: any[] = ((await api.dshRuns({ scope: curScope.value, key: curKey.value, limit: 3 }))?.data) || []
      const running = arr.find(x => x && x.status === 'running')
      if (running) rid = running.id
      else if (arr[0]) { applyFinished(arr[0]); return }
      if (!rid) return
    } catch { return }
  }
  let st: any = null
  try { st = (await api.dshRunState(rid))?.data } catch { forgetRun(); return }
  if (!st) { forgetRun(); return }
  if (st.status !== 'running') { forgetRun(); applyFinished(st); return }
  rememberRun(rid)
  const idx = Math.max(0, turns.value.length - 1)
  const ac = new AbortController()
  await snapPlan()
  const r = await followRun(rid, 0, idx, ac, '（已重连）')
  if (r.aborted) return
  if (r.done) {
    forgetRun()
    if (r.done.session_id && r.done.session_id !== curSid.value) { curSid.value = r.done.session_id; await reload() }
    fillAAt(idx, r.done.answer || '(空回包)')
    void checkPlanChange(idx)
  } else if (r.stoppedFlag) { forgetRun(); fillAAt(idx, '[已停止]') }
  else { forgetRun(); fillAAt(idx, '[失败] ' + String(r.errMsg || '流中断').slice(0, 200)) }
}
watch(() => [store.episodeId, route.path, studio.planId, ui.videoAnchor, ui.trafficAnchor], async () => {
  // 页面锚点变化即切会话（只断跟随不杀任务，切回自动重连）；无锚点只刷新列表不建垃圾会话
  try { aborter.value?.abort() } catch {}
  loading.value = false
  progress.value = ''
  if (pageScope.value === 'episode' && store.episodeId && !findSession('episode', store.episodeId)) {
    try { await api.dshEnsureEpisode(store.episodeId) } catch {}
  }
  await reload()
  await resumeIfAny()
})
onMounted(async () => {
  purgeLegacyDomainCaches()
  await loadSkills()
  await reload()
  await backToPageSessionSilent()
  await resumeIfAny()   // 刷新后把后台还在跑/刚跑完的那一轮接回来
})
// 一次性迁移：一集一会之前攒下的异域旧缓存（story/character/traffic/global 的 turns 与 run 游标）清掉，
// 只保留 episode 与 art 域；旧后缀 EP-xxx-2 的 turns 一起清（后端映射本就只剩这两域，删本地即对齐）。
function purgeLegacyDomainCaches() {
  try {
    if (localStorage.getItem('suli.dsh.purged-v1')) return
    const drop: string[] = []
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i) || ''
      if (k.startsWith('dsh-turns:') || k.startsWith('dsh-run:')) {
        const scope = k.split(':')[1] || ''
        if (scope && scope !== 'episode' && scope !== 'art') drop.push(k)
      }
    }
    drop.forEach(k => { try { localStorage.removeItem(k) } catch {} })
    try { localStorage.setItem('suli.dsh.purged-v1', String(Date.now())) } catch {}
  } catch {}
  // 一次性：单图页的占位会话键 studio-draft（没选方案时的兜底键）留下的旧桶
  try {
    if (!localStorage.getItem('suli.dsh.purged-v2')) {
      for (const k of ['dsh-turns:art:studio-draft', 'dsh-run:art:studio-draft']) {
        try { localStorage.removeItem(k) } catch {}
      }
      localStorage.setItem('suli.dsh.purged-v2', String(Date.now()))
    }
  } catch {}
}
async function backToPageSessionSilent() {
  // 首屏自动收敛到当前页面锚点会话（已有就不建，不打扰）；非集号域只在发送时建
  if (pageScope.value !== 'episode') return
  const epKey = store.episodeId
  if (!epKey || findSession('episode', epKey)) return
  try { await api.dshEnsureEpisode(epKey); await reload() } catch {}
}
</script>
<style scoped>
.right{width:440px;box-sizing:border-box;background:var(--suli-surface);border-left:1px solid var(--suli-border);padding:14px;display:flex;flex-direction:column;height:100vh;max-height:100vh;overflow:hidden;flex-shrink:0;position:relative}
.head{display:flex;align-items:center;gap:4px}
.agent-sub{display:flex;gap:6px;margin-top:8px;align-items:center}
.hint{font-size:12px;color:var(--suli-text-2);margin:6px 0}
.run-card{margin:6px 0;padding:8px 10px;display:flex;flex-direction:column;gap:6px}
.run-head{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.run-pulse{width:8px;height:8px;border-radius:50%;background:var(--suli-primary);box-shadow:0 0 0 0 rgba(251,114,153,.6);animation:runpulse 1.6s infinite}
@keyframes runpulse{0%{box-shadow:0 0 0 0 rgba(251,114,153,.55)}70%{box-shadow:0 0 0 8px rgba(251,114,153,0)}100%{box-shadow:0 0 0 0 rgba(251,114,153,0)}}
.run-acts{display:flex;flex-direction:column;gap:2px;max-height:150px;overflow:auto}
.run-act{display:flex;align-items:baseline;gap:6px;font-size:12px;line-height:1.6}
.run-dot{width:6px;height:6px;border-radius:50%;flex:0 0 6px;background:var(--suli-border-hover)}
.run-dot.tool{background:var(--suli-accent)}
.run-dot.result{background:var(--suli-text-3)}
.run-dot.write{background:var(--suli-primary)}
.run-dot.think{background:var(--suli-gold)}
.run-label{flex:1;min-width:0;color:var(--suli-text-2);word-break:break-all}
.run-time{color:var(--suli-text-3);flex:0 0 auto}
.run-foot{font-size:11px;line-height:1.6}
.cur-card{margin-top:8px;padding:10px 12px;cursor:pointer}
.cur-card:hover{border-color:var(--suli-primary)}
.cur-title{display:flex;gap:6px;align-items:center;font-size:12px;color:var(--suli-primary);font-weight:700}
.cur-ico{font-size:14px}
.cur-count{margin-left:auto;font-weight:400;color:var(--suli-text-3);font-size:11px}
.cur-key{margin-top:2px;font-size:14px;font-weight:800;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
/* 会话历史抽屉：盖住右侧面板，照参考（标题左＋三按钮右，空态居中） */
.hist-mask{position:absolute;inset:0;background:rgba(0,0,0,.35);z-index:40}
.hist-drawer{position:absolute;top:0;right:0;bottom:0;width:min(360px,100%);background:var(--suli-surface);border-left:1px solid var(--suli-border);box-shadow:var(--suli-shadow);z-index:41;display:flex;flex-direction:column;transform:translateX(100%);transition:transform .22s ease}
.hist-drawer.open{transform:translateX(0)}
.hist-head{display:flex;gap:2px;align-items:center;padding:12px 12px 8px;font-size:15px}
.hist-tools{display:flex;gap:8px;align-items:center;padding:0 12px 8px}
.hist-list{flex:1;overflow-y:auto;padding:4px 12px 12px;display:flex;flex-direction:column;gap:8px}
.hist-empty{text-align:center;color:var(--suli-text-3);font-size:13px;margin-top:48px}
.hist-item{padding:10px 12px;cursor:pointer}
.hist-item:hover{border-color:var(--suli-primary)}
.hist-item.active{border-color:var(--suli-primary)}
.hist-top{display:flex;gap:4px;align-items:center;min-width:0}
.dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.dot.on{background:var(--suli-success,#2da44e)}
.dot.off{background:var(--suli-text-3,#a3a3a3)}
.hist-key{font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:190px}
.hist-meta{margin-top:4px;font-size:11px;color:var(--suli-text-2)}
.hist-rename{display:flex;gap:6px;align-items:center}
.turns{flex:1;overflow-y:auto;overflow-x:hidden;overscroll-behavior:contain;margin-top:8px;display:flex;flex-direction:column;gap:8px;min-height:0}
.turn{display:flex;flex-direction:column;gap:8px}
.bubble-row{display:block}
.bubble-row.from-user{text-align:right}
.bubble-row.from-agent{text-align:left}
.bubble{display:inline-block;vertical-align:top;max-width:88%;padding:9px 11px;font-size:12px;white-space:pre-wrap;word-break:break-word;text-align:left;box-sizing:border-box}
.user-b{background:var(--suli-primary);color:#fff;border-radius:14px 4px 14px 14px}
.agent-b{background:var(--suli-surface);border:1px solid var(--suli-border);border-radius:4px 14px 14px 14px;color:var(--suli-text)}
.q{font-weight:600}
.user-b .md-view{color:#fff}
.user-b .md-view :deep(p),
.user-b .md-view :deep(li),
.user-b .md-view :deep(h1),
.user-b .md-view :deep(h2),
.user-b .md-view :deep(h3),
.user-b .md-view :deep(h4),
.user-b .md-view :deep(blockquote),
.user-b .md-view :deep(td),
.user-b .md-view :deep(th){color:#fff}
.user-b .md-view :deep(a){color:#fff;text-decoration:underline}
.user-b .md-view :deep(code){background:rgba(255,255,255,.22);color:#fff}
.user-b .md-view :deep(pre){background:rgba(0,0,0,.22)}
.user-b .md-view :deep(pre code){background:none}
.user-b .md-view :deep(blockquote){border-left-color:rgba(255,255,255,.6);background:rgba(255,255,255,.12)}
.user-b .md-view :deep(table),
.user-b .md-view :deep(th),
.user-b .md-view :deep(td){border-color:rgba(255,255,255,.45)}
.user-b .md-view :deep(.md-img){border-color:rgba(255,255,255,.5)}
.a{margin-top:0}
.a.thinking{font-size:12px;color:var(--suli-text-3,#a3a3a3)}
.agent-b .md-view{font-size:12.5px}
.files.files-end{justify-content:flex-end}
.msg-actions{display:flex;gap:0;margin-top:6px}
.from-user .msg-actions{justify-content:flex-end}
.msg-actions .el-button{font-size:11px;padding:3px 9px;min-height:0;color:var(--suli-primary,#FB7299);background:rgba(251,114,153,.1);border-radius:8px;box-shadow:0 1px 5px rgba(251,114,153,.35)}
.msg-actions .el-button:hover{background:rgba(251,114,153,.2)}
.user-b .file-chip{color:#fff;border-color:rgba(255,255,255,.5);background:transparent}
.turn-apply{margin-top:8px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;border-top:1px dashed var(--suli-border);padding-top:8px}
.apply-hint{flex:1;font-size:11px;color:var(--suli-text-2);min-width:140px}
.apply-msg{margin-top:6px;font-size:11px;color:var(--suli-success,#2da44e)}
.files{margin-top:6px;display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.thumb{width:72px;height:72px;border-radius:8px;border:1px solid var(--suli-border)}
.thumb :deep(img){object-fit:cover}
.file-chip{font-size:12px;color:var(--suli-text);text-decoration:none;border:1px solid var(--suli-border);border-radius:8px;padding:4px 8px;background:var(--suli-bg-2,#f4f4f5)}
.file-chip:hover{border-color:var(--suli-primary)}
.composer{flex-shrink:0;border-top:1px solid var(--suli-border);margin-top:auto;padding-top:8px;margin-bottom:12px;background:var(--suli-surface)}
.pending{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px}
.pend-chip{display:flex;align-items:center;gap:4px;border:1px solid var(--suli-border);border-radius:8px;padding:2px 4px 2px 2px;background:var(--suli-bg-2,#f4f4f5);max-width:100%}
.pend-thumb{width:32px;height:32px;border-radius:6px;object-fit:cover}
.pend-file{font-size:16px;padding:0 4px}
.pend-name{font-size:12px;max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.input-row{display:flex}
.msg-input{flex:1}
.toolbar{display:flex;align-items:center;gap:6px;margin-top:8px}
.tools{display:flex;gap:6px}
.tip{flex:1;text-align:center;font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
</style>
