<template>
  <div class="suli-card kun-page" style="padding:14px">
    <div class="eyebrow kana">絵コンテ STORYBOARD</div>
    <h3>剧本分镜 · 手工画布</h3>
    <el-input v-model="script" type="textarea" :rows="4" placeholder="剧本（手工排镜的底稿，只存不拆）" />
    <div style="margin-top:8px;display:flex;gap:8px;align-items:center;flex-wrap:wrap">
      <el-button @click="save">保存剧本</el-button>
      <el-button type="primary" @click="addShot" :disabled="!canAdd">添加新镜</el-button>
      <span style="flex:1" />
      <el-tag size="small" class="tnum">{{ stat.shots }}镜</el-tag>
      <el-tag size="small" class="tnum">{{ stat.total_s }}s</el-tag>
      <el-tag size="small" :type="stat.verdict === 'PASS' ? 'success' : stat.verdict === 'BLOCK' ? 'danger' : 'info'">{{ stat.verdict }}</el-tag>
    </div>
    <el-empty v-if="!rows.length" description="无分镜，从下面待添加行逐行加" :image-size="64" />
    <div v-else class="shot-flow">
      <div v-for="(r, i) in rows" :key="r.id" class="suli-card shot-card">
        <div class="shot-head">
          <span class="shot-no tnum">{{ i + 1 }}</span>
          <span class="shot-sid">{{ r.id }}</span>
          <el-select v-model="r.camera.crop" style="width:130px" @change="saveRow(r, true)">
            <el-option v-for="c in crops" :key="c.value" :label="c.label" :value="c.value" />
          </el-select>
          <el-select v-model="r.camera.movement" style="width:110px" placeholder="运镜" @change="saveRow(r, true)">
            <el-option v-for="m in movements" :key="m" :label="m" :value="m" />
          </el-select>
          <el-input-number v-model="r.duration_s" style="width:140px" :min="0.5" :max="30" :step="0.5" @change="saveRow(r)" />
          <span class="suli-muted" style="font-size:13px">秒</span>
          <span style="flex:1" />
          <el-button link @click="move(i, -1)" :disabled="i === 0">↑</el-button>
          <el-button link @click="move(i, 1)" :disabled="i === rows.length - 1">↓</el-button>
          <el-button link type="primary" @click="saveRow(r)">存</el-button>
          <el-popconfirm title="删掉该镜？" confirm-button-text="删" cancel-button-text="留" @confirm="removeShot(r.id)">
            <template #reference><el-button link type="danger">删</el-button></template>
          </el-popconfirm>
        </div>
        <el-input v-model="r.duty" placeholder="画面内容：一句话写清这镜拍什么" @blur="saveRow(r)" />
        <el-input v-model="r.sound" placeholder="口播/台词/字幕" @blur="saveRow(r)" />
        <div class="shot-pics">
          <div class="shot-pic">
            <span class="shot-kind">首帧</span>
            <el-image v-if="shotByKind(r, 'first')" :src="imgUrl(shotByKind(r, 'first').name)" :preview-src-list="[imgUrl(shotByKind(r, 'first').name)]" fit="cover" class="shot-thumb lg" preview-teleported />
            <el-button v-else link type="primary" @click="pickShotFile(r, 'first')">+首帧</el-button>
            <el-button v-if="shotByKind(r, 'first')" link type="danger" @click="delShotImg(r, shotByKind(r, 'first').name)">删</el-button>
          </div>
          <div class="shot-pic">
            <span class="shot-kind">尾帧</span>
            <el-image v-if="shotByKind(r, 'last')" :src="imgUrl(shotByKind(r, 'last').name)" :preview-src-list="[imgUrl(shotByKind(r, 'last').name)]" fit="cover" class="shot-thumb lg" preview-teleported />
            <el-button v-else link type="primary" @click="pickShotFile(r, 'last')">+尾帧</el-button>
            <el-button v-if="shotByKind(r, 'last')" link type="danger" @click="delShotImg(r, shotByKind(r, 'last').name)">删</el-button>
          </div>
          <div class="shot-pic">
            <span class="shot-kind">参考</span>
            <span v-for="im in shotRefImgs(r)" :key="im.name" class="shot-refwrap">
              <el-image :src="imgUrl(im.name)" :preview-src-list="[imgUrl(im.name)]" fit="cover" class="shot-thumb sm" preview-teleported />
              <el-button link type="danger" @click="delShotImg(r, im.name)">×</el-button>
            </span>
            <el-button link type="primary" @click="pickShotFile(r, 'ref')">+参考</el-button>
          </div>
        </div>
        <input :ref="(el: any) => { if (el) shotRefs[r.id] = el }" type="file" accept="image/*" hidden @change="(e: any) => onShotImg(r, e)" />
      </div>
    </div>
    <div class="suli-card" style="margin-top:10px;padding:10px;border-style:dashed">
      <div class="suli-muted" style="font-size:12px;margin-bottom:6px">待添加 · 写一行加一镜（回车即加）</div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
        <el-select v-model="draft.crop" size="small" style="width:120px">
          <el-option v-for="c in crops" :key="c.value" :label="c.label" :value="c.value" />
        </el-select>
        <el-select v-model="draft.movement" size="small" style="width:100px">
          <el-option v-for="m in movements" :key="m" :label="m" :value="m" />
        </el-select>
        <el-input v-model="draft.duty" size="small" placeholder="职责/内容" style="flex:2;min-width:160px" @keyup.enter="addShot" />
        <el-input v-model="draft.sound" size="small" placeholder="台词/声音" style="flex:2;min-width:140px" @keyup.enter="addShot" />
        <el-input-number v-model="draft.duration" size="small" :min="0.5" :max="30" :step="0.5" />
        <el-button type="primary" size="small" @click="addShot" :disabled="!canAdd">添加新镜</el-button>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import { useAppStore } from '../stores/app'
const store = useAppStore()
const script = ref('## EP001-SC001 内·洗衣房·夜\n沈禾：取衣牌呢？\n蒋姨：烘干机停了。')
const rows = computed(() => store.shots)
const crops = [
  { label: '大特写', value: 'extreme_close' }, { label: '特写', value: 'closeup' },
  { label: '近景', value: 'close' }, { label: '中近景', value: 'medium_close' },
  { label: '中景', value: 'medium' }, { label: '中全景', value: 'medium_full' },
  { label: '全景', value: 'full' }, { label: '远景', value: 'wide' },
  { label: '大远景', value: 'extreme_wide' },
]
const draft = ref({ crop: 'medium', movement: '固定', duty: '', sound: '', duration: 3 })
const shotRefs = ref<Record<string, HTMLInputElement>>({})
const shotKind = ref<Record<string, string>>({})
function imgUrl(name: string) { return `/api/images/${name}` }
function shotImgs(r: any): any[] {
  if (!r) return []
  if (r.images && r.images.length) return r.images
  if (r.image) return [{ name: r.image, kind: 'ref' }]
  return []
}
function shotByKind(r: any, kind: string) { return shotImgs(r).find(x => x.kind === kind) }
function shotRefImgs(r: any) { return shotImgs(r).filter(x => !x.kind || x.kind === 'ref') }
function shortId(id: string) { const p = String(id || '').split('-'); return p.length > 1 ? p[p.length - 1] : String(id || '') }
const movements = ['固定', '推', '拉', '摇', '移', '跟', '环绕', '升降', '手持', '航拍']
const canAdd = computed(() => draft.value.duty.trim() !== '' || draft.value.sound.trim() !== '')
async function save() { await api.saveScreenplay(store.episodeId, script.value); ElMessage.success('已保存') }
async function loadShots() { const r = await api.listShots(store.episodeId); store.shots = r.data; await loadStat() }
const stat = ref<any>({ verdict: 'draft', shots: 0, total_s: 0 })
async function loadStat() { try { const r = await api.reviewStat(store.episodeId); stat.value = r.data } catch {} }
async function addShot() {
  if (!canAdd.value) return ElMessage.warning('先写职责或台词')
  await api.createShot({ episode_id: store.episodeId, duty: draft.value.duty.trim(), sound: draft.value.sound.trim(), duration_s: draft.value.duration, camera: { crop: draft.value.crop, movement: draft.value.movement } })
  draft.value = { crop: 'medium', movement: '固定', duty: '', sound: '', duration: 3 }
  ElMessage.success('已加一镜')
  await loadShots()
}
async function saveRow(r: any, silent = false) {
  await api.updateShot(r.id, { duty: r.duty, duration_s: r.duration_s, sound: r.sound, camera: { crop: r.camera?.crop || 'medium', movement: r.camera?.movement || '固定' } })
  if (!silent) ElMessage.success('已保存')
  await loadStat()
}
async function move(i: number, dir: number) {
  const a = rows.value[i]
  const b = rows.value[i + dir]
  if (!a || !b) return
  const t = a.ord ?? i
  await api.updateShot(a.id, { ord: b.ord ?? (i + dir) })
  await api.updateShot(b.id, { ord: t })
  await loadShots()
}
async function removeShot(id: string) { await api.deleteShot(id); ElMessage.success('已删'); await loadShots() }
async function onShotImg(r: any, e: any) {
  const f = e.target.files?.[0]
  e.target.value = ''
  if (!f) return
  const kind = shotKind.value[r.id] || 'ref'
  await api.uploadShotImage(r.id, f, kind)
  ElMessage.success(kind === 'ref' ? '参考图已上传' : (kind === 'first' ? '首帧已上传' : '尾帧已上传'))
  await loadShots()
}
function pickShotFile(r: any, kind: string) { shotKind.value[r.id] = kind; shotRefs.value[r.id]?.click() }
async function delShotImg(r: any, name: string) { await api.deleteShotImage(r.id, name); ElMessage.success('已删'); await loadShots() }
onMounted(loadShots)
</script>
<style scoped>
.shot-flow { display: flex; flex-direction: column; gap: 12px; margin-top: 10px; }
.shot-card { padding: 14px; display: flex; flex-direction: column; gap: 10px; }
.shot-head { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.shot-no { width: 30px; height: 30px; border-radius: 50%; background: var(--suli-primary); color: #fff; font-size: 14px; font-weight: 800; display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; }
.shot-sid { font-family: var(--suli-mono); font-size: 13px; white-space: nowrap; }
.shot-pics { display: flex; gap: 16px; flex-wrap: wrap; align-items: center; padding: 4px 0; }
.shot-pic { display: flex; gap: 8px; align-items: center; }
.shot-kind { font-size: 13px; color: var(--suli-text-2); flex-shrink: 0; }
.shot-thumb { border-radius: 8px; }
.shot-thumb.lg { width: 96px; height: 72px; }
.shot-thumb.sm { width: 64px; height: 48px; }
.shot-refwrap { display: inline-flex; gap: 4px; align-items: center; }
</style>
