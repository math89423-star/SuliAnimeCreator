<template>
  <div class="studio-page">
    <!-- 面包屑 -->
    <div class="crumbs">
      <span class="crumb-main">Story Studio</span>
      <span class="crumb-sep">/</span>
      <span class="crumb-sub">新故事</span>
    </div>

    <div class="studio-grid">
      <!-- 左：创建表单 -->
      <div class="suli-card studio-form">
        <h2 class="form-title">创建故事</h2>

        <!-- 演员阵容 -->
        <div class="sec">
          <div class="sec-label"><span>演员阵容</span></div>
          <div v-if="!curChar" class="pick-btn" @click="charDialog = true">
            <el-icon class="pick-icon"><User /></el-icon> 选择角色
          </div>
          <div v-else class="char-card">
            <el-avatar :size="36" :src="charAvatar(curChar)" />
            <div class="char-meta">
              <b>{{ curChar.name || curChar.id }}</b>
              <span class="suli-muted">{{ curChar.id }}</span>
            </div>
            <span style="flex:1" />
            <el-button size="small" @click="charDialog = true">更换</el-button>
          </div>
          <div class="field-head" style="margin-top:10px">
            <span class="field-title">对白角色名</span>
          </div>
          <el-input v-model="castInput" placeholder="选角" @blur="saveCast" />
        </div>

        <!-- References -->
        <div class="sec">
          <div class="sec-label"><span>References</span></div>
          <div class="ref-row">
            <div v-for="im in refImages" :key="im.name" class="ref-thumb">
              <el-image :src="imgUrl(im.name)" fit="cover" :preview-src-list="[imgUrl(im.name)]" preview-teleported />
              <span class="ref-x" @click="delRef(im.name)">×</span>
            </div>
            <div class="pick-btn" @click="refFileEl?.click()">
              <el-icon class="pick-icon"><Plus /></el-icon> 添加参考
            </div>
          </div>
          <input ref="refFileEl" type="file" accept="image/*" hidden @change="onRef" />
        </div>

        <!-- 故事 -->
        <div class="sec">
          <div class="sec-label"><span>故事</span></div>
          <div class="field-head">
            <span class="field-title">故事提示词</span>
          </div>
          <el-input
            v-model="idea" type="textarea" :rows="5"
          />
          <div class="field-count suli-muted tnum">{{ idea.length }}字</div>
        </div>

        <!-- 设置 -->
        <div class="sec">
          <div class="sec-label"><span>设置</span></div>
          <div class="set-grid">
            <div class="set-item">
              <span class="set-k">宽高比</span>
              <el-select v-model="aspect" size="default">
                <el-option label="9:16 竖屏" value="9:16" />
                <el-option label="16:9 横屏" value="16:9" />
                <el-option label="1:1 方形" value="1:1" />
                <el-option label="3:4 竖构图" value="3:4" />
              </el-select>
            </div>
            <div class="set-item">
              <span class="set-k">时长</span>
              <el-select v-model.number="shotLen" size="default">
                <el-option :label="'4s'" :value="4" />
                <el-option :label="'6s'" :value="6" />
                <el-option :label="'8s'" :value="8" />
              </el-select>
            </div>
          </div>
        </div>

        <!-- 故事长度 -->
        <div class="sec">
          <div class="sec-label"><span>故事长度</span></div>
          <div class="len-head">
            <span class="set-k">视频数量</span>

          </div>
          <el-input-number v-model="videoCount" :min="2" :max="20" :step="1" class="len-num" />
          <div class="cost-row">
            <span class="suli-muted">{{ videoCount }} 个场景 · 每个 {{ shotLen }}s</span>
            <span class="tnum">{{ totalS }}s</span>
          </div>
          <div class="balance">你有 {{ confirmed.length }} 个已确认方向</div>
          <div class="form-actions">
            <el-button class="act-clear" @click="clearAll">清除</el-button>
            <el-button type="primary" class="act-go" :loading="loading" @click="suggest"><el-icon style="margin-right:4px"><Document /></el-icon>撰写脚本</el-button>
          </div>
        </div>
      </div>

      <!-- 右：预览 / 场景 -->
      <div class="suli-card studio-preview">
        <div class="prev-head">
          <div>
            <b>用视频讲述一个故事</b>

          </div>
          <span style="flex:1" />
          <el-button size="small" @click="histOpen = true"><el-icon style="margin-right:4px"><Files /></el-icon>聊本历史</el-button>
        </div>

        <!-- 空态：文案 + 三步卡占满列 -->
        <div v-if="!dirs.length && !loading" class="empty-wrap">
          <div class="empty">
            <div class="empty-icon"><el-icon><Document /></el-icon></div>
            <b>用视频讲述一个故事</b>
          </div>
        </div>

        <!-- 加载 -->
        <div v-if="loading" class="scene-grid">
          <div v-for="i in 3" :key="i" class="suli-card scene-card"><div class="skeleton" style="height:18px;width:40%" /><div class="skeleton" style="height:12px;margin-top:8px" /><div class="skeleton" style="height:56px;margin-top:8px" /></div>
        </div>

        <!-- 场景 -->
        <div v-else-if="dirs.length" class="scene-grid">
          <div v-for="d in dirs" :key="d.dir" class="suli-card scene-card">
            <div class="scene-top">
              <el-tag size="small" type="info">方向{{ d.dir }}</el-tag>
              <span class="suli-muted tnum">{{ (d.beats || []).length }} 拍</span>
            </div>
            <div class="scene-log">{{ d.logline }}</div>
            <div class="suli-muted scene-beats">{{ (d.beats || []).join(' → ') }}</div>
            <div class="scene-actions">
              <el-button size="small" type="primary" @click="confirm(d)">确认此方向</el-button>
              <el-button size="small" @click="genScreenplay(d)" :loading="genLoading">生成剧本</el-button>
              <el-button size="small" @click="copy(d.logline)">复制</el-button>
              <el-button size="small" @click="goDirect(d)">去导演页开拍 →</el-button>
            </div>
          </div>
        </div>

        <div class="prev-foot">
          <el-avatar :size="28" src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bdeb.png" />
          <span style="flex:1" />
          <el-button circle size="large" type="primary" @click="goBoard"><el-icon><ChatDotRound /></el-icon></el-button>
        </div>
      </div>
    </div>

    <!-- 选角弹窗 -->
    <el-dialog v-model="charDialog" title="选择角色" width="520px">
      <el-empty v-if="!chars.length" description="暂无角色" :image-size="48" />
      <div v-else class="char-list">
        <div
          v-for="c in chars" :key="c.id"
          class="char-item" :class="{ on: curId === c.id }" @click="pickChar(c.id)"
        >
          <el-avatar :size="32" :src="charAvatar(c)" />
          <div class="char-meta"><b>{{ c.name || c.id }}</b><span class="suli-muted">{{ c.id }}</span></div>
          <el-tag v-if="curId === c.id" size="small" type="success">当前</el-tag>
        </div>
      </div>
      <template #footer>
        <el-button @click="charDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 聊本历史 -->
    <el-drawer v-model="histOpen" title="聊本历史 · 已确认方向" size="420px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
        <span class="suli-muted" style="font-size:12px">{{ confirmed.length }} 条已确认</span>
        <span style="flex:1" />
        <el-button v-if="confirmed.length" size="small" type="danger" plain @click="clearConfirmed">清空</el-button>
      </div>
      <el-empty v-if="!confirmed.length" description="暂无" :image-size="48" />
      <el-table v-else :data="confirmed">
        <el-table-column prop="dir" label="方向" width="70" />
        <el-table-column prop="logline" label="logline" />
        <el-table-column label="操作" width="76">
          <template #default="scope">
            <el-button link type="danger" size="small" @click="removeConfirmed(scope.row, scope.$index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Plus, Document, Files, ChatDotRound } from '@element-plus/icons-vue'
import { api } from '../api/client'
import { copyText } from '../utils/clipboard'
import { castNames, loadCastInput, saveCastInput } from '../utils/cast'
import { purgeLegacySeeds } from '../utils/legacySeeds'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const router = useRouter()

/* —— 故事主体（沿用旧逻辑） —— */
const DRAFT_KEY = 'suli.story.idea'
/* 旧的演示种子只在没人动过时清一次；用户自己写的提示词一律不碰 */
purgeLegacySeeds()
const idea = ref(localStorage.getItem(DRAFT_KEY) || '')
watch(idea, v => { try { localStorage.setItem(DRAFT_KEY, v) } catch {} })

/* 对白角色名：用户点名的那批人；留空走后端自动取角（角色库/本集正文/占位） */
const castInput = ref(loadCastInput())
const castNamesList = () => castNames(castInput.value)
async function saveCast() {
  const names = saveCastInput(castInput.value)
  try {
    if (store.episodeId) await api.setEpisodeCast(store.episodeId, names)
  } catch {}
}
async function loadCast() {
  // 本集已记的角色名回填输入框；没有记忆就保持空（=自动取角）
  if (!store.episodeId) return
  try {
    const r: any = await api.getEpisodeCast(store.episodeId)
    const rows = ((r?.data?.cast) || []) as any[]
    if (rows.length && !castInput.value) {
      castInput.value = rows.map(c => c.name).filter(Boolean).join('、')
      saveCastInput(castInput.value)
    }
  } catch {}
}
const drafts = ref<any>(null)
const confirmed = ref<any[]>([])
const loading = ref(false)
const dirs = computed(() => (drafts.value?.drafts || []) as any[])

/* —— 故事设置（本地持久化，不影响旧接口） —— */
const SET_KEY = 'suli.story.studio'
function loadSet() {
  try { return JSON.parse(localStorage.getItem(SET_KEY) || '{}') } catch { return {} }
}
const _s = loadSet()
const engineModel = ref(_s.engineModel || 'tsubaki-video')
const resolution = ref(_s.resolution || '480p')
const aspect = ref(_s.aspect || '9:16')
const shotLen = ref(Number(_s.shotLen) || 4)
const videoCount = ref(Number(_s.videoCount) || 5)
watch([engineModel, resolution, aspect, shotLen, videoCount], () => {
  try {
    localStorage.setItem(SET_KEY, JSON.stringify({
      engineModel: engineModel.value, resolution: resolution.value,
      aspect: aspect.value, shotLen: shotLen.value, videoCount: videoCount.value,
    }))
  } catch {}
})
const modelOpts = [
  { label: 'Tsubaki Video', value: 'tsubaki-video' },
  { label: 'Tsubaki Flash', value: 'tsubaki-video-flash' },
  { label: 'V4.0 Preview', value: 'v4' },
  { label: 'MiniMax H3', value: 'h3' },
]
const totalS = computed(() => (videoCount.value || 0) * (shotLen.value || 0))

/* —— 角色 —— */
const chars = ref<any[]>([])
const curId = ref(store.selectedCharId || '')
const charDialog = ref(false)
const curChar = computed(() => chars.value.find(x => x.id === curId.value) || null)
function charAvatar(c: any) {
  const a = c?.avatar_path ? `/api/images/${c.avatar_path}` : ''
  return a
}
async function loadChars() {
  try {
    const r = await api.listCharacters()
    chars.value = (r as any)?.data || r || []
    if (store.selectedCharId && chars.value.find(x => x.id === store.selectedCharId)) curId.value = store.selectedCharId
    else if (!curId.value && chars.value[0]) curId.value = chars.value[0].id
  } catch {}
}
function pickChar(id: string) {
  curId.value = id
  store.selectedCharId = id
  charDialog.value = false
  ElMessage.success('已选角色 ' + id)
}

/* —— References（复用本集剧本参考图） —— */
const refImages = ref<any[]>([])
const refFileEl = ref<HTMLInputElement | null>(null)
function imgUrl(name: string) { return `/api/images/${name}` }
async function loadRefs() {
  try {
    const r = await api.getScreenplay(store.episodeId)
    refImages.value = ((r as any)?.data?.ref_images ?? []) as any[]
  } catch { refImages.value = [] }
}
async function onRef(e: any) {
  const f = e.target.files?.[0]
  e.target.value = ''
  if (!f) return
  try {
    await api.uploadEpisodeImage(store.episodeId, f)
    ElMessage.success('参考图已上传')
    await loadRefs()
  } catch { ElMessage.error('上传失败，后端未起？') }
}
async function delRef(name: string) {
  try {
    await api.deleteEpisodeImage(store.episodeId, name)
    await loadRefs()
  } catch { ElMessage.error('删除失败') }
}

/* —— 动作 —— */
const histOpen = ref(false)
async function suggest() {
  if (!idea.value.trim()) return ElMessage.warning('先写故事提示词')
  loading.value = true
  try {
    const n = Math.min(5, Math.max(2, Math.round(videoCount.value / 2) || 3))
    const r = await api.storyExpand(idea.value, n)
    drafts.value = (r as any)?.data || r
    if (!dirs.value.length) ElMessage.warning('方向为空，重试一次')
  } catch { ElMessage.error('后端未起') }
  finally { loading.value = false }
}
const genLoading = ref(false)
async function confirm(d: any) {
  try {
    await api.storyConfirm(d)
    try { await (api as any).confirmToEpisode(d, store.episodeId) } catch {}
    ElMessage.success('已确认方向' + d.dir + '（已落本集底稿）')
    await reloadConfirmed()
  } catch { ElMessage.error('确认失败，后端未起？') }
}
async function genScreenplay(d: any) {
  if (genLoading.value) return
  genLoading.value = true
  try {
    await confirm(d)
    const r: any = await (api as any).screenplayGenerate({ idea: idea.value, pick: d, target_s: totalS.value || 30, episode_id: store.episodeId, cast: castNamesList() })
    const md = r?.data?.screenplay_md ?? r?.screenplay_md ?? ''
    if (md) {
      await api.saveScreenplay(store.episodeId, md)
      ElMessage.success(`剧本已生成${md.length}字并落底稿（${r?.data?.engine ?? r?.engine ?? ''}）`)
    } else ElMessage.warning('生成为空，重试一次')
  } catch { ElMessage.error('剧本生成失败，后端未起？') }
  finally { genLoading.value = false }
}
async function reloadConfirmed() {
  try {
    const r = await api.storyList()
    confirmed.value = ((r as any)?.data?.confirmed || (r as any)?.confirmed || []) as any[]
  } catch {}
}
function confirmedKey(row: any, idx: number) {
  const id = String(row?.id || '').trim()
  if (id) return id
  const log = String(row?.logline || '').trim()
  if (log) return log
  return String(idx)
}
async function removeConfirmed(row: any, idx: number) {
  try {
    await api.deleteConfirmedOne(confirmedKey(row, idx))
    ElMessage.success('已删除')
    await reloadConfirmed()
  } catch (e: any) {
    ElMessage.error((e?.response?.data?.msg || e?.message || '删除失败').slice(0, 200))
    await reloadConfirmed()
  }
}
async function clearConfirmed() {
  try {
    await api.clearConfirmed()
    ElMessage.success('已清空已确认方向')
    await reloadConfirmed()
  } catch (e: any) {
    ElMessage.error((e?.response?.data?.msg || e?.message || '清空失败').slice(0, 200))
    await reloadConfirmed()
  }
}
function copy(t: string) { copyText(t) }
function clearAll() {
  idea.value = ''
  drafts.value = null
  videoCount.value = 5
  try { void api.clearDrafts() } catch {}
  ElMessage.success('已清空')
}
function goBoard() { router.push('/board') }
function goDirect(d: any) {
  confirm(d).finally(() => router.push('/director'))
}

watch(() => store.episodeId, () => { loadRefs(); loadCast() })
watch(() => store.selectedCharId, v => { if (v) curId.value = v })

onMounted(async () => {
  await loadChars()
  await loadRefs()
  await loadCast()
  await reloadConfirmed()
})
</script>

<style scoped>
.studio-page { max-width: none; margin: 0; width: 100%; min-height: 100%; display: flex; flex-direction: column; }
.crumbs { display: flex; gap: 8px; align-items: center; font-size: 13px; margin: 2px 2px 10px; }
.crumb-main { color: var(--suli-text-2); }
.crumb-sep { color: var(--suli-text-3); }
.crumb-sub { font-weight: 700; }
.studio-grid { display: grid; grid-template-columns: 400px minmax(0, 1fr); gap: 14px; align-items: stretch; flex: 1; min-height: 0; }
.studio-form { padding: 18px 18px 14px; align-self: start; max-height: 100%; overflow: auto; position: sticky; top: 0; }
.form-title { font-size: 20px; font-weight: 800; margin: 0; }
.form-sub { color: var(--suli-text-2); font-size: 13px; margin: 6px 0 4px; }
.sec { margin-top: 6px; }
.sec-label { display: flex; align-items: center; gap: 10px; color: var(--suli-text-3); font-size: 12px; margin: 14px 0 8px; }
.sec-label::before, .sec-label::after { content: ''; height: 1px; background: var(--suli-border); flex: 1; }
.pick-btn { display: flex; gap: 8px; align-items: center; justify-content: center; border: 1.5px solid var(--suli-border); border-radius: 12px; padding: 12px; font-weight: 600; cursor: pointer; background: #fff; }
.pick-btn:hover { border-color: var(--suli-primary); color: var(--suli-primary); }
.pick-icon { font-size: 15px; }
.char-card, .char-item { display: flex; gap: 10px; align-items: center; border: 1.5px solid var(--suli-border); border-radius: 12px; padding: 8px 10px; }
.char-list { display: flex; flex-direction: column; gap: 8px; }
.char-item { cursor: pointer; }
.char-item.on { border-color: var(--suli-primary); }
.char-meta { display: flex; flex-direction: column; line-height: 1.3; }
.char-meta .suli-muted { font-size: 11px; }
.ref-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: stretch; }
.ref-row .pick-btn { flex: 1; min-width: 140px; }
.ref-thumb { position: relative; width: 76px; height: 76px; border-radius: 10px; overflow: hidden; border: 1.5px solid var(--suli-border); }
.ref-thumb :deep(img) { width: 100%; height: 100%; object-fit: cover; display: block; }
.ref-x { position: absolute; top: 2px; right: 2px; width: 20px; height: 20px; border-radius: 50%; background: rgba(0,0,0,.55); color: #fff; font-size: 13px; line-height: 20px; text-align: center; cursor: pointer; }
.field-head { margin: 2px 0 6px; }
.field-title { font-weight: 700; font-size: 13px; }
.q { display: inline-flex; width: 16px; height: 16px; border-radius: 50%; background: var(--suli-bg-2); border: 1px solid var(--suli-border); color: var(--suli-text-2); font-size: 11px; align-items: center; justify-content: center; margin-left: 4px; cursor: help; }
.field-count { text-align: right; font-size: 11px; margin-top: 4px; }
.set-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 12px; }
.set-item { display: flex; flex-direction: column; gap: 6px; }
.set-k { font-size: 13px; font-weight: 700; }
.seg { display: flex; background: var(--suli-bg-2); border-radius: 10px; padding: 3px; gap: 3px; }
.seg span { flex: 1; text-align: center; padding: 7px 0; border-radius: 8px; font-size: 13px; cursor: pointer; color: var(--suli-text-2); }
.seg span.on { background: #fff; color: var(--suli-text); font-weight: 700; box-shadow: var(--suli-shadow-sm); }
.len-head { display: flex; align-items: center; }
.len-hint { margin-left: auto; font-size: 11px; }
.len-num { width: 100%; margin-top: 6px; }
.quick-row { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-top: 8px; }
.quick { text-align: center; border: 1.5px solid var(--suli-border); border-radius: 10px; padding: 7px 0; font-size: 13px; cursor: pointer; }
.quick.on { border-color: var(--suli-primary); color: var(--suli-primary); font-weight: 800; }
.cost-row { display: flex; justify-content: space-between; font-size: 13px; margin-top: 8px; }
.cost-row.total { align-items: center; margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--suli-border); }
.total-badge { background: #FFF3E6; color: #E8932B; border-radius: 8px; padding: 3px 10px; font-weight: 800; }
.balance { color: var(--el-color-error, #F56C6C); font-size: 12px; margin-top: 6px; }
.form-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; }
.act-clear { background: var(--suli-bg-2); border: none; }
.act-go { background: linear-gradient(180deg, #FFC46B, #FF9F43); border: none; font-weight: 800; }
.studio-preview { min-height: 0; display: flex; flex-direction: column; padding: 0; overflow: hidden; }
.prev-head { display: flex; gap: 10px; align-items: flex-start; padding: 16px 18px; border-bottom: 1px solid var(--suli-border); }
.prev-sub { font-size: 12px; margin-top: 4px; }
.empty-wrap { flex: 1; display: flex; flex-direction: column; overflow: auto; }
.empty { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; padding: 56px 40px 24px; text-align: center; }
.empty-icon { font-size: 40px; color: var(--suli-text-3); }
.empty p { max-width: 560px; font-size: 13px; }
.guide-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; padding: 0 18px 20px; }
.guide-card { padding: 14px; display: flex; flex-direction: column; gap: 6px; font-size: 13px; }
.guide-n { width: 24px; height: 24px; border-radius: 50%; background: var(--suli-bg-2); border: 1px solid var(--suli-border); font-size: 12px; font-weight: 800; display: flex; align-items: center; justify-content: center; }
.scene-grid { flex: 1; display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 12px; padding: 16px 18px; align-content: start; overflow: auto; }
.scene-card { padding: 12px; display: flex; flex-direction: column; gap: 8px; }
.scene-top { display: flex; align-items: center; gap: 8px; }
.scene-log { font-size: 13px; font-weight: 600; }
.scene-beats { font-size: 12px; }
.scene-actions { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px; }
.prev-foot { display: flex; gap: 10px; align-items: center; padding: 12px 16px; border-top: 1px solid var(--suli-border); }
@media (max-width: 1100px) { .studio-grid { grid-template-columns: 1fr; } .studio-form { position: static; max-height: none; } .studio-preview { min-height: 480px; } .guide-grid { grid-template-columns: 1fr; } }
</style>
