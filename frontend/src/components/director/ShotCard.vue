<template>
  <div class="suli-card shot-card">
    <div class="shot-top">
      <span class="shot-no tnum">{{ index + 1 }}</span>
      <span class="shot-sid">{{ shot.id }}</span>
      <el-button size="small" text @click="folded = !folded">{{ folded ? '▶ 展开' : '▼ 收起' }}</el-button>
      <el-button size="small" text @click="detailOpen = !detailOpen">{{ detailOpen ? '提示词 ▲' : '提示词 ▼' }}</el-button>
    </div>
    <div v-show="!folded" class="shot-body">
      <div class="shot-line">
        <el-image v-if="thumb" :src="imgUrl(thumb.name)" class="line-thumb" fit="cover" :preview-src-list="[imgUrl(thumb.name)]" preview-teleported />
        <div v-else class="line-thumb-empty">无图</div>
        <div class="line-main">
          <div class="line-duty" :title="shot.duty">{{ shot.duty || '（无内容）' }}</div>
          <div v-if="shot.duty_en" class="line-en" :title="shot.duty_en">{{ shot.duty_en }}</div>
          <div v-if="shot.sound" class="line-sound"><el-icon style="vertical-align:-2px;margin-right:2px"><Mic /></el-icon>{{ shot.sound }}</div>
          <div class="line-meta">
            <span class="tnum dur">{{ shot.duration_s }}s</span>
            <span><el-icon style="vertical-align:-2px;margin-right:2px"><VideoCamera /></el-icon>{{ cropLabel(shot) }} · {{ shot.camera?.movement }}</span>
            <el-tag v-if="shot.draft" size="small" type="warning">草案</el-tag>
            <el-tag v-if="shot.tier" size="small" :type="shot.tier === 'nsfw' ? 'danger' : 'info'">{{ tierLabel(shot.tier) }}</el-tag>
            <el-tag v-if="shot.water_level" size="small" type="danger" effect="plain">{{ waterLabel(shot.water_level) }}</el-tag>
            <el-tag v-if="shot.gen_mode" size="small" type="info" effect="plain">{{ GEN_LABEL[shot.gen_mode] || shot.gen_mode }}</el-tag>
            <el-tag v-if="refs.length" size="small" type="info">参考×{{ refs.length }}</el-tag>
            <el-tag v-if="!first" size="small" type="danger">缺首帧</el-tag>
          </div>
          <div v-if="lp" class="line-lp">
            <div class="lp-head">
              <span class="lp-tag">L-Port 提示词</span>
              <el-button size="small" text @click="copyLp">复制</el-button>
            </div>
            <div class="lp-body">{{ lp.director_cn || '—' }}</div>
            <div v-if="lp.camera_note" class="lp-sub">镜头：{{ lp.camera_note }}</div>
          </div>
        </div>
      </div>

      <div v-if="detailOpen" class="shot-detail">
        <div class="sd-sec">
          <div class="sd-head">
            <span>视频提示词</span>
            <el-tag v-if="vp.edited" size="small" type="warning">人工改</el-tag>
            <span style="flex:1" />
            <el-button size="small" text @click="copyText(draftPrompt)">复制</el-button>
            <el-button size="small" type="primary" plain :disabled="!promptDirty" @click="savePrompt">保存</el-button>
            <el-button v-if="vp.edited" size="small" @click="unlockPrompt">解锁</el-button>
          </div>
          <el-input v-model="draftPrompt" type="textarea" :autosize="{ minRows: 5, maxRows: 20 }" resize="vertical" />
          <div class="sd-meta">
            {{ vp.engine || '—' }}<template v-if="vp.video_model"> · {{ vp.video_model }}</template>
            · {{ vp.ref_mode || '—' }} · {{ vp.duration_s ?? shot.duration_s }}s<template v-if="vp.tier"> · {{ vp.tier }}</template>
            <template v-if="vp.source"> · {{ vp.source }}</template>
            <template v-if="vp.edited_at"> · 改于 {{ vp.edited_at }}</template>
          </div>
        </div>

        <div class="sd-sec">
          <div class="sd-head"><span>正向提示词</span><el-button size="small" text @click="copyText(positive)">复制</el-button></div>
          <div class="sd-body">{{ positive || '—' }}</div>
        </div>

        <div class="sd-sec">
          <div class="sd-head"><span>负向提示词</span><el-button size="small" type="primary" plain :disabled="!negDirty" @click="saveNegative">保存</el-button></div>
          <el-input v-model="draftNeg" type="textarea" :autosize="{ minRows: 2, maxRows: 8 }" resize="vertical" />
          <div class="sd-meta">{{ negativeNote }}</div>
        </div>

        <div class="sd-sec">
          <div class="sd-head"><span>参考图</span><span class="sd-count tnum">{{ refs.length }}</span></div>
          <div v-if="!refs.length" class="sd-body">—</div>
          <div v-for="x in refs" :key="x.name + x.kind" class="sd-ref">
            <el-image :src="imgUrl(x.name)" class="sd-ref-thumb" fit="cover" :preview-src-list="[imgUrl(x.name)]" preview-teleported />
            <div class="sd-ref-main">
              <div class="sd-ref-top">
                <el-tag size="small" :type="x.kind === 'first' ? 'danger' : 'info'" effect="plain">{{ refKind(x) }}</el-tag>
                <span class="sd-ref-name">{{ x.name }}</span>
                <span style="flex:1" />
                <el-button size="small" text :disabled="!imgDirty(x)" @click="saveImg(x)">保存</el-button>
              </div>
              <div class="sd-ref-edit">
                <el-select
                  v-if="x.kind !== 'first'"
                  v-model="imgDrafts[x.name].role"
                  size="small" style="width: 96px" placeholder="role"
                >
                  <el-option v-for="r in REF_ROLE_KEYS" :key="r" :label="REF_ROLE[r]" :value="r" />
                </el-select>
                <el-input
                  v-model="imgDrafts[x.name].desc"
                  size="small" placeholder="desc"
                  type="textarea" :autosize="{ minRows: 1, maxRows: 4 }" resize="vertical"
                />
              </div>
            </div>
          </div>
        </div>

        <div class="sd-sec">
          <div class="sd-head"><span>参数</span></div>
          <div class="sd-grid">
            <span class="sd-k">景别</span><span class="sd-v">{{ cropLabel(shot) }}</span>
            <span class="sd-k">运镜</span><span class="sd-v">{{ shot.camera?.movement || '—' }}</span>
            <span class="sd-k">时长</span><span class="sd-v tnum">{{ shot.duration_s }}s</span>
            <span class="sd-k">生成方式</span><span class="sd-v">{{ genModeText }}</span>
            <span class="sd-k">水位</span><span class="sd-v">{{ shot.water_level ? waterLabel(shot.water_level) : '—' }}</span>
            <span class="sd-k">分级</span><span class="sd-v">{{ shot.tier || '—' }}</span>
            <span class="sd-k">台词</span><span class="sd-v">{{ shot.sound || '—' }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Mic, VideoCamera } from '@element-plus/icons-vue'
import { api } from '../../api/client'
import { imgUrl, firstImg, refImgs, cropLabel } from '../../composables/useShotImages'
const props = defineProps<{ shot: any; index: number; tierLabel: (k: string) => string; onSaved?: () => void }>()
const WATER_LABEL: Record<string, string> = { tease: '暗示', undress: '半露', explicit: '直白', closeup: '特写' }
const GEN_LABEL: Record<string, string> = { 't2v': '纯文本', 'i2v-first': '首帧', 'i2v-first-last': '首尾帧', 'multi-ref': '多图参考' }
const waterLabel = (k: string) => WATER_LABEL[k] || k
const REF_KIND: Record<string, string> = { first: '首帧', ref: '参考', last: '尾帧' }
const REF_ROLE: Record<string, string> = {
  character: '角色', outfit: '服装', style: '风格', face: '脸', pose: '姿态', scene: '场景', prop: '道具', ending: '收尾',
}
const REF_ROLE_KEYS = ['character', 'outfit', 'style', 'face', 'pose', 'scene', 'prop']
const refKind = (x: any) => REF_KIND[x?.kind] || x?.kind || '参考'
const refRole = (x: any) => REF_ROLE[x?.role] || x?.role || ''
const folded = ref(false)
const detailOpen = ref(false)
const first = computed(() => firstImg(props.shot))
const refs = computed(() => refImgs(props.shot))
// 没有首帧但有参考图时，缩略图先用第一张参考图，别显示"无图"
const thumb = computed(() => first.value || refs.value[0] || null)
const vp = computed(() => props.shot?.lport_video_prompts || {})
// 意图 → 结算：型号不支持时组装层会降级，两个值不同就把降级结果一并显示
const genModeText = computed(() => {
  const want = GEN_LABEL[props.shot?.gen_mode] || '自动'
  const eff = GEN_LABEL[vp.value?.gen_mode_eff] || ''
  return eff && eff !== want ? `${want} → ${eff}` : want
})
const lp = computed(() => props.shot?.lport_prompts || null)
const positive = computed(() => (vp.value.prompt || props.shot?.duty_en || '').trim())
const negativeNote = computed(() => (
  vp.value.negative ? '随直投包下发；当前引擎无负向栏时由执行侧忽略'
    : '当前引擎无负向栏（Tsubaki Video 走正向描述），填了只随包下发'
))
const draftPrompt = ref('')
const draftNeg = ref('')
watch(() => vp.value.prompt, (v) => { draftPrompt.value = v || '' }, { immediate: true })
watch(() => (vp.value.negative ?? props.shot?.video_negative) || '', (v) => { draftNeg.value = v || '' }, { immediate: true })
const promptDirty = computed(() => draftPrompt.value !== (vp.value.prompt || ''))
const negDirty = computed(() => draftNeg.value !== ((vp.value.negative ?? props.shot?.video_negative) || ''))
// 参考图 role/desc 编辑缓冲：键用图名，脏了才亮保存
const imgDrafts = ref<Record<string, { role: string; desc: string }>>({})
watch(refs, (list: any[]) => {
  const next: Record<string, { role: string; desc: string }> = {}
  for (const x of list) {
    const base = { role: x.role || '', desc: x.desc || '' }
    const cur = imgDrafts.value[x.name]
    next[x.name] = cur && (cur.role !== base.role || cur.desc !== base.desc) ? cur : base
  }
  imgDrafts.value = next
}, { immediate: true, deep: true })
function imgDirty(x: any): boolean {
  const d = imgDrafts.value[x.name]
  return !!d && (d.role !== (x.role || '') || d.desc !== (x.desc || ''))
}
async function saveImg(x: any) {
  const d = imgDrafts.value[x.name]
  if (!d) return
  try {
    await api.setShotImageMeta(props.shot.id, x.name, { role: d.role, desc: d.desc })
    ElMessage.success('已保存')
    props.onSaved?.()
  } catch (e: any) { ElMessage.error('保存失败：' + (e?.message || e)) }
}
async function copyText(t: string) {
  if (!t) return
  try { await navigator.clipboard.writeText(t); ElMessage.success('已复制') }
  catch { ElMessage.warning('复制失败，手动选中吧') }
}
async function savePrompt() {
  const p = draftPrompt.value.trim()
  if (!p) return
  try {
    await api.saveVideoPrompt(props.shot.id, { prompt: p })
    ElMessage.success('已保存')
    props.onSaved?.()
  } catch (e: any) { ElMessage.error('保存失败：' + (e?.message || e)) }
}
async function unlockPrompt() {
  try {
    await api.unlockVideoPrompt(props.shot.id)
    ElMessage.success('已解锁')
    props.onSaved?.()
  } catch (e: any) { ElMessage.error('解锁失败：' + (e?.message || e)) }
}
async function saveNegative() {
  try {
    await api.updateShot(props.shot.id, { video_negative: draftNeg.value })
    ElMessage.success('已保存')
    props.onSaved?.()
  } catch (e: any) { ElMessage.error('保存失败：' + (e?.message || e)) }
}
async function copyLp() {
  const v = lp.value || {}
  const t = [v.director_cn, v.camera_note ? `镜头：${v.camera_note}` : ''].filter(Boolean).join('\n')
  if (!t) return
  try { await navigator.clipboard.writeText(t); ElMessage.success('已复制') }
  catch { ElMessage.warning('复制失败，手动选中吧') }
}
</script>
<style scoped>
.shot-card { padding: 10px 12px; display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.shot-top { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.shot-no { width: 28px; height: 28px; border-radius: 50%; background: var(--suli-primary); color: #fff; font-size: 13px; font-weight: 800; display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; }
.shot-sid { font-family: var(--suli-mono); font-size: 12px; }
.shot-detail { display: flex; flex-direction: column; gap: 12px; border-top: 1px dashed var(--suli-line, #e4e4e7); padding-top: 10px; margin-top: 2px; }
.sd-sec { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.sd-head { display: flex; gap: 8px; align-items: center; font-size: 12px; font-weight: 700; }
.sd-count { color: var(--suli-muted, #909399); font-weight: 400; }
.sd-body { font-size: 12px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; color: var(--suli-text-2, #444); }
.sd-meta { font-size: 11px; color: var(--suli-muted, #909399); }
.sd-ref { display: flex; gap: 8px; align-items: flex-start; }
.sd-ref-thumb { width: 56px; height: 56px; border-radius: 6px; flex-shrink: 0; }
.sd-ref-main { min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.sd-ref-top { display: flex; gap: 6px; align-items: center; }
.sd-ref-name { font-family: var(--suli-mono); font-size: 11px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sd-ref-desc { font-size: 11px; color: var(--suli-muted, #909399); line-height: 1.5; word-break: break-word; }
.sd-ref-edit { display: flex; gap: 6px; align-items: flex-start; margin-top: 2px; }
.sd-grid { display: grid; grid-template-columns: 56px 1fr 56px 1fr; gap: 4px 10px; font-size: 12px; }
.sd-k { color: var(--suli-muted, #909399); }
.sd-v { word-break: break-word; }
</style>
