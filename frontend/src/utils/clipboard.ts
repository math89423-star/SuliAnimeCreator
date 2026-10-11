import { ElMessage } from 'element-plus'
export async function copyText(t: string) {
  try {
    await navigator.clipboard.writeText(t)
    ElMessage.success('已复制')
  } catch {
    const ta = document.createElement('textarea')
    ta.value = t
    document.body.appendChild(ta)
    ta.select()
    try { document.execCommand('copy'); ElMessage.success('已复制') }
    catch { ElMessage.error('复制失败，请手动选择') }
    document.body.removeChild(ta)
  }
}
