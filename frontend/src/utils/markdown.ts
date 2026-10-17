/** 零依赖 mini-markdown：覆盖 Agent 大纲常用写法（标题/加粗/列表/任务勾选/表格/代码/引用/分割线/链接/图片/删除线/emoji图标）。
 * 先转义 HTML 再套格式，v-html 直用不怕注入。不求全，只求大纲好看。
 * 图标：unicode emoji 原样保留；:shortcode: 按下表转图标，未知保留原文。
 */
function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

const EMOJI: Record<string, string> = {
  check: '✅', cross: '❌', x: '❌', star: '⭐', fire: '🔥', warning: '⚠️',
  info: 'ℹ️', question: '❓', idea: '💡', book: '📖', film: '🎬', art: '🎨',
  music: '🎵', mic: '🎤', camera: '📷', video: '🎥', image: '🖼️', link: '🔗',
  clock: '⏰', calendar: '📅', pin: '📌', pushpin: '📌', rocket: '🚀', sparkles: '✨',
  heart: '❤️', thumbsup: '+1', thumbup: '👍', thumbsdown: '👎', clap: '👏',
  eyes: '👀', chat: '💬', memo: '📝', pencil: '✏️', plus: '➕', minus: '➖',
  gear: '⚙️', tool: '🛠️', search: '🔍', trash: '🗑️', folder: '📁', file: '📄',
  review: '🔎', pass: '✅', fail: '❌', block: '⛔', revise: '✏️', draft: '📝',
  shot: '🎬', cut: '✂️', sound: '🔊', mute: '🔇', episode: '📺', project: '📦',
  character: '🧑‍🎨', costume: '👗', first: '🥇', ref: '🖼️', upload: '📤', download: '📥',
  play: '▶️', stop: '⏹️', pause: '⏸️', ok: '👌', good: '👍', bad: '👎', tada: '🎉',
};

function emojify(s: string): string {
  return s.replace(/:([a-z0-9_+-]+):/g, (m, name: string) => {
    const k = String(name || '').toLowerCase()
    if (k === 'thumbsup' || k === '+1') return '👍'
    return (EMOJI as Record<string, string>)[k] ?? m
  })
}

function safeImgSrc(src: string): string {
  const t = String(src || '').trim()
  if (!t) return ''
  const low = t.toLowerCase()
  if (low.startsWith('javascript:') || low.startsWith('vbscript:') || low.startsWith('data:text/html')) return ''
  return t
}

function inline(s: string): string {
  // 先把行内代码抠出来占位，避免里面的 :emoji: / ~~  被误转
  const codes: string[] = []
  s = s.replace(/`([^`\n]+)`/g, (_m, c: string) => {
    codes.push(`<code>${c}</code>`)
    return `\u0000${codes.length - 1}\u0000`
  })
  // 图片 ![alt](src) —— alt/src 已是转义后文本，直接拼
  s = s.replace(/!\[([^\]\n]*)\]\(([^)\s]+)(?:\s+&quot;([^&]*?)&quot;)?\)/g, (_m, alt: string, src: string) => {
    const safe = safeImgSrc(src)
    if (!safe) return alt || ''
    const a = String(alt || '').slice(0, 120)
    return `<span class="md-img-wrap"><img class="md-img" src="${safe}" alt="${a}" loading="lazy" onerror="this.style.display='none'" /></span>`
  })
  s = s.replace(/\[([^\]\n]+)\]\(([^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  s = s.replace(/__([^_]+)__/g, '<strong>$1</strong>')
  s = s.replace(/~~([^~\n]+)~~/g, '<del>$1</del>')
  s = s.replace(/(^|[\s（(])\*([^*\n]+)\*/g, '$1<em>$2</em>')
  s = emojify(s)
  // 还原行内代码
  s = s.replace(/\u0000(\d+)\u0000/g, (_m, n: string) => codes[Number(n)] ?? '')
  return s
}

const TABLE_SEP = /^\s*\|?(\s*:?-+:?\s*\|)+\s*:?-+:?\s*\|?\s*$/

function splitRow(line: string): string[] {
  let t = line.trim()
  if (t.startsWith('|')) t = t.slice(1)
  if (t.endsWith('|')) t = t.slice(0, -1)
  return t.split('|').map(c => c.trim())
}

export function renderMarkdown(src: string): string {
  const lines = (src || '').replace(/\r\n/g, '\n').split('\n')
  const out: string[] = []
  let i = 0
  let inCode = false
  let codeBuf: string[] = []
  let para: string[] = []
  const flushPara = () => {
    if (para.length) { out.push(`<p>${inline(para.join('<br />'))}</p>`); para = [] }
  }
  const isListItem = (l: string) => /^\s*([-*+]\s+|\d+[.、]\s+)/.test(l)

  while (i < lines.length) {
    const line = lines[i]
    // 代码围栏
    if (/^\s*```/.test(line)) {
      flushPara()
      if (!inCode) { inCode = true; codeBuf = [] }
      else { inCode = false; out.push(`<div class="md-code-wrap"><button class="md-copy" data-copy="1" title="复制代码块">复制</button><pre><code>${escapeHtml(codeBuf.join('\n'))}</code></pre></div>`) }
      i++
      continue
    }
    if (inCode) { codeBuf.push(line); i++; continue }
    const t = line.trim()
    if (!t) { flushPara(); i++; continue }
    // 表格：表头 + 分隔行 + 数据行
    if (t.includes('|') && i + 1 < lines.length && TABLE_SEP.test(lines[i + 1])) {
      flushPara()
      const head = splitRow(t)
      i += 2
      const rows: string[][] = []
      while (i < lines.length && lines[i].includes('|') && lines[i].trim()) { rows.push(splitRow(lines[i])); i++ }
      const th = head.map(c => `<th>${inline(escapeHtml(c))}</th>`).join('')
      const tb = rows.map(r => `<tr>${head.map((_, k) => `<td>${inline(escapeHtml(r[k] || ''))}</td>`).join('')}</tr>`).join('')
      out.push(`<div class="md-table-wrap"><table><thead><tr>${th}</tr></thead><tbody>${tb}</tbody></table></div>`)
      continue
    }
    // 标题
    const h = t.match(/^(#{1,4})\s+(.+)/)
    if (h) { flushPara(); const lv = h[1].length; out.push(`<h${lv}>${inline(escapeHtml(h[2]))}</h${lv}>`); i++; continue }
    // 分割线
    if (/^(\*{3,}|-{3,}|_{3,})\s*$/.test(t)) { flushPara(); out.push('<hr />'); i++; continue }
    // 引用
    if (/^&gt;/.test(escapeHtml(t)) || /^>/.test(t)) {
      flushPara()
      const qs: string[] = []
      while (i < lines.length && /^\s*>/.test(lines[i])) { qs.push(lines[i].replace(/^\s*>\s?/, '')); i++ }
      out.push(`<blockquote>${qs.map(q => inline(escapeHtml(q))).join('<br />')}</blockquote>`)
      continue
    }
    // 列表（连续成组，支持 - [ ] / - [x] 任务勾选）
    if (isListItem(line)) {
      flushPara()
      const ordered = /^\s*\d+[.、]/.test(line)
      const items: string[] = []
      while (i < lines.length && isListItem(lines[i])) {
        items.push(lines[i].replace(/^\s*([-*+]\s+|\d+[.、]\s+)/, ''))
        i++
      }
      const tag = ordered ? 'ol' : 'ul'
      const lis = items.map(it => {
        const m = String(it).match(/^\[([ xX])\]\s+(.*)$/)
        if (!ordered && m) {
          const checked = m[1].toLowerCase() === 'x'
          return `<li class="md-task"><input type="checkbox" disabled${checked ? ' checked' : ''} />${inline(escapeHtml(m[2]))}</li>`
        }
        return `<li>${inline(escapeHtml(it))}</li>`
      }).join('')
      out.push(`<${tag}>${lis}</${tag}>`)
      continue
    }
    para.push(escapeHtml(t))
    i++
  }
  flushPara()
  if (inCode) out.push(`<div class="md-code-wrap"><button class="md-copy" data-copy="1" title="复制代码块">复制</button><pre><code>${escapeHtml(codeBuf.join('\n'))}</code></pre></div>`)
  return out.join('\n')
}
