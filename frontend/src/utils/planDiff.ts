/** 方案变更对比：逐字段给旧值/新值，参考图按文件名比增删。
 *  基准统一是后端方案字段（title/intent_text/engines/ref_images/note/tier/clothing_level），
 *  before 可以是写盘前快照（后端 prev）或回合前的方案详情。
 */

import { tierLabel } from './tier'

export interface PlanDiffRow {
  key: string
  label: string
  before: string
  after: string
}

const TEXT_FIELDS: { key: string; label: string }[] = [
  { key: 'title', label: '标题' },
  { key: 'intent_text', label: '意图' },
  // note（备注）：创作页没有编辑口，右栏 agent 仍可写入——变更卡是它唯一的可见渠道
  { key: 'note', label: '备注' },
]

function text(v: any): string {
  return String(v ?? '').trim()
}

function engineText(v: any): string {
  return Array.isArray(v) ? v.map(x => String(x || '')).filter(Boolean).join('、') : ''
}

/** 水位档显示：空 = 常规 */
function tierText(v: any): string {
  const k = String(v ?? '').trim()
  return k ? tierLabel(k) : '常规'
}

export function refNames(v: any): string[] {
  if (!Array.isArray(v)) return []
  return v.map(x => String((x as any)?.name || '')).filter(Boolean)
}

function clip(s: string, n = 240): string {
  return s.length > n ? s.slice(0, n) + '…' : s
}

/** 两份方案状态之差（空数组 = 没变）。 */
export function diffPlanRows(before: any, after: any): PlanDiffRow[] {
  const b = before || {}
  const a = after || {}
  const rows: PlanDiffRow[] = []
  for (const f of TEXT_FIELDS) {
    const bv = text(b[f.key])
    const av = text(a[f.key])
    if (bv === av) continue
    rows.push({ key: f.key, label: f.label, before: clip(bv), after: clip(av) })
  }
  const be = engineText(b.engines)
  const ae = engineText(a.engines)
  if (be !== ae) rows.push({ key: 'engines', label: '目标引擎', before: be, after: ae })
  const bt = tierText(b.tier)
  const at = tierText(a.tier)
  if (bt !== at) rows.push({ key: 'tier', label: '水位', before: bt, after: at })
  const bc = text(b.clothing_level)
  const ac = text(a.clothing_level)
  if (bc !== ac) rows.push({ key: 'clothing_level', label: '衣物档', before: bc, after: ac })
  const bn = refNames(b.ref_images)
  const an = refNames(a.ref_images)
  const added = an.filter(n => !bn.includes(n))
  const removed = bn.filter(n => !an.includes(n))
  if (added.length) rows.push({ key: 'ref_add', label: '参考图', before: '', after: added.join('\n') })
  if (removed.length) rows.push({ key: 'ref_del', label: '参考图', before: removed.join('\n'), after: '' })
  return rows
}

/** 有基准才比：没有改前快照 = 没有变更可比（别把「无基准」当成「全字段新增」）。 */
export function planChangeRows(before: any, after: any): PlanDiffRow[] {
  if (!before) return []
  return diffPlanRows(before, after)
}
