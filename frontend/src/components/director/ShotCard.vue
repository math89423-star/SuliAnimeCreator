<template>
  <div class="suli-card shot-card">
    <div class="shot-top">
      <span class="shot-no tnum">{{ index + 1 }}</span>
      <span class="shot-sid">{{ shot.id }}</span>
      <el-button size="small" text @click="folded = !folded">{{ folded ? '▶ 展开' : '▼ 收起' }}</el-button>
    </div>
    <div v-show="!folded" class="shot-body">
      <div class="shot-line">
        <el-image v-if="first" :src="imgUrl(first.name)" class="line-thumb" fit="cover" :preview-src-list="[imgUrl(first.name)]" preview-teleported />
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
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Mic, VideoCamera } from '@element-plus/icons-vue'
import { imgUrl, firstImg, refImgs, cropLabel } from '../../composables/useShotImages'
const props = defineProps<{ shot: any; index: number; tierLabel: (k: string) => string }>()
const folded = ref(false)
const first = computed(() => firstImg(props.shot))
const refs = computed(() => refImgs(props.shot))
// L-Port 回传的详细提示词（seg_prompt 逐镜回传，见导演页「提示词」页签）
const lp = computed(() => (props.shot?.lport_prompts || null))
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
.shot-line { display: flex; gap: 12px; align-items: flex-start; }
.line-thumb { width: 150px; aspect-ratio: 3 / 4; border-radius: 10px; flex-shrink: 0; cursor: zoom-in; overflow: hidden; }
.line-thumb-empty { width: 150px; aspect-ratio: 3 / 4; border-radius: 10px; border: 1px dashed var(--suli-border); display: flex; align-items: center; justify-content: center; color: var(--suli-text-3); font-size: 12px; flex-shrink: 0; }
.line-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.line-duty { font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: 600; }
.line-en { font-size: 12px; color: var(--suli-text-2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.line-sound { font-size: 12px; color: var(--suli-text-2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.dur { font-weight: 800; }
.line-meta { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; font-size: 12px; color: var(--suli-text-2); }
.line-lp { margin-top: 4px; border: 1px dashed var(--suli-border); border-radius: 8px; padding: 6px 8px; background: var(--suli-bg-2); }
.lp-head { display: flex; gap: 6px; align-items: center; }
.lp-tag { font-size: 11px; font-weight: 700; color: var(--suli-primary); }
.lp-body { font-size: 12px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; margin-top: 2px; }
.lp-sub { font-size: 11px; color: var(--suli-text-2); margin-top: 2px; }
.shot-body { display: flex; flex-direction: column; gap: 8px; }
</style>
