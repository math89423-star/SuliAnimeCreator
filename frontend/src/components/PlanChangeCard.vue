<template>
  <div class="pcc">
    <div class="pcc-head">
      <b>方案变更</b>
      <span class="suli-muted tnum">{{ rows.length }} 项</span>
      <span style="flex:1" />
      <span class="pcc-id">{{ planId }}</span>
      <el-button v-if="action" size="small" text @click="$emit('action')">载入</el-button>
    </div>
    <div class="pcc-body">
      <div v-for="r in rows" :key="r.key" class="pcc-row">
        <span class="pcc-label">{{ r.label }}</span>
        <div class="pcc-lines">
          <div v-if="r.before" class="pcc-old">{{ r.before }}</div>
          <div v-if="r.after" class="pcc-new">{{ r.after }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PlanDiffRow } from '../utils/planDiff'

defineProps<{ planId: string; rows: PlanDiffRow[]; action?: boolean }>()
defineEmits<{ (e: 'action'): void }>()
</script>

<style scoped>
.pcc{margin-top:8px;border:1px solid var(--suli-border);border-radius:10px;background:var(--suli-bg-2);overflow:hidden}
.pcc-head{display:flex;align-items:center;gap:6px;padding:6px 9px;font-size:12px;border-bottom:1px solid var(--suli-border)}
.pcc-id{font-size:11px;color:var(--suli-text-3);max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pcc-body{max-height:160px;overflow:auto;padding:7px 9px;display:flex;flex-direction:column;gap:7px}
.pcc-row{display:flex;gap:8px;align-items:flex-start}
.pcc-label{flex:0 0 54px;font-size:11px;color:var(--suli-text-2);line-height:1.5;padding-top:1px}
.pcc-lines{flex:1;min-width:0;display:flex;flex-direction:column;gap:2px}
.pcc-old{font-size:11.5px;line-height:1.5;color:var(--suli-text-3);text-decoration:line-through;word-break:break-word;white-space:pre-wrap}
.pcc-new{font-size:11.5px;line-height:1.5;color:var(--suli-success);word-break:break-word;white-space:pre-wrap}
</style>
