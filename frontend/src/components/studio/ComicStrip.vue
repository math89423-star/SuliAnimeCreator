<template>
  <div class="comic-bar">
    <!-- 集号 + 大纲 -->
    <div class="comic-row">
      <span class="lbl">集号</span>
      <b class="tnum ep">{{ episodeId || '未选' }}</b>
      <el-button size="small" :loading="outlineLoading" @click="$emit('read-outline')">读大纲</el-button>
      <el-button size="small" :disabled="!outline" @click="$emit('apply-outline')">写入本页</el-button>
      <span class="suli-muted tnum">{{ outline ? `${outline.length} 字` : '未读' }}</span>
      <span style="flex:1" />
      <el-button size="small" type="primary" @click="$emit('new-page')">+ 新页</el-button>
    </div>

    <div v-if="outline" class="outline-box">
      <div class="outline-head">
        <b>大纲</b>
        <span style="flex:1" />
        <el-button size="small" text @click="expanded = !expanded">{{ expanded ? '收起' : '展开' }}</el-button>
      </div>
      <pre v-if="expanded" class="outline-md">{{ outline }}</pre>
      <div v-else class="outline-peek">{{ peek }}</div>
    </div>

    <slot name="script" />

    <!-- 页条：第几页 -->
    <div class="strip-head">
      <span class="lbl">页</span>
      <span class="suli-muted tnum">{{ pages.length }}</span>
    </div>
    <div class="page-strip">
      <div
        v-for="p in pages" :key="p.index"
        class="page-card" :class="{ active: p.index === currentPageIndex }"
        @click="$emit('select-page', p.index)"
      >
        <div class="page-thumb">
          <el-image v-if="p.image" :src="p.image.url" fit="cover" :preview-src-list="[p.image.url]" preview-teleported hide-on-click-modal />
          <span v-else class="page-no">{{ p.index }}</span>
        </div>
        <div class="page-meta">
          <b>第{{ p.index }}页</b>
          <el-tag size="small" type="info">{{ p.panelCount }} 格</el-tag>
        </div>
        <div class="page-sub tnum">{{ p.promptCount ? `${p.promptCount} 提示词` : '—' }}</div>
      </div>
      <div v-if="!pages.length" class="suli-muted strip-empty">无页</div>
    </div>

    <!-- 格条：当前页的第几格 -->
    <div class="strip-head">
      <span class="lbl">格</span>
      <span class="suli-muted tnum">{{ panels.length }}</span>
      <span style="flex:1" />
      <el-button size="small" type="primary" plain :disabled="!currentPageIndex" @click="$emit('new-panel')">+ 一格</el-button>
    </div>
    <div class="page-strip">
      <div
        v-for="p in panels" :key="p.planId"
        class="page-card" :class="{ active: p.planId === currentPlanId }"
        @click="$emit('select', p.planId)"
      >
        <div class="page-thumb">
          <el-image v-if="p.image" :src="p.image.url" fit="cover" :preview-src-list="[p.image.url]" preview-teleported hide-on-click-modal />
          <span v-else class="page-no">{{ p.panelIndex }}</span>
        </div>
        <div class="page-meta">
          <b>第{{ p.panelIndex }}格</b>
          <el-tag size="small" :type="statusType(p.status)">{{ statusLabel(p.status) }}</el-tag>
        </div>
        <div class="page-sub tnum">{{ p.promptCount ? `${p.promptCount} 提示词` : '—' }}</div>
      </div>
      <div v-if="!panels.length" class="suli-muted strip-empty">无格</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

/** 一格 = 一个方案（一次直投 = 一格出图） */
export interface ComicPanel {
  planId: string
  pageIndex: number
  panelIndex: number
  title: string
  status: string
  promptCount: number
  image: { name: string; path: string; url: string } | null
}
/** 一页 = 若干格（按 pageIndex 聚合） */
export interface ComicPage {
  index: number
  panels: ComicPanel[]
  panelCount: number
  promptCount: number
  image: { name: string; path: string; url: string } | null
}

const props = defineProps<{
  pages: ComicPage[]
  panels: ComicPanel[]
  currentPageIndex: number
  currentPlanId: string
  episodeId: string
  outline: string
  outlineLoading?: boolean
}>()

defineEmits<{
  (e: 'select', planId: string): void
  (e: 'select-page', pageIndex: number): void
  (e: 'new-page'): void
  (e: 'new-panel'): void
  (e: 'read-outline'): void
  (e: 'apply-outline'): void
}>()

const expanded = ref(false)
const peek = computed(() => {
  const t = (props.outline || '').replace(/^#+\s*/gm, '').trim()
  return t.length > 160 ? t.slice(0, 160) + '…' : t
})
const STATUS_LABEL: Record<string, string> = { draft: '草案', pushed: '已投', returned: '已回传' }
function statusLabel(s: string) { return STATUS_LABEL[s] || s }
function statusType(s: string): 'success' | 'warning' | 'info' {
  return s === 'returned' ? 'success' : s === 'pushed' ? 'warning' : 'info'
}
</script>

<style scoped>
.comic-bar { margin-top:10px; }
.comic-row { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.comic-row .lbl { font-size:13px; color:var(--suli-text-2); }
.comic-row .ep { font-size:14px; }
.outline-box { margin-top:8px; border:1px solid var(--el-border-color-lighter); border-radius:10px; padding:8px 10px; background:var(--el-fill-color-lighter); }
.outline-head { display:flex; align-items:center; gap:8px; font-size:13px; }
.outline-md { margin:6px 0 0; max-height:220px; overflow:auto; white-space:pre-wrap; word-break:break-word; font-size:12px; line-height:1.5; }
.outline-peek { margin-top:4px; font-size:12px; color:var(--suli-text-2); white-space:pre-wrap; word-break:break-word; }
.strip-head { display:flex; align-items:center; gap:6px; margin-top:10px; }
.strip-head .lbl { font-size:12px; color:var(--suli-text-2); font-weight:600; }
.page-strip { display:flex; gap:10px; overflow-x:auto; padding:6px 2px 4px; align-items:stretch; }
.page-card { flex:0 0 auto; width:104px; border:1px solid var(--el-border-color-lighter); border-radius:10px; padding:6px; cursor:pointer; background:var(--suli-surface); }
.page-card:hover { border-color:var(--suli-primary); }
.page-card.active { border-color:var(--suli-primary); box-shadow:0 0 0 1px var(--suli-primary) inset; }
.page-thumb { width:92px; height:116px; border-radius:8px; overflow:hidden; background:var(--el-fill-color-light); display:flex; align-items:center; justify-content:center; }
.page-thumb :deep(.el-image) { width:100%; height:100%; }
.page-no { font-size:24px; font-weight:800; color:var(--suli-text-3); }
.page-meta { display:flex; align-items:center; gap:6px; margin-top:6px; font-size:12px; }
.page-meta b { font-size:12px; }
.page-sub { margin-top:2px; font-size:11px; color:var(--suli-text-3); }
.strip-empty { font-size:12px; padding:12px 4px; }
</style>
