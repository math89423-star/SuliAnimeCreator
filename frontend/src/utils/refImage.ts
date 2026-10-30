export type RefImg = { name: string; path: string; url: string }

/** 参考图地址：优先 url；只存了 path/name 时按 basename 兜底（/api/images/<name>）。 */
export function refUrl(r: RefImg): string {
  if (!r) return ''
  if (r.url) return r.url
  const base = String(r.path || r.name || '').replace(/\\/g, '/').split('/').pop() || ''
  return base ? `/api/images/${encodeURIComponent(base)}` : ''
}
