import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
/** 分集域：当前集 + 分镜 + 右侧Agent回填信号 */
export const useEpisodeStore = defineStore('episode', () => {
  const EP_KEY = 'suli.episodeId'
  const episodeId = ref(localStorage.getItem(EP_KEY) || 'EP-DEMO01')
  watch(episodeId, v => { try { localStorage.setItem(EP_KEY, v || '') } catch {} })
  const shots = ref<any[]>([])
  const lastSavedAt = ref(0)
  function touchSaved() { lastSavedAt.value = Date.now() }
  // 右侧Agent接受并填充中央：自增序号 + 目标集号，导演/分镜页监听后刷新
  const centralApplySeq = ref(0)
  const centralApplyEpisode = ref('')
  function requestCentralApply(eid: string) {
    centralApplyEpisode.value = eid
    centralApplySeq.value += 1
  }
  return { episodeId, shots, lastSavedAt, touchSaved, centralApplySeq, centralApplyEpisode, requestCentralApply }
})
