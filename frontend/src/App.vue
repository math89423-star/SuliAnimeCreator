<template>
  <el-config-provider :locale="zhCn">
  <div class="shell bg-radial">
    <LeftNav v-if="!store.leftCollapsed" />
    <div v-else class="rail">
      <el-button circle @click="store.toggleLeft()">›</el-button>
    </div>
    <div class="main">
      <div class="topbar suli-card">
        <div class="topbar-row">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>SuliAnimeCreator</el-breadcrumb-item>
            <el-breadcrumb-item>{{ route.meta.title || '工作台' }}</el-breadcrumb-item>
          </el-breadcrumb>
          <span style="flex:1" />
          <span class="suli-muted hide-narrow">项目</span>
          <el-select v-model="store.projectId" placeholder="项目" class="hide-narrow" style="width:140px" size="small">
            <el-option v-for="p in store.projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
          <el-button size="small" class="hide-narrow" @click="newProject">新建</el-button>
          <span class="suli-muted">Episode</span>
          <el-input v-model="store.episodeId" style="width:110px" size="small" />
          <span v-if="store.lastSavedAt" class="suli-muted tnum hide-narrow">已保存 {{ fmtTime(store.lastSavedAt) }}</span>
          <el-button size="small" circle title="刷新后端状态" @click="refresh"><el-icon><Refresh /></el-icon></el-button>
          <el-button size="small" circle title="帮助" @click="store.toggleRight()"><el-icon><QuestionFilled /></el-icon></el-button>
          <div class="user" title="本地用户"><el-icon><UserFilled /></el-icon></div>
        </div>
      </div>
      <div class="center"><router-view /><el-backtop target=".center" :bottom="70" title="回顶部" /></div>
    </div>
    <RightChat v-if="!store.rightCollapsed" />
    <div v-else class="rail">
      <el-button circle @click="store.toggleRight()">‹</el-button>
    </div>
    <QuickRef />
    <el-button
      v-if="!store.quickRef.open" class="qr-fab" circle size="large"
      :title="store.quickRef.minimized ? ('速查：' + store.quickRef.tool) : '速查本'"
      :style="{ right: store.rightCollapsed ? '60px' : '456px' }"
      @click="store.openQuickRef()">📖</el-button>
  </div>
  </el-config-provider>
</template>
<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, QuestionFilled, UserFilled } from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import LeftNav from './components/LeftNav.vue'
import RightChat from './components/RightChat.vue'
import QuickRef from './components/QuickRef.vue'
import { useAppStore } from './stores/app'
import { api } from './api/client'
const store = useAppStore()
const route = useRoute()
function fmtTime(ts: number) {
  const d = new Date(ts)
  return String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0') + ':' + String(d.getSeconds()).padStart(2, '0')
}
async function refresh() {
  try { store.health = (await api.health()).data; ElMessage.success('后端已接通') }
  catch { store.health = null; ElMessage.error('后端未起：后端 python run.py ＋ 前端 npm run dev') }
}
async function loadProjects() {
  try {
    const r = await api.listProjects()
    store.projects = r.data
    if (!store.projectId && store.projects[0]) store.projectId = store.projects[0].id
  } catch {}
}
async function newProject() {
  const r = await api.createProject('新项目' + new Date().toISOString().slice(5, 10))
  store.projects.unshift(r.data)
  store.projectId = r.data.id
}
onMounted(async () => { try { store.health = (await api.health()).data } catch {} await loadProjects() })
</script>
<style>
html,body,#app{height:100%;margin:0}
.shell{display:flex;height:100vh;background:var(--suli-bg)}
.main{flex:1;display:flex;flex-direction:column;min-width:0}
.topbar{margin:12px 12px 0;padding:8px 12px;display:flex;flex-direction:column;gap:6px}
.topbar-row{display:flex;gap:8px;align-items:center;width:100%}
.topbar-steps{display:flex;gap:8px;align-items:center;width:100%;border-top:1px solid var(--suli-border);padding-top:6px}
.topbar-steps .el-steps{flex:1}
.center{flex:1;padding:12px 16px;overflow:auto}
.rail{width:44px;display:flex;align-items:flex-start;justify-content:center;padding-top:12px}
.user{width:28px;height:28px;border-radius:50%;background:var(--suli-surface-2);border:1px solid var(--suli-border);display:flex;align-items:center;justify-content:center}
.qr-fab{position:fixed;bottom:16px;z-index:1890;box-shadow:var(--suli-shadow);background:var(--suli-surface)}
@media (max-width: 1100px) { .topbar-steps{max-width:340px} }
@media (max-width: 900px) { .topbar-steps, .hide-narrow{display:none} }
</style>
