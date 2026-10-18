<template>
  <div class="lab">
    <div class="suli-card head">
      <div class="head-row">
        <h3 style="margin:0">拉片室</h3>
        <span style="flex:1" />
      </div>
      <div style="margin-top:10px">
        <el-radio-group v-model="tab" size="small">
          <el-radio-button value="work">工作台</el-radio-button>
          <el-radio-button value="lib">素材源</el-radio-button>
          <el-radio-button value="reports">报告</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <div v-show="tab === 'work'" class="cols">
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
            <div>选择视频</div>
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
            <el-input v-model="url" size="small" placeholder="视频直链" clearable @keydown.enter="useUrl" />
            <el-button size="small" :disabled="!url.trim()" @click="useUrl">用直链</el-button>
          </div>
          <div class="url-row" style="margin-top:6px">
            <el-input v-model="hurl" size="small" placeholder="hanime1.me 链接 / id" clearable @keydown.enter="fetchHanime" />
            <el-button size="small" type="primary" :disabled="!hurl.trim()" :loading="hfetching" @click="fetchHanime">{{ hfetching ? '下载中…' : 'H站下载' }}</el-button>
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
          <el-button type="primary" style="width:100%;margin-top:10px" :disabled="!src" :loading="framing" @click="doFrames">
            {{ framing ? '抽帧中…' : (segIsPartial ? `抽帧（区间 ${segDur.toFixed(1)}s）` : '开始抽帧（全片）') }}
          </el-button>
        </div>

        <div class="suli-card sect">
          <div class="sect-title">③ 拉片报告</div>
          <el-input v-model="ask" type="textarea" :rows="3" placeholder="分析侧重" />
          <div class="row" style="margin-top:8px">
            <el-checkbox v-model="deep" size="small">深度拆解</el-checkbox>
            <el-select v-if="deep" v-model="deepModel" size="small" style="width:175px">
              <el-option label="LongCat 2.5 Free" value="longcat-2.5-preview-free" />
              <el-option label="DeepSeek V4.1 Flash" value="deepseek-v4.1-flash" />
            </el-select>
          </div>
          <div class="suli-muted" style="font-size:12px;margin:6px 0">会话：{{ sessionLabel }}</div>
          <div class="row">
            <el-button type="primary" :disabled="deep ? !src : !frames.length" :loading="analyzing" @click="analyze(deep)">
              <el-icon style="margin-right:4px"><MagicStick /></el-icon>{{ analyzing ? (deep ? '深度拆解中…' : '分析中…') : (report ? '重新分析' : (deep ? '深度拆解' : 'Agent 拉片分析')) }}
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
            <div v-if="videoErr" class="suli-muted" style="font-size:12px;color:var(--suli-warning)">⚠ 浏览器放不了这个视频编码</div>
          </template>
          <el-empty v-else description="暂无预览" :image-size="72" />
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
          <el-empty v-if="!frames.length" description="暂无帧" :image-size="72" />
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
            {{ deep ? '详细设计报告' : '拉片报告' }}
            <span style="flex:1" />
            <el-button v-if="report" size="small" text @click="copyReport">复制报告</el-button>
          </div>
          <MarkdownView v-if="report" :content="report" />
          <div v-else class="suli-muted">等待 Agent 输出…</div>
        </div>
      </div>
    </div>

    <div v-show="tab === 'lib'" class="suli-card sect">
      <div class="sect-title">
        素材源
        <span class="suli-muted" style="font-size:12px;font-weight:400">已拉好的素材都在这里（uploads 库）；支持全选批量删除与手动上传；载入即本地文件模式（抽帧零拷贝）</span>
      </div>
      <div class="lib-bar">
        <el-checkbox :model-value="allSel" :indeterminate="someSel" size="small" @change="toggleAll">全选</el-checkbox>
        <span v-if="sel.length" class="suli-muted" style="font-size:12px">已选 {{ sel.length }} 个</span>
        <span style="flex:1" />
        <el-button size="small" type="primary" plain :loading="uploading" @click="pickUpload">上传视频</el-button>
        <el-button size="small" type="danger" plain :disabled="!sel.length" :loading="deleting" @click="delSelected">删除所选{{ sel.length ? `（${sel.length}）` : '' }}</el-button>
        <el-button size="small" :loading="mediaLoading" @click="loadMedia">刷新</el-button>
        <input ref="libFileInput" type="file" accept="video/*" multiple hidden @change="onLibPick" />
      </div>
      <div v-if="!media.length && !mediaLoading" class="suli-muted" style="padding:20px 0;text-align:center;font-size:12.5px">
        还没有素材——点「上传视频」，或去「工作台」贴个 H 站链接，拉好的都会出现在这里
      </div>
      <div v-else class="media-grid">
        <div v-for="m in media" :key="m.name" class="media-card" :class="{ picked: sel.includes(m.name) }">
          <div class="media-thumb">
            <video :src="m.url" muted playsinline preload="metadata" @loadedmetadata="onMediaMeta(m, $event)" />
            <el-checkbox class="media-check" :model-value="sel.includes(m.name)" @change="toggleSel(m.name)" />
          </div>
          <div class="media-name" :title="m.name">{{ m.name }}</div>
          <div class="media-meta suli-muted">
            <el-tag size="small" effect="plain" :type="m.name.startsWith('hanime1-') ? 'danger' : 'info'">{{ m.name.startsWith('hanime1-') ? 'H站' : '上传' }}</el-tag>
            <span>{{ mb(m.bytes) }}</span>
            <span>{{ m.dur ? m.dur.toFixed(1) + 's' : '…' }}</span>
            <span>{{ fmtTime(m.mtime) }}</span>
          </div>
          <div class="row">
            <el-button size="small" type="primary" @click="loadMaterial(m)">载入拉片</el-button>
            <el-button size="small" text type="danger" @click="delMaterial(m)">删除</el-button>
          </div>
        </div>
      </div>
    </div>

    <div v-show="tab === 'reports'" class="suli-card sect">
      <div class="sect-title">
        报告历史
        <span class="suli-muted" style="font-size:12px;font-weight:400">拉片 / 深度拆解报告自动入库——跑完即存，刷新、关页都不丢</span>
        <span style="flex:1" />
        <el-button size="small" :loading="repLoading" @click="loadReports">刷新</el-button>
      </div>
      <div v-if="!reports.length && !repLoading" class="suli-muted" style="padding:18px 0;text-align:center;font-size:12.5px">
        还没有报告——跑一次「Agent 拉片分析」或「深度拆解（复刻级）」，出稿后会自动出现在这里
      </div>
      <div v-else class="rep-list">
        <div v-for="r in reports" :key="r.id" class="rep-row" :class="{ picked: repCur === r.id }">
          <div class="rep-main" @click="openReport(r)">
            <div class="rep-title">
              <el-tag size="small" :type="r.kind === 'deep' ? 'warning' : 'info'" effect="plain">{{ r.kind === 'deep' ? '深度拆解' : '拉片' }}</el-tag>
              <span class="rep-name" :title="r.title">{{ r.title }}</span>
            </div>
            <div class="suli-muted" style="font-size:12px">
              {{ r.source || '—' }} · {{ r.model || '默认模型' }} · {{ r.chars }} 字<span v-if="r.image_count"> · 配图 {{ r.image_count }}</span> · {{ fmtTime(r.created_at / 1000) }}
            </div>
          </div>
          <div class="row">
            <el-button size="small" text @click.stop="copyReportById(r)">复制</el-button>
            <el-button size="small" text type="danger" @click.stop="delReport(r)">删除</el-button>
          </div>
        </div>
      </div>
      <div v-if="repMd" class="rep-view">
        <div class="sect-title" style="margin-top:10px">
          {{ repTitle || '报告' }}
          <span v-if="repImages.length" class="suli-muted" style="font-size:12px;font-weight:400">配图 {{ repImages.length }} 帧</span>
          <span style="flex:1" />
          <el-button size="small" text @click="repMd = ''; repImages = []">收起</el-button>
        </div>
        <div v-if="repImages.length" class="rep-thumbs">
          <el-image
            v-for="(n, i) in repImages"
            :key="n + '-' + i"
            :src="`/api/images/${n}`"
            :preview-src-list="repPreview"
            :initial-index="i"
            fit="cover"
            class="rep-thumb"
            lazy
            hide-on-click-modal
          />
        </div>
        <MarkdownView :content="repMd" />
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, VideoCamera, MagicStick, CaretRight, VideoPause, DArrowLeft, DArrowRight } from '@element-plus/icons-vue'
import { api } from '../api/client'
import { useAppStore } from '../stores/app'
import MarkdownView from '../components/MarkdownView.vue'

const store = useAppStore()

type Src = { name: string; path: string; url: string; dur: number; bytes: number } | null

const src = ref<Src>(null)
const url = ref('')
const hurl = ref('')
const maxFrames = ref(12)
const scene = ref(0.35)
const framing = ref(false)
const hfetching = ref(false)
const tab = ref<'work' | 'lib' | 'reports'>('work')
const frames = ref<{ name: string; url: string; time_s?: number }[]>([])
const durationS = ref(0)
const mode = ref('')
const segInfo = ref<{ start: number; end: number } | null>(null)
const ask = ref('')
const deep = ref(false)
const deepModel = ref('longcat-2.5-preview-free')
const reports = ref<{ id: string; title: string; kind: string; source: string; model: string; created_at: number; chars: number; image_count?: number }[]>([])
const repLoading = ref(false)
const repCur = ref('')
const repTitle = ref('')
const repMd = ref('')
const repImages = ref<string[]>([])
const repPreview = computed(() => repImages.value.map(n => `/api/images/${n}`))
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
      tab: tab.value, src: src.value, url: url.value, maxFrames: maxFrames.value, scene: scene.value,
      frames: frames.value, durationS: durationS.value, mode: mode.value, segInfo: segInfo.value,
      segStart: segStart.value, segEnd: segEnd.value, loopSeg: loopSeg.value,
      ask: ask.value, report: report.value, deep: deep.value, deepModel: deepModel.value, ts: Date.now(),
    }))
  } catch {}
}
let pt: ReturnType<typeof setTimeout> | null = null
function persistSoon() { if (pt) clearTimeout(pt); pt = setTimeout(persist, 300) }
function restore() {
  try {
    const d = JSON.parse(localStorage.getItem(LS_KEY) || '{}')
    if (!d || typeof d !== 'object') return
    if (d.tab === 'lib' || d.tab === 'work' || d.tab === 'reports') tab.value = d.tab
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
    if (typeof d.deep === 'boolean') deep.value = d.deep
    if (typeof d.deepModel === 'string' && d.deepModel) deepModel.value = d.deepModel
  } catch {}
}
watch([tab, src, url, maxFrames, scene, frames, durationS, mode, segInfo, segStart, segEnd, loopSeg, ask, report, deep, deepModel], persistSoon, { deep: true })

/* —— 素材源（拉片室已拉素材库：uploads 视频列表）—— */
type MediaItem = { name: string; url: string; bytes: number; mtime: number; dur?: number }
const media = ref<MediaItem[]>([])
const mediaLoading = ref(false)
const sel = ref<string[]>([])
const libFileInput = ref<HTMLInputElement | null>(null)
const uploading = ref(false)
const deleting = ref(false)
const allSel = computed(() => media.value.length > 0 && sel.value.length === media.value.length)
const someSel = computed(() => sel.value.length > 0 && sel.value.length < media.value.length)
function fmtTime(ts: number) {
  const d = new Date(ts * 1000)
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getMonth() + 1}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}
async function loadMedia() {
  mediaLoading.value = true
  try {
    const d: any = await api.mediaList()
    media.value = ((d?.data || d || []) as any[]).map(x => ({ ...x, dur: 0 }))
    sel.value = sel.value.filter(n => media.value.some(m => m.name === n))
  } catch { ElMessage.error('素材列表加载失败') } finally { mediaLoading.value = false }
}
function onMediaMeta(m: MediaItem, e: Event) {
  const v = e.target as HTMLVideoElement
  const dd = v?.duration
  if (isFinite(dd) && dd > 0) m.dur = dd
}
function loadMaterial(m: MediaItem) {
  src.value = { name: m.name, path: m.name, url: m.url, dur: m.dur || 0, bytes: m.bytes }
  frames.value = []; durationS.value = 0; mode.value = ''; segInfo.value = null
  url.value = ''; videoErr.value = false; videoDur.value = 0; resetSeg()
  tab.value = 'work'
  ElMessage.success(`已载入：${m.name}`)
}
async function delMaterial(m: MediaItem) {
  try {
    await ElMessageBox.confirm(`删除素材「${m.name}」？文件会从 uploads 真删。`, '确认删除', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch { return }
  try {
    await api.mediaDelete(m.name)
    media.value = media.value.filter(x => x.name !== m.name)
    sel.value = sel.value.filter(n => n !== m.name)
    if (src.value?.path === m.name) clearSrc()
    ElMessage.success('已删除')
  } catch { ElMessage.error('删除失败') }
}
function toggleSel(name: string) {
  const i = sel.value.indexOf(name)
  if (i >= 0) sel.value.splice(i, 1)
  else sel.value.push(name)
}
function toggleAll(v: any) { sel.value = v ? media.value.map(m => m.name) : [] }
function pickUpload() { libFileInput.value?.click() }
async function onLibPick(e: Event) {
  const input = e.target as HTMLInputElement
  const files = Array.from(input.files || [])
  input.value = ''
  if (!files.length) return
  uploading.value = true
  try {
    let okN = 0
    for (const f of files) {
      if (!f.type.startsWith('video/')) { ElMessage.warning(`跳过非视频：${f.name}`); continue }
      if (f.size > 300 * 1024 * 1024) { ElMessage.warning(`超过 300MB 上限：${f.name}`); continue }
      await api.uploadFile(f)
      okN++
    }
    if (okN) { ElMessage.success(`已上传 ${okN} 个视频`); await loadMedia() }
  } catch { ElMessage.error('上传失败，后端未起？') } finally { uploading.value = false }
}
async function delSelected() {
  const names = [...sel.value]
  if (!names.length || deleting.value) return
  try {
    await ElMessageBox.confirm(`删除选中的 ${names.length} 个素材？文件会从 uploads 真删。`, '确认删除', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch { return }
  deleting.value = true
  try {
    const d: any = await api.mediaBatchDelete(names)
    const row = d?.data || d || {}
    const deleted: string[] = row.deleted || []
    media.value = media.value.filter(x => !deleted.includes(x.name))
    sel.value = sel.value.filter(n => !deleted.includes(n))
    if (src.value?.path && deleted.includes(src.value.path)) clearSrc()
    ElMessage.success(`已删除 ${deleted.length} 个素材`)
    if ((row.missing?.length || 0) + Object.keys(row.errors || {}).length > 0) ElMessage.warning('部分文件未能删除')
  } catch { ElMessage.error('批量删除失败') } finally { deleting.value = false }
}
watch(tab, (v) => {
  if (v === 'lib') { videoEl.value?.pause(); loadMedia() }
})

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
async function fetchHanime() {
  const q = hurl.value.trim()
  if (!q || hfetching.value) return
  hfetching.value = true
  try {
    const d: any = await api.hanime1Fetch(q)
    const row = d?.data || d
    if (!row?.path) throw new Error(row?.msg || '下载失败')
    src.value = { name: row.name || 'hanime1 视频', path: row.path, url: row.url, dur: row.duration_s || 0, bytes: row.bytes || 0 }
    frames.value = []; durationS.value = 0; mode.value = ''; segInfo.value = null
    url.value = ''; videoErr.value = false; videoDur.value = 0; resetSeg()
    hurl.value = ''
    ElMessage.success(`${row.cached ? '本地已有，直接复用' : '已下载入库'}：${row.name}${row.bytes ? '（' + mb(row.bytes) + '）' : ''}`)
  } catch (e: any) {
    ElMessage.error('H站下载失败：' + (e?.response?.data?.msg || e?.message || '未知错误'))
  } finally {
    hfetching.value = false
  }
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
  lines.push('（本轮完整重做：即使帧与上一轮相同，也重新出报告，不要复用上一轮结论。）')
  const extra = ask.value.trim()
  if (extra) lines.push(`补充侧重：${extra}`)
  lines.push('帧引用（按时间顺序，括号内为该帧在片中的时间）：')
  lines.push(frames.value.map(frameRefLine).join('\n'))
  return lines.join('\n')
}
function buildDeepBrief(): string {
  const lines: string[] = []
  if (store.episodeId) lines.push(`集号：${store.episodeId}`)
  const s = src.value
  const how = s?.path ? `本地素材（uploads）：${s.path}` : `视频直链：${s?.url || ''}`
  const dur = durationS.value || videoDur.value || 0
  lines.push(`【深度拉片请求】参考片：${s?.name || '本地上传视频'}（片长 ${dur ? dur.toFixed(1) + 's' : '未知'}；${how}）。`)
  if (segIsPartial.value) {
    lines.push(`素材区间：${fmtT(segStart.value)} → ${fmtT(effEnd.value)}（${segDur.value.toFixed(1)}s），只拆这个区间。`)
  }
  lines.push('目标：复刻级拆解 → 详细设计报告（复刻规格版）。执行《深度拉片工作流》：')
  lines.push('先重读 ../skills/video/deep-teardown/SKILL.md（每轮都重读，以文件最新版为准，不要凭记忆跑旧流程）。')
  lines.push('按 S0 切点扫描 → S1 逐镜帧墙 → 逐镜镜头卡 → S2 关键镜精拆 → S3 节奏结构 → S4 详细设计报告 逐步跑完。')
  lines.push('本轮为完整重跑：切点/帧墙现场重新生成，逐镜交给本轮工具结果（即使与上一轮同源，也不要复用上一轮结论与数据）。')
  lines.push('每镜必须配 1 张帧图：用本轮 shots-frames 返回的 frames[] 里该镜的中间帧，在镜块里写 ![镜 N · 时间码](/api/images/<name>)（name 逐字复制，别手敲）。')
  lines.push('交稿前自检：报告里 /api/images/ 的引用数 ≥ 镜数，不够就补齐再交。')
  lines.push('只出报告：不落盘、不出分镜、不改任何库；报告全文直接输出（这就是交付物）。')
  const extra = ask.value.trim()
  if (extra) lines.push(`补充侧重：${extra}`)
  return lines.join('\n')
}
async function analyze(deepMode = false) {
  if (analyzing.value) return
  if (deepMode ? !src.value : !frames.value.length) return
  const scope = store.episodeId ? 'episode' : 'lab'
  const key = store.episodeId || 'video-lab'
  analyzing.value = true
  progress.value = '建会话…'
  report.value = ''
  try {
    await api.dshEnsure(scope, key)
  } catch { ElMessage.error('Agent 会话建失败，后端未起？'); analyzing.value = false; progress.value = ''; return }
  progress.value = deepMode ? '深度拆解中…（切点 → 逐镜帧墙 → 镜头卡 → 设计报告）' : 'Agent 拉片分析中…'
  const c = new AbortController()
  ac = c
  let done: any = null
  let errMsg = ''
  try {
    const payload: { scope: string; key: string; message: string; model?: string } = {
      scope, key, message: deepMode ? buildDeepBrief() : buildBrief(),
    }
    if (deepMode && deepModel.value) payload.model = deepModel.value
    await api.dshRunStream(payload, (ev: string, d: any) => {
      if (ev === 'dsh') progress.value = `${deepMode ? '深度拆解中' : 'Agent 拉片分析中'}… 事件 ${d?.n ?? ''}`
      else if (ev === 'retry') progress.value = d?.msg || '自动重试中…'
      else if (ev === 'done') done = d
      else if (ev === 'error') errMsg = d?.msg || '调用失败'
    }, c.signal)
    if (done) {
      report.value = done.answer || '(空回包)'
      progress.value = ''
      persist()
      ElMessage.success(deepMode ? '详细设计报告已生成（已存报告历史）' : '拉片报告已生成（已存报告历史）')
      if (tab.value === 'reports') loadReports()
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

/* —— 报告历史（后端报告库：拉片/深度拆解跑完自动入库） —— */
async function loadReports() {
  repLoading.value = true
  try {
    const r: any = await api.reportList()
    reports.value = (r?.data ?? r)?.items || []
  } catch {
    ElMessage.error('报告列表拉取失败（后端未起？）')
  } finally { repLoading.value = false }
}
async function openReport(r: { id: string; title: string }) {
  try {
    const d: any = await api.reportGet(r.id)
    const dd = d?.data ?? d
    repCur.value = r.id
    repTitle.value = dd?.title || r.title
    repMd.value = dd?.report_md || ''
    repImages.value = Array.isArray(dd?.images) ? dd.images : []
  } catch { ElMessage.error('报告读取失败') }
}
async function copyReportById(r: { id: string }) {
  try {
    const d: any = await api.reportGet(r.id)
    const dd = d?.data ?? d
    copyText(dd?.report_md || '')
  } catch { ElMessage.error('报告读取失败') }
}
async function delReport(r: { id: string; title: string }) {
  try {
    await ElMessageBox.confirm(`删除报告「${r.title}」？`, '删除报告', { type: 'warning' })
  } catch { return }
  try {
    await api.reportDelete(r.id)
    if (repCur.value === r.id) { repCur.value = ''; repMd.value = '' }
    await loadReports()
    ElMessage.success('已删除')
  } catch { ElMessage.error('删除失败') }
}
watch(tab, v => { if (v === 'reports') loadReports() }, { immediate: true })

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
.lib-bar { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin: 2px 0 10px; }
.media-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 10px; }
.media-thumb { position: relative; }
.media-check { position: absolute; left: 6px; top: 6px; background: rgba(0, 0, 0, .45); border-radius: 6px; padding: 1px 5px; }
.media-card.picked { border-color: var(--suli-primary); box-shadow: 0 0 0 1px var(--suli-primary); }
.media-card { border: 1px solid var(--suli-border); border-radius: 12px; padding: 8px; display: flex; flex-direction: column; gap: 6px; background: var(--suli-bg-2); }
.media-card video { width: 100%; aspect-ratio: 16/9; object-fit: contain; background: #0b0b0d; border-radius: 8px; display: block; }
.media-name { font-size: 12.5px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.media-meta { font-size: 11.5px; display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.media-card .row { margin-top: 0; }
.rep-list { display: flex; flex-direction: column; gap: 8px; }
.rep-row { display: flex; gap: 8px; align-items: center; border: 1px solid var(--suli-border); border-radius: 12px; padding: 8px 10px; background: var(--suli-bg-2); }
.rep-row.picked { border-color: var(--suli-primary); box-shadow: 0 0 0 1px var(--suli-primary); }
.rep-main { flex: 1; min-width: 0; cursor: pointer; display: flex; flex-direction: column; gap: 3px; }
.rep-title { display: flex; gap: 8px; align-items: center; min-width: 0; }
.rep-name { font-weight: 600; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rep-view { margin-top: 6px; }
.rep-thumbs { display: grid; grid-template-columns: repeat(auto-fill, minmax(104px, 1fr)); gap: 6px; margin: 4px 0 10px; }
.rep-thumb { width: 100%; aspect-ratio: 16/10; border: 1px solid var(--suli-border); border-radius: 6px; cursor: zoom-in; }
.rep-row .row { margin-top: 0; flex-shrink: 0; }
@media (max-width: 900px) {
  .cols { flex-direction: column; }
  .col-left { width: 100%; }
}
</style>
