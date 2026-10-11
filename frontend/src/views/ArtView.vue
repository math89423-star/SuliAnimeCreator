<template>
  <div class="suli-card kun-page" style="padding:14px">
    <div class="eyebrow kana">画材 ART TOOLS</div>
    <h3>美术工具</h3>
    <el-button @click="loadTools" :loading="loading">刷新工具</el-button>
    <span class="suli-muted" style="margin-left:8px;font-size:12px">点开进右侧速查浮窗，不跳新页面，切路由保留</span>
    <el-empty v-if="!tools.length && !loading" description="无工具" :image-size="64" />
    <el-table v-else :data="pageRows" style="margin-top:8px">
      <el-table-column prop="name" label="工具" width="110" />
      <el-table-column prop="desc" label="说明" />
      <el-table-column label="打开" width="110"><template #default="s"><el-button link type="primary" @click="openInRef(s.row.id)">速查打开</el-button></template></el-table-column>
    </el-table>
    <el-pagination v-if="pg.total.value > 0" v-model:current-page="pg.page.value" v-model:page-size="pg.pageSize.value" :total="pg.total.value" layout="prev, pager, next, total" style="margin-top:8px;justify-content:flex-end" />
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '../api/client'
import { usePagination } from '../composables/usePagination'
import { useAppStore } from '../stores/app'
const store = useAppStore()
const tools = ref<any[]>([])
const loading = ref(false)
const pg = usePagination(() => tools.value, 5)
const pageRows = pg.rows
async function loadTools() { loading.value = true; try { const r = await api.artTools(); tools.value = r.data; pg.reset() } finally { loading.value = false } }
function openInRef(id: string) { store.openQuickRef(id) }
onMounted(loadTools)
</script>
