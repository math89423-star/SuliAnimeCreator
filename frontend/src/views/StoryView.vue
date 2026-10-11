<template>
  <div class="suli-card kun-page" style="padding:14px">
    <div class="eyebrow kana">ストーリー STORY</div>
    <h3>故事</h3>
    <el-input v-model="idea" type="textarea" :rows="3" placeholder="想法" />
    <div style="margin-top:8px;display:flex;gap:8px">
      <el-button type="primary" @click="suggest" :loading="loading">发散</el-button>
      <el-button @click="reloadConfirmed">已确认列表</el-button>
    </div>
    <el-empty v-if="!dirs.length && !loading" description="无方向" :image-size="64" />
    <div v-if="loading" style="margin-top:8px"><div class="skeleton" /><div class="skeleton" style="margin-top:8px" /></div>
    <div v-else class="suli-grid-3" style="margin-top:8px">
      <div v-for="d in dirs" :key="d.dir" class="suli-card" style="padding:10px">
        <b>方向{{ d.dir }}</b>
        <div style="font-size:13px;margin:6px 0">{{ d.logline }}</div>
        <div class="suli-muted">节拍：{{ (d.beats || []).join('→') }}</div>
        <div style="margin-top:8px;display:flex;gap:6px">
          <el-button size="small" type="primary" @click="confirm(d)">确认此方向</el-button>
          <el-button size="small" @click="copy(d.logline)">复制</el-button>
        </div>
      </div>
    </div>
    <div v-if="confirmed.length" style="margin-top:10px">
      <b>已确认（{{ confirmed.length }}）</b>
      <el-table :data="confirmed" style="margin-top:6px"><el-table-column prop="dir" label="方向" width="70" /><el-table-column prop="logline" label="logline" /></el-table>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import { copyText } from '../utils/clipboard'
const idea = ref('灰水村血税牢，星璃登场')
const drafts = ref<any>(null)
const confirmed = ref<any[]>([])
const loading = ref(false)
const dirs = computed(() => (drafts.value?.drafts || []) as any[])
async function suggest() {
  loading.value = true
  try { const r = await api.storySuggest(idea.value); drafts.value = r.data }
  catch { ElMessage.error('后端未起') }
  finally { loading.value = false }
}
async function confirm(d: any) {
  await api.storyConfirm(d)
  ElMessage.success('已确认方向' + d.dir)
  await reloadConfirmed()
}
async function reloadConfirmed() {
  try { const r = await api.storyList(); confirmed.value = (r.data as any).confirmed || [] }
  catch {}
}
function copy(t: string) { copyText(t) }
onMounted(reloadConfirmed)
</script>
