<template>
  <div class="script-box">
    <div class="script-head">
      <b>剧本</b>
      <span class="suli-muted tnum">{{ panels.length }} 格</span>
      <span style="flex:1" />
      <el-button size="small" :loading="busy === 'outline'" @click="$emit('from-outline')">从大纲转</el-button>
      <el-button size="small" :loading="busy === 'save'" @click="$emit('save')">存剧本</el-button>
      <el-button size="small" type="primary" :loading="busy === 'split'" @click="$emit('split')">拆格</el-button>
    </div>

    <div class="script-meta">
      <label class="m-row">
        <span class="m-lbl">前提</span>
        <el-input v-model="meta.premise" size="small" placeholder="一句话剧情前提" />
      </label>
      <label class="m-row">
        <span class="m-lbl">角色</span>
        <el-input v-model="meta.characters" size="small" placeholder="谁、外观锚点、关系" />
      </label>
      <label class="m-row">
        <span class="m-lbl">画风</span>
        <el-input v-model="meta.style_hint" size="small" placeholder="线条/上色/配色/表面" />
      </label>
      <label class="m-row m-row-tier">
        <span class="m-lbl">默认水位</span>
        <el-select v-model="meta.tier" size="small" clearable placeholder="常规">
          <el-option v-for="t in TIERS" :key="t.value" :label="t.label" :value="t.value" />
        </el-select>
      </label>
    </div>

    <div v-if="!panels.length" class="suli-muted script-empty">无格</div>

    <div v-else class="script-table">
      <div class="srow srow-head">
        <span class="c-page">页</span>
        <span class="c-panel">格</span>
        <span class="c-text">画面</span>
        <span class="c-dialogue">台词</span>
        <span class="c-camera">景别/运镜</span>
        <span class="c-tier">水位</span>
        <span class="c-cloth">衣物</span>
        <span class="c-op"></span>
      </div>
      <div v-for="(p, i) in panels" :key="i" class="srow">
        <span class="c-page"><el-input v-model="p.page" size="small" type="number" :min="1" /></span>
        <span class="c-panel"><el-input v-model="p.panel" size="small" type="number" :min="1" /></span>
        <span class="c-text"><el-input v-model="p.text" size="small" type="textarea" :rows="1" autosize /></span>
        <span class="c-dialogue"><el-input v-model="p.dialogue" size="small" type="textarea" :rows="1" autosize /></span>
        <span class="c-camera"><el-input v-model="p.camera" size="small" /></span>
        <span class="c-tier">
          <el-select v-model="p.tier" size="small" clearable placeholder="常规">
            <el-option v-for="t in TIERS" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </span>
        <span class="c-cloth">
          <el-select v-model="p.clothing_level" size="small" clearable placeholder="—">
            <el-option v-for="c in CLOTH" :key="c" :label="c" :value="c" />
          </el-select>
        </span>
        <span class="c-op"><el-button size="small" text type="danger" @click="remove(i)">删</el-button></span>
      </div>
    </div>

    <div v-if="panels.length" class="script-foot">
      <el-button size="small" text @click="addRow">+ 格</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { TIERS, CLOTH } from '../../utils/tier'

export interface ScriptPanel {
  page: number
  panel: number
  text: string
  dialogue: string
  camera: string
  note?: string
  tier?: string
  clothing_level?: string
}

/** 本本元信息：前提 / 角色 / 画风 / 默认水位 */
export interface ScriptMeta {
  premise: string
  characters: string
  style_hint: string
  tier: string
}

const props = defineProps<{
  panels: ScriptPanel[]
  meta: ScriptMeta
  busy?: string
}>()

const emit = defineEmits<{
  (e: 'from-outline'): void
  (e: 'save'): void
  (e: 'split'): void
  (e: 'update:panels', v: ScriptPanel[]): void
  (e: 'update:meta', v: ScriptMeta): void
}>()

function remove(i: number) {
  emit('update:panels', props.panels.filter((_, k) => k !== i))
}
function addRow() {
  const last = props.panels[props.panels.length - 1]
  const next = {
    page: last ? last.page : 1,
    panel: last ? last.panel + 1 : 1,
    text: '',
    dialogue: '',
    camera: '',
    note: '',
    tier: props.meta.tier || '',
    clothing_level: '',
  }
  emit('update:panels', [...props.panels, next])
}
</script>

<style scoped>
.script-box { margin-top:10px; border:1px solid var(--el-border-color-lighter); border-radius:10px; padding:8px 10px; }
.script-head { display:flex; align-items:center; gap:8px; font-size:13px; }
.script-empty { font-size:12px; padding:10px 2px; }
.script-meta { margin-top:6px; display:grid; grid-template-columns:repeat(2,minmax(200px,1fr)); gap:4px 12px; }
.m-row { display:flex; align-items:center; gap:6px; }
.m-lbl { font-size:12px; color:var(--suli-text-2); width:52px; flex:0 0 auto; }
.m-row-tier :deep(.el-select) { flex:1; }
.script-table { margin-top:6px; max-height:320px; overflow:auto; }
.srow { display:grid; grid-template-columns:52px 52px minmax(140px,2fr) minmax(90px,1fr) minmax(90px,1fr) 92px 74px 36px; gap:6px; align-items:start; padding:3px 0; }
.srow-head { font-size:12px; color:var(--suli-text-2); border-bottom:1px solid var(--suli-border); padding-bottom:5px; position:sticky; top:0; background:var(--suli-surface); }
.srow :deep(.el-textarea__inner) { padding:4px 6px; }
.script-foot { margin-top:4px; }
</style>
