<template>
  <div class="suli-card kun-page director">
    <div class="dir-head">
      <h3 style="margin:0">导演 · 动画</h3>
      <el-tag size="small" class="tnum">{{ store.episodeId }}</el-tag>
    </div>
    <el-tabs v-model="dtab" class="dir-tabs">
      <el-tab-pane label="剧本" name="script">
        <div class="script-refs top">
          <span class="suli-muted" style="font-size:12px">参考图</span>
          <span v-for="im in scriptRefs" :key="im.name" class="shot-refwrap col">
            <el-image :src="imgUrl(im.name)" :preview-src-list="[imgUrl(im.name)]" fit="cover" class="shot-thumb sm" preview-teleported />
            <span class="ref-label-row">
              <span
                v-if="editingRef !== im.name" class="ref-label" :title="im.label || im.name"
                @click="editingRef = im.name; refLabelText = im.label || ''"
              >{{ im.label || '未命名' }}</span>
              <el-input
                v-else v-model="refLabelText" size="small" class="ref-input" placeholder="命名"
                maxlength="40" @keydown.enter="saveRefLabel(im)" @keydown.esc="editingRef = ''" @blur="saveRefLabel(im)"
              />
              <el-button link type="danger" @click="delScriptRef(im.name)">×</el-button>
            </span>
          </span>
          <el-button link type="primary" @click="scriptFileEl?.click()">+参考图</el-button>
        </div>
        <input ref="scriptFileEl" type="file" accept="image/*" hidden @change="onScriptRef" />
        <el-input v-model="script" type="textarea" :rows="22" />
        <div class="script-foot">
          <div class="foot-actions">
            <el-button size="small" @click="() => saveScript()" :loading="scriptSaving">保存剧本</el-button>
            <el-button size="small" type="primary" @click="genOutline" :loading="agentLoading">生成</el-button>
            <el-popconfirm title="清空剧本，并连带清理大纲和全部草案？此操作不可恢复" confirm-button-text="清空" cancel-button-text="留着" @confirm="clearScript">
              <template #reference><el-button size="small" type="danger" text :loading="clearingScript">清空</el-button></template>
            </el-popconfirm>
          </div>
          <div class="foot-status">
            <span v-if="scriptSaving" class="st"><LoadingSpinner :size="12" /> 保存中…</span>
            <span v-else-if="scriptSaveErr" class="st err"><i class="dot"></i>保存失败：{{ scriptSaveErr }}</span>
            <span v-else-if="scriptDirty" class="st warn"><i class="dot"></i>未保存</span>
            <span v-else-if="scriptSavedAt" class="st ok"><i class="dot"></i>已保存 {{ scriptSavedAt }}</span>
          </div>
          <span class="suli-muted tnum foot-count">{{ script.length }}字</span>
        </div>
      </el-tab-pane>
      <el-tab-pane label="大纲" name="outline">
        <input ref="outlineFileEl" type="file" accept="image/*" hidden @change="onScriptRef" />
        <el-empty v-if="!outline.md" description="暂无大纲" :image-size="64">
          <el-button size="small" type="primary" @click="dtab = 'script'">去剧本</el-button>
        </el-empty>
        <div v-if="outline.md" class="suli-card outline-card">
          <div class="outline-head"><b>方案大纲</b><el-button size="small" text @click="outlineFileEl?.click()" title="上传参考图（与「剧本」页签同一清单，可作大纲/手帧参考）">+参考图</el-button><el-button size="small" text @click="outlineFolded = !outlineFolded">{{ outlineFolded ? '▶ 展开' : '▼ 收起' }}</el-button><el-button size="small" text @click="toggleOutlineEdit">{{ outlineEditing ? '预览' : '编辑' }}</el-button><el-button v-if="outlineEditing" size="small" type="primary" @click="saveOutlineEdit" :loading="outlineSaving">保存</el-button><span style="flex:1" /><el-button size="small" text @click="zoomOutline(-0.1)">A-</el-button><el-button size="small" text @click="resetOutlineZoom" title="重置缩放">{{ Math.round(outlineZoom * 100) }}%</el-button><el-button size="small" text @click="zoomOutline(0.1)">A+</el-button><el-button v-if="agentLoading" size="small" @click="stopAgent">停止</el-button><el-button size="small" @click="regenOutline" :loading="agentLoading">重新生成</el-button><el-dropdown trigger="click" @command="onDraftMode">
            <el-button size="small" type="primary" :loading="agentLoading || draftLiteLoading">② 生成草案<el-icon style="margin-left:4px"><ArrowDown /></el-icon></el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="lite"><el-icon style="margin-right:4px"><Lightning /></el-icon><b>快速模式</b></el-dropdown-item>
                <el-dropdown-item command="expert"><el-icon style="margin-right:4px"><MagicStick /></el-icon><b>专家模式</b></el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown><el-popconfirm title="清空大纲，并连带清理全部草案？此操作不可恢复" confirm-button-text="清空" cancel-button-text="留着" @confirm="clearOutline"><template #reference><el-button size="small" type="danger" text :loading="clearingOutline">清空</el-button></template></el-popconfirm></div>
          <div v-show="!outlineFolded" class="outline-main">
            <el-image v-if="outline.image" :src="`/api/images/${outline.image}`" class="outline-thumb" fit="cover" :preview-src-list="[`/api/images/${outline.image}`]" preview-teleported />
            <div v-if="!outlineEditing" class="outline-textwrap">
              <MarkdownView class="outline-text" :content="outline.md" :style="{ zoom: outlineZoom, maxHeight: outlineMaxH + 'px' }" />
              <div class="outline-rz" title="上下拖动调整高度，双击恢复默认" @mousedown="startOutlineResize" @dblclick="resetOutlineMaxH" />
            </div>
            <div v-else class="outline-editwrap">
              <el-input v-model="outlineDraft" type="textarea" :rows="16" />
              <div style="display:flex;gap:8px;align-items:center">
                <el-tag v-if="outlineDirty" size="small" type="warning">未存*</el-tag>
                <span style="flex:1" />
                <span class="suli-muted tnum" style="font-size:12px">{{ outlineDraft.length }}字</span>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
      <el-tab-pane label="提示词" name="prompts">
        <div class="prompt-head">
          <span class="suli-muted tnum" style="font-size:12px">已回传 {{ lpDoneCount }}/{{ store.shots.length }}</span>
          <span style="flex:1" />
          <el-button size="small" @click="reloadPrompts" :loading="promptRefreshing">刷新</el-button>
          <el-button size="small" type="primary" plain :disabled="!lpDoneCount" @click="copyAllPrompts">复制全部</el-button>
        </div>
      <!-- 组装工具条：动作在左，设置在右 -->
      <div class="dir-bar">
        <div class="bar-group">
          <el-button type="primary" size="small" @click="downloadBundle" :loading="bundleLoading" :disabled="!store.episodeId" title="L-Port 上传草案包用的 ZIP（manifest+shots+prompts+图）">导出草案包ZIP</el-button>
          <el-button size="small" @click="downloadDraft" :loading="docLoading" :disabled="!store.episodeId" title="人读版交接文档（.md，L-Port 上传请用左边 ZIP）">草案文档</el-button>
          <el-button size="small" type="success" plain @click="pushToLport" :loading="pushing" :disabled="!store.episodeId" title="自动投递到 L-Port 收件箱 suli_packages，投完自动等回执">直投 L-Port</el-button>
          <el-popconfirm title="清空本集全部草案分镜？此操作不可恢复" confirm-button-text="清空" cancel-button-text="留着" @confirm="clearShots">
            <template #reference><el-button size="small" type="danger" :loading="clearing" :disabled="!store.shots.length">清空</el-button></template>
          </el-popconfirm>
        </div>
        <span class="bar-spacer" />
        <div class="bar-group">
          <el-select v-model="globalTier" size="small" class="w-tier" placeholder="分级" title="不选则按内容自动推导：分镜分级栏 → 大纲档位行">
            <el-option v-for="t in tierOpts" :key="t.key" :label="t.label" :value="t.key" />
          </el-select>
          <el-select v-model="engine" size="small" class="w-engine" placeholder="引擎">
            <el-option v-for="e in engineOpts" :key="e.key" :label="e.label" :value="e.key" />
          </el-select>
          <el-select v-if="engine === 'pixai'" v-model="pixaiModel" size="small" class="w-model" placeholder="型号">
            <el-option v-for="m in pixaiModels" :key="m.key" :label="m.label" :value="m.key" />
          </el-select>
          <el-select v-if="engine === 'pixai'" v-model="refMode" size="small" class="w-ref">
            <el-option label="首尾帧" value="startframe" />
            <el-option v-if="refSupportsMulti" label="参考图" value="reference" />
          </el-select>
        </div>
      </div>
      <div v-if="pushing" class="push-status">
        <LoadingSpinner :size="14" />
        <span class="suli-muted" style="font-size:12px">正在投递到 L-Port 收件箱…</span>
      </div>
      <div v-for="p in curPushes" :key="p.pkg" class="push-status">
        <LoadingSpinner v-if="!p.done" :size="14" />
        <span v-else class="push-dot ok" />
        <span class="suli-muted tnum" style="font-size:12px">{{ pushLine(p) }}</span>
        <el-button v-if="p.done" size="small" link @click="stopWait(p.pkg)">关闭</el-button>
        <el-button v-else size="small" link @click="stopWait(p.pkg)">停止等待</el-button>
      </div>
      <div v-if="otherPushCount" class="push-status">
        <span class="suli-muted" style="font-size:12px">另有 {{ otherPushCount }} 个其他集投递在等回执</span>
      </div>
        <el-empty v-if="!store.shots.length" description="暂无分镜" :image-size="64">
          <el-button size="small" type="primary" @click="dtab = 'outline'">去大纲页生成草案</el-button>
        </el-empty>
        <div v-else class="prompt-list">
          <div v-for="(r, i) in promptRows" :key="r.id" class="prompt-row">
            <div class="pr-left">
              <span class="pr-no tnum">{{ String(i + 1).padStart(2, '0') }}</span>
              <span class="pr-sid">{{ r.id }}</span>
              <span class="tnum pr-dur">{{ r.duration_s }}s</span>
              <el-tag size="small" :type="r.lp ? 'success' : 'info'">{{ r.lp ? '已回传' : '未回传' }}</el-tag>
              <div class="pr-thumb" :class="{ on: imgMode[r.id] }" @click="toggleImg(r)">
                <el-image v-if="thumbOf(r)" :src="imgUrl(thumbOf(r).name)" fit="cover" />
                <div v-else class="pr-thumb-empty">无图</div>
                <span class="pr-thumb-tag">{{ imgMode[r.id] ? '图像' : '视频' }}</span>
              </div>
            </div>
            <template v-if="imgMode[r.id]">
              <div class="pr-body">
                <div v-if="!r.img" class="pr-empty">该镜还没有出图方案</div>
                <template v-else>
                  <div class="pr-line">
                    <b class="pr-k">方案</b>
                    <span class="pr-v">{{ r.img.title || r.img.plan_id }} · {{ r.img.status }}<template v-if="r.img.tier"> · {{ r.img.tier }}</template><template v-if="r.img.clothing_level"> · {{ r.img.clothing_level }}</template></span>
                  </div>
                  <div v-for="(eng, k) in r.img.prompts" :key="k" class="pr-eng">
                    <div class="pr-line"><b class="pr-k">{{ k }}</b><span class="pr-v pr-video">{{ eng.positive || '—' }}</span></div>
                    <div v-if="eng.negative" class="pr-line"><b class="pr-k">负向</b><span class="pr-v">{{ eng.negative }}</span></div>
                  </div>
                  <div v-if="!Object.keys(r.img.prompts || {}).length" class="pr-empty">方案还没回传提示词</div>
                </template>
              </div>
            </template>
            <template v-else>
            <div v-if="r.lpv" class="pr-body">
              <div class="pr-line">
                <b class="pr-k">视频提示词</b>
                <div class="pr-v" style="flex:1;min-width:0">
                  <el-input v-model="vpDrafts[r.id]" type="textarea" :autosize="{ minRows: 4, maxRows: 18 }" resize="vertical" />
                </div>
              </div>
              <div class="pr-line">
                <b class="pr-k">参数</b>
                <span class="pr-v">{{ r.lpv.engine || '—' }}<template v-if="r.lpv.video_model"> · {{ r.lpv.video_model }}</template> · {{ genModeText(r) }} · {{ r.lpv.duration_s }}s<template v-if="r.lpv.tier"> · {{ r.lpv.tier }}</template></span>
                <el-tag v-if="r.lpv.edited" size="small" type="warning">人工改</el-tag>
              </div>
              <div v-if="(r.images || []).length" class="pr-line pr-refs-row">
                <b class="pr-k">参考图</b>
                <div class="pr-v pr-refs">
                  <div v-for="im in r.images" :key="im.kind + im.name" class="pr-ref">
                    <el-image :src="imgUrl(im.name)" class="pr-ref-thumb" fit="cover" :preview-src-list="[imgUrl(im.name)]" preview-teleported />
                    <el-tag size="small" :type="im.kind === 'first' ? 'danger' : 'info'" effect="plain">{{ REF_KIND[im.kind] || im.kind }}</el-tag>
                    <el-select v-if="im.kind !== 'first'" v-model="refDraft(r.id, im.name).role" size="small" class="pr-ref-role" placeholder="role">
                      <el-option v-for="rk in REF_ROLE_KEYS" :key="rk" :label="REF_ROLE[rk]" :value="rk" />
                    </el-select>
                    <el-input v-model="refDraft(r.id, im.name).desc" size="small" class="pr-ref-desc" placeholder="desc" />
                    <el-button size="small" text :disabled="!refDirty(r.id, im)" @click="saveRef(r.id, im)">保存</el-button>
                  </div>
                </div>
              </div>
              <div v-if="(r.lpv.applied || []).length" class="pr-line"><b class="pr-k">调整</b><span class="pr-v">{{ (r.lpv.applied || []).join('；') }}</span></div>
              <div v-if="r.lpv.ref_note" class="pr-line"><b class="pr-k">参考</b><span class="pr-v">{{ r.lpv.ref_note }}</span></div>
              <div class="pr-meta">L-Port 定稿 · {{ r.lpv.source }}<template v-if="r.lpv.package_id"> · {{ r.lpv.package_id }}</template> · {{ r.lpv.at }}<template v-if="r.lpv.edited_at"> · 改于 {{ r.lpv.edited_at }}</template></div>
            </div>
            <div v-if="r.lp" class="pr-body">
              <div class="pr-line"><b class="pr-k">导演提示词</b><span class="pr-v">{{ r.lp.director_cn || '—' }}</span></div>
              <div v-if="r.lp.camera_note" class="pr-line"><b class="pr-k">镜头</b><span class="pr-v">{{ r.lp.camera_note }}</span></div>
              <div v-if="r.lp.key_text_en" class="pr-line"><b class="pr-k">英文关键帧</b><span class="pr-v">{{ r.lp.key_text_en }}</span></div>
              <div v-if="(r.lp.ref_missing || []).length" class="pr-line"><b class="pr-k">参考待补</b><span class="pr-v">{{ (r.lp.ref_missing || []).join('、') }}</span></div>
              <div class="pr-meta">来源 {{ r.lp.source }}<template v-if="r.lp.package_id"> · {{ r.lp.package_id }}</template> · {{ r.lp.at }}</div>
            </div>
            <div v-if="!r.lp && !r.lpv" class="pr-body pr-empty">—</div>
            </template>
            <div class="pr-right">
              <el-button v-if="r.lp || r.lpv" size="small" @click="copyPrompt(r)">复制</el-button>
              <el-button v-if="r.lpv" size="small" type="primary" :disabled="!vpDirty(r)" @click="saveVp(r)">保存</el-button>
              <el-button v-if="r.lpv?.edited" size="small" @click="unlockVp(r)">解锁</el-button>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api/client'
import { directorApi } from '../api/director'
import { useAppStore } from '../stores/app'
import { useSettingsStore } from '../stores/settings'
import { useAgentDirect } from '../composables/useAgentDirect'
import { ArrowDown, Lightning, MagicStick } from '@element-plus/icons-vue'
import MarkdownView from '../components/MarkdownView.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import { castNames, loadCastInput } from '../utils/cast'

const store = useAppStore()
const settings = useSettingsStore()

// 分级四档（真源在后端 /director/tiers）：'' = 按镜设置
const tierOpts = ref<{ key: string; label: string }[]>([{ key: '', label: '不分级' }])
const agentTier = ref('')
const globalTier = ref('')
// 目标引擎：默认 PixAI 视频（v4.0 系列）；h3 = MiniMax 字段格式
const engineOpts = ref<{ key: string; label: string }[]>([{ key: 'pixai', label: 'PixAI 视频' }])
const engine = ref('pixai')
const refMode = ref('startframe')
// PixAI 视频各型号能力不同（时长上限/有无音频/参考图语义），组装时透传给后端
const pixaiModels = ref<any[]>([
  { key: 'tsubaki-video', label: 'Tsubaki Video', ref: 'multi' },
  { key: 'tsubaki-video-flash', label: 'Tsubaki Video Flash', ref: 'multi' },
  { key: 'v4', label: 'V4.0 Preview / Lite', ref: 'multi' },
  { key: 'v3.2', label: 'V3.2', ref: 'startframe' },
  { key: 'v3.0', label: 'V3.0 Lite', ref: 'startframe' },
  { key: 'v2.7', label: 'V2.7 HD', ref: 'startframe' },
])
const pixaiModel = ref('tsubaki-video')
const refSupportsMulti = computed(() => (pixaiModels.value.find(m => m.key === pixaiModel.value) || {}).ref === 'multi')
function assembleParams() { return { tier: globalTier.value, engine: engine.value, ref_mode: refMode.value, pixai_model: pixaiModel.value } }
const dtab = ref('outline')

// 剧本页（与分镜页同一份后端数据）
const script = ref('')
const savedScript = ref('')
const scriptLoadedFor = ref('')   // 文本框里的稿属于哪一集（防跨集误写/误清）
const scriptDirty = computed(() => script.value !== savedScript.value)
let suspendScriptWatch = false
let scriptTimer: any = null
const scriptSaving = ref(false)
const scriptSavedAt = ref('')
const scriptSaveErr = ref('')
const scriptClearing = ref(false)
async function saveScript(silent = false, force = false) {
  if (scriptClearing.value) return          // 清空进行中：连 3s 自动保存一起丢，别把稿写回来
  const eid = store.episodeId
  // 集号切走（或本页还没为当前集加载过）时先把新集读回来 —— 否则会把上一集的稿/空内容写进当前集
  if (!eid || (scriptLoadedFor.value && scriptLoadedFor.value !== eid)) { await loadScript(); return }
  // 自动保存（切页/切集 debounce 触发）绝不允许把非空剧本写空；要清空只能手动 + 二次确认 + force
  if (silent && !script.value.trim()) return
  if (!script.value.trim() && savedScript.value.trim() && !force) {
    try {
      await ElMessageBox.confirm('这会清空本集剧本正文（不可撤销），确定？', '清空剧本',
        { confirmButtonText: '清空', cancelButtonText: '取消', type: 'warning' })
    } catch { return }
    force = true
  }
  scriptSaving.value = true
  try {
    const r: any = await api.saveScreenplay(eid, script.value, force ? { force: true } : {})
    if (r?.data?.kept) {
      // 后端拒绝了空覆盖：把库里的真稿读回来，别让界面留个空框
      scriptSaveErr.value = r.data.msg || '空内容被拒绝覆盖'
      ElMessage.warning(`已拒绝空内容覆盖，剧本仍是 ${r.data.chars} 字`)
      await loadScript()
      return
    }
    if (scriptClearing.value) return
    savedScript.value = script.value
    scriptSavedAt.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
    scriptSaveErr.value = ''
    if (!silent) ElMessage.success('已保存')
  } catch (e: any) {
    scriptSaveErr.value = e?.response?.data?.msg || e?.message || '后端未起？'
    if (!silent) ElMessage.error('保存失败，后端未起？')
  } finally { scriptSaving.value = false }
}
watch(script, () => {
  if (suspendScriptWatch) return
  clearTimeout(scriptTimer)
  scriptTimer = setTimeout(() => saveScript(true), 3000)
})
const scriptRefs = ref<any[]>([])
const scriptFileEl = ref<HTMLInputElement | null>(null)
const outlineFileEl = ref<HTMLInputElement | null>(null)
function imgUrl(name: string) { return `/api/images/${name}` }
async function loadScript() {
  suspendScriptWatch = true
  try {
    const r = await api.getScreenplay(store.episodeId)
    script.value = ((r as any).data?.screenplay_md ?? '') as string
    savedScript.value = script.value
    scriptRefs.value = ((r as any).data?.ref_images ?? []) as any[]
    scriptLoadedFor.value = store.episodeId
  } catch {} finally { suspendScriptWatch = false }
}
async function loadScriptRefs() {
  try {
    const r = await api.getScreenplay(store.episodeId)
    scriptRefs.value = ((r as any).data?.ref_images ?? []) as any[]
  } catch {}
}
async function onScriptRef(e: any) {
  const f = e.target.files?.[0]
  e.target.value = ''
  if (!f) return
  try {
    await api.uploadEpisodeImage(store.episodeId, f)
    ElMessage.success('参考图已上传')
    await loadScriptRefs()
  } catch { ElMessage.error('上传失败，后端未起或需重启？') }
}
async function delScriptRef(name: string) {
  try {
    await api.deleteEpisodeImage(store.episodeId, name)
    ElMessage.success('已删')
    await loadScriptRefs()
  } catch { ElMessage.error('删除失败，后端未起或需重启？') }
}
// 参考图命名：点名字进编辑，回车/失焦保存（无变化则直接收起），Esc 取消
const editingRef = ref('')
const refLabelText = ref('')
async function saveRefLabel(im: any) {
  if (editingRef.value !== im.name) return
  editingRef.value = ''
  const v = (refLabelText.value || '').trim().slice(0, 40)
  if (v === (im.label || '')) return
  try {
    await api.setEpisodeImageMeta(store.episodeId, im.name, { label: v })
    im.label = v
    ElMessage.success(v ? `已命名 ${v}` : '已清除命名')
  } catch { ElMessage.error('命名失败，后端未起或需重启？') }
}
const totalS = computed(() => Math.round((store.shots || []).reduce((a: number, s: any) => a + (Number(s.duration_s) || 0), 0) * 10) / 10)

async function refresh() {
  try { const r = await api.listShots(store.episodeId); store.shots = (r as any).data } catch {}
  syncRefDrafts()
}

// 提示词回传页：L-Port 逐镜详细提示词（scriptboard shots[].lport_prompts，seg_prompt 回传）
const promptRefreshing = ref(false)
// 图/影两态：收起=视频提示词，点图展开=图像提示词（按引擎分栏）
const imgPlans = ref<Record<string, any>>({})
const imgMode = ref<Record<string, boolean>>({})
async function loadImgPlans() {
  if (!store.episodeId) { imgPlans.value = {}; return }
  try { imgPlans.value = (await api.plansByShot(store.episodeId)) || {} }
  catch { imgPlans.value = {} }
}
function toggleImg(r: any) { imgMode.value[r.id] = !imgMode.value[r.id] }
// 参考图 role/desc：键用「镜id::图名」，脏了才亮保存
const REF_KIND: Record<string, string> = { first: '首帧', ref: '参考', last: '尾帧' }
const REF_ROLE: Record<string, string> = {
  character: '角色', outfit: '服装', style: '风格', face: '脸', pose: '姿态', scene: '场景', prop: '道具', ending: '收尾',
}
const REF_ROLE_KEYS = ['character', 'outfit', 'style', 'face', 'pose', 'scene', 'prop']
const refDrafts = ref<Record<string, { role: string; desc: string }>>({})
function refKey(sid: string, name: string) { return `${sid}::${name}` }
function syncRefDrafts() {
  const next: Record<string, { role: string; desc: string }> = {}
  for (const sh of (store.shots as any[])) {
    for (const im of (sh.images || [])) {
      const k = refKey(sh.id, im.name)
      const base = { role: im.role || '', desc: im.desc || '' }
      const cur = refDrafts.value[k]
      // 没改过的跟服务端走；改过没存的保留，别被刷新冲掉
      next[k] = cur && (cur.role !== base.role || cur.desc !== base.desc) ? cur : base
    }
  }
  refDrafts.value = next
}
function refDraft(sid: string, name: string) {
  const k = refKey(sid, name)
  if (!refDrafts.value[k]) {
    const im = ((store.shots as any[]).find((x: any) => x.id === sid)?.images || []).find((y: any) => y.name === name) || {}
    refDrafts.value[k] = { role: im.role || '', desc: im.desc || '' }
  }
  return refDrafts.value[k]
}
function refDirty(sid: string, im: any) {
  const d = refDrafts.value[refKey(sid, im.name)]
  return !!d && (d.role !== (im.role || '') || d.desc !== (im.desc || ''))
}
async function saveRef(sid: string, im: any) {
  const d = refDrafts.value[refKey(sid, im.name)]
  if (!d) return
  try {
    await api.setShotImageMeta(sid, im.name, { role: d.role, desc: d.desc })
    ElMessage.success('已保存')
    await refresh()
  } catch (e: any) { ElMessage.error('保存失败：' + (e?.message || e)) }
}
// 生成方式：镜上的是意图，回传里的是按型号结算后的结果，降级了就两个都显示
const GEN_LABEL: Record<string, string> = { 't2v': '纯文本', 'i2v-first': '首帧', 'i2v-first-last': '首尾帧', 'multi-ref': '多图参考' }
function genModeText(r: any) {
  const want = GEN_LABEL[r.gen_mode] || ''
  const eff = GEN_LABEL[r.lpv?.gen_mode_eff] || ''
  if (want && eff && want !== eff) return `${want}→${eff}`
  return eff || want || (r.lpv?.ref_mode || '—')
}
function thumbOf(r: any) {
  const imgs = r.images || []
  return imgs.find((x: any) => x.kind === 'first') || imgs[0] || null
}
const promptRows = computed(() => (store.shots as any[]).map((s: any) => ({
  ...s,
  lp: s.lport_prompts || null,
  lpv: s.lport_video_prompts || null,
  img: imgPlans.value[s.id] || null,
})))
// 视频提示词人工编辑缓冲：draft 存在且与库值不同才算脏；保存后 reload 会把 draft 归位
const vpDrafts = ref<Record<string, string>>({})
watch(promptRows, (rows: any[]) => {
  const next: Record<string, string> = {}
  for (const r of rows) {
    if (!r.lpv?.prompt) continue
    const cur = vpDrafts.value[r.id]
    next[r.id] = cur !== undefined && cur !== r.lpv.prompt ? cur : r.lpv.prompt
  }
  vpDrafts.value = next
}, { immediate: true })
function vpDirty(r: any): boolean {
  return !!r.lpv?.prompt && (vpDrafts.value[r.id] ?? r.lpv.prompt) !== r.lpv.prompt
}
async function saveVp(r: any) {
  const p = (vpDrafts.value[r.id] || '').trim()
  if (!p) return
  try {
    await api.saveVideoPrompt(r.id, { prompt: p })
    ElMessage.success('已保存')
    await reloadPrompts()
  } catch (e: any) {
    ElMessage.error('保存失败：' + (e?.message || e))
  }
}
async function unlockVp(r: any) {
  try {
    await api.unlockVideoPrompt(r.id)
    ElMessage.success('已解锁')
    await reloadPrompts()
  } catch (e: any) {
    ElMessage.error('解锁失败：' + (e?.message || e))
  }
}
const lpDoneCount = computed(() => promptRows.value.filter((r: any) => r.lp || r.lpv).length)
async function reloadPrompts() {
  promptRefreshing.value = true
  try { await Promise.all([refresh(), loadImgPlans()]) } catch {} finally { promptRefreshing.value = false }
}
function promptText(r: any): string {
  if (r.lpv?.prompt) {
    return `【${r.id}】${r.lpv.video_model || r.lpv.engine || ''} · ${r.lpv.ref_mode || ''} · ${r.lpv.duration_s || r.duration_s}秒\n${r.lpv.prompt}`
  }
  const lp = r.lp
  if (!lp) return ''
  const L: string[] = [`【${r.id}】${r.duration_s}秒`]
  if (lp.director_cn) L.push(String(lp.director_cn))
  if (lp.camera_note) L.push(`镜头：${lp.camera_note}`)
  if (lp.key_text_en) L.push(`Key frame: ${lp.key_text_en}`)
  return L.join('\n')
}
async function copyPrompt(r: any) {
  const text = promptText(r)
  if (!text) return
  try { await navigator.clipboard.writeText(text); ElMessage.success('已复制') }
  catch { ElMessage.warning('复制失败，手动选中吧') }
}
async function copyAllPrompts() {
  const chunks = promptRows.value.filter((r: any) => r.lp || r.lpv).map(promptText).filter(Boolean)
  if (!chunks.length) return
  try { await navigator.clipboard.writeText(chunks.join('\n\n')); ElMessage.success(`已复制 ${chunks.length} 镜提示词`) }
  catch { ElMessage.warning('复制失败，手动选中吧') }
}

// 顶部切换 + 清理已移至全局顶栏与各页签内按钮，此处仅保留数据刷新函数

// 草案包 ZIP：L-Port「上传草案包」吃的机器包（manifest.json+shots.json+prompts+图），对照 POSITIONING §2
const bundleLoading = ref(false)
async function downloadBundle() {
  bundleLoading.value = true
  try {
    const blob = await directorApi.exportBundle({ episode_id: store.episodeId, project_id: store.projectId || '', engine: engine.value, pixai_model: pixaiModel.value, tier: globalTier.value, ref_mode: refMode.value })
    const url = URL.createObjectURL(new Blob([blob as any], { type: 'application/zip' }))
    const a = document.createElement('a')
    a.href = url
    a.download = `草案包-${store.episodeId}.zip`
    a.click()
    setTimeout(() => URL.revokeObjectURL(url), 5000)
    ElMessage.success('草案包ZIP已下载，拿到 L-Port 剧本页上传草案包')
  } catch { ElMessage.error('下载失败，后端未起？') }
  finally { bundleLoading.value = false }
}
// 草案文档：方向草案交接件（大纲全文 + 草案表 + 逐镜提示词），落一个 .md（人读版，不进 L-Port）
const docLoading = ref(false)
const clearing = ref(false)
const clearingScript = ref(false)
async function clearScript() {
  clearingScript.value = true
  scriptClearing.value = true
  // 先掐掉 3s 自动保存的定时器：否则它会在清空之后拿旧稿再 PUT 一次，刷新就又回来了
  clearTimeout(scriptTimer)
  try {
    const r = await api.clearEpisode(store.episodeId, 'script')
    script.value = ''
    savedScript.value = ''
    scriptLoadedFor.value = ''
    await loadScript()
    await refresh()
    await loadOutline()
    ElMessage.success(`已清空剧本，连带清理大纲和草案${(r as any)?.data?.shot_count ?? 0}镜`)
  } catch { ElMessage.error('清空失败，后端未起？') }
  finally { scriptClearing.value = false; clearingScript.value = false }
}
async function clearShots() {
  clearing.value = true
  try {
    await api.clearEpisode(store.episodeId, 'shots')
    await refresh()
    ElMessage.success('本集草案已清空')
  } catch { ElMessage.error('清空失败，后端未起？') }
  finally { clearing.value = false }
}
async function downloadDraft() {
  docLoading.value = true
  try {
    const blob = await api.draftDoc({ episode_id: store.episodeId, engine: engine.value, pixai_model: pixaiModel.value, tier: globalTier.value, ref_mode: refMode.value })
    const url = URL.createObjectURL(new Blob([blob as any], { type: 'text/markdown' }))
    const a = document.createElement('a')
    a.href = url
    a.download = `DRAFT-${store.episodeId}.md`
    a.click()
    setTimeout(() => URL.revokeObjectURL(url), 5000)
    ElMessage.success('草案文档已下载（人读版；L-Port 上传请用草案包ZIP）')
  } catch { ElMessage.error('下载失败，后端未起？') }
  finally { docLoading.value = false }
}

// 草案直投 L-Port：投进收件箱 suli_packages/<pkg>/，拿 package_id 轮询回执，等 L-Port 登记即亮
// 多包并行：localStorage 记数组 [{pkg, at, eid, shots}]，一个全局轮询同时跟所有包，互不覆盖
const PUSH_KEY = 'suli.director.pushes'
const PUSH_TTL = 10 * 60 * 1000
interface PendingPush { pkg: string; at: number; eid: string; shots: number; done: boolean; count: number }
const pushing = ref(false)
const pushes = ref<PendingPush[]>([])
let waitTimer: any = null
const curPushes = computed(() => pushes.value.filter(p => p.eid === store.episodeId))
const otherPushCount = computed(() => pushes.value.filter(p => p.eid !== store.episodeId && !p.done).length)
function pushLine(p: PendingPush) {
  if (p.done) return `L-Port 回执已到 ${p.pkg}（${p.count}条）`
  return `已投递 ${p.pkg}（${p.shots}镜）→ L-Port 收件箱，等待回执中…`
}
function savePushes() {
  try { localStorage.setItem(PUSH_KEY, JSON.stringify(pushes.value)) } catch {}
}
function loadPushes(): PendingPush[] {
  try {
    const d = JSON.parse(localStorage.getItem(PUSH_KEY) || '[]')
    if (Array.isArray(d)) return d.filter(x => x?.pkg && x?.at && x?.eid)
  } catch {}
  // 兼容单包旧键（suli.director.push）：有就并进来并删旧键
  try {
    const o = JSON.parse(localStorage.getItem('suli.director.push') || 'null')
    if (o?.pkg && o?.at && o?.eid) {
      localStorage.removeItem('suli.director.push')
      return [{ pkg: o.pkg, at: o.at, eid: o.eid, shots: 0, done: false, count: 0 }]
    }
  } catch {}
  return []
}
function clearPushStorage() {
  try { localStorage.removeItem(PUSH_KEY) } catch {}
}
async function pushToLport() {
  if (pushing.value || !store.episodeId) return
  pushing.value = true
  try {
    const r: any = await directorApi.pushToLport({
      episode_id: store.episodeId, project_id: store.projectId || '',
      engine: engine.value, pixai_model: pixaiModel.value,
      tier: globalTier.value, ref_mode: refMode.value,
    })
    const d = (r as any)?.data ?? r
    pushes.value = [...pushes.value.filter(p => p.pkg !== d.package_id),
      { pkg: d.package_id, at: Date.now(), eid: store.episodeId, shots: d.shot_count || 0, done: false, count: 0 }]
    savePushes()
    ElMessage.success(`已直投 L-Port（${d.shot_count}镜），等待回执`)
    ensurePoller(true)
  } catch (e: any) {
    ElMessage.error(String(e?.response?.data?.msg || '直投失败（L-Port 没起？先用导出ZIP手工搬）').slice(0, 140))
  } finally { pushing.value = false }
}
// 单轮询同时跟所有未完成的包：哪个包先到回执就亮哪个
function ensurePoller(immediate = false) {
  clearTimeout(waitTimer)
  if (!pushes.value.some(p => !p.done && Date.now() - p.at < PUSH_TTL)) return
  const tick = async () => {
    const pend = pushes.value.filter(p => !p.done)
    if (!pend.length) return
    await Promise.all(pend.map(async (p) => {
      if (Date.now() - p.at > PUSH_TTL) return
      try {
        const r: any = await api.receipts({ package_id: p.pkg })
        const rows = (r as any)?.data ?? r ?? []
        const n = Array.isArray(rows) ? rows.length : 0
        if (n > 0) {
          p.done = true
          p.count = n
          ElMessage.success(`L-Port 回执已到 ${p.pkg}（${n}条）`)
        }
      } catch {}
    }))
    // 过期的静默清掉（界面不再显示），其余没到的继续等
    pushes.value = pushes.value.filter(p => p.done || Date.now() - p.at < PUSH_TTL)
    savePushes()
    clearPushStorageIfEmpty()
    if (pushes.value.some(p => !p.done)) waitTimer = setTimeout(tick, 5000)
  }
  if (immediate) tick()
  else waitTimer = setTimeout(tick, 5000)
}
function clearPushStorageIfEmpty() {
  if (!pushes.value.length) clearPushStorage()
}
function stopWait(pkg?: string) {
  clearTimeout(waitTimer)
  if (pkg) pushes.value = pushes.value.filter(p => p.pkg !== pkg)
  else pushes.value = []
  savePushes()
  clearPushStorageIfEmpty()
  ensurePoller()
}
// 刷新/切回：读回没过期的投递，后台轮询自动续上，回来立刻查一次
function resumePush() {
  clearTimeout(waitTimer)
  pushes.value = loadPushes().filter(p => Date.now() - p.at < PUSH_TTL)
  savePushes()
  clearPushStorageIfEmpty()
  ensurePoller(true)
}
watch(dtab, v => { if (v === 'prompts') refresh() })
watch(() => store.episodeId, () => { resumePush() })

// 单图Agent导演域（抽到 composable，大纲 brief 留在视图）
const { agentTotal, agentLoading, outline, loadOutline, stopAgent, runBrief } = useAgentDirect(
  () => store.episodeId, refresh,
)
// 离开页面时清掉剧本自动保存的 debounce：否则组件销毁后它还会拿旧/空文本再 PUT 一次（2026-10-16 清库事故）
onUnmounted(() => { clearTimeout(scriptTimer); clearTimeout(waitTimer) })
function pickOutlineImage(): string {
  if (outline.value.image) return outline.value.image
  if (scriptRefs.value[0]?.name) return scriptRefs.value[0].name
  for (const s of store.shots as any[]) {
    const imgs = (s.images?.length ? s.images : (s.image ? [{ name: s.image, kind: 'ref' }] : [])) as any[]
    const hit = imgs.find(x => x.kind === 'first') || imgs[0]
    if (hit?.name) return hit.name
  }
  return ''
}
async function runOutlineBrief(imgName: string) {
  try { await api.dshEnsure('episode', store.episodeId) }
  catch { ElMessage.error('Agent会话建失败，后端未起？'); return }
  const brief = [
    `@data/uploads/${imgName}`,
    `集号：${store.episodeId}`,
    '请按这张单图出方案大纲：看图写一份方案大纲markdown（含：方向一句话 / 基调与档位 / 分镜大纲表：镜号/内容一句话/预计时长/运镜方向/备注 / 合计时长），2-5镜，单镜3-8秒。然后 PUT /api/v1/scriptboard/outline/<集号> 保存 {outline_md: 全文, outline_image: 本图basename}，最后回复方向一句话+镜数+合计时长。只出大纲，不要写分镜库。',
    `总时长要求：${agentTotal.value}秒内，按此时长分配镜数与每镜秒数（优先保证单镜3-8秒）。`,
    castNames(loadCastInput()).length ? `出镜角色（点名照写，别自造人名）：${castNames(loadCastInput()).join('、')}。` : '出镜角色：查角色库取现有角色名，查不到用「主角/对手」占位，别自造人名。',
    `目标引擎：${(engineOpts.value.find(e => e.key === engine.value) || {}).label || engine.value}${engine.value === 'pixai' ? '（提示词按 PixAI 视频格式：@image1 参考行 + [0-Xs] beat + 相机动词 + Voice/SFX 行，见 skills/video/pixai-video-prompting）' : '（提示词按 MiniMax H3 字段格式，见 skills/video/h3-prompt-writing）'}。`,
    agentTier.value ? `分级档位：${tierLabel(agentTier.value)}（${agentTier.value}）。按 skills/video/nsfw-directing 的该档水位出镜：成年虚构角色锚定、微动作预算（一镜一事件、呼吸级幅度）、遮挡结构、锚点carry；duty_en 用英文写可见层动作。` : '',
  ].filter(Boolean).join('\n')
  await runBrief(brief, 'Agent看图出大纲中…', '大纲已存，确认后点 ② 转草案', loadOutline)
}
async function genOutline() {
  if (settings.settings.outlineMode === 'expert') return genOutlineHere()
  return genOutlineLite()
}
async function genOutlineHere() {
  if (agentLoading.value) return
  const img = pickOutlineImage()
  if (!img) return ElMessage.warning('还没有参考图，先去「剧本」页签或大纲页签点「+参考图」传一张，或给分镜挂图')
  dtab.value = 'outline'
  await runOutlineBrief(img)
}
async function genOutlineLite() {
  // 轻链默认：不走 dsh，直接调 outline/generate 落盘
  if (agentLoading.value) return
  const img = pickOutlineImage()
  dtab.value = 'outline'
  try {
    await api.outlineGenerate(store.episodeId, {
      total_s: agentTotal.value || 15,
      engine: engine.value || 'pixai',
      tier: agentTier.value || globalTier.value || '',
      hint: script.value.slice(0, 800),
      image: img,
      cast: castNames(loadCastInput()),  // 故事页点名；空数组=没点名，后端按「本集已记 → 正文说话人 → 角色库」取角
    })
    await loadOutline()
    ElMessage.success('大纲已存（轻），确认后点 ② 生成草案')
  } catch { ElMessage.error('轻大纲失败，后端未起？') }
}
async function regenOutline() {
  if (agentLoading.value) return
  if (settings.settings.outlineMode !== 'expert') {
    dtab.value = 'outline'
    return genOutlineLite()
  }
  const img = pickOutlineImage()
  if (!img) return ElMessage.warning('还没有参考图，先传一张图')
  await runOutlineBrief(img)
}

function onDraftMode(cmd: string) { if (cmd === 'expert') buildDraftShots(); else buildDraftShotsLite() }
async function buildDraftShots() {
  if (agentLoading.value || !outline.value.md) return
  const brief = [
    `集号：${store.episodeId}`,
    '读取本集已存方案大纲（GET /api/v1/scriptboard/outline/<集号>），按大纲建草案分镜写入分镜库：',
    '每镜 create 时带 draft:true；字段照单图导演规范（duty 中文看板 / duty_en 英文可见层动作 / duration_s / sound / tier / camera）；',
    `首镜挂大纲配图为首帧（attach kind=first，大纲配图：${outline.value.image || '无'}）；`,
    '最后回复镜清单（镜id/时长/运镜/内容一句话）+合计时长。只建草案，不要改大纲。',
  ].join('\n')
  await runBrief(brief, 'Agent按大纲建草案分镜中…', '分镜已写库，去「提示词」页查看', async () => { await refresh(); dtab.value = 'prompts' })
}
const draftLiteLoading = ref(false)
async function buildDraftShotsLite() {
  // 轻转草案：不走 dsh，直接调 draft/from-outline 落盘
  if (draftLiteLoading.value || agentLoading.value) return
  if (!outline.value.md) return ElMessage.warning('先有大纲再转草案')
  draftLiteLoading.value = true
  try {
    const r = await api.draftFromOutline(store.episodeId, {
      total_s: Math.round(totalS.value) || 15,
      tier: agentTier.value || globalTier.value || '',
    })
    const created = (r as any)?.data?.created || (r as any)?.created || []
    await refresh()
    dtab.value = 'prompts'
    ElMessage.success(`分镜已写库：${created.length}镜`)
  } catch (e: any) {
    ElMessage.error((e?.response?.data?.msg || '轻转草案失败').slice(0, 120))
  } finally {
    draftLiteLoading.value = false
  }
}

const outlineFolded = ref(false)
const outlineEditing = ref(false)
const outlineDraft = ref('')
const outlineSaving = ref(false)
const clearingOutline = ref(false)
async function clearOutline() {
  clearingOutline.value = true
  try {
    const r = await api.clearEpisode(store.episodeId, 'outline')
    outlineEditing.value = false
    await loadOutline()
    await refresh()
    ElMessage.success(`已清空大纲，连带清理草案${(r as any)?.data?.shot_count ?? 0}镜`)
  } catch { ElMessage.error('清空失败，后端未起？') }
  finally { clearingOutline.value = false }
}
const outlineDirty = computed(() => outlineDraft.value !== (outline.value.md || ''))
function toggleOutlineEdit() {
  if (!outlineEditing.value) outlineDraft.value = outline.value.md || ''
  outlineEditing.value = !outlineEditing.value
}
async function saveOutlineEdit() {
  outlineSaving.value = true
  try {
    await api.saveOutline(store.episodeId, { outline_md: outlineDraft.value, outline_image: outline.value.image || '' })
    await loadOutline()
    outlineEditing.value = false
    ElMessage.success('大纲已保存')
  } catch { ElMessage.error('保存失败，后端未起？') }
  finally { outlineSaving.value = false }
}
const outlineMaxH = ref(Math.min(1600, Math.max(200, Number(localStorage.getItem('suli.outlineMaxH')) || 560)))
function persistOutlineMaxH() { try { localStorage.setItem('suli.outlineMaxH', String(outlineMaxH.value)) } catch {} }
function resetOutlineMaxH() { outlineMaxH.value = 560; persistOutlineMaxH() }
let orz: { y: number; h: number } | null = null
function startOutlineResize(e: MouseEvent) {
  orz = { y: e.clientY, h: outlineMaxH.value }
  window.addEventListener('mousemove', onOutlineResizeMove)
  window.addEventListener('mouseup', onOutlineResizeEnd, { once: true })
  e.preventDefault()
}
function onOutlineResizeMove(e: MouseEvent) {
  if (!orz) return
  outlineMaxH.value = Math.min(1600, Math.max(200, Math.round(orz.h + e.clientY - orz.y)))
}
function onOutlineResizeEnd() {
  window.removeEventListener('mousemove', onOutlineResizeMove)
  orz = null
  persistOutlineMaxH()
}
const outlineZoom = ref(Math.min(2, Math.max(0.5, Number(localStorage.getItem('suli.outlineZoom')) || 1)))
function resetOutlineZoom() {
  outlineZoom.value = 1
  try { localStorage.setItem('suli.outlineZoom', '1') } catch {}
}
function zoomOutline(d: number) {
  outlineZoom.value = Math.min(2, Math.max(0.5, +(outlineZoom.value + d).toFixed(2)))
  try { localStorage.setItem('suli.outlineZoom', String(outlineZoom.value)) } catch {}
}
function tierLabel(key: string) { return (tierOpts.value.find(t => t.key === key) || {} as any).label || key }
watch(() => store.centralApplySeq, async (seq, prev) => {
  if (!seq || seq === prev) return
  const target = (store as any).centralApplyEpisode || store.episodeId
  if (target && target !== store.episodeId) store.episodeId = target
  await loadScript()
  await refresh()
  await loadOutline()
})
onMounted(async () => {
  try {
    const e = await api.directorEngines()
    const erows = ((e as any)?.data || e || []) as any[]
    if (erows.length) {
      engineOpts.value = erows.map(x => ({ key: x.key, label: x.label }))
      const px = erows.find(x => x.key === 'pixai')
      if (px && px.models?.length) pixaiModels.value = px.models
    }
  } catch {}
  try {
    const r = await api.directorTiers()
    const rows = ((r as any)?.data || r || []) as any[]
    tierOpts.value = [{ key: '', label: '不分级' }, ...rows.map(t => ({ key: t.key, label: t.label }))]
  } catch {}
  await loadScript()
  await refresh()
  await loadImgPlans()
  await loadOutline()
  resumePush()
})
watch(() => store.episodeId, () => { imgMode.value = {}; loadImgPlans() })
</script>
<style scoped>
.director.kun-page { max-width: none; margin: 0; }
.director { padding: 12px !important; min-height: 100%; display: flex; flex-direction: column; }
.dir-head { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.dir-tabs { margin-top: 8px; flex: 1; min-height: 0; display: flex; flex-direction: column; }
.dir-tabs :deep(.el-tabs__content) { flex: 1; min-height: 0; overflow: auto; }
.dir-bar { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-top: 10px; padding: 8px 10px; border: 1.5px solid var(--suli-border); border-radius: var(--suli-radius-sm); background: var(--suli-surface); }
.dir-bar .bar-group { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.bar-spacer { flex: 1 1 auto; min-width: 4px; }
.w-tier { width: 150px; }
.w-engine { width: 240px; }
.w-model { width: 210px; }
.w-ref { width: 190px; }
.push-status { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-top: 8px; padding: 8px 10px; border: 1px dashed var(--suli-border); border-radius: 8px; background: var(--suli-surface); }
.push-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
.push-dot.ok { background: var(--el-color-success); }
.script-refs { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-top: 8px; }
.script-refs.top { margin-top: 0; margin-bottom: 8px; }
.shot-refwrap { display: inline-flex; gap: 4px; align-items: center; }
.shot-refwrap.col { flex-direction: column; align-items: center; }
.ref-label-row { display: inline-flex; gap: 2px; align-items: center; max-width: 104px; }
.ref-label { font-size: 11px; color: var(--suli-text-2); max-width: 80px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; cursor: pointer; }
.ref-label:hover { color: var(--suli-primary); }
.ref-input { max-width: 80px; }
.shot-thumb.sm { width: 96px; aspect-ratio: 3 / 4; border-radius: 10px; overflow: hidden; cursor: zoom-in; }
.shot-thumb.sm :deep(img) { width: 100%; height: 100%; object-fit: cover; display: block; }
.script-foot { margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--suli-border); display: flex; gap: 14px; align-items: center; flex-wrap: wrap; }
.foot-actions { display: flex; gap: 8px; align-items: center; }
.foot-status { display: flex; align-items: center; min-width: 0; }
.st { display: inline-flex; gap: 6px; align-items: center; font-size: 12px; color: var(--suli-text-2); white-space: nowrap; }
.st .dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
.st.ok .dot { background: var(--el-color-success); }
.st.warn .dot { background: var(--el-color-warning); }
.st.err { color: var(--el-color-danger); }
.st.err .dot { background: var(--el-color-danger); }
.foot-count { margin-left: auto; font-size: 12px; }
.outline-card { margin-top: 10px; padding: 10px 12px; display: flex; flex-direction: column; gap: 8px; }
.outline-head { display: flex; gap: 8px; align-items: center; }
.outline-main { display: flex; gap: 10px; align-items: flex-start; }
.outline-thumb { width: 320px; aspect-ratio: 3 / 4; border-radius: 10px; flex-shrink: 0; cursor: zoom-in; overflow: hidden; }
.outline-thumb :deep(img) { width: 100%; height: 100%; object-fit: cover; display: block; }
.outline-textwrap { flex: 1; min-width: 0; position: relative; padding-bottom: 12px; }
.outline-editwrap { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 8px; }
.outline-text { max-height: 560px; overflow-y: auto; }
.outline-rz { position: absolute; left: 0; right: 0; bottom: 0; height: 12px; cursor: ns-resize; display: flex; align-items: center; justify-content: center; }
.outline-rz::after { content: ''; width: 56px; height: 4px; border-radius: 999px; background: var(--el-border-color); }
.outline-rz:hover::after { background: var(--suli-primary); }
.shot-prompt { font-size: 13px; white-space: pre-wrap; background: var(--el-fill-color-lighter); border-radius: 8px; padding: 10px; }
/* 提示词回传页（L-Port seg_prompt 逐镜回传） */
.prompt-head { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin: 6px 0 10px; }
.prompt-list { display: flex; flex-direction: column; gap: 8px; }
.prompt-row { display: flex; gap: 12px; align-items: flex-start; padding: 10px 12px; border: 1px solid var(--suli-border); border-radius: 10px; background: var(--suli-surface); }
.pr-left { display: flex; flex-direction: column; gap: 4px; align-items: center; flex-shrink: 0; width: 132px; }
.pr-no { width: 26px; height: 26px; border-radius: 50%; background: var(--suli-primary); color: #fff; font-size: 12px; font-weight: 800; display: inline-flex; align-items: center; justify-content: center; }
.pr-sid { font-family: var(--suli-mono); font-size: 11px; word-break: break-all; text-align: center; }
.pr-dur { font-size: 12px; color: var(--suli-text-2); }
.pr-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.pr-empty { color: var(--suli-text-3); font-size: 12px; }
.pr-line { display: flex; gap: 8px; font-size: 13px; line-height: 1.6; }
.pr-k { flex-shrink: 0; width: 74px; color: var(--suli-text-2); font-weight: 600; }
.pr-v { min-width: 0; white-space: pre-wrap; word-break: break-word; }
.pr-meta { font-size: 11px; color: var(--suli-text-3); }
.pr-right { flex-shrink: 0; }
.pr-thumb { position: relative; width: 116px; height: 84px; border-radius: 8px; overflow: hidden; cursor: pointer; border: 1px solid var(--suli-border); margin-top: 2px; }
.pr-thumb :deep(img) { width: 100%; height: 100%; object-fit: cover; }
.pr-thumb.on { border-color: var(--suli-primary); box-shadow: 0 0 0 2px color-mix(in srgb, var(--suli-primary) 30%, transparent); }
.pr-thumb-empty { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 12px; color: var(--suli-text-3); background: var(--suli-surface-2, #fafafa); }
.pr-thumb-tag { position: absolute; left: 4px; bottom: 4px; font-size: 11px; padding: 0 6px; border-radius: 999px; background: rgba(0,0,0,.55); color: #fff; }
.pr-eng { display: flex; flex-direction: column; gap: 2px; padding-top: 4px; border-top: 1px dashed var(--suli-border); }
.pr-refs { display: flex; flex-wrap: wrap; gap: 6px; }
.pr-ref { display: flex; align-items: center; gap: 6px; padding: 4px 6px; border: 1px solid var(--suli-border); border-radius: 8px; }
.pr-ref-thumb { width: 40px; height: 40px; border-radius: 6px; overflow: hidden; }
.pr-ref-role { width: 92px; }
.pr-ref-desc { width: 220px; }
@media (max-width: 900px) {
  .outline-thumb { width: 170px; }
  .outline-text { max-height: 340px; }
}
</style>
