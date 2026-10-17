<template>
  <div class="md-view" v-html="html" @click="onClick" />
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { renderMarkdown } from '../utils/markdown'
import { copyText } from '../utils/clipboard'
const props = defineProps<{ content: string }>()
const html = computed(() => renderMarkdown(props.content || ''))
function onClick(e: MouseEvent) {
  const btn = (e.target as HTMLElement)?.closest?.('.md-copy') as HTMLElement | null
  if (!btn) return
  const wrap = btn.closest('.md-code-wrap')
  const code = wrap?.querySelector('pre code')
  const text = (code?.textContent ?? '').replace(/\n$/, '')
  if (!text) return
  btn.textContent = '已复制'
  setTimeout(() => { btn.textContent = '复制' }, 1200)
  copyText(text)
}
</script>
<style scoped>
.md-view { font-size: 13px; line-height: 1.75; color: var(--el-text-color-primary, #303133); word-break: break-word; }
.md-view :deep(p) { margin: 0 0 8px; }
.md-view :deep(h1), .md-view :deep(h2), .md-view :deep(h3), .md-view :deep(h4) { margin: 12px 0 6px; line-height: 1.4; }
.md-view :deep(h1) { font-size: 16px; }
.md-view :deep(h2) { font-size: 15px; }
.md-view :deep(h3), .md-view :deep(h4) { font-size: 14px; }
.md-view :deep(h1):first-child, .md-view :deep(h2):first-child, .md-view :deep(p):first-child { margin-top: 0; }
.md-view :deep(ul), .md-view :deep(ol) { margin: 0 0 8px; padding-left: 20px; }
.md-view :deep(li) { margin: 2px 0; }
.md-view :deep(code) { font-family: var(--suli-mono, monospace); font-size: 12px; background: var(--el-fill-color-light, #f2f3f5); border-radius: 4px; padding: 1px 5px; }
.md-view :deep(pre) { background: var(--el-fill-color-lighter, #f4f4f5); border-radius: 8px; padding: 10px; overflow-x: auto; }
.md-view :deep(pre code) { background: none; padding: 0; }
.md-view :deep(.md-code-wrap) { position: relative; margin: 0 0 8px; }
.md-view :deep(.md-code-wrap pre) { margin: 0; padding-top: 28px; }
.md-view :deep(.md-copy) { position: absolute; top: 6px; right: 6px; font-size: 11px; line-height: 1; padding: 4px 10px; border-radius: 6px; border: 1px solid var(--el-border-color, #dcdfe6); background: #fff; color: var(--el-text-color-secondary, #606266); cursor: pointer; }
.md-view :deep(.md-copy:hover) { color: var(--el-color-primary, #409eff); border-color: var(--el-color-primary, #409eff); }
.md-view :deep(blockquote) { margin: 0 0 8px; padding: 6px 10px; border-left: 3px solid var(--el-border-color, #dcdfe6); color: var(--el-text-color-secondary, #606266); background: var(--el-fill-color-lighter, #f4f4f5); border-radius: 0 8px 8px 0; }
.md-view :deep(hr) { border: none; border-top: 1px solid var(--el-border-color, #dcdfe6); margin: 10px 0; }
.md-view :deep(a) { color: var(--el-color-primary, #409eff); }
.md-view :deep(del) { color: var(--el-text-color-secondary, #606266); }
.md-view :deep(.md-task) { list-style: none; margin-left: -20px; display: flex; gap: 6px; align-items: flex-start; }
.md-view :deep(.md-task input) { margin-top: 5px; accent-color: var(--el-color-primary, #409eff); }
.md-view :deep(.md-img-wrap) { display: block; margin: 6px 0; }
.md-view :deep(.md-img) { max-width: 100%; border-radius: 8px; border: 1px solid var(--el-border-color, #dcdfe6); display: block; }
.md-table-wrap, .md-view :deep(.md-table-wrap) { overflow-x: auto; margin: 0 0 8px; }
.md-view :deep(table) { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.md-view :deep(th), .md-view :deep(td) { border: 1px solid var(--el-border-color, #dcdfe6); padding: 5px 8px; text-align: left; vertical-align: top; }
.md-view :deep(th) { background: var(--el-fill-color-light, #f2f3f5); white-space: nowrap; }
</style>
