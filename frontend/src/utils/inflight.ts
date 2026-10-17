/** 并发去重：同一 key 的在途 Promise 复用，settle 后自动移除。
 * 用在目录/列表类请求上：页面重挂载（顶栏项目/集号变化会换 router-view key）、
 * 连点刷新时都只发一次请求，不再堆出一串慢请求把按钮拖在转圈状态。 */
const inflight = new Map<string, Promise<unknown>>()

export function once<T>(key: string, fn: () => Promise<T>): Promise<T> {
  const hit = inflight.get(key)
  if (hit) return hit as Promise<T>
  const p = fn()
  inflight.set(key, p)
  p.catch(() => {}).finally(() => { inflight.delete(key) })
  return p
}
