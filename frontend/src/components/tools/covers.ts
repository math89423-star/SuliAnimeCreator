// 美术页卡片封面：全部取自各工具内部的真实资产（非 emoji），来源见各条注释。
export type ToolCover =
  | { kind: 'svg'; svg: string }
  | { kind: 'strip'; hexes: string[] }
  | { kind: 'specimen'; title: string; chips: string[]; dots?: string[] }
  | { kind: 'img'; src: string; alt: string }

/* ---------- SVG 基础（与两工具内常量一致：INK #4a4238 / RED #c0392b） ---------- */
const INK = '#4a4238'
const RED = '#c0392b'
const FILL = '#e9e2d6'
const DIM = 'rgba(74,66,56,.12)'

/* 构图手册 figure 剪影（CompositionCamera.vue figure() 原样） */
const FIGURE = `<g transform="translate(100,70)" opacity="1" stroke="${INK}" stroke-width="1.8" fill="${FILL}" stroke-linejoin="round">
    <circle cx="0" cy="-40" r="10"/>
    <path d="M-8 -24 Q0 -31 8 -24 L6 8 L-6 8 Z"/>
    <path d="M-7 -22 L-13 6 M7 -22 L13 6"/>
    <path d="M-3.5 8 L-4.5 50 M3.5 8 L4.5 50"/>
  </g>`

/* 构图手册：shotSvg('bust') 原样复刻（CompositionCamera.vue:1182-1200，半身像取景框） */
const CAMERA_BUST = `<svg viewBox="0 0 200 130" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:100%">` +
  FIGURE +
  `<rect x="0" y="0" width="200" height="10" fill="${DIM}"/>` +
  `<rect x="0" y="72" width="200" height="58" fill="${DIM}"/>` +
  `<rect x="0" y="10" width="66" height="62" fill="${DIM}"/>` +
  `<rect x="134" y="10" width="66" height="62" fill="${DIM}"/>` +
  `<rect x="66" y="10" width="68" height="62" rx="4" fill="none" stroke="${RED}" stroke-width="1.8"/></svg>`

/* 镜头语法：demo('push') 原样复刻（ShotGrammar.vue:134-139，push in 相机前进） */
const GRAMMAR_PUSH = `<svg viewBox="0 0 220 132" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:100%">` +
  `<defs><marker id="arw" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6 Z" fill="${RED}"/></marker></defs>` +
  `<line x1="14" y1="114" x2="206" y2="114" stroke="${INK}" stroke-width="1.4"/>` +
  `<g transform="translate(130,66) scale(0.62)" stroke="${INK}" stroke-width="2.4" fill="${FILL}"><circle cx="0" cy="-40" r="10"/><path d="M-8 -24 Q0 -31 8 -24 L6 8 L-6 8 Z"/><path d="M-7 -22 L-13 6 M7 -22 L13 6"/><path d="M-3.5 8 L-4.5 50 M3.5 8 L4.5 50"/></g>` +
  `<g transform="translate(40,60)"><rect x="-13" y="-8" width="23" height="15" rx="3" fill="#fff" stroke="${INK}" stroke-width="1.6"/><circle cx="8" cy="0" r="4.5" fill="${RED}" opacity=".85"/></g>` +
  `<path d="M52 60 L104 60" fill="none" stroke="${RED}" stroke-width="1.8" stroke-dasharray="5 3" marker-end="url(#arw)"/>` +
  `<circle r="4.2" fill="${RED}" opacity=".9"><animateMotion path="M52 60 L104 60" dur="1.8s" repeatCount="indefinite"/></circle>` +
  `<text x="14" y="18" font-size="9.5" fill="#8d8173" font-family="sans-serif">push in 相机前进·背景视差</text></svg>`

export const TOOL_COVERS: Record<string, ToolCover> = {
  // 构图机位：半身像取景框 SVG（工具内景别"半身像"bust 条目同款）
  'composition-camera': { kind: 'svg', svg: CAMERA_BUST },
  // 服装穿搭：首个流派"学院 JK"真实配图（public/tools/costume/0.jpg，脚本补全）
  'costume': { kind: 'img', src: '/tools/costume/0.jpg', alt: '学院JK' },
  // 配色：红系前 8 个真实色值（PaletteTool.vue DATA 红系）
  'palette': { kind: 'strip', hexes: ['#FF0000', '#E34234', '#FF2400', '#DC143C', '#800020', '#CB4154', '#FD5E53', '#DE3163'] },
  // 花语：首花"樱花"真实实物图（public/tools/flowers/cherry_blossoms.jpg，脚本补全）
  'flowers': { kind: 'img', src: '/tools/flowers/cherry_blossoms.jpg', alt: '樱花' },
  // 取名："清冷疏离"池前 5 个真实单字（NamingTool.vue:142 CN_POOLS）
  'naming': { kind: 'specimen', title: '凛', chips: ['霜', '澈', '寂', '雪'] },
  // 镜头语法：push in 机位前进 SVG（工具内运镜"push"条目同款）
  'shot-grammar': { kind: 'svg', svg: GRAMMAR_PUSH },
  // 分级：模型分流真实 cover 徽（NsfwGuide.vue:261-279）
  'nsfw-guide': { kind: 'specimen', title: 'Pony', chips: ['Ill', 'SDXL', 'Flux', 'Neg'] },
}

export const FALLBACK_COVER: ToolCover = { kind: 'specimen', title: '工', chips: [] }

export function coverOf(id: string): ToolCover {
  return TOOL_COVERS[id] || FALLBACK_COVER
}
