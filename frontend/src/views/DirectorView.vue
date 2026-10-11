<template>
  <div class="suli-card kun-page" style="padding:14px">
    <div class="eyebrow kana">監督 DIRECTOR</div>
    <h3>导演</h3>
    <div style="display:flex;gap:8px;flex-wrap:wrap">
      <el-button type="primary" @click="assemble" :loading="loading" :disabled="!store.shots.length">按选中镜组装</el-button>
      <el-button @click="assembleEp" :loading="loading" :disabled="!store.shots.length">按整集组装8-block</el-button>
    </div>
    <div v-if="loading"><div class="skeleton" /><div class="skeleton" style="margin-top:8px" /></div>
    <div v-else-if="!list.length" class="suli-muted" style="padding:18px 4px;font-size:13px">暂无提示词，先组装（按选中镜 / 按整集）</div>
    <div v-else style="margin-top:8px;display:flex;flex-direction:column;gap:8px">
      <div v-for="p in list" :key="p.shot_id" class="suli-card" style="padding:10px">
        <div style="display:flex;gap:8px;align-items:center"><b>{{ p.shot_id }}</b><span class="suli-muted">命中锁 {{ (p.locks_hit || []).join(',') || '无' }}</span><span style="flex:1" /><el-button size="small" @click="copy(p.assembled_en)">复制英文</el-button></div>
        <div style="font-size:13px;margin-top:6px;white-space:pre-wrap">{{ p.assembled_en }}</div>
      </div>
    </div>
    <div style="margin-top:10px">
      <b>执行回执</b>
      <span class="suli-muted" style="margin-left:8px">只存事实</span>
      <span style="float:right"><el-button size="small" @click="loadReceipts">刷新回执</el-button></span>
    </div>
    <div v-if="!receiptRows.length" class="suli-muted" style="padding:10px 4px;font-size:13px">暂无回执</div>
    <el-table v-else :data="receiptRows" size="small" style="margin-top:6px">
      <el-table-column prop="shot_id" label="镜" width="170" />
      <el-table-column prop="task_id" label="任务" width="170" />
      <el-table-column prop="engine" label="引擎" width="90" />
      <el-table-column prop="status" label="态" width="80" />
      <el-table-column prop="media_url" label="媒体" />
    </el-table>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import { useAppStore } from '../stores/app'
import { copyText } from '../utils/clipboard'
const store = useAppStore()
const prompts = ref<any>(null)
const loading = ref(false)
const list = computed(() => (prompts.value?.prompts || []) as any[])
async function assemble() {
  loading.value = true
  try { const ids = store.shots.map((s: any) => s.id); const r = await api.assemble(ids); prompts.value = r.data }
  finally { loading.value = false }
}
async function assembleEp() {
  loading.value = true
  try { const r = await api.assembleEpisode(store.episodeId, {}); prompts.value = r.data; ElMessage.success('8-block组装' + (r.data as any).count + '镜') }
  finally { loading.value = false }
}
function copy(t: string) { copyText(t) }
const receiptRows = ref<any[]>([])
async function loadReceipts() { try { const r = await api.receipts(); receiptRows.value = r.data } catch {} }
onMounted(loadReceipts)
</script>
