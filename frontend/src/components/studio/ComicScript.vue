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

    <div v-if="!panels.length" class="suli-muted script-empty">无格</div>

    <div v-else class="script-table">
      <div class="srow srow-head">
        <span class="c-page">页</span>
        <span class="c-panel">格</span>
        <span class="c-text">画面</span>
        <span class="c-dialogue">台词</span>
        <span class="c-camera">景别/运镜</span>
        <span class="c-op"></span>
      </div>
      <div v-for="(p, i) in panels" :key="i" class="srow">
        <span class="c-page"><el-input v-model="p.page" size="small" type="number" :min="1" /></span>
        <span class="c-panel"><el-input v-model="p.panel" size="small" type="number" :min="1" /></span>
        <span class="c-text"><el-input v-model="p.text" size="small" type="textarea" :rows="1" autosize /></span>
        <span class="c-dialogue"><el-input v-model="p.dialogue" size="small" type="textarea" :rows="1" autosize /></span>
        <span class="c-camera"><el-input v-model="p.camera" size="small" /></span>
        <span class="c-op"><el-button size="small" text type="danger" @click="remove(i)">删</el-button></span>
      </div>
    </div>

    <div v-if="panels.length" class="script-foot">
      <el-button size="small" text @click="addRow">+ 格</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
export interface ScriptPanel {
  page: number
  panel: number
  text: string
  dialogue: string
  camera: string
  note?: string
}

const props = defineProps<{
  panels: ScriptPanel[]
  busy?: string
}>()

const emit = defineEmits<{
  (e: 'from-outline'): void
  (e: 'save'): void
  (e: 'split'): void
  (e: 'update:panels', v: ScriptPanel[]): void
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
  }
  emit('update:panels', [...props.panels, next])
}
</script>

<style scoped>
.script-box { margin-top:10px; border:1px solid var(--el-border-color-lighter); border-radius:10px; padding:8px 10px; }
.script-head { display:flex; align-items:center; gap:8px; font-size:13px; }
.script-empty { font-size:12px; padding:10px 2px; }
.script-table { margin-top:6px; max-height:320px; overflow:auto; }
.srow { display:grid; grid-template-columns:56px 56px minmax(160px,2fr) minmax(100px,1fr) minmax(100px,1fr) 40px; gap:6px; align-items:start; padding:3px 0; }
.srow-head { font-size:12px; color:var(--suli-text-2); border-bottom:1px solid var(--suli-border); padding-bottom:5px; position:sticky; top:0; background:var(--suli-surface); }
.srow :deep(.el-textarea__inner) { padding:4px 6px; }
.script-foot { margin-top:4px; }
</style>
