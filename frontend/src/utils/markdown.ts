/** 零依赖 mini-markdown：覆盖 Agent 大纲常用写法（标题/加粗/列表/表格/代码/引用/分割线/链接）。
 * 先转义 HTML 再套格式，v-html 直用不怕注入。不求全，只求大纲好看。
 */
function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

function inline(s: string): string {
  s = s.replace(/`([^`\n]+)`/g, '<code>$1</code>')
  s = s.replace(/\[([^\]\n]+)\]\(([^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  s = s.replace(/__([^_]+)__/g, '<strong>$1</strong>')
  s = s.replace(/(^|[\s（(])\*([^*\n]+)\*/g, '$1<em>$2</em>')
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
    // 列表（连续成组）
    if (isListItem(line)) {
      flushPara()
      const ordered = /^\s*\d+[.、]/.test(line)
      const items: string[] = []
      while (i < lines.length && isListItem(lines[i])) {
        items.push(lines[i].replace(/^\s*([-*+]\s+|\d+[.、]\s+)/, ''))
        i++
      }
      const tag = ordered ? 'ol' : 'ul'
      out.push(`<${tag}>${items.map(it => `<li>${inline(escapeHtml(it))}</li>`).join('')}</${tag}>`)
      continue
    }
    para.push(escapeHtml(t))
    i++
  }
  flushPara()
  if (inCode) out.push(`<div class="md-code-wrap"><button class="md-copy" data-copy="1" title="复制代码块">复制</button><pre><code>${escapeHtml(codeBuf.join('\n'))}</code></pre></div>`)
  return out.join('\n')
}
