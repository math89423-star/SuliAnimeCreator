/** 单图Agent导演域：传图 → 出大纲 → 转草案。只管大纲流，不管组装。 */
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

export function useAgentDirect(getEpisodeId: () => string, afterShots: () => Promise<void>) {
  const agentFileEl = ref<HTMLInputElement | null>(null)
  const agentImg = ref<{ name: string; path: string; url: string } | null>(null)
  const agentAsk = ref('')
  const agentTotal = ref(15)
  const agentLoading = ref(false)
  const agentProgress = ref('')
  const agentAnswer = ref('')
  const agentAborter = ref<AbortController | null>(null)
  const outline = ref({ md: '', image: '' })

  async function loadOutline() {
    try {
      const r = await api.getOutline(getEpisodeId())
      outline.value = { md: (r as any).data.outline_md || '', image: (r as any).data.outline_image || '' }
    } catch {}
  }
  async function onAgentFile(e: any) {
    const f = e.target.files?.[0]
    e.target.value = ''
    if (!f) return
    if (!f.type.startsWith('image/')) return ElMessage.warning('只要图片')
    if (f.size > 10 * 1024 * 1024) return ElMessage.warning('图片超过10MB')
    try {
      const d = await api.uploadFile(f)
      const row = (d as any)?.data || d
      agentImg.value = { name: f.name, path: row.path, url: row.url }
      agentAnswer.value = ''
    } catch { ElMessage.error('上传失败，后端未起？') }
  }
  function stopAgent() { agentAborter.value?.abort() }

  async function runBrief(brief: string, progressing: string, doneHint: string, after?: () => Promise<void>) {
    agentLoading.value = true
    agentProgress.value = '建会话…'
    agentAnswer.value = ''
    try {
      await api.dshEnsure('episode', getEpisodeId())
    } catch { ElMessage.error('Agent会话建失败，后端未起？'); agentLoading.value = false; return }
    agentProgress.value = progressing
    const ac = new AbortController()
    agentAborter.value = ac
    try {
      let done: any = null
      let errMsg = ''
      await api.dshRunStream(
        { scope: 'episode', key: getEpisodeId(), message: brief },
        (ev, d) => {
          if (ev === 'dsh') agentProgress.value = `${progressing}事件 ${d.n || ''}`
          else if (ev === 'done') done = d
          else if (ev === 'error') errMsg = (d as any).msg || '调用失败'
        },
        ac.signal,
      )
      if (done) {
        agentAnswer.value = done.answer || '(空回包)'
        agentProgress.value = doneHint
        if (after) await after()
      } else {
        agentAnswer.value = '❌ ' + (errMsg || '流中断')
        agentProgress.value = ''
      }
    } finally {
      agentLoading.value = false
      agentAborter.value = null
    }
  }

  return { agentFileEl, agentImg, agentAsk, agentTotal, agentLoading, agentProgress, agentAnswer, agentAborter, outline, loadOutline, onAgentFile, stopAgent, runBrief, afterShots }
}
