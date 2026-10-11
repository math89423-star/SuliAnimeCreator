import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './styles/theme.css'
import App from './App.vue'
import router from './router'
import { useAppStore } from './stores/app'
const app = createApp(App).use(createPinia()).use(router)
router.afterEach((to) => {
  const map: any = { '': 'gallery', story: 'story', character: 'character', board: 'scriptboard', director: 'director', art: 'art' }
  const key = String(to.path).replace('/', '') || ''
  try { useAppStore().switchModule(map[key] || 'gallery') } catch {}
  document.title = `${String(to.meta.title || '工作台')} - SuliAnimeCreator`
})
app.mount('#app')
