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
          <span class="suli-muted hide-mid">项目</span>
          <el-select v-model="store.projectId" placeholder="项目" class="hide-narrow top-sel-project" size="small">
            <el-option v-for="p in store.projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
          <el-button size="small" class="hide-narrow" @click="openProjectDialog('create')">新建</el-button>
          <el-button size="small" class="hide-narrow" :disabled="!store.projectId" @click="openProjectDialog('rename')">改名</el-button>
          <el-dropdown trigger="click" @command="confirmDeleteProject" class="hide-narrow">
            <el-button size="small" type="danger" plain :disabled="!store.projectId" :loading="deletingProject">删除</el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="detach">仅删除项目…</el-dropdown-item>
                <el-dropdown-item command="cascade" divided>删除项目及内容…</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <span class="suli-muted hide-mid">Episode</span>
          <el-select v-model="episodePick" filterable placeholder="选择集号" class="top-sel-episode" size="small" :loading="episodeLoading" @change="onEpisodePicked">
            <el-option
              v-for="e in episodeOptions"
              :key="e.id"
              :label="episodeOptionLabel(e)"
              :value="e.id"
            />
          </el-select>
          <el-button size="small" @click="openEpisodeDialog('create')">新建集</el-button>
          <el-dropdown trigger="click" @command="confirmDeleteEpisode">
            <el-button size="small" type="danger" plain :disabled="!episodePick || !store.projectId" :loading="deletingEpisode">删除集</el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="unregister">仅移出项目…</el-dropdown-item>
                <el-dropdown-item command="delete" divided>移出并删除内容…</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button v-if="route.path.startsWith('/traffic')" size="small" @click="store.openTrafficHist()">历史包</el-button>
          <span v-if="store.lastSavedAt" class="suli-muted tnum hide-narrow">已保存 {{ fmtTime(store.lastSavedAt) }}</span>
        </div>
      </div>
      <div class="center"><router-view :key="route.path + '|' + store.projectId + '|' + store.episodeId" /><el-backtop target=".center" :bottom="70" title="回顶部" /></div>
    </div>
    <RightChat v-if="showRight" />
    <div v-else-if="!hideRight" class="rail">
      <el-button circle @click="store.toggleRight()">‹</el-button>
    </div>
    <QuickRef />
    <el-dialog v-model="episodeDialog" title="集号管理" width="480px">
      <el-radio-group v-model="episodeMode" style="margin-bottom:12px">
        <el-radio-button label="create">新建集号</el-radio-button>
        <el-radio-button label="attach">加入已有集号</el-radio-button>
      </el-radio-group>
      <el-form label-width="100px">
        <el-form-item :label="episodeMode === 'create' ? '集号（可选）' : '集号'">
          <el-input v-model="episodeForm.episode_id" :placeholder="episodeMode === 'create' ? '留空自动生成 EP-XXXXXX' : '输入已有的集号，例如 EP-81695F'" />
        </el-form-item>
        <el-form-item label="标题（可选）">
          <el-input v-model="episodeForm.title" placeholder="例如 首集 · 星环第七格" maxlength="120" />
        </el-form-item>
      </el-form>
      <div class="suli-muted" style="font-size:12px">
        新建集号会自动归属当前项目并切换；加入已有集号若属于其他项目，需要二次确认迁移。
      </div>
      <template #footer>
        <el-button size="small" @click="episodeDialog = false">取消</el-button>
        <el-button size="small" type="primary" :loading="episodeSaving" @click="submitEpisodeDialog">确定</el-button>
      </template>
    </el-dialog>
    <el-dialog v-model="projectDialog" :title="projectMode === 'create' ? '新建项目' : '重命名项目'" width="420px">
      <el-form label-width="70px" @submit.prevent="submitProjectDialog">
        <el-form-item label="项目名">
          <el-input
            v-model="projectForm.name" placeholder="例如 星环第七格" maxlength="80" show-word-limit clearable
            @keydown.enter.prevent="submitProjectDialog"
          />
        </el-form-item>
      </el-form>
      <div class="suli-muted" style="font-size:12px">
        {{ projectMode === 'create' ? '创建后自动切换到新项目。' : '只改名，不切换项目、不动集号。' }}
      </div>
      <template #footer>
        <el-button size="small" @click="projectDialog = false">取消</el-button>
        <el-button size="small" type="primary" :loading="projectSaving" @click="submitProjectDialog">确定</el-button>
      </template>
    </el-dialog>
    <el-button
      v-if="!store.quickRef.open" class="qr-fab" circle size="large"
      :title="store.quickRef.minimized ? ('速查：' + store.quickRef.tool) : '速查本'"
      :style="{ right: fabRight }"
      @click="store.openQuickRef()"><el-icon><Notebook /></el-icon></el-button>
  </div>
  </el-config-provider>
</template>
<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Notebook } from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import LeftNav from './components/LeftNav.vue'
import RightChat from './components/RightChat.vue'
import QuickRef from './components/QuickRef.vue'
import { useAppStore } from './stores/app'
import { useSettingsStore } from './stores/settings'
import { api } from './api/client'
const store = useAppStore()
const settings = useSettingsStore()
const route = useRoute()
// 这一页要不要右侧 Agent 栏：路由 meta 说了算（设置页不挂），再叠上用户的折叠偏好
const hideRight = computed(() => route.meta.noRightChat === true)
const showRight = computed(() => !hideRight.value && !store.rightCollapsed)
// 速查球的位置：右侧 Agent 栏在时贴它的左边；本页没有 Agent 栏时贴窗口右边（内容让出这条道）
const fabRight = computed(() => (showRight.value ? '456px' : hideRight.value ? '16px' : '60px'))
const projectEpisodes = ref<any[]>([])
const episodeLoading = ref(false)
const episodePick = ref('')
const episodeDialog = ref(false)
const episodeMode = ref<'create' | 'attach'>('create')
const episodeForm = ref({ episode_id: '', title: '' })
const episodeSaving = ref(false)
const deletingProject = ref(false)
const deletingEpisode = ref(false)
let episodeReq = 0
const episodeOptions = computed(() => {
  const rows = [...projectEpisodes.value]
  if (store.episodeId && !rows.some(e => e.id === store.episodeId)) {
    rows.unshift({ id: store.episodeId, title: '未归属当前项目', unassigned: true })
  }
  return rows
})
function episodeOptionLabel(e: any) {
  const title = e.title && e.title !== e.id ? ` · ${e.title}` : ''
  const count = typeof e.shot_count === 'number' ? ` · ${e.shot_count}镜` : ''
  const scope = e.unassigned ? '（未归属）' : ''
  return `${e.id}${title}${count}${scope}`
}
function apiError(e: any, fallback: string) {
  return (e?.response?.data?.msg || e?.message || fallback).slice(0, 200)
}
function forgetCtx(pid: string) {
  if (!pid) return
  try {
    const m = readCtx()
    delete m[pid]
    writeCtx(m)
  } catch {}
}
function fmtTime(ts: number) {
  const d = new Date(ts)
  return String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0') + ':' + String(d.getSeconds()).padStart(2, '0')
}
async function loadProjects() {
  try {
    const r = await api.listProjects()
    store.projects = r.data
    if (!store.projectId && store.projects[0]) store.projectId = store.projects[0].id
  } catch {}
}
async function loadProjectEpisodes(pid: string = store.projectId) {
  const req = ++episodeReq
  projectEpisodes.value = []
  if (!pid) {
    episodePick.value = store.episodeId || ''
    return []
  }
  episodeLoading.value = true
  try {
    const r = await api.listProjectEpisodes(pid)
    if (req !== episodeReq) return projectEpisodes.value
    projectEpisodes.value = (r.data?.episodes || []) as any[]
    return projectEpisodes.value
  } catch {
    if (req === episodeReq) projectEpisodes.value = []
    return []
  } finally {
    if (req === episodeReq) episodeLoading.value = false
  }
}
async function syncBackendCurrent() {
  const pid = store.projectId
  const eid = store.episodeId
  if (!pid || !eid) return
  if (!projectEpisodes.value.some(e => e.id === eid)) return
  const row = (store.projects || []).find((p: any) => p.id === pid)
  if (row && row.current_episode_id === eid) return
  try {
    const r = await api.updateProject(pid, { current_episode_id: eid })
    const i = (store.projects || []).findIndex((p: any) => p.id === pid)
    if (i >= 0) store.projects[i] = r.data
  } catch {}
}
async function afterProjectSelected(pid: string) {
  await loadProjectEpisodes(pid)
  if (!pid) {
    episodePick.value = ''
    return
  }
  const backendCurrent = (store.projects.find((p: any) => p.id === pid) as any)?.current_episode_id || ''
  if (backendCurrent && backendCurrent !== store.episodeId) {
    store.episodeId = backendCurrent
    snapshotCtx(pid)
  } else {
    await syncBackendCurrent()
    snapshotCtx(pid)
  }
  episodePick.value = store.episodeId || ''
}
async function switchEpisode(eid: string) {
  const pid = store.projectId
  const target = (eid || '').trim()
  if (!pid) {
    episodePick.value = store.episodeId || ''
    return ElMessage.warning('先选择或新建项目')
  }
  if (!target) {
    episodePick.value = store.episodeId || ''
    return ElMessage.warning('请选择或新建集号')
  }
  if (target === store.episodeId) return
  try {
    await api.updateProject(pid, { current_episode_id: target })
    store.episodeId = target
    snapshotCtx(pid)
    episodePick.value = target
    ElMessage.success(`已切换到集号 ${target}`)
  } catch (e: any) {
    episodePick.value = store.episodeId || ''
    await loadProjectEpisodes(pid)
    ElMessage.error(apiError(e, '切换集号失败'))
  }
}
function onEpisodePicked(v: string) {
  void switchEpisode(v)
}
function openEpisodeDialog(mode: 'create' | 'attach') {
  if (!store.projectId) return ElMessage.warning('先选择或新建项目')
  episodeMode.value = mode
  episodeForm.value = {
    episode_id: mode === 'attach' ? store.episodeId || '' : '',
    title: '',
  }
  episodeDialog.value = true
}
async function submitEpisodeDialog() {
  const pid = store.projectId
  if (!pid) return ElMessage.warning('先选择或新建项目')
  const eid = (episodeForm.value.episode_id || '').trim()
  const title = (episodeForm.value.title || '').trim()
  if (episodeMode.value === 'attach' && !eid) return ElMessage.warning('请输入已有的集号')
  episodeSaving.value = true
  try {
    let r: any
    try {
      r = await api.createProjectEpisode(pid, { episode_id: eid || undefined, title: title || undefined })
    } catch (e: any) {
      const owner = /已属于项目 (\S+)/.exec(apiError(e, ''))?.[1] || ''
      if (e?.response?.status === 409 && owner && episodeMode.value === 'attach') {
        try {
          await ElMessageBox.confirm(`集号 ${eid} 已属于项目 ${owner}，是否迁移到当前项目？原项目只移除归属，不删除内容。`, '迁移集号', { type: 'warning', confirmButtonText: '迁移', cancelButtonText: '取消' })
        } catch { return }
        r = await api.createProjectEpisode(pid, { episode_id: eid, title: title || undefined, move: true })
      } else {
        throw e
      }
    }
    const created = r.data
    store.episodeId = created.id
    snapshotCtx(pid)
    await loadProjectEpisodes(pid)
    await syncBackendCurrent()
    episodePick.value = created.id
    episodeDialog.value = false
    ElMessage.success(`已切换到集号 ${created.id}`)
  } catch (e: any) {
    ElMessage.error(apiError(e, '集号操作失败'))
  } finally {
    episodeSaving.value = false
  }
}
async function confirmDeleteProject(mode: 'detach' | 'cascade') {
  const pid = store.projectId
  if (!pid) return ElMessage.warning('先选择项目')
  const target = (store.projects.find((p: any) => p.id === pid) as any) || { id: pid, name: pid }
  let episodes: any[] = []
  let receiptCount = 0
  try {
    const r = await api.listProjectEpisodes(pid)
    episodes = (r.data?.episodes || []) as any[]
  } catch {
    episodes = []
  }
  try {
    const r = await api.receipts({ project_id: pid })
    receiptCount = ((r as any)?.data || []).length
  } catch {
    receiptCount = 0
  }
  const shots = episodes.reduce((n: number, e: any) => n + (Number(e.shot_count) || 0), 0)
  const detail = mode === 'cascade'
    ? `将删除项目「${target.name}」及其 ${episodes.length} 个集号的内容、${shots} 镜分镜、${receiptCount} 条回执和相关会话映射（上传文件保留）。此操作不可恢复。`
    : `将删除项目「${target.name}」本身；${episodes.length} 个集号内容、${shots} 镜分镜和 ${receiptCount} 条回执会保留。`
  try {
    await ElMessageBox.confirm(detail, '删除项目', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch {
    return
  }
  deletingProject.value = true
  try {
    const r = await api.deleteProject(pid, mode)
    const deleted = (r as any)?.data || {}
    store.projects = (store.projects || []).filter((p: any) => p.id !== pid)
    forgetCtx(pid)
    const next = (store.projects[0] as any)?.id || ''
    store.projectId = next
    ElMessage.success(mode === 'cascade'
      ? `已删除项目及内容：${(deleted.episodes || []).length}集 / ${deleted.shots || 0}镜 / ${deleted.receipts || 0}条回执`
      : '已删除项目，内容已保留')
  } catch (e: any) {
    ElMessage.error(apiError(e, '删除项目失败'))
  } finally {
    deletingProject.value = false
  }
}
async function confirmDeleteEpisode(mode: 'unregister' | 'delete') {
  const pid = store.projectId
  const eid = episodePick.value || store.episodeId
  if (!pid) return ElMessage.warning('先选择项目')
  if (!eid) return ElMessage.warning('请选择或新建集号')
  const target = projectEpisodes.value.find((e: any) => e.id === eid) as any
  const title = target?.title && target.title !== eid ? ` · ${target.title}` : ''
  const shots = Number(target?.shot_count) || 0
  const detail = mode === 'delete'
    ? `将把集号 ${eid}${title} 移出当前项目，并删除其内容、${shots} 镜分镜及相关回执和会话映射（上传文件保留）。此操作不可恢复。`
    : `将把集号 ${eid}${title} 移出当前项目；其内容、${shots} 镜分镜和回执会保留，可稍后重新加入。`
  try {
    await ElMessageBox.confirm(detail, '删除集号', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch {
    return
  }
  deletingEpisode.value = true
  try {
    await api.removeProjectEpisode(pid, eid, mode)
    await loadProjectEpisodes(pid)
    const remaining = projectEpisodes.value
    const next = remaining.some((e: any) => e.id === store.episodeId && e.id !== eid) ? store.episodeId : (remaining[0]?.id || '')
    // 如果删的是当前集，切到下一集或清空；删的是其他集，保持当前集并同步后端 current
    if (eid === store.episodeId) {
      store.episodeId = next
      snapshotCtx(pid)
      episodePick.value = next
      if (next) await syncBackendCurrent()
    } else {
      episodePick.value = store.episodeId || ''
    }
    ElMessage.success(mode === 'delete' ? `已删除集号 ${eid} 及内容` : `已将集号 ${eid} 移出项目`)
  } catch (e: any) {
    ElMessage.error(apiError(e, '删除集号失败'))
    await loadProjectEpisodes(pid)
    episodePick.value = store.episodeId || ''
  } finally {
    deletingEpisode.value = false
  }
}
const projectDialog = ref(false)
const projectMode = ref<'create' | 'rename'>('create')
const projectForm = ref({ name: '' })
const projectSaving = ref(false)
function defaultProjectName() {
  return '新项目' + new Date().toISOString().slice(5, 10)
}
function openProjectDialog(mode: 'create' | 'rename') {
  if (mode === 'rename' && !store.projectId) return ElMessage.warning('先选择项目')
  projectMode.value = mode
  if (mode === 'create') {
    projectForm.value = { name: defaultProjectName() }
  } else {
    const cur = (store.projects.find((p: any) => p.id === store.projectId) as any) || { name: '' }
    projectForm.value = { name: cur.name || '' }
  }
  projectDialog.value = true
}
async function submitProjectDialog() {
  const name = (projectForm.value.name || '').trim()
  if (!name) return ElMessage.warning('项目名不能为空')
  projectSaving.value = true
  try {
    if (projectMode.value === 'create') {
      const r = await api.createProject(name)
      store.projects.unshift(r.data)
      // 只改 projectId：下面的 watcher 会先快照旧现场、再给新项目铺干净现场（顺序不能反，否则快照到的是清空后的状态）
      store.projectId = r.data.id
      projectDialog.value = false
      ElMessage.success('已新建并切换：' + (r.data.name || r.data.id))
    } else {
      const pid = store.projectId
      const r = await api.updateProject(pid, { name })
      const i = (store.projects || []).findIndex((p: any) => p.id === pid)
      if (i >= 0) store.projects[i] = r.data
      projectDialog.value = false
      ElMessage.success('已改名：' + (r.data.name || pid))
    }
  } catch (e: any) {
    ElMessage.error(apiError(e, projectMode.value === 'create' ? '新建项目失败' : '改名失败'))
  } finally {
    projectSaving.value = false
  }
}
// 项目 ↔ 工作现场绑定：每个项目记住自己的 Episode + 当前角色。
// 以前项目只是顶栏标签（点了跟没点一样）；现在新建/换项目时整个工作区一起换。
const PROJ_CTX_KEY = 'suli.projectCtx'
function readCtx(): Record<string, { episodeId: string; charId: string }> {
  try { return JSON.parse(localStorage.getItem(PROJ_CTX_KEY) || '{}') } catch { return {} }
}
function writeCtx(m: Record<string, { episodeId: string; charId: string }>) {
  try { localStorage.setItem(PROJ_CTX_KEY, JSON.stringify(m)) } catch {}
}
function snapshotCtx(pid: string) {
  if (!pid) return
  const m = readCtx()
  m[pid] = { episodeId: store.episodeId || '', charId: store.selectedCharId || '' }
  writeCtx(m)
}
function applyCtx(pid: string, fresh = false) {
  const m = readCtx()
  const c = (!fresh && pid) ? m[pid] : null
  if (c) {
    store.episodeId = c.episodeId || ''
    store.selectedCharId = c.charId || ''
  } else {
    store.episodeId = ''
    store.selectedCharId = ''
    if (pid) { m[pid] = { episodeId: '', charId: '' }; writeCtx(m) }
  }
}
watch(() => store.projectId, async (nv, ov) => {
  if (!ov || nv === ov) return
  snapshotCtx(ov)
  applyCtx(nv || '')
  await afterProjectSelected(nv || '')
})
watch(() => store.episodeId, (v) => {
  if ((v || '') !== episodePick.value) episodePick.value = v || ''
})
onMounted(async () => {
  try { settings.apply() } catch {}
  store.leftCollapsed = settings.settings.leftCollapsed
  store.rightCollapsed = settings.settings.rightCollapsed
  if (!store.episodeId && settings.settings.defaultEpisode) store.episodeId = settings.settings.defaultEpisode
  try { store.health = (await api.health()).data } catch {} await loadProjects()
  // 启动时回到本项目的工作现场（有记录就恢复，没有就把现状记下来）
  if (store.projectId) {
    const c = readCtx()[store.projectId]
    if (c) { store.episodeId = c.episodeId || ''; store.selectedCharId = c.charId || '' }
    else snapshotCtx(store.projectId)
    await afterProjectSelected(store.projectId)
  } else {
    episodePick.value = store.episodeId || ''
  }
})
</script>
<style>
html,body,#app{height:100%;margin:0;overflow:hidden}
.shell{display:flex;height:100vh;max-height:100vh;overflow:hidden;background:var(--suli-bg)}
.main{flex:1;display:flex;flex-direction:column;min-width:0}
.topbar{margin:12px 12px 0;padding:8px 12px;display:flex;flex-direction:column;gap:6px}
.topbar-row{display:flex;gap:8px;align-items:center;width:100%}
/* 顶栏不许被挤成竖排：标签不换行、选择器可缩但不塌 */
.topbar-row .el-breadcrumb{flex:0 0 auto;white-space:nowrap}
.topbar-row .suli-muted{white-space:nowrap}
.top-sel-project{width:140px;min-width:96px;flex:0 1 auto}
.top-sel-episode{width:150px;min-width:110px;flex:0 1 auto}
.topbar-steps{display:flex;gap:8px;align-items:center;width:100%;border-top:1px solid var(--suli-border);padding-top:6px}
.topbar-steps .el-steps{flex:1}
.center{flex:1;padding:12px;overflow:auto}
.rail{width:44px;display:flex;align-items:flex-start;justify-content:center;padding-top:12px}
.qr-fab{position:fixed;bottom:16px;z-index:1890;box-shadow:var(--suli-shadow);background:var(--suli-surface)}
@media (max-width: 1100px) { .topbar-steps{max-width:340px} }
@media (max-width: 900px) { .topbar-steps, .hide-narrow{display:none} }
/* 中等宽度：顶栏标签先让位（选择器本身带占位文字，语义不丢） */
@media (max-width: 1500px) { .hide-mid{display:none} }
</style>
