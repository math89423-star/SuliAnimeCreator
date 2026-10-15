import { createRouter, createWebHistory } from 'vue-router'

export const routes = [
  { path: '/', component: () => import('../views/GalleryView.vue'), meta: { title: '展览', icon: 'House' } },
  { path: '/story', component: () => import('../views/StoryView.vue'), meta: { title: '故事', icon: 'Reading' } },
  { path: '/character', component: () => import('../views/CharacterView.vue'), meta: { title: '角色', icon: 'User' } },
  { path: '/director', component: () => import('../views/DirectorView.vue'), meta: { title: '导演', icon: 'VideoCamera' } },
  { path: '/board', component: () => import('../views/ScriptboardView.vue'), meta: { title: '剧本分镜', icon: 'Film' } },
  { path: '/traffic', component: () => import('../views/TrafficView.vue'), meta: { title: '投流批量', icon: 'Present' } },
  { path: '/art', component: () => import('../views/ArtView.vue'), meta: { title: '美术工具', icon: 'Picture' } },
  { path: '/settings', component: () => import('../views/SettingsView.vue'), meta: { title: '设置', icon: 'Setting' } },
]

export default createRouter({ history: createWebHistory(), routes })
