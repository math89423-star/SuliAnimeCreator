<template>
  <div class="suli-card agent-direct">
    <div class="agent-head">
      <b>单图Agent导演</b>
      <span style="flex:1" />
      <el-button v-if="loading" size="small" @click="$emit('stop')">停止</el-button>
    </div>
    <div class="agent-main">
      <div class="pic-box-lg">
        <SlotZoomImage :src="img?.url || ''" aspect="3/4" :lens-size="220" @upload="$emit('pick')" />
        <div class="pic-actions">
          <el-button link type="primary" size="small" @click="$emit('pick')">{{ img ? '重选' : '传图' }}</el-button>
          <el-button v-if="img" link type="danger" size="small" @click="$emit('clear')">清除</el-button>
        </div>
      </div>
      <div class="agent-fields">
        <el-input v-model="ask" type="textarea" class="grow-area" resize="none" placeholder="补充要求" />
        <div class="shot-row agent-btn-row">
          <el-button type="primary" size="small" @click="$emit('outline')" :loading="loading" :disabled="!img">让Agent出大纲</el-button>
          <el-button size="small" @click="$emit('draft')" :loading="loading" :disabled="!outlineMd">转草案分镜</el-button>
          <span v-if="progress" class="suli-muted" style="font-size:12px">{{ progress }}</span>
          <span class="bar-spacer" />
          <el-input-number v-model="total" size="small" style="width:104px" :min="4" :max="90" :step="1" controls-position="right" />
          <span class="suli-muted" style="font-size:12px">秒</span>
          <el-select v-model="tier" size="small" class="w-agent-tier" placeholder="分级">
            <el-option v-for="t in tierOpts" :key="t.key" :label="t.label" :value="t.key" />
          </el-select>
        </div>
      </div>
    </div>
    <div v-if="answer" class="shot-prompt">{{ answer }}</div>
  </div>
</template>
<script setup lang="ts">
import SlotZoomImage from '../SlotZoomImage.vue'
const ask = defineModel<string>('ask', { required: true })
const total = defineModel<number>('total', { required: true })
const tier = defineModel<string>('tier', { required: true })
defineProps<{ img: { name: string; path: string; url: string } | null; loading: boolean; progress: string; answer: string; outlineMd: string; tierOpts: { key: string; label: string }[] }>()
defineEmits<{ (e: 'pick'): void; (e: 'clear'): void; (e: 'stop'): void; (e: 'outline'): void; (e: 'draft'): void }>()
</script>
<style scoped>
.agent-direct { margin-top: 8px; padding: 10px 12px; display: flex; flex-direction: column; gap: 8px; border-color: var(--suli-primary); }
.agent-head { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.agent-main { display: flex; gap: 12px; align-items: stretch; }
.agent-fields { flex: 1; display: flex; flex-direction: column; gap: 8px; min-width: 0; align-self: stretch; }
.agent-btn-row { margin-top: auto; }
.pic-box-lg { display: flex; flex-direction: column; gap: 6px; flex: 0 0 300px; width: 300px; }
.pic-actions { display: flex; gap: 2px; }
.shot-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.bar-spacer { flex: 1 1 auto; min-width: 4px; }
.w-agent-tier { width: 170px; }
.shot-prompt { font-size: 13px; white-space: pre-wrap; background: var(--el-fill-color-lighter); border-radius: 8px; padding: 10px; }
@media (max-width: 900px) { .pic-box-lg { flex: 0 0 auto; width: 100%; } }
</style>
