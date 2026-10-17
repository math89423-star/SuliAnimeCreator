/** 对白角色名（cast）本地记忆：故事页点名 → 大纲/剧本生成共用。留空=后端自动取角。 */
export const CAST_KEY = 'suli.story.cast'

export function castNames(raw: string): string[] {
  return String(raw || '').split(/[，,、]/).map(s => s.trim()).filter(Boolean)
}

export function loadCastInput(): string {
  try { return localStorage.getItem(CAST_KEY) || '' } catch { return '' }
}

export function saveCastInput(raw: string): string[] {
  const names = castNames(raw)
  try {
    if (names.length) localStorage.setItem(CAST_KEY, raw.trim())
    else localStorage.removeItem(CAST_KEY)
  } catch {}
  return names
}
