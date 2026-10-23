<!-- 方案意图编辑器：contenteditable 自由文本 + 内联 @参考N 丸子引用。
     打 @ 唤起参考图候选（缩略图 + token + 文件名），选中插入带缩略图的原子丸子；
     序列化成纯文本 token 走 v-model，载入时按 token 还原丸子。 -->
<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { refUrl, type RefImg } from '../../utils/refImage'

const props = defineProps<{ modelValue: string; refs: RefImg[] }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: string): void }>()

const editor = ref<HTMLDivElement | null>(null)

// 富文本丸子：所见即内容（contenteditable=false原子节点），光标天然对齐；
// 尺寸行内style钉死，不依赖样式表
const PILL_STYLE =
  'display:inline-flex;align-items:center;gap:3px;height:1.3em;max-height:1.3em;' +
  'padding:0 7px 0 3px;border-radius:5px;vertical-align:-0.25em;font-size:.92em;' +
  'white-space:nowrap;font-weight:600;background:rgba(99,102,241,.12);color:#6366f1;'
const PILL_IMG_STYLE =
  'width:1.15em;height:1.15em;max-width:1.15em;max-height:1.15em;flex:none;' +
  'object-fit:cover;border-radius:3px;'

const RE_REF_TOKEN = /(@参考[1-6])/g
const RE_REF_ONE = /@参考([1-6])/

function pillNode(token: string): HTMLSpanElement {
  const span = document.createElement('span')
  span.className = 'pill'
  span.contentEditable = 'false'
  span.dataset.name = token
  span.setAttribute('style', PILL_STYLE)
  const m = token.match(RE_REF_ONE)
  const r = m ? props.refs[Number(m[1]) - 1] : null
  if (r) {
    const img = document.createElement('img')
    img.src = refUrl(r)
    img.alt = ''
    img.className = 'pill-thumb'
    img.setAttribute('style', PILL_IMG_STYLE)
    img.contentEditable = 'false'
    img.draggable = false
    span.appendChild(img)
  }
  span.appendChild(document.createTextNode(token))
  return span
}

/** 编辑器 DOM → 纯文本：丸子还原成 token，BR 还原成换行。 */
function serializeNode(node: Node): string {
  if (node.nodeType === Node.TEXT_NODE) return node.textContent || ''
  if (node.nodeName === 'BR') return '\n'
  if (node instanceof HTMLElement) {
    if (node.classList.contains('pill')) return node.dataset.name || ''
    let s = ''
    node.childNodes.forEach((c) => { s += serializeNode(c) })
    if (node.nodeName === 'DIV' || node.nodeName === 'P') return s + '\n'
    return s
  }
  return ''
}

function readText(): string {
  const el = editor.value
  if (!el) return props.modelValue
  let s = ''
  el.childNodes.forEach((c) => { s += serializeNode(c) })
  return s.replace(/\n+$/, '')
}

/** 纯文本 → 编辑器 DOM：token 段落还原成丸子。 */
function renderText(text: string) {
  const el = editor.value
  if (!el) return
  el.innerHTML = ''
  const frag = document.createDocumentFragment()
  text.split('\n').forEach((line, li) => {
    if (li > 0) frag.appendChild(document.createElement('br'))
    line.split(RE_REF_TOKEN).forEach((p) => {
      if (!p) return
      if (RE_REF_ONE.test(p)) frag.appendChild(pillNode(p))
      else frag.appendChild(document.createTextNode(p))
    })
  })
  if (!frag.hasChildNodes()) frag.appendChild(document.createElement('br'))
  el.appendChild(frag)
}

// 编辑器里的内容已经和 modelValue 一致时（自己刚回写的）不重建，保光标
watch(() => props.modelValue, (v) => {
  const el = editor.value
  if (!el) return
  if (readText() === v) return
  renderText(v)
})

function insertNodesAtCaret(nodes: Node[]) {
  const el = editor.value
  if (!el) return
  el.focus()
  const sel = window.getSelection()
  let range: Range
  if (sel && sel.rangeCount && el.contains(sel.getRangeAt(0).startContainer)) {
    range = sel.getRangeAt(0)
  } else {
    range = document.createRange()
    range.selectNodeContents(el)
    range.collapse(false)
  }
  const pre = range.cloneRange()
  pre.selectNodeContents(el)
  pre.setEnd(range.startContainer, range.startOffset)
  const needLeadingSpace = !!pre.toString() && !/\s$/.test(pre.toString())
  range.deleteContents()
  const frag = document.createDocumentFragment()
  if (needLeadingSpace) frag.appendChild(document.createTextNode(' '))
  nodes.forEach((n) => frag.appendChild(n))
  const lastNode = frag.lastChild as Node | null
  range.insertNode(frag)
  const after = document.createRange()
  if (lastNode && lastNode.parentNode) after.setStartAfter(lastNode)
  else after.selectNodeContents(el)
  after.collapse(false)
  sel?.removeAllRanges()
  sel?.addRange(after)
  emit('update:modelValue', readText())
}

/** 参考图缩略图角标 @参考N 落到意图里：外部（参考图区按钮）经 ref 调它。 */
function insertToken(i: number) {
  if (i < 0 || i >= props.refs.length) return
  insertNodesAtCaret([pillNode('@参考' + (i + 1)), document.createTextNode(' ')])
}
defineExpose({ insertToken })

// ── @ 联想：光标前有 @xxx 待补全时弹出候选，↑↓选择、Enter/Tab 确认 ──
const mentionOpen = ref(false)
const mentionFilter = ref('')
const mentionIndex = ref(0)

const candidates = computed(() => {
  const list = props.refs.map((r, i) => ({
    token: '@参考' + (i + 1), sub: r.name, url: refUrl(r),
  }))
  const q = mentionFilter.value
  if (!q) return list
  return list.filter((c) => c.token.startsWith('@' + q))
})

/** 光标前的 @xxx 待补全：返回过滤词 + 待删选区。 */
function getAtQuery(): { filter: string; del: Range } | null {
  const sel = window.getSelection()
  const el = editor.value
  if (!sel || !sel.rangeCount || !el) return null
  const r = sel.getRangeAt(0)
  if (!r.collapsed || !el.contains(r.startContainer)) return null
  let node: Node | null = r.startContainer
  let offset = r.startOffset
  if (node.nodeType !== Node.TEXT_NODE) {
    const prev = offset > 0 ? node.childNodes[offset - 1] : null
    if (!prev || prev.nodeType !== Node.TEXT_NODE) return null
    node = prev
    offset = (prev.textContent || '').length
  }
  const m = ((node.textContent || '').slice(0, offset)).match(/@([\w\u4e00-\u9fa5]*)$/)
  if (!m) return null
  const del = document.createRange()
  del.setStart(node, offset - m[0].length)
  del.setEnd(node, offset)
  return { filter: m[1], del }
}

function updateMention() {
  const q = getAtQuery()
  if (!q || !props.refs.length) {
    mentionOpen.value = false
    return
  }
  mentionFilter.value = q.filter
  mentionIndex.value = 0
  mentionOpen.value = true
}

function onInput() {
  emit('update:modelValue', readText())
  updateMention()
}

function applyMention(token: string) {
  const el = editor.value
  const q = getAtQuery()
  if (!el || !q) {
    mentionOpen.value = false
    return
  }
  el.focus()
  const sel = window.getSelection()
  sel?.removeAllRanges()
  sel?.addRange(q.del)
  const frag = document.createDocumentFragment()
  frag.appendChild(pillNode(token))
  frag.appendChild(document.createTextNode(' '))
  const lastNode = frag.lastChild as Node | null
  q.del.deleteContents()
  q.del.insertNode(frag)
  const after = document.createRange()
  if (lastNode && lastNode.parentNode) after.setStartAfter(lastNode)
  else after.selectNodeContents(el)
  after.collapse(false)
  sel?.removeAllRanges()
  sel?.addRange(after)
  emit('update:modelValue', readText())
  mentionOpen.value = false
}

function onKeydown(e: KeyboardEvent) {
  if (!mentionOpen.value || !candidates.value.length) return
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    mentionIndex.value = (mentionIndex.value + 1) % candidates.value.length
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    mentionIndex.value = (mentionIndex.value - 1 + candidates.value.length) % candidates.value.length
  } else if (e.key === 'Enter' || e.key === 'Tab') {
    e.preventDefault()
    const c = candidates.value[mentionIndex.value]
    if (c) applyMention(c.token)
  } else if (e.key === 'Escape') {
    e.preventDefault()
    mentionOpen.value = false
  }
}

/** 粘贴只收纯文本（contenteditable 默认会吃富文本，丸子结构会被冲掉） */
function onPaste(e: ClipboardEvent) {
  e.preventDefault()
  const text = e.clipboardData?.getData('text/plain') || ''
  if (text) insertNodesAtCaret([document.createTextNode(text)])
}
</script>

<template>
  <div class="textarea-wrap">
    <div
      ref="editor"
      class="intent-editor"
      contenteditable="true"
      @input="onInput"
      @keydown="onKeydown"
      @click="updateMention"
      @blur="mentionOpen = false"
      @paste="onPaste"
    />
    <div v-if="mentionOpen && candidates.length" class="mention-popup">
      <div class="mention-popup-title">参考图</div>
      <button
        v-for="(c, i) in candidates"
        :key="c.token"
        :class="['mention-item', { active: i === mentionIndex }]"
        @mousedown.prevent="applyMention(c.token)"
      >
        <img v-if="c.url" :src="c.url" class="mention-thumb" alt="" />
        <span class="mention-name">{{ c.token }}</span>
        <span class="mention-sub">{{ c.sub }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.textarea-wrap { position: relative; display: block; min-width: 0 }
.intent-editor { width: 100%; box-sizing: border-box; min-height: 96px; height: 250px; max-height: 80vh; padding: 5px 11px; border: 1px solid var(--el-border-color); border-radius: var(--el-border-radius-base); font-size: 14px; line-height: 1.5; overflow-y: auto; outline: none; transition: border-color .2s; background: var(--el-fill-color-blank); resize: vertical }
.intent-editor:hover { border-color: var(--el-border-color-hover) }
.intent-editor:focus { border-color: var(--el-color-primary) }
.mention-popup { position: absolute; left: 0; bottom: 100%; z-index: 30; min-width: 220px; max-width: 340px; margin-bottom: 6px; background: var(--el-bg-color-overlay); border: 1px solid var(--el-border-color-light); border-radius: 10px; box-shadow: var(--el-box-shadow-light); padding: 6px 0 }
.mention-popup-title { font-size: 12px; color: var(--el-text-color-secondary); padding: 2px 10px 6px }
.mention-item { display: flex; align-items: center; gap: 8px; width: 100%; padding: 6px 10px; border: none; background: none; cursor: pointer; text-align: left; color: inherit }
.mention-item:hover, .mention-item.active { background: var(--el-fill-color-light) }
.mention-thumb { width: 40px; height: 40px; object-fit: cover; border-radius: 6px; flex: 0 0 auto }
.mention-name { font-size: 13px; font-weight: 600; color: var(--el-color-primary); flex: 0 0 auto }
.mention-sub { font-size: 12px; color: var(--el-text-color-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap }
</style>
