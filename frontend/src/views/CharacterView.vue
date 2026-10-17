<template>
  <div class="suli-card kun-page" style="padding:14px">
    <h3>原创角色设计</h3>
    <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
      <el-select v-model="curId" placeholder="角色" style="width:220px" @change="loadChar" :disabled="charLoading">
        <el-option v-for="c in chars" :key="c.id" :label="c.name+'('+c.id+')'" :value="c.id" />
      </el-select>
      <el-input v-model="cname" placeholder="角色名" style="width:160px" />
      <el-button type="primary" @click="create" :loading="charLoading">新建</el-button>
      <el-button @click="reloadChars">刷新</el-button>
    </div>
    <div v-if="charLoading" style="margin-top:10px"><div class="skeleton" style="height:16px" /><div class="skeleton" style="height:16px;margin-top:8px" /></div>
    <el-empty v-else-if="!curId" description="无角色" :image-size="72" />
    <el-tabs v-else v-model="ctab" style="margin-top:8px">
      <el-tab-pane label="设定四维" name="dims">
        <el-form label-width="70px" style="width:100%">
          <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="形象"><el-button size="small" @click="avatarInput?.click()">选择图片</el-button><input ref="avatarInput" type="file" accept="image/*" hidden @change="onAvatar" /><span v-if="form.avatar_path" class="suli-muted" style="margin-left:8px">{{ form.avatar_path }}</span></el-form-item>
          <el-form-item v-for="d in dims" :key="d.key" :label="d.label">
            <el-input v-model="form[d.key]" type="textarea" :rows="2" />
          </el-form-item>
        </el-form>
        <div style="display:flex;gap:8px;margin-top:8px">
          <el-select v-model="itDim" style="width:120px"><el-option v-for="d in dims" :key="d.key" :label="d.label" :value="d.key" /></el-select>
          <el-input v-model="itIns" placeholder="指令" style="flex:1" />
          <el-button type="primary" @click="doIterate" :disabled="!itIns.trim()">迭代</el-button>
          <el-button @click="freeze">冻结最新</el-button>
        </div>
        <el-table :data="vRows" style="margin-top:8px">
          <el-table-column prop="version_no" label="版" width="60" />
          <el-table-column prop="dimension" label="维度" width="90" />
          <el-table-column prop="instruction" label="指令" />
          <el-table-column prop="frozen" label="冻" width="50" />
          <el-table-column label="操作" width="140"><template #default="s"><el-popconfirm title="回滚到该版本？" confirm-button-text="回滚" cancel-button-text="取消" @confirm="doRollback(s.row.id)"><template #reference><el-button link type="primary">回滚</el-button></template></el-popconfirm></template></el-table-column>
        </el-table>
        <el-pagination v-if="vPage.total.value > 0" v-model:current-page="vPage.page.value" v-model:page-size="vPage.pageSize.value" :total="vPage.total.value" layout="prev, pager, next, sizes, total" @change="() => {}" style="margin-top:8px;justify-content:flex-end" />
      </el-tab-pane>
      <el-tab-pane label="18槽位设定图" name="slots">
        <div v-for="sec in sections" :key="sec" class="suli-card worksec" style="margin-bottom:12px;padding:12px">
          <div class="worksec-head">
            <b>{{ secLabel(sec) }}</b>
            <span style="margin-left:8px"><el-radio-group v-model="attire[sec]" size="small"><el-radio-button v-for="a in attires" :key="a" :value="a">{{ a === 'dressed' ? '着装' : '无着装' }}</el-radio-button></el-radio-group></span>
            <el-popconfirm :title="`清空${secLabel(sec)}（${attireLabel(attire[sec])}）整组？图与中英提示词一并删除`" confirm-button-text="清空" cancel-button-text="取消" width="260" @confirm="clearSection(sec)">
              <template #reference><el-button size="small" type="danger" plain>清空本组</el-button></template>
            </el-popconfirm>
          </div>
          <div style="display:flex;gap:8px;align-items:center;margin-top:10px;flex-wrap:wrap">
            <span class="suli-muted" style="font-size:12px">槽位提示词出稿引擎</span>
            <el-select v-model="imgEngine" size="small" style="width:270px">
              <el-option v-for="m in imgModels" :key="m.key" :label="m.label" :value="m.key" />
            </el-select>
            <span class="suli-muted" style="font-size:12px">{{ imgModelHint }}</span>
          </div>
          <div class="slot-worklist" style="margin-top:10px">
            <div v-for="s in slots" :key="s" class="slot-card slot-workcard suli-card" style="padding:12px">
              <div class="slot-topbar">
                <div class="slot-name">
                  <el-button size="small" text @click="toggleFold(sec, s)">{{ foldedMap[pkey(sec, s)] ? '▶ 展开' : '▼ 收起' }}</el-button>
                  <b>{{ slotLabel(s) }}</b><span class="suli-muted">{{ kindOf(sec, attire[sec]) }}</span>
                  <span v-if="foldedMap[pkey(sec, s)]" class="suli-muted tnum fold-summary">{{ imgMap[pkey(sec, s)] ? '有图' : '无图' }} · 中{{ (promptCnMap[pkey(sec, s)] || '').length }}字 · 英{{ (promptMap[pkey(sec, s)] || '').length }}字</span>
                </div>
                <div class="slot-head-btns"><el-button size="small" @click="slotRefs[pkey(sec, s)]?.click()">{{ imgMap[pkey(sec, s)] ? '更换图片' : '传图' }}</el-button><el-popconfirm title="清除该槽位？（图 + 中/英提示词）" confirm-button-text="清除" cancel-button-text="取消" width="240" @confirm="clearSlot(sec, s)"><template #reference><el-button size="small" type="danger" plain>清除</el-button></template></el-popconfirm><input :ref="(el: any) => { if (el) slotRefs[pkey(sec, s)] = el }" type="file" accept="image/*" hidden @change="(e: any) => onSlot(sec, s, e)" /></div>
              </div>
              <div v-show="!foldedMap[pkey(sec, s)]" class="slot-main">
              <div class="slot-left">
                <SlotZoomImage :src="imgMap[pkey(sec, s)]" @upload="slotRefs[pkey(sec, s)]?.click()" />
              </div>
              <div class="slot-right">
                <div class="prompt-block">
                  <div class="slot-title"><div class="slot-name"><el-tag size="small">中文</el-tag><span class="suli-muted tnum">{{ (promptCnMap[pkey(sec, s)] || '').length }}字</span></div><div class="slot-head-btns"><el-button size="small" @click="genPromptCn(sec, s)">生成中文</el-button><el-button size="small" @click="savePromptCn(sec, s)">保存中文</el-button><el-popconfirm title="清空中文提示词？" confirm-button-text="清空" cancel-button-text="取消" @confirm="clearPrompt(sec, s, 'cn')"><template #reference><el-button size="small" type="danger" plain>清空</el-button></template></el-popconfirm></div></div>
                  <el-input v-model="promptCnMap[pkey(sec, s)]" type="textarea" :rows="5" placeholder="中文描述：发型 / 表情 / 服装 / 色彩…" class="slot-prompt prompt-cn" />
                </div>
                <div class="prompt-block">
                  <div class="slot-title"><div class="slot-name"><el-tag size="small" type="info">英文</el-tag><span class="suli-muted tnum">{{ (promptMap[pkey(sec, s)] || '').length }}字</span></div><div class="slot-head-btns"><el-button size="small" @click="genPrompt(sec, s)">生成英文</el-button><el-button size="small" type="primary" @click="savePrompt(sec, s)">保存英文</el-button><el-popconfirm title="清空英文提示词？" confirm-button-text="清空" cancel-button-text="取消" @confirm="clearPrompt(sec, s, 'en')"><template #reference><el-button size="small" type="danger" plain>清空</el-button></template></el-popconfirm></div></div>
                  <el-input v-model="promptMap[pkey(sec, s)]" type="textarea" :rows="5" placeholder="English prompt…" class="slot-prompt prompt-en" />
                </div>
              </div>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
      <el-tab-pane label="服装四分类" name="outfits">
        <div class="worksec" style="padding:12px">
          <div class="outfit-toolbar">
            <el-input v-model="outName" placeholder="服装名" style="width:200px" />
            <el-select v-model="outCat" style="width:170px"><el-option v-for="c in outCats" :key="c" :label="outCatLabel(c) + '（' + c + '）'" :value="c" /></el-select>
            <el-button type="primary" @click="addOutfit">新增</el-button>
            <span class="suli-muted" style="font-size:12px">共 <b class="tnum">{{ outfits.length }}</b> 件 · <b>{{ outCatLabel(outCat) }}</b>{{ catDescMap[outCat] ? '：' + catDescMap[outCat] : '' }}</span>
          </div>
          <div class="outfit-list">
            <div v-for="o in oRows" :key="o.id" class="outfit-card suli-card" :class="{ active: !!o.is_active }">
              <div class="outfit-topbar">
                <div class="outfit-name">
                  <span class="outfit-chip">{{ outCatChip(o.category) }}</span>
                  <b>{{ o.name }}</b>
                  <el-tag v-if="o.is_active" size="small" type="success">已激活</el-tag>
                  <el-tag size="small" type="info" effect="plain">{{ outCatLabel(o.category) }}</el-tag>
                  <span v-if="o.description" class="suli-muted tnum" style="font-size:12px">{{ o.description.length }}字描述</span>
                  <span class="suli-muted tnum" style="font-size:12px">#{{ o.id }}</span>
                </div>
                <div class="slot-head-btns">
                  <el-button size="small" type="primary" plain :disabled="!!o.is_active" @click="actOutfit(o.id)">激活</el-button>
                  <el-button size="small" @click="startEditOutfit(o)">{{ editId === o.id ? '收起' : '编辑' }}</el-button>
                  <el-popconfirm title="删掉这件服装？" confirm-button-text="删" cancel-button-text="留" @confirm="delOutfit(o.id)"><template #reference><el-button size="small" type="danger" plain>删</el-button></template></el-popconfirm>
                </div>
              </div>
              <div v-if="editId === o.id" class="outfit-edit">
                <div class="outfit-edit-row">
                  <el-input v-model="editForm.name" placeholder="服装名" style="width:200px" />
                  <el-select v-model="editForm.category" style="width:170px"><el-option v-for="c in outCats" :key="c" :label="outCatLabel(c) + '（' + c + '）'" :value="c" /></el-select>
                  <span class="suli-muted" style="font-size:12px">分类说明{{ catDescMap[editForm.category] ? '：' + catDescMap[editForm.category] : '待填（后端 outfit-categories）' }}</span>
                </div>
                <el-input v-model="editForm.description" type="textarea" :rows="2" placeholder="服装细节：版型 / 材质 / 配色 / 配饰…（供槽位提示词与交付包引用）" />
                <div class="outfit-edit-actions"><el-button size="small" @click="editId = null">取消</el-button><el-button size="small" type="primary" @click="saveOutfitEdit(o.id)">保存</el-button></div>
              </div>
              <div v-else-if="o.description" class="outfit-desc">{{ o.description }}</div>
            </div>
            <el-empty v-if="!oRows.length" description="暂无服装：左侧填名称与分类，点「新增」" :image-size="60" />
          </div>
          <el-pagination v-if="oPage.total.value > 0" v-model:current-page="oPage.page.value" v-model:page-size="oPage.pageSize.value" :total="oPage.total.value" :page-sizes="[8, 16, 32]" layout="prev, pager, next, sizes, total" style="margin-top:8px;justify-content:flex-end" />
        </div>
      </el-tab-pane>
      <el-tab-pane label="文档交付" name="doc">
        <el-input v-model="docHtml" type="textarea" :rows="6" placeholder="文档" />
        <div style="margin-top:8px;display:flex;gap:8px"><el-button @click="loadDoc">读取</el-button><el-button type="primary" @click="saveDoc">保存</el-button><el-button @click="loadPack">交付包</el-button></div>
        <pre v-if="pack" class="suli-pre">{{ pack }}</pre>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { api, DIMS } from '../api/client'
import SlotZoomImage from '../components/SlotZoomImage.vue'
import { usePagination } from '../composables/usePagination'
import { useAppStore } from '../stores/app'
const store = useAppStore()
const cname = ref('')  // 新建角色的输入框：空着让用户自己起名，不再预填演示名
const chars = ref<any[]>([])
const curId = ref('')
const form = ref<any>({ name: '', hairstyle: '', face: '', physique: '', identity: '' })
const dims = DIMS
const ctab = ref('dims')
const sections = ['head', 'half', 'full']
const attires = ['undressed', 'dressed']
const slots = ['front', 'side', 'back']
const attire = ref<any>({ head: 'dressed', half: 'dressed', full: 'dressed' })
const imgModels = ref<any[]>([{ key: 'novelai', label: 'NovelAI（英文 tag 轨）' }, { key: 'tsubaki3', label: 'Tsubaki.3（中文自然语言）' }, { key: 'seedream', label: 'Seedream（自然语言）' }])
const imgEngine = ref('tsubaki3')
const imgModelHint = computed(() => { const m = imgModels.value.find(x => x.key === imgEngine.value); return m ? (m.hint || '') : '' })
const promptMap = ref<any>({})
const promptCnMap = ref<any>({})
const foldedMap = ref<Record<string, boolean>>({})
function toggleFold(sec: string, s: string) { const k = pkey(sec, s); foldedMap.value[k] = !foldedMap.value[k] }
const avatarInput = ref<HTMLInputElement | null>(null)
const slotRefs = ref<Record<string, HTMLInputElement>>({})
const itDim = ref('identity')
const itIns = ref('')
const versions = ref<any[]>([])
const vPage = usePagination(() => versions.value, 5)
const vRows = vPage.rows
const outName = ref('长外套')
const outCat = ref('top')
const outCats = ['headwear', 'top', 'bottom', 'shoes']
const outfits = ref<any[]>([])
const oPage = usePagination(() => outfits.value, 8)
const oRows = oPage.rows
const catDescMap = ref<Record<string, string>>({})
const editId = ref<number | null>(null)
const editForm = ref<any>({ name: '', category: 'top', description: '' })
const docHtml = ref('')
const pack = ref<any>(null)
const charLoading = ref(false)
const charError = ref('')
const imgMap = ref<any>({})
function secLabel(s: string) { return s === 'head' ? '头部三视图' : s === 'half' ? '半身三视图' : '全身三视图' }
function slotLabel(s: string) { return s === 'front' ? '正面' : s === 'side' ? '侧面' : '背面' }
function kindOf(sec: string, a: string) { return `${sec}_${a}` }
function pkey(sec: string, s: string) { return `${kindOf(sec, attire.value[sec])}|${s}` }
async function reloadChars() {
  charLoading.value = true; charError.value = ''
  try {
    const r = await api.listCharacters(); chars.value = r.data
    if (store.selectedCharId && (chars.value as any[]).find(x => x.id === store.selectedCharId)) curId.value = store.selectedCharId
    if (!curId.value && chars.value[0]) curId.value = chars.value[0].id
    if (curId.value) await loadChar()
  }
  catch { charError.value = '后端未起' }
  finally { charLoading.value = false }
}
async function create() { const r = await api.createCharacter({ name: cname.value }); chars.value.unshift(r.data); curId.value = r.data.id; await loadChar() }
async function saveDims(silent = false) { if (!curId.value) return; await api.updateCharacter(curId.value, form.value); store.touchSaved(); if (!silent) ElMessage.success('已保存') }
// 3 秒无操作自动存（四维表单 + 文档），存后顶栏显示已保存时刻
let suspendWatch = false
let dimsTimer: any = null
let docTimer: any = null
watch(form, () => {
  if (suspendWatch || !curId.value) return
  clearTimeout(dimsTimer)
  dimsTimer = setTimeout(() => saveDims(true), 3000)
}, { deep: true })
watch(docHtml, () => {
  if (suspendWatch || !curId.value) return
  clearTimeout(docTimer)
  docTimer = setTimeout(async () => { await api.saveDoc(curId.value, docHtml.value); store.touchSaved() }, 3000)
})
async function loadChar() {
  suspendWatch = true
  try {
    const r = await api.listCharacters(); const c = (r.data as any[]).find(x => x.id === curId.value); if (c) form.value = { ...c }; await loadPrompts(); await loadAssets(); await loadOutfits(); await loadDoc(); await loadVersions()
  } finally { suspendWatch = false }
}
async function loadAssets() {
  if (!curId.value) return
  try {
    const r = await api.listAssets(curId.value)
    const m: any = {}
    const idm: any = {}
    for (const a of (r.data as any[])) {
      const k = `${a.kind}|${a.slot}`
      if (!m[k] || (a.id || 0) > (idm[k] || 0)) { m[k] = a.url; idm[k] = a.id || 0 }
    }
    imgMap.value = { ...imgMap.value, ...m }
  } catch {}
}
async function loadPrompts() {
  if (!curId.value) return
  const r = await api.listSlotPrompts(curId.value)
  const m: any = {}
  const mc: any = {}
  for (const p of r.data as any[]) {
    const slot = String(p.slot || '')
    if (slot.endsWith('_cn')) { mc[`${p.kind}|${slot.slice(0, -3)}`] = p.prompt }
    else { m[`${p.kind}|${slot}`] = p.prompt }
  }
  promptMap.value = m
  promptCnMap.value = mc
}
async function genPrompt(sec: string, s: string) { if (!curId.value) return ElMessage.warning('未选角色'); const k = kindOf(sec, attire.value[sec]); const r = await api.genSlotPrompt(curId.value, k, s, imgEngine.value === 'novelai' ? 'novelai' : 'novelai'); promptMap.value[`${k}|${s}`] = (r.data as any).prompt }
async function savePrompt(sec: string, s: string) { const k = kindOf(sec, attire.value[sec]); await api.saveSlotPrompt(curId.value, k, s, promptMap.value[`${k}|${s}`] || ''); ElMessage.success('已保存英文提示词') }
async function genPromptCn(sec: string, s: string) { if (!curId.value) return ElMessage.warning('未选角色'); const k = kindOf(sec, attire.value[sec]); const r = await api.genSlotPrompt(curId.value, k, s + '_cn', imgEngine.value === 'novelai' ? 'tsubaki3' : imgEngine.value); promptCnMap.value[`${k}|${s}`] = (r.data as any).prompt }
async function savePromptCn(sec: string, s: string) { const k = kindOf(sec, attire.value[sec]); await api.saveSlotPrompt(curId.value, k, s + '_cn', promptCnMap.value[`${k}|${s}`] || ''); ElMessage.success('已保存中文提示词') }
function attireLabel(a: string) { return a === 'dressed' ? '着装' : '无着装' }
function dropKey(map: any, key: string) { const m: any = { ...map }; delete m[key]; return m }
// 清除三件套：先等后端删记录回 200，再删本地键——后端失败就保留画面，不做"假清除"
async function clearPrompt(sec: string, s: string, which: 'cn' | 'en') {
  if (!curId.value) return ElMessage.warning('未选角色')
  const k = kindOf(sec, attire.value[sec])
  await api.clearSlotPrompts(curId.value, k, s, which)
  if (which === 'cn') promptCnMap.value = dropKey(promptCnMap.value, `${k}|${s}`)
  else promptMap.value = dropKey(promptMap.value, `${k}|${s}`)
  ElMessage.success(which === 'cn' ? '已清空中文提示词' : '已清空英文提示词')
}
async function clearSlot(sec: string, s: string) {
  if (!curId.value) return ElMessage.warning('未选角色')
  const k = kindOf(sec, attire.value[sec])
  const r: any = await api.clearSlotAssets(curId.value, k, s)
  await api.clearSlotPrompts(curId.value, k, s, 'both')
  imgMap.value = dropKey(imgMap.value, `${k}|${s}`)
  promptCnMap.value = dropKey(promptCnMap.value, `${k}|${s}`)
  promptMap.value = dropKey(promptMap.value, `${k}|${s}`)
  foldedMap.value[pkey(sec, s)] = false
  ElMessage.success(`已清除 ${secLabel(sec)}·${slotLabel(s)}：图 ${r?.data?.cleared ?? 0} 张 + 中英提示词`)
}
async function clearSection(sec: string) {
  if (!curId.value) return ElMessage.warning('未选角色')
  const k = kindOf(sec, attire.value[sec])
  const r: any = await api.clearSlotAssets(curId.value, k)
  await api.clearSlotPrompts(curId.value, k, '', 'both')
  for (const s of slots) {
    imgMap.value = dropKey(imgMap.value, `${k}|${s}`)
    promptCnMap.value = dropKey(promptCnMap.value, `${k}|${s}`)
    promptMap.value = dropKey(promptMap.value, `${k}|${s}`)
  }
  ElMessage.success(`已清空${secLabel(sec)}（${attireLabel(attire.value[sec])}）整组：图 ${r?.data?.cleared ?? 0} 张 + 三槽中英提示词`)
}
async function doIterate() { await api.iterate(curId.value, itDim.value, itIns.value); ElMessage.success('已迭代'); await loadVersions(); vPage.reset(); const r = await api.listCharacters(); const c = (r.data as any[]).find(x => x.id === curId.value); if (c) form.value = { ...c } }
async function loadVersions() { const r = await api.listVersions(curId.value); versions.value = r.data; vPage.reset() }
async function doRollback(id: number) { await api.rollback(curId.value, id); ElMessage.success('已回滚'); await loadChar() }
async function freeze() { const r = await api.freezeVersions(curId.value); ElMessage.success('已冻结，共' + (r.data as any).total + '版'); await loadVersions() }
async function delOutfit(id: number) { await api.deleteOutfit(curId.value, id); ElMessage.success('已删'); await loadOutfits() }
async function addOutfit() { await api.createOutfit(curId.value, { name: outName.value, category: outCat.value }); ElMessage.success('已新增'); await loadOutfits(); oPage.reset() }
async function loadOutfits() {
  const r = await api.listOutfits(curId.value); outfits.value = r.data; oPage.reset(); editId.value = null
  try {
    const c = await api.listOutfitCats(curId.value)
    const m: Record<string, string> = {}
    for (const row of (c.data as any[])) m[row.category] = row.description || ''
    catDescMap.value = m
  } catch {}
}
async function actOutfit(id: number) { await api.activateOutfit(curId.value, id); ElMessage.success('已激活'); await loadOutfits() }
// 卡片式一行一件：分类中文名 + 首字色块，编辑态就地改名/改分类/补描述
const outCatMap: Record<string, string> = { headwear: '头饰', top: '上装', bottom: '下装', shoes: '鞋' }
function outCatLabel(c: string) { return outCatMap[c] || c }
function outCatChip(c: string) { return (outCatMap[c] || c).slice(0, 1) }
function startEditOutfit(o: any) {
  if (editId.value === o.id) { editId.value = null; return }
  editId.value = o.id
  editForm.value = { name: o.name || '', category: o.category || 'top', description: o.description || '' }
}
async function saveOutfitEdit(id: number) {
  await api.updateOutfit(curId.value, id, editForm.value)
  ElMessage.success('已保存服装')
  await loadOutfits()
}
async function loadDoc() { const r = await api.getDoc(curId.value); docHtml.value = (r.data as any).doc_html || '' }
async function saveDoc() { await api.saveDoc(curId.value, docHtml.value); store.touchSaved(); ElMessage.success('已保存') }
async function loadPack() { const r = await api.pack(curId.value); pack.value = r.data }
async function onAvatar(e: any) { const f = e.target.files?.[0]; if (!f || !curId.value) return; api.uploadAvatar(curId.value, f).then(r => { form.value.avatar_path = (r.data as any).path; ElMessage.success('已上传') }) }
async function onSlot(sec: string, s: string, e: any) { const f = e.target.files?.[0]; if (!f || !curId.value) return; const k = kindOf(sec, attire.value[sec]); const r = await api.uploadSlotImage(curId.value, k, s, f); imgMap.value[`${k}|${s}`] = (r.data as any).url; ElMessage.success('已上传') }
onMounted(async () => {
  await reloadChars()
  try {
    const r = await api.imageModels()
    const rows = (r?.data || r || []) as any[]
    if (rows.length) imgModels.value = rows.map(x => ({ key: x.key, label: x.label, hint: x.hint || '' }))
  } catch {}
})
</script>
<style scoped>
.kun-page{max-width:none;margin:0;width:100%;box-sizing:border-box}
.worksec-head { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.worksec { max-width: 1140px; margin: 0 auto 4px; }
.slot-worklist { display: flex; flex-direction: column; gap: 12px; }
.slot-workcard { display: flex; flex-direction: column; gap: 10px; }
.slot-topbar { display: flex; gap: 8px; align-items: center; justify-content: space-between; }
.fold-summary { font-size: 12px; }
.slot-main { display: flex; gap: 16px; align-items: stretch; }
.slot-left, .slot-right { flex: 1 1 0; min-width: 0; }
.slot-right { display: flex; flex-direction: column; gap: 12px; }
.prompt-block { flex: 1 1 0; display: flex; flex-direction: column; gap: 6px; min-height: 0; }
.slot-title { display: flex; gap: 8px; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.slot-title b { font-size: 14px; }
.slot-name { display: flex; gap: 8px; align-items: center; min-width: 0; }
.slot-head-btns { display: flex; gap: 6px; align-items: center; flex-shrink: 0; }
.slot-prompt { flex: 1; }
.slot-prompt :deep(.el-textarea__inner) { min-height: 130px; height: 100%; resize: vertical; border-radius: 12px; line-height: 1.7; }
.prompt-cn :deep(.el-textarea__inner) { background: #fff; }
.prompt-en :deep(.el-textarea__inner) { background: var(--suli-bg-2); font-family: var(--suli-mono); font-size: 13px; }
.slot-actions { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; margin-top: 2px; }
/* 服装四分类：一行一件卡片（与槽位卡同族：顶栏 + 体部） */
.outfit-toolbar { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.outfit-list { display: flex; flex-direction: column; gap: 10px; margin-top: 12px; }
.outfit-card { padding: 12px; display: flex; flex-direction: column; gap: 8px; transition: border-color 0.15s, box-shadow 0.15s; }
.outfit-card:hover { border-color: var(--suli-border-hover); box-shadow: var(--suli-shadow-sm); }
.outfit-card.active { border-color: var(--suli-primary); }
.outfit-topbar { display: flex; gap: 8px; align-items: center; justify-content: space-between; flex-wrap: wrap; }
.outfit-name { display: flex; gap: 8px; align-items: center; min-width: 0; flex-wrap: wrap; }
.outfit-chip { width: 26px; height: 26px; flex: 0 0 26px; border-radius: 8px; display: inline-flex; align-items: center; justify-content: center; background: var(--suli-bg-2); color: var(--suli-text-2); font-size: 13px; font-weight: 800; border: 1.5px solid var(--suli-border); }
.outfit-card.active .outfit-chip { background: var(--suli-primary); border-color: var(--suli-primary); color: #fff; }
.outfit-desc { color: var(--suli-text-2); font-size: 13px; line-height: 1.7; white-space: pre-wrap; word-break: break-word; }
.outfit-edit { display: flex; flex-direction: column; gap: 8px; padding-top: 8px; border-top: 1px dashed var(--suli-border); }
.outfit-edit-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.outfit-edit-actions { display: flex; gap: 8px; justify-content: flex-end; }
@media (max-width: 900px) {
  .slot-main { flex-direction: column; }
  .slot-left, .slot-right { flex: none; width: 100%; max-width: none; }
  .slot-prompt :deep(.el-textarea__inner) { min-height: 160px; }
}
</style>
