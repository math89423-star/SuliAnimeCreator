/** 导演组装域：单镜/整集/8-block/交付包 + 回执。不碰 Agent 大纲。 */
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import { copyText } from '../utils/clipboard'

export function useShotAssemble(getShots: () => any[], getParams: () => any, refresh: () => Promise<void>) {
  const vmap = ref<Record<string, any>>({})
  const vloading = ref(false)
  const oneLoading = ref('')
  const prompts8 = ref<any>(null)
  const loading8 = ref(false)
  const list8 = computed(() => (prompts8.value?.prompts || []) as any[])
  const bundleLoading = ref(false)
  const receiptRows = ref<any[]>([])

  async function assembleOne(s: any) {
    oneLoading.value = s.id
    try {
      const r = await api.assembleI2VA([s], getParams())
      const p = (r as any).data?.prompts?.[0]
      if (p) { vmap.value = { ...vmap.value, [s.id]: p }; copyText(p.prompt); ElMessage.success(p.mode === 'I2VA' ? 'I2VA已组装并复制' : '缺首帧，已回退T2VA并复制') }
    } finally { oneLoading.value = '' }
  }
  async function assembleAll() {
    vloading.value = true
    try {
      await refresh()
      const r = await api.assembleI2VA(getShots(), getParams())
      const m: Record<string, any> = {}
      for (const p of ((r as any).data?.prompts || [])) m[p.shot_id] = p
      vmap.value = m
      const n = Object.values(m).filter((p: any) => p.mode === 'I2VA').length
      ElMessage.success(`组装${(r as any).data.count}镜，其中${n}镜有首帧`)
    } finally { vloading.value = false }
  }
  async function assembleVEp(episodeId: string) {
    vloading.value = true
    try {
      const r = await api.assembleI2VAEpisode(episodeId, getParams())
      const m: Record<string, any> = {}
      for (const p of ((r as any).data?.prompts || [])) m[p.shot_id] = p
      vmap.value = m
      await refresh()
      ElMessage.success(`组装${(r as any).data.count}镜，共${(r as any).data.total_s}s`)
    } finally { vloading.value = false }
  }
  async function assemble8() {
    loading8.value = true
    try {
      await refresh()
      const r = await api.assemble(getShots())
      prompts8.value = (r as any).data
    } finally { loading8.value = false }
  }
  async function downloadBundle(args: { episode_id: string; engine: string; pixai_model: string; tier: string }) {
    bundleLoading.value = true
    try {
      const blob = await api.exportBundle(args)
      const url = URL.createObjectURL(new Blob([blob as any], { type: 'application/zip' }))
      const a = document.createElement('a')
      a.href = url
      a.download = `PKG-${args.episode_id}-${Date.now()}.zip`
      a.click()
      setTimeout(() => URL.revokeObjectURL(url), 5000)
      ElMessage.success('交付包已下载，拷给 L-Port 即交付')
    } catch { ElMessage.error('下载失败') }
    finally { bundleLoading.value = false }
  }
  async function loadReceipts() { try { const r = await api.receipts(); receiptRows.value = (r as any).data } catch {} }
  function copy(t: string) { copyText(t) }

  return { vmap, vloading, oneLoading, prompts8, loading8, list8, bundleLoading, receiptRows, assembleOne, assembleAll, assembleVEp, assemble8, downloadBundle, loadReceipts, copy }
}
