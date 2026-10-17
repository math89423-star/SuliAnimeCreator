<template>
  <div class="lab">
    <div class="suli-card head">
      <div class="head-row">
        <h3 style="margin:0">拉片室</h3>
        <el-tag size="small" effect="plain">找参考 · 抽帧 · 反推手法</el-tag>
        <span style="flex:1" />
        <span class="suli-muted" style="font-size:12px">抽帧走本项目 ffmpeg 工具；分析由 Agent 逐帧看图产出报告</span>
      </div>
      <div class="suli-muted" style="font-size:12px;margin-top:6px">
        上传对标视频（或粘贴直链）→ 时间轴圈选片段 → 抽关键帧 → Agent 反推运镜 / 节奏 / 钩子。只借手法，不抄画面。
      </div>
    </div>

    <div class="cols">
      <!-- 左列：操作 -->
      <div class="col-left">
        <div class="suli-card sect">
          <div class="sect-title">① 视频源</div>
          <div
            v-if="!src"
            class="drop"
            :class="{ over: dragOver }"
            @dragover.prevent="dragOver = true"
            @dragleave.prevent="dragOver = false"
            @drop.prevent="onDrop"
            @click="pickFile"
          >
            <el-icon :size="26"><UploadFilled /></el-icon>
            <div>拖入视频文件，或点击选择</div>
            <div class="suli-muted" style="font-size:12px">≤300MB · mp4 / webm / mov</div>
          </div>
          <div v-else class="src-row">
            <el-icon :size="22"><VideoCamera /></el-icon>
            <div class="src-meta">
              <div class="src-name" :title="src.name">{{ src.name }}</div>
              <div class="suli-muted" style="font-size:12px">
                {{ src.dur ? src.dur.toFixed(1) + 's' : '片长待载入' }}{{ src.bytes ? ' · ' + mb(src.bytes) : '' }}
              </div>
            </div>
            <el-button size="small" text @click="clearSrc">换</el-button>
          </div>
          <div class="url-row">
            <el-input v-model="url" size="small" placeholder="或粘贴视频直链（http/https）…" clearable @keydown.enter="useUrl" />
            <el-button size="small" :disabled="!url.trim()" @click="useUrl">用直链</el-button>
          </div>
          <input ref="fileInput" type="file" accept="video/*" hidden @change="onPick" />
        </div>

        <div class="suli-card sect">
          <div class="sect-title">② 抽帧参数</div>
          <div class="param">
            <span>帧数上限</span>
            <span class="tnum val">{{ maxFrames }}</span>
          </div>
          <el-slider v-model="maxFrames" :min="4" :max="24" :step="1" />
          <div class="param" style="margin-top:10px">
            <span>切镜灵敏度</span>
            <span class="tnum val">{{ scene.toFixed(2) }}</span>
          </div>
          <el-slider v-model="scene" :min="0.1" :max="0.9" :step="0.05" />
          <div class="suli-muted" style="font-size:12px">灵敏度调低抓更多变化，调高只留强切镜；无切点自动转均匀采样。</div>
          <el-button type="primary" style="width:100%;margin-top:10px" :disabled="!src" :loading="framing" @click="doFrames">
            {{ framing ? '抽帧中…（下载 + ffmpeg）' : (segIsPartial ? `抽帧（区间 ${segDur.toFixed(1)}s）` : '开始抽帧（全片）') }}
          </el-button>
        </div>

        <div class="suli-card sect">
          <div class="sect-title">③ 拉片报告</div>
          <el-input v-model="ask" type="textarea" :rows="3" placeholder="分析侧重（可选）…例如：重点反推性行为段的机位选择与切换节奏" />
          <div class="suli-muted" style="font-size:12px;margin:6px 0">会话：{{ sessionLabel }}</div>
          <div class="row">
            <el-button type="primary" :disabled="!frames.length" :loading="analyzing" @click="analyze">
              <el-icon style="margin-right:4px"><MagicStick /></el-icon>{{ report ? '重新分析' : 'Agent 拉片分析' }}
            </el-button>
            <el-button v-if="analyzing" @click="stopAnalyze">停止</el-button>
          </div>
          <div v-if="progress" class="suli-muted" style="font-size:12px;margin-top:6px">{{ progress }}</div>
        </div>
      </div>

      <!-- 右列：播放器/时间轴 + 帧墙 + 报告 -->
      <div class="col-right">
        <div class="suli-card sect">
          <div class="sect-title">
            预览与选区
            <span v-if="src" class="suli-muted" style="font-size:12px;font-weight:400">拖动两侧手柄圈定要拉片的片段；抽帧与报告只针对所选区间</span>
          </div>
          <template v-if="src">
            <video
              ref="videoEl"
              :src="src.url"
              class="video"
              preload="metadata"
              playsinline
              @loadedmetadata="onMeta"
              @timeupdate="onTime"
              @play="playing = true"
              @pause="playing = false"
              @error="videoErr = true"
            />
            <div class="ctrl">
              <el-button size="small" circle title="跳到区间起点" @click="seekVideo(segStart)"><el-icon><DArrowLeft /></el-icon></el-button>
              <el-button size="small" circle :title="playing ? '暂停' : '播放'" @click="togglePlay">
                <el-icon><VideoPause v-if="playing" /><CaretRight v-else /></el-icon>
              </el-button>
              <el-button size="small" circle title="跳到区间终点" @click="seekVideo(effEnd)"><el-icon><DArrowRight /></el-icon></el-button>
              <span class="tnum t">{{ fmtT(curT) }} / {{ fmtT(videoDur || durationS) }}</span>
              <span style="flex:1" />
              <el-checkbox v-model="loopSeg" size="small">循环选区</el-checkbox>
              <el-button size="small" text :disabled="segIsFull" @click="resetSeg">全片</el-button>
            </div>
            <div
              ref="trackEl"
              class="track"
              @pointerdown="onTrackDown"
              @pointermove="onTrackMove"
              @pointerup="onTrackUp"
              @pointercancel="onTrackUp"
            >
              <div class="sel" :style="selStyle" />
              <div class="ph" :style="{ left: pctOf(curT) + '%' }" />
              <div class="hnd hnd-l" :style="{ left: pctOf(segStart) + '%' }" data-h="l" />
              <div class="hnd hnd-r" :style="{ left: pctOf(effEnd) + '%' }" data-h="r" />
            </div>
            <div class="seg-info">
              <span class="suli-muted">区间</span>
              <span class="tnum">{{ fmtT(segStart) }} → {{ fmtT(effEnd) }}</span>
              <span class="suli-muted">（{{ segDur.toFixed(1) }}s{{ segIsFull ? ' · 全片' : '' }}）</span>
            </div>
            <div v-if="videoErr" class="suli-muted" style="font-size:12px;color:var(--suli-warning)">⚠ 浏览器放不了这个视频编码，时间轴不可用；抽帧仍可走全片。</div>
          </template>
          <el-empty v-else description="上传视频后在这里预览并圈选片段" :image-size="72" />
        </div>

        <div class="suli-card sect">
          <div class="sect-title">
            关键帧
            <span v-if="frames.length" class="suli-muted" style="font-size:12px;font-weight:400">
              {{ frames.length }} 帧{{ segInfo ? ` · 区间 ${fmtT(segInfo.start)}–${fmtT(segInfo.end)}` : '' }} · 片长 {{ durationS ? durationS.toFixed(1) + 's' : '—' }}{{ modeText ? ' · ' + modeText : '' }}
            </span>
            <span style="flex:1" />
            <el-button v-if="frames.length" size="small" text @click="copyFrameRefs">复制帧引用</el-button>
          </div>
          <el-empty v-if="!frames.length" description="还没抽帧——先在左侧选视频" :image-size="72" />
          <div v-else class="grid">
            <div v-for="(f, i) in frames" :key="f.name" class="cell" :title="f.name">
              <el-image
                :src="f.url"
                :preview-src-list="previewList"
                :initial-index="i"
                fit="cover"
                class="im"
                hide-on-click-modal
                lazy
              />
              <span class="idx tnum">{{ i + 1 }}</span>
              <span v-if="f.time_s != null" class="tm tnum">{{ f.time_s.toFixed(1) }}s</span>
            </div>
          </div>
        </div>

        <div v-if="report || analyzing" class="suli-card sect">
          <div class="sect-title">
            拉片报告
            <span style="flex:1" />
            <el-button v-if="report" size="small" text @click="copyReport">复制报告</el-button>
          </div>
          <MarkdownView v-if="report" :content="report" />
          <div v-else class="suli-muted">等待 Agent 输出…</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 拉片室：参考视频 → 时间轴圈选片段 → 抽关键帧 → Agent 逐帧反推手法。
 * 抽帧走 /v1/tools/video-frames（支持 start_s/end_s 区间）；分析复用 dsh 会话
 * （有集号 → episode/集号；无集号 → lab/video-lab 独立会话）。
 * 状态持久化 localStorage（刷新/切页不丢帧与报告）。
 */
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, VideoCamera, MagicStick, CaretRight, VideoPause, DArrowLeft, DArrowRight } from '@element-plus/icons-vue'
import { api } from '../api/client'
import { useAppStore } from '../stores/app'
import MarkdownView from '../components/MarkdownView.vue'

const store = useAppStore()

type Src = { name: string; path: string; url: string; dur: number; bytes: number } | null

const src = ref<Src>(null)
const url = ref('')
const maxFrames = ref(12)
const scene = ref(0.35)
const framing = ref(false)
const frames = ref<{ name: string; url: string; time_s?: number }[]>([])
const durationS = ref(0)
const mode = ref('')
const segInfo = ref<{ start: number; end: number } | null>(null)
const ask = ref('')
const analyzing = ref(false)
const progress = ref('')
const report = ref('')
const fileInput = ref<HTMLInputElement | null>(null)
const videoEl = ref<HTMLVideoElement | null>(null)
const trackEl = ref<HTMLElement | null>(null)
const dragOver = ref(false)
const videoErr = ref(false)
const videoDur = ref(0)
const curT = ref(0)
const playing = ref(false)
const segStart = ref(0)
const segEnd = ref(0)   // 0 = 未设置（到片尾）
const loopSeg = ref(false)
let dragH: 'l' | 'r' | 'seek' | '' = ''
let ac: AbortController | null = null

const previewList = computed(() => frames.value.map(f => f.url))
const modeText = computed(() => (mode.value === 'uniform' ? '均匀采样' : mode.value === 'scene' ? '场景切帧' : ''))
const sessionLabel = computed(() => (store.episodeId ? `EP 会话（${store.episodeId}）` : '拉片室独立会话'))
const effEnd = computed(() => {
  const d = videoDur.value || durationS.value
  if (segEnd.value > 0) return d > 0 ? Math.min(segEnd.value, d) : segEnd.value
  return d
})
const segDur = computed(() => Math.max(0, effEnd.value - segStart.value))
const segIsFull = computed(() => segStart.value <= 0.05 && (!segEnd.value || Math.abs(effEnd.value - (videoDur.value || durationS.value)) < 0.15))
const segIsPartial = computed(() => segDur.value > 0 && !segIsFull.value)
const selStyle = computed(() => {
  const l = pctOf(segStart.value)
  const r = pctOf(effEnd.value)
  return { left: l + '%', width: Math.max(0, r - l) + '%' }
})
function mb(n: number) { return n < 1024 * 1024 ? (n / 1024).toFixed(0) + 'KB' : (n / 1024 / 1024).toFixed(1) + 'MB' }
function fmtT(t: number) {
  if (!isFinite(t) || t < 0) t = 0
  const m = Math.floor(t / 60)
  const s = t - m * 60
  return `${String(m).padStart(2, '0')}:${s.toFixed(1).padStart(4, '0')}`
}
function pctOf(t: number) {
  const d = videoDur.value || durationS.value || 1
  return Math.max(0, Math.min(100, (t / d) * 100))
}

/* —— 持久化：刷新/切页不丢 —— */
const LS_KEY = 'suli.videoLab.v1'
function persist() {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify({
      src: src.value, url: url.value, maxFrames: maxFrames.value, scene: scene.value,
      frames: frames.value, durationS: durationS.value, mode: mode.value, segInfo: segInfo.value,
      segStart: segStart.value, segEnd: segEnd.value, loopSeg: loopSeg.value,
      ask: ask.value, report: report.value, ts: Date.now(),
    }))
  } catch {}
}
let pt: ReturnType<typeof setTimeout> | null = null
function persistSoon() { if (pt) clearTimeout(pt); pt = setTimeout(persist, 300) }
function restore() {
  try {
    const d = JSON.parse(localStorage.getItem(LS_KEY) || '{}')
    if (!d || typeof d !== 'object') return
    if (d.src && typeof d.src === 'object') src.value = d.src
    if (typeof d.url === 'string') url.value = d.url
    if (typeof d.maxFrames === 'number') maxFrames.value = Math.min(24, Math.max(4, d.maxFrames))
    if (typeof d.scene === 'number') scene.value = Math.min(0.9, Math.max(0.1, d.scene))
    if (Array.isArray(d.frames)) frames.value = d.frames.filter((f: any) => f && f.name && f.url)
    if (typeof d.durationS === 'number') durationS.value = d.durationS
    if (typeof d.mode === 'string') mode.value = d.mode
    if (d.segInfo && typeof d.segInfo === 'object') segInfo.value = d.segInfo
    if (typeof d.segStart === 'number') segStart.value = Math.max(0, d.segStart)
    if (typeof d.segEnd === 'number') segEnd.value = Math.max(0, d.segEnd)
    if (typeof d.loopSeg === 'boolean') loopSeg.value = d.loopSeg
    if (typeof d.ask === 'string') ask.value = d.ask
    if (typeof d.report === 'string') report.value = d.report
  } catch {}
}
watch([src, url, maxFrames, scene, frames, durationS, mode, segInfo, segStart, segEnd, loopSeg, ask, report], persistSoon, { deep: true })

/* —— 视频源 —— */
function pickFile() { fileInput.value?.click() }
async function onDrop(e: DragEvent) {
  dragOver.value = false
  const f = e.dataTransfer?.files?.[0]
  if (f) await acceptFile(f)
}
async function onPick(e: Event) {
  const input = e.target as HTMLInputElement
  const f = input.files?.[0]
  input.value = ''
  if (f) await acceptFile(f)
}
function resetSeg() { segStart.value = 0; segEnd.value = 0; curT.value = 0 }
async function acceptFile(f: File) {
  if (!f.type.startsWith('video/')) return ElMessage.warning('只接受视频文件')
  if (f.size > 300 * 1024 * 1024) return ElMessage.warning('视频超过 300MB 上限')
  try {
    const d: any = await api.uploadFile(f)
    const row = d?.data || d
    src.value = { name: f.name, path: row.path, url: row.url, dur: await probeVideoDur(f), bytes: f.size }
    frames.value = []; durationS.value = 0; mode.value = ''; segInfo.value = null
    url.value = ''; videoErr.value = false; videoDur.value = 0; resetSeg()
  } catch { ElMessage.error('上传失败，后端未起？') }
}
function useUrl() {
  const u = url.value.trim()
  if (!u.startsWith('http://') && !u.startsWith('https://')) return ElMessage.warning('直链须 http(s) 开头')
  src.value = { name: decodeURIComponent(u.split('/').pop() || '直链视频').slice(0, 80), path: '', url: u, dur: 0, bytes: 0 }
  frames.value = []; durationS.value = 0; mode.value = ''; segInfo.value = null
  videoErr.value = false; videoDur.value = 0; resetSeg()
}
function clearSrc() {
  src.value = null; frames.value = []; durationS.value = 0; mode.value = ''; report.value = ''
  segInfo.value = null; videoErr.value = false; videoDur.value = 0; resetSeg()
}
function probeVideoDur(f: File): Promise<number> {
  return new Promise(resolve => {
    try {
      const u = URL.createObjectURL(f)
      const v = document.createElement('video')
      v.preload = 'metadata'
      v.onloadedmetadata = () => { const d = v.duration || 0; URL.revokeObjectURL(u); resolve(d) }
      v.onerror = () => { URL.revokeObjectURL(u); resolve(0) }
      v.src = u
      setTimeout(() => resolve(0), 8000)
    } catch { resolve(0) }
  })
}

/* —— 播放器与时间轴 —— */
function onMeta() {
  const v = videoEl.value
  if (!v) return
  const d = v.duration
  if (isFinite(d) && d > 0) videoDur.value = d
}
function onTime() {
  const v = videoEl.value
  if (!v) return
  curT.value = v.currentTime || 0
  const end = effEnd.value
  if (loopSeg.value && !v.paused && end > 0 && curT.value >= end - 0.06) v.currentTime = segStart.value
}
function seekVideo(t: number) {
  const v = videoEl.value
  if (!v) return
  const d = videoDur.value || durationS.value
  const tt = d > 0 ? Math.max(0, Math.min(t, d)) : Math.max(0, t)
  try { v.currentTime = tt } catch {}
  curT.value = tt
}
function togglePlay() {
  const v = videoEl.value
  if (!v) return
  if (v.paused) {
    const end = effEnd.value
    if (end > 0 && (v.currentTime < segStart.value || v.currentTime >= end - 0.05)) v.currentTime = segStart.value
    v.play().catch(() => {})
  } else {
    v.pause()
  }
}
function tOfX(clientX: number) {
  const el = trackEl.value
  if (!el) return 0
  const r = el.getBoundingClientRect()
  const d = videoDur.value || durationS.value || 0
  if (!r.width || d <= 0) return 0
  return Math.max(0, Math.min(d, ((clientX - r.left) / r.width) * d))
}
function onTrackDown(e: PointerEvent) {
  const target = e.target as HTMLElement
  const h = target.dataset?.h
  dragH = h === 'l' || h === 'r' ? h : 'seek'
  try { (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId) } catch {}
  handleDrag(e)
}
function onTrackMove(e: PointerEvent) { if (dragH) handleDrag(e) }
function onTrackUp(e: PointerEvent) {
  dragH = ''
  try { (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId) } catch {}
}
function handleDrag(e: PointerEvent) {
  const d = videoDur.value || durationS.value
  if (d <= 0) return
  const t = tOfX(e.clientX)
  if (dragH === 'l') {
    const maxT = Math.max(0, effEnd.value - 0.2)
    segStart.value = Math.max(0, Math.min(t, maxT))
    seekVideo(segStart.value)
  } else if (dragH === 'r') {
    const minT = segStart.value + 0.2
    segEnd.value = Math.max(minT, Math.min(t, d))
    seekVideo(segEnd.value)
  } else if (dragH === 'seek') {
    seekVideo(t)
  }
}

/* —— 抽帧 —— */
async function doFrames() {
  if (!src.value || framing.value) return
  framing.value = true
  try {
    const p: any = src.value.path
      ? { path: src.value.path, max_frames: maxFrames.value, scene: scene.value }
      : { url: src.value.url, max_frames: maxFrames.value, scene: scene.value }
    if (videoDur.value > 0) {
      p.start_s = Math.round(segStart.value * 10) / 10
      p.end_s = Math.round(effEnd.value * 10) / 10
    }
    const r: any = await api.videoFrames(p)
    const d = r?.data ?? r
    frames.value = (d?.frames || []).map((x: any) => ({
      name: x.name,
      url: x.url,
      time_s: typeof x.time_s === 'number' ? x.time_s : undefined,
    }))
    durationS.value = Number(d?.duration_s) || 0
    mode.value = d?.mode || ''
    if (typeof d?.start_s === 'number' && typeof d?.end_s === 'number') segInfo.value = { start: d.start_s, end: d.end_s }
    if (!frames.value.length) { ElMessage.warning('没抽出关键帧，试试调低灵敏度'); return }
    if (src.value && !src.value.dur && durationS.value) src.value = { ...src.value, dur: durationS.value }
    ElMessage.success(`已抽 ${frames.value.length} 帧（${modeText.value || '场景切帧'}）`)
  } catch (e: any) {
    ElMessage.error((e?.response?.data?.msg || e?.message || '抽帧失败').slice(0, 140))
  } finally { framing.value = false }
}

/* —— 拉片分析（复用 dsh 会话：有集用集，无集走 lab 独立会话） —— */
function buildBrief(): string {
  const lines: string[] = []
  if (store.episodeId) lines.push(`集号：${store.episodeId}`)
  lines.push(`【拉片请求】参考片：${src.value?.name || '本地上传视频'}（片长 ${durationS.value ? durationS.value.toFixed(1) + 's' : '未知'}，${frames.value.length} 帧）。`)
  if (segInfo.value && segInfo.value.end > segInfo.value.start + 0.05) {
    lines.push(`素材区间：${fmtT(segInfo.value.start)} → ${fmtT(segInfo.value.end)}（${(segInfo.value.end - segInfo.value.start).toFixed(1)}s）`)
  }
  lines.push('以下是对标参考视频按时间顺序抽出的关键帧，请看图逐帧分析，产出一份拉片报告（只出报告：不出分镜、不落盘、不改任何库）：')
  lines.push('1) 每帧：景别 / 主体 / 动作一句话（引用时带上该帧的时间标注）')
  lines.push('2) 运镜与节奏：几秒一切、爆点落在哪、镜头怎么动')
  lines.push('3) 开场 3 秒钩子是什么')
  lines.push('4) 手法清单：可直接借鉴进我们后续分镜的点（运镜 / 节奏 / 构图 / 可见层写法），只借手法不抄画面；每条标出出现的大致秒数（如「2.4s 推镜」）')
  const extra = ask.value.trim()
  if (extra) lines.push(`补充侧重：${extra}`)
  lines.push('帧引用（按时间顺序，括号内为该帧在片中的时间）：')
  lines.push(frames.value.map(frameRefLine).join('\n'))
  return lines.join('\n')
}
async function analyze() {
  if (!frames.value.length || analyzing.value) return
  const scope = store.episodeId ? 'episode' : 'lab'
  const key = store.episodeId || 'video-lab'
  analyzing.value = true
  progress.value = '建会话…'
  report.value = ''
  try {
    await api.dshEnsure(scope, key)
  } catch { ElMessage.error('Agent 会话建失败，后端未起？'); analyzing.value = false; progress.value = ''; return }
  progress.value = 'Agent 拉片分析中…'
  const c = new AbortController()
  ac = c
  let done: any = null
  let errMsg = ''
  try {
    await api.dshRunStream({ scope, key, message: buildBrief() }, (ev: string, d: any) => {
      if (ev === 'dsh') progress.value = `Agent 拉片分析中… 事件 ${d?.n ?? ''}`
      else if (ev === 'retry') progress.value = '检测到拒答，自动重试中…'
      else if (ev === 'done') done = d
      else if (ev === 'error') errMsg = d?.msg || '调用失败'
    }, c.signal)
    if (done) {
      report.value = done.answer || '(空回包)'
      progress.value = ''
      persist()
      ElMessage.success('拉片报告已生成')
    } else {
      report.value = '[失败] ' + (errMsg || '流中断')
      progress.value = ''
    }
  } catch (e: any) {
    if (c.signal.aborted) {
      progress.value = ''
      ElMessage.info('已停止')
    } else {
      report.value = '[失败] ' + String(e?.message || e).slice(0, 200)
      progress.value = ''
    }
  } finally {
    analyzing.value = false
    ac = null
  }
}
function stopAnalyze() { ac?.abort() }

/* —— 杂项 —— */
function copyText(t: string) {
  navigator.clipboard?.writeText(t).then(() => ElMessage.success('已复制')).catch(() => ElMessage.warning('复制失败'))
}
function frameRefLine(f: { name: string; time_s?: number }) {
  return `@data/uploads/${f.name}${f.time_s != null ? ` （约 ${f.time_s.toFixed(1)}s）` : ''}`
}
function copyReport() { copyText(report.value) }
function copyFrameRefs() { copyText(frames.value.map(frameRefLine).join('\n')) }

onMounted(restore)
</script>

<style scoped>
.lab { display: flex; flex-direction: column; gap: 12px; }
.head { padding: 12px 14px; }
.head-row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.cols { display: flex; gap: 12px; align-items: flex-start; }
.col-left { width: 360px; flex-shrink: 0; display: flex; flex-direction: column; gap: 12px; }
.col-right { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 12px; }
.sect { padding: 12px 14px; }
.sect-title { font-weight: 700; font-size: 13px; display: flex; gap: 8px; align-items: baseline; margin-bottom: 8px; flex-wrap: wrap; }
.drop { border: 1.5px dashed var(--suli-border-hover); border-radius: 12px; padding: 22px 10px; display: flex; flex-direction: column; align-items: center; gap: 6px; color: var(--suli-text-2); cursor: pointer; transition: border-color .15s, background .15s; }
.drop:hover, .drop.over { border-color: var(--suli-primary); background: var(--el-color-primary-light-9); }
.src-row { display: flex; gap: 8px; align-items: center; border: 1.5px solid var(--suli-border); border-radius: 12px; padding: 8px 10px; }
.src-meta { flex: 1; min-width: 0; }
.src-name { font-weight: 600; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.url-row { display: flex; gap: 8px; margin-top: 8px; }
.param { display: flex; justify-content: space-between; font-size: 13px; align-items: baseline; }
.param .val { color: var(--suli-primary); font-weight: 700; }
.row { display: flex; gap: 8px; align-items: center; margin-top: 8px; }
.video { width: 100%; max-height: 340px; background: #000; border-radius: 10px; display: block; }
.ctrl { display: flex; gap: 8px; align-items: center; margin-top: 8px; flex-wrap: wrap; }
.ctrl .t { font-size: 12px; }
.track { position: relative; height: 26px; margin-top: 10px; background: var(--suli-bg-2); border: 1px solid var(--suli-border); border-radius: 8px; cursor: pointer; touch-action: none; user-select: none; }
.sel { position: absolute; top: 0; bottom: 0; background: var(--el-color-primary-light-7); border-radius: 8px; pointer-events: none; }
.ph { position: absolute; top: 2px; bottom: 2px; width: 2px; background: var(--suli-text); border-radius: 2px; pointer-events: none; opacity: .75; }
.hnd { position: absolute; top: -3px; bottom: -3px; width: 14px; margin-left: -7px; background: var(--suli-primary); border-radius: 7px; cursor: ew-resize; box-shadow: 0 1px 4px rgba(0, 0, 0, .25); }
.hnd::after { content: ''; position: absolute; left: 6px; top: 7px; bottom: 7px; width: 2px; background: rgba(255, 255, 255, .85); border-radius: 2px; }
.seg-info { display: flex; gap: 8px; align-items: baseline; font-size: 12.5px; margin-top: 8px; flex-wrap: wrap; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 8px; }
.cell { position: relative; border-radius: 10px; overflow: hidden; border: 1px solid var(--suli-border); aspect-ratio: 16/9; background: var(--suli-bg-2); }
.im { width: 100%; height: 100%; display: block; cursor: zoom-in; }
.idx { position: absolute; left: 6px; top: 6px; background: rgba(0, 0, 0, .55); color: #fff; font-size: 11px; padding: 1px 6px; border-radius: 6px; }
.tm { position: absolute; left: 6px; bottom: 6px; background: rgba(0, 0, 0, .55); color: #fff; font-size: 11px; padding: 1px 6px; border-radius: 6px; }
@media (max-width: 900px) {
  .cols { flex-direction: column; }
  .col-left { width: 100%; }
}
</style>
