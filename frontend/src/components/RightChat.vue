<template>
  <div class="right">
    <div class="head"><h4 style="margin:0">Agent</h4><span style="flex:1" /><el-button size="small" circle @click="store.toggleRight()">›</el-button></div>
    <div style="display:flex;gap:6px;margin-top:8px;align-items:center">
      <el-segmented v-model="scope" :options="scopeOpts" size="small" @change="reload" />
      <span style="flex:1" />
      <el-button size="small" @click="ensure">新建</el-button>
    </div>
    <div v-if="loadingList"><div class="skeleton" style="margin-top:8px;height:40px" /></div>
    <el-empty v-else-if="!sessions.length" description="无会话" :image-size="48">
      <el-button size="small" type="primary" @click="ensure">新建会话</el-button>
    </el-empty>
    <div v-else style="margin-top:8px;display:flex;flex-direction:column;gap:6px">
      <div
        v-for="s in sessions" :key="s.key + s.dsh_session_id"
        class="suli-card conv" :class="{ active: curKey === s.key }"
        @click="pick(s)"
      >
        <div style="display:flex;gap:6px;align-items:center">
          <b style="font-size:13px">{{ s.key }}</b>
          <el-tag size="small" :type="s.dsh_session_id ? 'success' : 'info'">{{ s.dsh_session_id ? '进行中' : '未建' }}</el-tag>
        </div>
        <div class="suli-muted tnum" style="font-size:11px;margin-top:2px">{{ rel(s.last_active) }}</div>
      </div>
    </div>
    <el-input v-model="msg" placeholder="指令" @keyup.enter="send" style="margin-top:8px" />
    <div style="margin-top:8px;display:flex;gap:8px">
      <el-button type="primary" size="small" @click="send" :loading="loading" :disabled="!msg.trim() || !curKey">发送</el-button>
    </div>
    <div v-if="loading && progress" class="hint">{{ progress }}</div>
    <el-empty v-else-if="!turns.length" description="无对话" :image-size="64" />
    <div v-else style="margin-top:8px;display:flex;flex-direction:column;gap:8px">
      <div v-for="(t, i) in turns" :key="i" class="suli-card" style="padding:8px">
        <div style="font-size:12px;font-weight:700">› {{ t.q }}</div>
        <div style="font-size:12px;white-space:pre-wrap;margin-top:4px">{{ t.a }}</div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import { useAppStore } from '../stores/app'
const store = useAppStore()
const route = useRoute()
const scopeOpts = [
  { label: '故事', value: 'story' },
  { label: '角色', value: 'character' },
  { label: '分镜', value: 'episode' },
]
const scope = ref('episode')
const sessions = ref<any[]>([])
const curKey = ref('')
const curSid = ref('')
const msg = ref('')
const turns = ref<{ q: string; a: string }[]>([])
const loading = ref(false)
const loadingList = ref(false)
const progress = ref('')
function autoKey() {
  if (scope.value === 'character') return store.selectedCharId || 'global'
  if (scope.value === 'episode') return store.episodeId || 'global'
  return 'global'
}
function rel(ts: number) {
  if (!ts) return '未开始'
  const s = Math.floor((Date.now() - ts) / 1000)
  if (s < 60) return '刚刚'
  if (s < 3600) return Math.floor(s / 60) + '分钟前'
  if (s < 86400) return Math.floor(s / 3600) + '小时前'
  return Math.floor(s / 86400) + '天前'
}
function histKey() { return `dsh-turns:${scope.value}:${curKey.value || 'new'}` }
function loadLocal() { try { turns.value = JSON.parse(localStorage.getItem(histKey()) || '[]') } catch { turns.value = [] } }
function saveLocal() { try { localStorage.setItem(histKey(), JSON.stringify(turns.value.slice(-30))) } catch {} }
async function reload() {
  loadingList.value = true
  try {
    const r = await api.dshSessions(scope.value)
    sessions.value = r.data as any[]
    if (!sessions.value.find(s => s.key === curKey.value)) {
      curKey.value = (sessions.value[0] || {}).key || ''
      curSid.value = (sessions.value[0] || {}).dsh_session_id || ''
    } else {
      curSid.value = (sessions.value.find(s => s.key === curKey.value) || {}).dsh_session_id || ''
    }
    loadLocal()
  } catch { ElMessage.error('后端未起') }
  finally { loadingList.value = false }
}
async function ensure() {
  const k = autoKey()
  await api.dshEnsure(scope.value, k)
  await reload()
  curKey.value = k
  curSid.value = (sessions.value.find(s => s.key === k) || {}).dsh_session_id || ''
  loadLocal()
  ElMessage.success('已新建')
}
function pick(s: any) { curKey.value = s.key; curSid.value = s.dsh_session_id || ''; loadLocal() }
async function send() {
  if (!msg.value.trim() || loading.value || !curKey.value) return
  const q = msg.value.trim()
  msg.value = ''
  loading.value = true
  progress.value = '运行中…'
  try {
    let done: any = null
    let errMsg = ''
    await api.dshRunStream(
      { scope: scope.value, key: curKey.value, message: q, session_id: curSid.value || undefined },
      (ev, d) => {
        if (ev === 'dsh') progress.value = `运行中…事件 ${d.n || ''}`
        else if (ev === 'done') done = d
        else if (ev === 'error') errMsg = (d as any).msg || '调用失败'
      },
    )
    if (done) {
      if (done.session_id && done.session_id !== curSid.value) { curSid.value = done.session_id; await reload() }
      turns.value.push({ q, a: done.answer || '(空回包)' })
      saveLocal()
    } else {
      turns.value.push({ q, a: '❌ ' + (errMsg || '流中断') })
      ElMessage.error((errMsg || '流中断').slice(0, 120))
    }
  } catch {
    turns.value.push({ q, a: '❌ 流连接失败' })
    ElMessage.error('流连接失败')
  } finally { loading.value = false; progress.value = '' }
}
watch(() => [store.episodeId, store.selectedCharId, route.path], () => {
  if (route.path.startsWith('/character')) scope.value = 'character'
  else if (route.path.startsWith('/board')) scope.value = 'episode'
  else if (route.path.startsWith('/story')) scope.value = 'story'
  reload()
})
onMounted(reload)
</script>
<style scoped>
.right{width:440px;background:var(--suli-surface);border-left:1px solid var(--suli-border);padding:14px;overflow:auto;flex-shrink:0}
.head{display:flex;align-items:center}
.hint{font-size:12px;color:var(--suli-text-2);margin:6px 0}
.conv{padding:8px;cursor:pointer}
.conv.active{border-color:var(--suli-primary)}
</style>
