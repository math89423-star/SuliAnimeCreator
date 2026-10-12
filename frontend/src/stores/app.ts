/** app 门面：保持旧 `useAppStore` 可用。新代码请按域直引 useProjectStore/useEpisodeStore/useUiStore。 */
import { defineStore, storeToRefs } from 'pinia'
import { useProjectStore } from './project'
import { useEpisodeStore } from './episode'
import { useUiStore } from './ui'

export const useAppStore = defineStore('app', () => {
  const project = useProjectStore()
  const episode = useEpisodeStore()
  const ui = useUiStore()
  const { projectId, projects, selectedCharId } = storeToRefs(project)
  const { episodeId, shots, lastSavedAt, centralApplySeq, centralApplyEpisode } = storeToRefs(episode)
  const { module, health, leftCollapsed, rightCollapsed, quickRef } = storeToRefs(ui)
  return {
    module, episodeId, projectId, projects, selectedCharId, lastSavedAt, shots, health,
    leftCollapsed, rightCollapsed, quickRef, centralApplySeq, centralApplyEpisode,
    touchSaved: episode.touchSaved,
    switchModule: ui.switchModule, toggleLeft: ui.toggleLeft, toggleRight: ui.toggleRight,
    openQuickRef: ui.openQuickRef, closeQuickRef: ui.closeQuickRef, minimizeQuickRef: ui.minimizeQuickRef,
    requestCentralApply: episode.requestCentralApply,
  }
})
