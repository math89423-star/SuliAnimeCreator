import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { PlanDiffRow } from '../utils/planDiff'
/** 单图创作域：当前方案快照（右侧 Agent 按它做页面感知） */
export const useStudioStore = defineStore('studio', () => {
  const planId = ref('')
  const planTitle = ref('')
  const intentText = ref('')
  const engines = ref<string[]>([])
  const note = ref('')
  const refNames = ref<string[]>([])
  /** agent 改盘后由右栏写入：方案页据此重拉表单并显示变更卡 */
  const remoteChange = ref<{ planId: string; rows: PlanDiffRow[]; created?: boolean } | null>(null)

  function setPlan(p: {
    id?: string
    title?: string
    intent_text?: string
    engines?: string[]
    note?: string
    ref_images?: { name?: string }[]
  }) {
    planId.value = p.id || ''
    planTitle.value = p.title || ''
    intentText.value = p.intent_text || ''
    engines.value = Array.isArray(p.engines) ? [...p.engines] : []
    note.value = p.note || ''
    refNames.value = (p.ref_images || []).map(x => x?.name || '').filter(Boolean)
  }

  /** 右栏发现 agent 改了方案：记下变更，方案页据此重拉并出变更卡 */
  function setRemoteChange(c: { planId: string; rows: PlanDiffRow[]; created?: boolean } | null) {
    remoteChange.value = c || null
  }

  /** 当前页文本块：原样贴进消息，agent 看到的就是屏幕上这份方案 */
  function contextBlock(): string {
    const lines = ['页面：单图创作（studio）']
    if (planId.value) lines.push(`方案 id：${planId.value}`)
    if (planTitle.value.trim()) lines.push(`方案标题：${planTitle.value.trim()}`)
    if (intentText.value.trim()) lines.push(`意图文本：${intentText.value.trim()}`)
    if (engines.value.length) lines.push(`目标引擎：${engines.value.join('、')}`)
    if (note.value.trim()) lines.push(`约束/改图：${note.value.trim()}`)
    if (refNames.value.length) lines.push(`参考图：${refNames.value.join('、')}`)
    lines.push('（本页方案落库：POST /api/v1/art/plans，字段 id / title / intent_text / engines / ref_images[{name,path}] / note）')
    return lines.join('\n')
  }

  return { planId, planTitle, intentText, engines, note, refNames, remoteChange, setPlan, setRemoteChange, contextBlock }
})
