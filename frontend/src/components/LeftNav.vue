<template>
  <div class="left">
    <div class="brand">
      <div class="mark">S</div>
      <div><div class="logo">SuliAnimeCreator</div><div class="sub">原创漫剧工作台</div></div>
      <span style="flex:1" />
      <el-button size="small" circle @click="store.toggleLeft()">‹</el-button>
    </div>
    <el-menu :default-active="route.path" router>
      <el-menu-item index="/"><el-icon><House /></el-icon>展览</el-menu-item>
      <el-menu-item index="/story"><el-icon><Reading /></el-icon>故事</el-menu-item>
      <el-menu-item index="/character"><el-icon><User /></el-icon>角色</el-menu-item>
      <el-menu-item index="/director"><el-icon><VideoCamera /></el-icon>导演</el-menu-item>
      <el-menu-item index="/board"><el-icon><Film /></el-icon>剧本分镜</el-menu-item>
      <el-menu-item index="/video"><el-icon><VideoPlay /></el-icon>拉片室</el-menu-item>
      <el-menu-item index="/traffic"><el-icon><Present /></el-icon>投流批量</el-menu-item>
      <el-menu-item index="/art"><el-icon><Picture /></el-icon>美术工具</el-menu-item>
      <el-menu-item index="/studio"><el-icon><MagicStick /></el-icon>单图创作</el-menu-item>
    </el-menu>
    <div class="bottom">
      <el-menu :default-active="route.path" router>
        <el-menu-item index="/settings"><el-icon><Setting /></el-icon>设置</el-menu-item>
      </el-menu>
    </div>
  </div>
</template>
<script setup lang="ts">
import { useRoute } from 'vue-router'
import { House, Reading, User, Film, VideoCamera, VideoPlay, Picture, Setting, Present, MagicStick } from '@element-plus/icons-vue'
import { useAppStore } from '../stores/app'
const store = useAppStore()
const route = useRoute()
</script>
<style scoped>
.left{width:212px;box-sizing:border-box;background:var(--suli-surface);border-right:1px solid var(--suli-border);display:flex;flex-direction:column;max-height:100vh;overflow-y:auto;overflow-x:hidden;flex-shrink:0}
.brand{display:flex;gap:10px;align-items:center;padding:12px;border-bottom:1px solid var(--suli-border)}
.mark{width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,var(--suli-primary),var(--suli-accent));color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:15px;box-shadow:var(--suli-shadow-sm)}
.logo{font-weight:650;font-size:13px;letter-spacing:-0.01em}.sub{font-size:12px;color:var(--suli-text-2)}
.bottom{margin-top:auto;border-top:1px solid var(--suli-border)}
.left .el-menu-item .el-icon{margin-right:2px}
</style>
