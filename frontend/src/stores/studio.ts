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
  /** 本方案的水位档（tease/undress/explicit/closeup，空=常规）：agent 要按它写，不降档 */
  const tier = ref('')
  const pageMode = ref('panel')
  /** 漫画页上下文（漫画模式）：集号 / 页序 / 格序 / 大纲快照 / 上一格成图 */
  const pageCtx = ref<{ episode_id: string; index: number; panel_index: number; outline_text: string; prev_image: string } | null>(null)
  /** 漫画剧本（页/格分条）：agent 要能看见并改写它 */
  const scriptPanels = ref<{ page: number; panel: number; text: string; dialogue: string; camera: string; tier?: string; clothing_level?: string }[]>([])
  /** agent 改盘后由右栏写入：方案页据此重拉表单并显示变更卡 */
  const remoteChange = ref<{ planId: string; rows: PlanDiffRow[]; created?: boolean } | null>(null)
  /** 右栏点了别的方案会话：方案页据此切到那个方案（会话和表单必须同一个方案） */
  const planPick = ref('')
  function pickPlan(id: string) { planPick.value = id }

  function setPlan(p: {
    id?: string
    title?: string
    intent_text?: string
    engines?: string[]
    note?: string
    ref_images?: { name?: string }[]
    tier?: string
    page_mode?: string
  }) {
    planId.value = p.id || ''
    planTitle.value = p.title || ''
    intentText.value = p.intent_text || ''
    engines.value = Array.isArray(p.engines) ? [...p.engines] : []
    note.value = p.note || ''
    refNames.value = (p.ref_images || []).map(x => x?.name || '').filter(Boolean)
    tier.value = p.tier || ''
    pageMode.value = p.page_mode || 'panel'
  }

  /** 右栏发现 agent 改了方案：记下变更，方案页据此重拉并出变更卡 */
  function setRemoteChange(c: { planId: string; rows: PlanDiffRow[]; created?: boolean } | null) {
    remoteChange.value = c || null
  }

  /** 漫画页上下文（漫画模式）：右栏据此知道这是第几页第几格、大纲是什么、上一格长什么样 */
  function setPageCtx(p: { episode_id: string; index: number; panel_index: number; outline_text: string; prev_image: string } | null) {
    pageCtx.value = p || null
  }

  /** 漫画剧本（页/格分条）：右栏据此看到当前这一本的剧本，agent 照着改 */
  function setScript(panels: { page: number; panel: number; text: string; dialogue: string; camera: string; tier?: string; clothing_level?: string }[]) {
    scriptPanels.value = panels || []
  }

  /** 当前页文本块：原样贴进消息，agent 看到的就是屏幕上这份方案 */
  function contextBlock(): string {
    const pg = pageCtx.value
    const lines = [pg
      ? `页面：创作（studio）· 漫画第 ${pg.index || 0} 页 第 ${pg.panel_index || 1} 格`
      : '页面：创作（studio）· 单图']
    if (planId.value) lines.push(`方案 id：${planId.value}`)
    if (planTitle.value.trim()) lines.push(`方案标题：${planTitle.value.trim()}`)
    if (intentText.value.trim()) lines.push(`意图文本：${intentText.value.trim()}`)
    if (engines.value.length) lines.push(`目标引擎：${engines.value.join('、')}`)
    if (note.value.trim()) lines.push(`约束/改图：${note.value.trim()}`)
    if (refNames.value.length) lines.push(`参考图：${refNames.value.join('、')}`)
    if (tier.value) lines.push(`本方案水位：${tier.value}（按该档位如实写，不降档）`)
    if (pageMode.value && pageMode.value !== 'panel') lines.push(`本方案出图模式：${pageMode.value}（整页单图多格）`)
    if (pg) {
      lines.push(`漫画页：${pg.episode_id || '（未绑集号）'} 第 ${pg.index || 0} 页 第 ${pg.panel_index || 1} 格`)
      if (pg.prev_image) lines.push(`上一格成图：${pg.prev_image}`)
      if (pg.outline_text) lines.push(`本页大纲（${pg.outline_text.length}字）：\n${pg.outline_text.slice(0, 1200)}`)
    }
    if (scriptPanels.value.length) {
      lines.push(`漫画剧本（${scriptPanels.value.length} 格）：`)
      for (const s of scriptPanels.value.slice(0, 20)) {
        const bits = [s.text]
        if (s.dialogue) bits.push(`台词:${s.dialogue}`)
        if (s.camera) bits.push(s.camera)
        if (s.tier) bits.push(`水位:${s.tier}`)
        if (s.clothing_level) bits.push(`衣物:${s.clothing_level}`)
        lines.push(`  第${s.page}页 第${s.panel}格：${bits.filter(Boolean).join(' / ')}`)
      }
    }
    lines.push('（本页方案落库：POST /api/v1/art/plans，字段 id / title / intent_text / engines / ref_images[{name,path}] / note / tier / clothing_level / page_mode / page{episode_id,index,panel_index,prev_plan_id,outline_text,image}）')
    lines.push('（漫画剧本落库：POST /api/v1/art/comic-script，body {episode_id, premise, characters, style_hint, tier, panels:[{page,panel,text,dialogue,camera,note,tier,clothing_level}]}；拆格 POST /api/v1/art/comic-script/split）')
    lines.push('（L-Port 整页分镜回传落库：POST /api/v1/art/comic-plan/import，body {episode_id, panel_plan}）')
    return lines.join('\n')
  }

  return { planId, planTitle, intentText, engines, note, refNames, pageCtx, pageMode, scriptPanels, remoteChange, planPick, setPlan, setPageCtx, setScript, setRemoteChange, pickPlan, contextBlock }
})
