import { defineStore } from 'pinia'
import { ref } from 'vue'
/** 项目域：顶栏项目切换 + 当前角色 */
export const useProjectStore = defineStore('project', () => {
  const projectId = ref('')
  const projects = ref<any[]>([])
  const selectedCharId = ref('')
  return { projectId, projects, selectedCharId }
})
