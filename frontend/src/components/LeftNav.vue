<template>
  <div class="left">
    <div class="brand">
      <div class="mark">S</div>
      <div><div class="logo">SuliAnimeCreator</div><div class="sub">原创漫剧工作台</div></div>
      <span style="flex:1" />
      <el-button size="small" circle @click="store.toggleLeft()">‹</el-button>
    </div>
    <el-menu :default-active="route.path" router>
      <el-menu-item index="/"><el-icon><House /></el-icon>展览 <span class="kana">トップ</span></el-menu-item>
      <el-menu-item index="/story"><el-icon><Reading /></el-icon>故事 <span class="kana">ストーリー</span></el-menu-item>
      <el-menu-item index="/character"><el-icon><User /></el-icon>角色 <span class="kana">キャラ</span></el-menu-item>
      <el-menu-item index="/board"><el-icon><Film /></el-icon>剧本分镜 <span class="kana">絵コンテ</span></el-menu-item>
      <el-menu-item index="/director"><el-icon><VideoCamera /></el-icon>导演 <span class="kana">監督</span></el-menu-item>
      <el-menu-item index="/art"><el-icon><Picture /></el-icon>美术工具 <span class="kana">画材</span></el-menu-item>
    </el-menu>
    <div class="foot">
      <el-tag size="small" :type="store.health ? 'success' : 'warning'">{{ store.health ? '后端已接通' : '本地Mock' }}</el-tag>
      <span style="flex:1" />
      <el-button size="small" @click="store.toggleRight()">{{ store.rightCollapsed ? '开Agent' : '收Agent' }}</el-button>
    </div>
  </div>
</template>
<script setup lang="ts">
import { useRoute } from 'vue-router'
import { House, Reading, User, Film, VideoCamera, Picture } from '@element-plus/icons-vue'
import { useAppStore } from '../stores/app'
const store = useAppStore()
const route = useRoute()
</script>
<style scoped>
.left{width:212px;background:var(--suli-surface);border-right:1px solid var(--suli-border);display:flex;flex-direction:column}
.brand{display:flex;gap:10px;align-items:center;padding:12px;border-bottom:1px solid var(--suli-border)}
.mark{width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,var(--suli-primary),var(--suli-accent));color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:15px;box-shadow:var(--suli-shadow-sm)}
.logo{font-weight:650;font-size:13px;letter-spacing:-0.01em}.sub{font-size:12px;color:var(--suli-text-2)}
.foot{margin-top:auto;padding:12px;display:flex;gap:8px;align-items:center;border-top:1px solid var(--suli-border)}
.left .kana{font-size:10px;opacity:.7}
.left .el-menu-item .el-icon{margin-right:2px}
</style>
