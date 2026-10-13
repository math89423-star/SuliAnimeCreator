<template>
  <div class="right">
    <div class="head"><h4 style="margin:0">Agent</h4><span style="flex:1" /><el-tag size="small" type="info" title="dsh 只做 skill 导演判断，草案发散走轻链">单会话·skill</el-tag><el-button size="small" circle @click="store.toggleRight()">›</el-button></div>
    <div style="display:flex;gap:6px;margin-top:8px;align-items:center">
      <span class="suli-muted" style="font-size:12px">本集 {{ store.episodeId }} · skill {{ skills.length ? `${skills.length}已载` : '载入中…' }}</span>
      <span style="flex:1" />
      <el-button size="small" @click="backToEpisode">本集会话</el-button>
      <el-button size="small" @click="ensure">新建</el-button>
    </div>
    <div v-if="loadingList"><div class="skeleton" style="margin-top:8px;height:32px" /></div>
    <el-button v-else-if="!sessions.length" size="small" type="primary" style="margin-top:8px" @click="ensure">新建会话</el-button>
    <div v-else style="margin-top:8px">
      <div class="suli-card sess-head" @click="open = !open" title="点击展开/收起会话列表">
        <template v-if="!renaming">
          <b style="font-size:13px">{{ curKey || '无会话' }}</b>
          <el-tag v-if="curSess" size="small" :type="curSess.dsh_session_id ? 'success' : 'info'">{{ curSess.dsh_session_id ? '进行中' : '未建' }}</el-tag>
          <span style="flex:1" />
          <span class="suli-muted" style="font-size:12px">{{ open ? '▲' : '▼' }}</span>
          <el-button size="small" text circle title="重命名当前会话" @click.stop="startRename">✎</el-button>
          <el-button size="small" text circle title="删除当前会话" @click.stop="delCurrent">✕</el-button>
        </template>
        <template v-else>
          <el-input
            ref="renameInput" v-model="renameText" size="small" style="flex:1;min-width:0"
            placeholder="新会话名，回车确定" maxlength="60"
            @click.stop @keydown.enter="doRename" @keydown.esc="renaming = false"
          />
          <el-button size="small" type="primary" @click.stop="doRename">确定</el-button>
          <el-button size="small" @click.stop="renaming = false">取消</el-button>
        </template>
      </div>
      <div v-if="open" class="sess-drop">
        <div
          v-for="s in sessions" :key="s.scope + ':' + s.key + s.dsh_session_id"
          class="suli-card sess-item" :class="{ active: curKey === s.key && curScope === s.scope }"
          @click="pickAndClose(s)"
        >
          <div style="display:flex;gap:6px;align-items:center">
            <b style="font-size:12px">{{ s.key }}</b>
            <el-tag size="small" :type="s.dsh_session_id ? 'success' : 'info'">{{ s.dsh_session_id ? '进行中' : '未建' }}</el-tag>
            <span style="flex:1" />
            <span class="suli-muted tnum" style="font-size:11px">{{ rel(s.last_active) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 消息区：居中滚动（常驻占位把输入框压到底；无会话时内部留空） -->
    <div ref="turnBox" class="turns">
      <el-empty v-if="!turns.length && !loading" description="无对话" :image-size="64" />
      <template v-else>
        <div v-for="(t, i) in turns" :key="i" class="turn">
          <div class="bubble-row from-user">
            <div class="bubble user-b">
              <div class="q">{{ t.q }}</div>
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
                >📎 {{ f.name }}</a>
              </div>
            </div>
          </div>
          <div class="bubble-row from-agent">
            <div class="bubble agent-b">
              <div v-if="!t.a" class="a thinking">思考中…</div>
              <MarkdownView v-else class="a-md" :content="t.a" />
          <div v-if="canApply(t)" class="turn-apply">
            <template v-if="!probe[i]">
              <span class="apply-hint">{{ applyHint(t) }}</span>
              <el-button size="small" type="primary" @click="probeCentral(t, i)" :loading="probingIdx === i">✓ 接受并填充中央</el-button>
            </template>
            <template v-else>
              <span class="apply-hint">{{ probeText(probe[i]) }}</span>
              <el-button size="small" type="primary" @click="applyTurnToCentral(t, i)" :loading="applyingIdx === i">确认填充</el-button>
              <el-button size="small" @click="cancelProbe(i)">取消</el-button>
            </template>
          </div>
          <div v-if="applyMsg[i]" class="apply-msg">{{ applyMsg[i] }}</div>
              <div class="msg-actions">
                <el-button text size="small" @click="quoteText(t.a)">引用</el-button>
                <el-button text size="small" @click="copyText(t.a || '')">复制</el-button>
                <el-button text size="small" @click="delTurn(i)">删除</el-button>
              </div>
            </div>
          </div>
        </div>
      </template>
      <div v-if="loading && progress" class="hint">{{ progress }}</div>
    </div>

    <!-- 输入区：沉底 -->
    <div class="composer">
      <div v-if="pending.length" class="pending">
        <div v-for="(f, i) in pending" :key="i" class="pend-chip">
          <img v-if="f.kind === 'image'" :src="f.url" class="pend-thumb" />
          <span v-else class="pend-file">📎</span>
          <span class="pend-name">{{ f.name }}</span>
          <el-button size="small" text circle @click="pending.splice(i, 1)">✕</el-button>
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
          <el-button circle size="small" @click="imgInput?.click()" :loading="uploading" title="上传图片">🖼</el-button>
          <el-button circle size="small" @click="fileInput?.click()" :loading="uploading" title="上传文件">📎</el-button>
        </div>
        <span class="tip suli-muted">Enter 发送 · Shift+Enter 换行</span>
        <el-button v-if="loading" type="danger" round size="small" @click="stop">⏹ 停止</el-button>
        <el-button v-else type="primary" round size="small" @click="send" :disabled="!msg.trim() && !pending.length">发送</el-button>
      </div>
      <input ref="imgInput" type="file" accept="image/*" multiple hidden @change="onPick($event, 'image')" />
      <input ref="fileInput" type="file" multiple hidden @change="onPick($event, 'file')" />
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import MarkdownView from './MarkdownView.vue'
import { useAppStore } from '../stores/app'

interface Att { name: string; url: string; path: string; kind: 'image' | 'file' }
interface Turn { q: string; a: string; files?: Att[]; applied?: boolean }

const store = useAppStore()
const route = useRoute()
// 不再按故事/角色/分镜分页：单会话列表，scope 只剩存储字段（存量历史沿用原值）
const curScope = ref('episode')
const sessions = ref<any[]>([])
const curKey = ref('')
const curSid = ref('')
const msg = ref('')

function routeScope() {
  if (route.path.startsWith('/character')) return 'character'
  if (route.path.startsWith('/board')) return 'episode'
  return 'story'
}
function findSession(scope: string, key: string) {
  return sessions.value.find(s => s.scope === scope && s.key === key)
}
// 当前选中的会话行（表头展示用）
const curSess = computed(() => findSession(curScope.value, curKey.value))
// 下拉展开/收起（自研，不用 el-select：它的 teleported 遮罩卡死时会吃掉整行点击）
const open = ref(false)
const turns = ref<Turn[]>([])
const loading = ref(false)
const loadingList = ref(false)
const progress = ref('')
const pending = ref<Att[]>([])
const uploading = ref(false)
const aborter = ref<AbortController | null>(null)
const turnBox = ref<HTMLElement | null>(null)
const imgInput = ref<HTMLInputElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const applyingIdx = ref(-1)
const probingIdx = ref(-1)
const probe = ref<Record<number, any>>({})
const applyMsg = ref<Record<number, string>>({})

function autoKey() {
  if (routeScope() === 'character') return store.selectedCharId || 'global'
  if (routeScope() === 'episode') return store.episodeId || 'global'
  return 'global'
}
function rel(ts: number) {
  if (!ts) return '未开始'
  const s = Math.floor((Date.now() - ts) / 1000)
  if (s < 60) return '刚刚'
  if (s < 3600) return Math.floor(s / 60) + '分钟前'
  if (s < 86400) return Math.floor(s / 3600) + '小时前'
  return Math.floor(s / 86400) + '天前'
}
function histKey() { return `dsh-turns:${curScope.value}:${curKey.value || 'new'}` }
function loadLocal() { try { turns.value = JSON.parse(localStorage.getItem(histKey()) || '[]') } catch { turns.value = [] } }
function saveLocal() { try { localStorage.setItem(histKey(), JSON.stringify(turns.value.slice(-30))) } catch {} }
function scrollBottom() {
  nextTick(() => {
    const el = turnBox.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

// 接受并填充中央：像批准diff一样，一键把Agent落盘结果拉到中央工作区
function extractEpisodes(t: Turn): string[] {
  const txt = `${t.q || ''}\n${t.a || ''}`
  const m = txt.match(/EP-[A-Za-z0-9\u4e00-\u9fa5_-]+/g) || []
  // 占位写法（EP-xxx 之类）不算落盘引用
  return [...new Set(m.filter(x => !/x{2,}/i.test(x)))]
}
function extractShots(t: Turn): string[] {
  const m = (t.a || '').match(/SHOT-[A-Za-z0-9_-]+/g)
  return m ? [...new Set(m)] : []
}
function detectTargetEpisode(t: Turn): string {
  if (/^EP-/.test(curKey.value)) return curKey.value
  const eps = extractEpisodes(t)
  if (eps.length) return eps[0]
  if (curKey.value && /^EP-/.test(curKey.value)) return curKey.value
  return store.episodeId
}
function canApply(t: Turn) {
  if (!t.a) return false
  if (t.applied) return false
  if (/^(❌|⏹)/.test(t.a.trim())) return false
  // 只有提到真实集号/镜号（即有落盘内容可拉）才给填充入口，纯问答不挂按钮
  if (!extractEpisodes(t).length && !extractShots(t).length) return false
  return true
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
  return `磁盘 ${p.target}：${p.rows.length}镜${p.oChars ? `＋大纲${p.oChars}字` : ''}${p.imgNote}${same ? ' → 刷新中央' : ` → 中央将从 ${store.episodeId} 切换`}`
}
function cancelProbe(i: number) { probe.value[i] = null }
// 第一步：验盘——把目标集的落盘现状摆出来批（diff 预览），空盘直接拦下
async function probeCentral(t: Turn, i: number) {
  const target = detectTargetEpisode(t)
  if (!target) return ElMessage.warning('找不到目标集号')
  probingIdx.value = i
  try {
    const [sR, oR] = await Promise.all([
      api.listShots(target),
      api.getOutline(target).catch(() => null),
    ])
    const rows = ((sR as any)?.data ?? sR ?? []) as any[]
    const oChars = ((((oR as any)?.data?.outline_md) || '') as string).length
    if (!rows.length && !oChars) {
      ElMessage.warning(`目标 ${target} 暂无落盘内容（无镜、无大纲）`)
      return
    }
    const oImg = ((((oR as any)?.data?.outline_image) || '') as string)
    const firstImg = (rows[0] as any)?.images?.[0]?.name || ''
    probe.value[i] = { target, rows, oChars, imgNote: (oImg || firstImg) ? ` · 首帧 ${oImg || firstImg}` : '' }
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
    // 单会话收敛：一集一会话，优先选中本集 episode 会话
    const epKey = store.episodeId
    const epSess = findSession('episode', epKey)
    const cur = epSess || findSession(curScope.value, curKey.value) || sessions.value[0]
    curKey.value = (cur || {}).key || epKey || ''
    curScope.value = (cur || {}).scope || 'episode'
    curSid.value = (cur || {}).dsh_session_id || ''
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
async function backToEpisode() {
  // 一键回到本集单会话：没有就建，有就选中
  const epKey = store.episodeId
  if (!epKey) return ElMessage.warning('先选集号')
  try { await api.dshEnsureEpisode(epKey) } catch {}
  await reload()
  curKey.value = epKey
  curScope.value = 'episode'
  curSid.value = (findSession('episode', epKey) || {}).dsh_session_id || ''
  loadLocal()
  scrollBottom()
}
async function ensure(silent = false) {
  const sc = routeScope()
  const base = autoKey()
  // 同名已存在就顺延，保证每次新建都多出一行：EP-5S01 → EP-5S01-2 → …
  let k = base
  let n = 2
  while (findSession(sc, k)) k = `${base}-${n++}`
  try {
    await api.dshEnsure(sc, k)
  } catch { ElMessage.error('新建失败，后端未起？'); return }
  await reload()
  curKey.value = k
  curScope.value = sc
  curSid.value = (findSession(sc, k) || {}).dsh_session_id || ''
  loadLocal()
  if (!silent) ElMessage.success(`已新建 ${k}`)
}
function pick(s: any) {
  curKey.value = s.key
  curScope.value = s.scope || routeScope()
  curSid.value = s.dsh_session_id || ''
  loadLocal()
  scrollBottom()
  // 点卡即进入该对话：聚焦输入框，可直接继续聊
  nextTick(() => {
    const ta = document.querySelector('.right .msg-input textarea') as HTMLElement | null
    ta?.focus()
  })
}
function pickAndClose(s: any) {
  pick(s)
  open.value = false
}

function delCurrent() {
  const s = findSession(curScope.value, curKey.value)
  if (s) delSession(s)
  else ElMessage.warning('无可删会话')
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
  // 索引键的状态（验盘/回执）一起清，免得错位挂到别的轮
  probe.value = {}
  applyMsg.value = {}
  saveLocal()
}

// 行内改名：不经弹窗，直接在表头改（弹窗层在此页曾无响应）
const renaming = ref(false)
const renameText = ref('')
const renameInput = ref<any>(null)
function startRename() {
  const s = findSession(curScope.value, curKey.value)
  if (!s) return ElMessage.warning('无可改名会话')
  renaming.value = true
  renameText.value = s.key
  nextTick(() => {
    const el = renameInput.value as any
    const inp = el?.$el?.querySelector?.('input') || el
    inp?.focus?.()
    inp?.select?.()
  })
}
async function doRename() {
  const s = findSession(curScope.value, curKey.value)
  if (!s) { renaming.value = false; return }
  const v = (renameText.value || '').trim()
  if (!v) return ElMessage.warning('名字不能为空')
  if (v === s.key) { renaming.value = false; return }
  try {
    await api.dshRename(s.scope, s.key, v)
  } catch (e: any) {
    ElMessage.error((e?.response?.data?.msg || e?.message || '改名失败').slice(0, 120))
    return
  }
  // 本地聊天记录跟着改名搬家
  try {
    const oldH = localStorage.getItem(`dsh-turns:${s.scope}:${s.key}`)
    if (oldH !== null) {
      localStorage.setItem(`dsh-turns:${s.scope}:${v}`, oldH)
      localStorage.removeItem(`dsh-turns:${s.scope}:${s.key}`)
    }
  } catch {}
  await reload()
  curKey.value = v
  curScope.value = s.scope
  curSid.value = (findSession(s.scope, v) || {}).dsh_session_id || ''
  loadLocal()
  renaming.value = false
  ElMessage.success(`已改名 ${v}`)
}

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
    curKey.value = (sessions.value[0] || {}).key || ''
    curSid.value = (sessions.value[0] || {}).dsh_session_id || ''
    loadLocal()
    scrollBottom()
  }
  ElMessage.success(remoteOk ? '会话已删除' : '本地已删除（后端待重启同步，刷新后若重现请重启后端）')
}

function stop() {
  aborter.value?.abort()
}

async function onPick(e: Event, kind: 'image' | 'file') {
  const input = e.target as HTMLInputElement
  const files = Array.from(input.files || [])
  input.value = ''
  if (!files.length) return
  const limit = kind === 'image' ? 10 * 1024 * 1024 : 20 * 1024 * 1024
  uploading.value = true
  try {
    for (const f of files) {
      if (kind === 'image' && !f.type.startsWith('image/')) continue
      if (f.size > limit) { ElMessage.warning(`${f.name} 超过${limit / 1024 / 1024}MB，已跳过`); continue }
      const d = await api.uploadFile(f)
      const row = d?.data || d
      pending.value.push({ name: f.name, url: row.url, path: row.path, kind })
    }
  } catch {
    ElMessage.error('上传失败，后端未起？')
  } finally {
    uploading.value = false
  }
}

async function send() {
  const text = msg.value.trim()
  if ((!text && !pending.value.length) || loading.value) return
  // 无会话时自动建一个再发，不让按钮成死路
  if (!curKey.value) {
    try { await ensure(true) } catch { ElMessage.error('新建会话失败，后端未起？'); return }
  }
  if (!curKey.value) return
  // 附件以后端 cwd 为基准的 @path 引用拼进消息，dsh 侧可直接读取；分镜域默认带上集号，防 agent 从图片文件名猜集号
  const refs = pending.value.map(f => `@data/uploads/${f.path}`).join('\n')
  const ctx = /^EP-/.test(curKey.value) ? `集号：${curKey.value}` : ''
  const q = [ctx, text, refs].filter(Boolean).join('\n')
  const files = pending.value.slice()
  msg.value = ''
  pending.value = []
  // 先行落屏：用户消息与附件立刻可见，不等回包
  turns.value.push({ q: text || '(附件)', a: '', files })
  saveLocal()
  const idx = turns.value.length - 1
  const fillA = (a: string) => { if (turns.value[idx]) { turns.value[idx].a = a; saveLocal() } }
  loading.value = true
  progress.value = '运行中…'
  scrollBottom()
  const ac = new AbortController()
  aborter.value = ac
  try {
    let done: any = null
    let errMsg = ''
    await api.dshRunStream(
      { scope: curScope.value, key: curKey.value, message: q, session_id: curSid.value || undefined },
      (ev, d) => {
        if (ev === 'dsh') progress.value = `运行中…事件 ${d.n || ''}`
        else if (ev === 'done') done = d
        else if (ev === 'error') errMsg = (d as any).msg || '调用失败'
      },
      ac.signal,
    )
    if (done) {
      if (done.session_id && done.session_id !== curSid.value) { curSid.value = done.session_id; await reload() }
      fillA(done.answer || '(空回包)')
    } else {
      fillA('❌ ' + (errMsg || '流中断'))
      ElMessage.error((errMsg || '流中断').slice(0, 120))
    }
  } catch (e: any) {
    if (ac.signal.aborted) {
      fillA('⏹ 已停止')
    } else {
      fillA('❌ 流连接失败')
      ElMessage.error('流连接失败')
    }
  } finally { loading.value = false; progress.value = ''; aborter.value = null }
  scrollBottom()
}
watch(() => [store.episodeId, store.selectedCharId, route.path], () => {
  reload()
})
onMounted(async () => { await loadSkills(); await reload(); await backToEpisodeSilent() })
async function backToEpisodeSilent() {
  // 首屏自动收敛到本集单会话（已有就不建，不打扰）
  const epKey = store.episodeId
  if (!epKey || findSession('episode', epKey)) return
  try { await api.dshEnsureEpisode(epKey); await reload() } catch {}
}
</script>
<style scoped>
.right{width:440px;box-sizing:border-box;background:var(--suli-surface);border-left:1px solid var(--suli-border);padding:14px;display:flex;flex-direction:column;height:100vh;max-height:100vh;overflow:hidden;flex-shrink:0}
.head{display:flex;align-items:center}
.hint{font-size:12px;color:var(--suli-text-2);margin:6px 0}
.sess-head{display:flex;gap:6px;align-items:center;padding:8px;cursor:pointer}
.sess-drop{margin-top:6px;display:flex;flex-direction:column;gap:6px;max-height:220px;overflow-y:auto}
.sess-item{padding:8px;cursor:pointer}
.sess-item.active{border-color:var(--suli-primary)}
.turns{flex:1;overflow-y:auto;overflow-x:hidden;overscroll-behavior:contain;margin-top:8px;display:flex;flex-direction:column;gap:8px;min-height:0}
.turn{display:flex;flex-direction:column;gap:8px}
.bubble-row{display:block}
.bubble-row.from-user{text-align:right}
.bubble-row.from-agent{text-align:left}
.bubble{display:inline-block;vertical-align:top;max-width:88%;padding:9px 11px;font-size:12px;white-space:pre-wrap;word-break:break-word;text-align:left;box-sizing:border-box}
.user-b{background:var(--suli-primary);color:#fff;border-radius:14px 4px 14px 14px}
.agent-b{background:var(--suli-surface);border:1px solid var(--suli-border);border-radius:4px 14px 14px 14px;color:var(--suli-text)}
.q{font-weight:600}
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
