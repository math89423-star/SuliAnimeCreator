/** 水位档与衣物档（与后端 / L-Port comic_page_diverge / skills/video/nsfw-directing 同一套） */

export interface TierOpt {
  value: string
  label: string
}

/** 四档水位：tease 暗示 / undress 半露 / explicit 直白 / closeup 特写 */
export const TIERS: TierOpt[] = [
  { value: 'tease', label: '暗示' },
  { value: 'undress', label: '半露' },
  { value: 'explicit', label: '直白' },
  { value: 'closeup', label: '特写' },
]

/** 衣物档 L0-L4：L0 完整 → L4 全裸（跨格只许收紧，不许倒退） */
export const CLOTH: string[] = ['L0', 'L1', 'L2', 'L3', 'L4']

export function tierLabel(t: string): string {
  return TIERS.find(x => x.value === t)?.label || t
}
