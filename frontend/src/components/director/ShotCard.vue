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
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed, ref } from 'vue'
import { Mic, VideoCamera } from '@element-plus/icons-vue'
import { imgUrl, firstImg, refImgs, cropLabel } from '../../composables/useShotImages'
const props = defineProps<{ shot: any; index: number; tierLabel: (k: string) => string }>()
const folded = ref(false)
const first = computed(() => firstImg(props.shot))
const refs = computed(() => refImgs(props.shot))
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
.shot-body { display: flex; flex-direction: column; gap: 8px; }
</style>
