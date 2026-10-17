import { createRouter, createWebHistory } from 'vue-router'

const CHUNK_RELOAD_KEY = 'suli-chunk-reloaded'
// 页面壳太旧（构建哈希已换）时，懒加载 chunk 会 404：自动硬刷新一次自愈，避免“点了导航没反应”
function withChunkRecovery(loader: () => Promise<unknown>) {
  return () =>
    loader().catch((err) => {
      try {
        if (!sessionStorage.getItem(CHUNK_RELOAD_KEY)) {
          sessionStorage.setItem(CHUNK_RELOAD_KEY, '1')
          window.location.reload()
        }
      } catch {}
      throw err
    })
}

export const routes = [
  { path: '/', component: withChunkRecovery(() => import('../views/GalleryView.vue')), meta: { title: '展览', icon: 'House' } },
  { path: '/story', component: withChunkRecovery(() => import('../views/StoryView.vue')), meta: { title: '故事', icon: 'Reading' } },
  { path: '/character', component: withChunkRecovery(() => import('../views/CharacterView.vue')), meta: { title: '角色', icon: 'User' } },
  { path: '/director', component: withChunkRecovery(() => import('../views/DirectorView.vue')), meta: { title: '导演', icon: 'VideoCamera' } },
  { path: '/board', component: withChunkRecovery(() => import('../views/ScriptboardView.vue')), meta: { title: '剧本分镜', icon: 'Film' } },
  { path: '/video', component: withChunkRecovery(() => import('../views/VideoLabView.vue')), meta: { title: '拉片室', icon: 'VideoPlay' } },
  { path: '/traffic', component: withChunkRecovery(() => import('../views/TrafficView.vue')), meta: { title: '投流批量', icon: 'Present' } },
  { path: '/art', component: withChunkRecovery(() => import('../views/ArtView.vue')), meta: { title: '美术工具', icon: 'Picture' } },
  { path: '/settings', component: withChunkRecovery(() => import('../views/SettingsView.vue')), meta: { title: '设置', icon: 'Setting' } },
]

export default createRouter({ history: createWebHistory(), routes })
