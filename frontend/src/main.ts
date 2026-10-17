import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './styles/theme.css'
// 编程式 API（ElMessage/ElMessageBox）是手写 import，resolver 不会自动带样式，必须显式引
import 'element-plus/theme-chalk/el-message.css'
import 'element-plus/theme-chalk/el-message-box.css'
import App from './App.vue'
import router from './router'
import { useAppStore } from './stores/app'
import { useSettingsStore } from './stores/settings'
const app = createApp(App).use(createPinia()).use(router)
router.afterEach((to) => {
  const map: any = { '': 'gallery', story: 'story', character: 'character', board: 'scriptboard', director: 'director', art: 'art', settings: 'settings' }
  const key = String(to.path).replace('/', '') || ''
  try { useAppStore().switchModule(map[key] || 'gallery') } catch {}
  try { useSettingsStore().apply() } catch {}
  document.title = `${String(to.meta.title || '工作台')} - SuliAnimeCreator`
})
app.mount('#app')
