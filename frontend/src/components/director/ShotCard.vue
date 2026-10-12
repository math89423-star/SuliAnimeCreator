<template>
  <div class="suli-card shot-card">
    <div class="shot-top">
      <span class="shot-no tnum">{{ index + 1 }}</span>
      <span class="shot-sid">{{ shot.id }}</span>
      <el-tag v-if="result" size="small" :type="result.mode === 'I2VA' ? 'success' : 'warning'">{{ result.mode }}</el-tag>
      <el-tag v-if="result?.missing_image" size="small" type="danger">缺首帧</el-tag>
      <el-tag v-if="(result?.refs?.length || 0) > 1" size="small" type="info">多图×{{ result.refs.length }}</el-tag>
      <span style="flex:1" />
      <el-button size="small" type="primary" @click="$emit('assemble', shot)" :loading="loading">组装本镜</el-button>
      <el-button v-if="result" size="small" @click="$emit('copy', result.prompt)">复制{{ engine === 'pixai' ? '提示词' : 'H3' }}</el-button>
      <el-button size="small" @click="$emit('board')">分镜改</el-button>
    </div>
    <div class="shot-line">
      <el-image v-if="first" :src="imgUrl(first.name)" class="line-thumb" fit="cover" :preview-src-list="[imgUrl(first.name)]" preview-teleported />
      <div v-else class="line-thumb-empty">无图</div>
      <div class="line-main">
        <div class="line-duty" :title="shot.duty">{{ shot.duty || '（无内容）' }}</div>
        <div class="line-meta">
          <span class="tnum">{{ shot.duration_s }}s</span>
          <span>{{ cropLabel(shot) }} · {{ shot.camera?.movement }}</span>
          <el-tag v-if="shot.draft" size="small" type="warning">草案</el-tag>
          <el-tag v-if="shot.tier" size="small">{{ tierLabel(shot.tier) }}</el-tag>
          <el-tag v-if="refs.length" size="small" type="info">参考×{{ refs.length }}</el-tag>
        </div>
      </div>
    </div>
    <div v-if="result?.applied?.length" class="shot-applied">{{ result.applied.join('；') }}</div>
    <div v-if="result" class="shot-prompt">{{ result.prompt }}</div>
  </div>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { imgUrl, firstImg, refImgs, cropLabel } from '../../composables/useShotImages'
const props = defineProps<{ shot: any; index: number; result: any; loading: boolean; engine: string; tierLabel: (k: string) => string }>()
defineEmits<{ (e: 'assemble', s: any): void; (e: 'copy', t: string): void; (e: 'board'): void }>()
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
.line-duty { font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.line-meta { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; font-size: 12px; color: var(--suli-text-2); }
.shot-applied { font-size: 12px; color: var(--suli-warning, #b26a00); background: #FFF7E6; border-radius: 8px; padding: 6px 8px; }
.shot-prompt { font-size: 13px; white-space: pre-wrap; background: var(--el-fill-color-lighter); border-radius: 8px; padding: 10px; }
</style>
