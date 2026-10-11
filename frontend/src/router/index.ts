import { createRouter, createWebHistory } from 'vue-router'

export const routes = [
  { path: '/', component: () => import('../views/GalleryView.vue'), meta: { title: '展览', icon: '🏠' } },
  { path: '/story', component: () => import('../views/StoryView.vue'), meta: { title: '故事', icon: '📖' } },
  { path: '/character', component: () => import('../views/CharacterView.vue'), meta: { title: '角色', icon: '🧬' } },
  { path: '/board', component: () => import('../views/ScriptboardView.vue'), meta: { title: '剧本分镜', icon: '🎬' } },
  { path: '/director', component: () => import('../views/DirectorView.vue'), meta: { title: '导演', icon: '🎞️' } },
  { path: '/art', component: () => import('../views/ArtView.vue'), meta: { title: '美术工具', icon: '🎨' } },
]

export default createRouter({ history: createWebHistory(), routes })
