import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
/** 项目域：顶栏项目切换 + 当前角色 */
export const useProjectStore = defineStore('project', () => {
  const projectId = ref(localStorage.getItem('suli.projectId') || '')
  const projects = ref<any[]>([])
  const selectedCharId = ref(localStorage.getItem('suli.selectedCharId') || '')
  watch(projectId, v => { try { localStorage.setItem('suli.projectId', v || '') } catch {} })
  watch(selectedCharId, v => { try { localStorage.setItem('suli.selectedCharId', v || '') } catch {} })
  return { projectId, projects, selectedCharId }
})
